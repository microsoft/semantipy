from __future__ import annotations

__all__ = ["apply", "resolve", "cast", "diff"]

from typing import TypeVar, Callable, overload

from semantipy.dispatch_utils import semantic_function_dispatch
from semantipy.semantics import Semantics, Text
from semantipy.renderer import Renderer

from .base import semantipy_op
from .context import context


SemanticTypeA = TypeVar("SemanticTypeA", bound=Semantics)
SemanticTypeB = TypeVar("SemanticTypeB", bound=Semantics)


@overload
def apply(s: SemanticTypeA, changes: Semantics, /) -> SemanticTypeA: ...


@overload
def apply(s: SemanticTypeA, index: Semantics, changes: Semantics, /) -> SemanticTypeA: ...


def _apply_preprocessor(func: Callable, s: Semantics, index_or_changes: Semantics, changes: Semantics | None = None) -> dict:
    if changes is None:
        return {"s": s, "changes": index_or_changes}
    else:
        return {"s": s, "index": index_or_changes, "changes": changes}


@semantipy_op(preprocessor=_apply_preprocessor)
def apply(s: SemanticTypeA, index_or_changes: Semantics, changes: Semantics | None = None, /) -> SemanticTypeA:
    raise NotImplementedError()


@semantipy_op
def resolve(s: Semantics, target_type: type[SemanticTypeA] | None = None) -> SemanticTypeA:
    """Compute the value of a semantic expression.

    Examples of semantic expressions:

    1. Constructing a unit test for a specific function.
    2. Computing the value of a mathematical expression.
    3. Answering the factual question, e.g., "What is the birth date of George Washington?"
    4. Generating a report based on a set of data.
    """
    raise NotImplementedError()


@semantipy_op
def cast(s: Semantics, target_type: type[SemanticTypeA], renderer: Renderer | None = None) -> SemanticTypeA:
    """Cast a semantic object to a different type.
    The operation does not change the semantics of the object.

    Based on the implementation, it may add or change some information to the original object.
    For example, casting a `Text` object to a `PythonFunction` object may generate code solely based on little information.
    It's recommended to use `evaluate` in this case for clarity.
    It's up to the implementation to decide the extent to which the object can be changed.
    """
    raise NotImplementedError()


@semantipy_op
def diff(s: Semantics, t: Semantics) -> Semantics:
    raise NotImplementedError()
