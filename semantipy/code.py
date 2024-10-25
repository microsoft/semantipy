"""WIP: Code related semantics and semantic operations."""

import inspect
import typing
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Optional

from pydantic import ConfigDict

from semantipy.semantics import Text, SemanticModel


class PythonFunction(SemanticModel):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    entrypoint: Text
    content: Text
    intent: Optional[Text] = None

    @staticmethod
    def _execute_code(code: str, fn_name: str) -> Callable[..., Any]:
        """Execute the code and return the defined function within the code."""
        globals_ = {}

        globals_.update({"typing": typing})
        globals_.update({name: getattr(typing, name) for name in dir(typing)})

        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp:
            temp.write(code)

        compiled = compile(code, temp.name, "exec")
        exec(compiled, globals_)

        if fn_name not in globals_:
            raise NameError(f"Function '{fn_name}' not found in the code execution result.")
        return globals_[fn_name]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(content={self.content!r}, entrypoint={self.entrypoint!r}, intent={self.intent!r})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, PythonFunction)
            and self.content == other.content
            and self.entrypoint == other.entrypoint
            and self.intent == other.intent
        )

    def signature(self) -> inspect.Signature:
        return inspect.signature(self._execute_code(self.content, self.entrypoint))

    def __call__(self, *args, **kwargs):
        program = self._execute_code(self.content, self.entrypoint)
        return program(*args, **kwargs)
