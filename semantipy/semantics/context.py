from __future__ import annotations

__all__ = ["RoleContext", "Strategy", "TextualStrategy", "Guard", "Guards"]

from typing import Dict, List, Any, Callable
from typing_extensions import Self

from pydantic import model_validator, Field

from .base import Semantics
from .element import Text
from .container import SemanticModel, SemanticContent, SemanticRootModel


class RoleContext(SemanticContent):
    """Functional context provides an extra "role", which implies what the context is used for."""
    role: Semantics


class Strategy(Semantics):
    """Strategy is a hint for compiler about how the operator should be executed.

    Since lots of operators are basically LLM-centered, the strategy can be thought of
    as a prompt engineering hint, which can effectively optimize the prompt.
    """


class TextualStrategy(Text, Strategy):
    """This is currently the only available kind of strategy."""


class Guard(SemanticModel):
    input: Dict[str, Any]
    """Input case."""
    expected: Dict[str, Any] | Any | None = Field(default=None)
    """If provided, the output must match this."""
    checker: Callable[[Any, Guard], bool] | None = Field(default=None)
    """Receives the output and the guard itself, returns True if the output is valid."""

    def check(self, output: Any) -> bool:
        if self.checker is not None:
            return self.checker(output, self)
        else:
            return output == self.expected

    @model_validator(mode="after")
    def check_expected_or_checker(self) -> Self:
        if self.expected is None and self.checker is None:
            raise ValueError("either expected or checker must be provided")
        return self


class Guards(SemanticRootModel):
    root: List[Guard]

    def append(self, guard: Guard):
        if not isinstance(guard, Guard):
            raise TypeError(f"Expected Guard, but got {type(guard)}")
        self.root.append(guard)
        return self

    def extend(self, guards: List[Guard] | Guards):
        if isinstance(guards, Guards):
            guards = guards.root
        if not isinstance(guards, list):
            raise TypeError(f"Expected List[Guard], but got {type(guards)}")
        if not all(isinstance(guard, Guard) for guard in guards):
            raise TypeError(f"Expected input to be a list of Guard")
        self.root.extend(guards)
        return self
