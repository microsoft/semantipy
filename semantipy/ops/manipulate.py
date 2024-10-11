from __future__ import annotations

__all__ = ["apply", "resolve", "cast", "diff"]

from typing import TypeVar, Callable, overload

from semantipy.semantics import TextOrSemantics, Text, Semantics, SemanticModel, SemanticType
from semantipy.renderer import Renderer

from .base import semantipy_op
from .context import context


SemanticTypeA = TypeVar("SemanticTypeA", bound=Semantics)
SemanticTypeB = TypeVar("SemanticTypeB", bound=Semantics)


class ApplyArgs(SemanticModel):
    s: TextOrSemantics
    changes: TextOrSemantics
    where: TextOrSemantics | None = None


@overload
def apply(s: SemanticTypeA, changes: Semantics | str, /) -> SemanticTypeA: ...


@overload
def apply(s: SemanticTypeA, where: Semantics | str, changes: Semantics | str, /) -> SemanticTypeA: ...


@overload
def apply(s: str, changes: Semantics | str, /) -> Text: ...


@overload
def apply(s: str, where: Semantics | str, changes: Semantics | str, /) -> Text: ...


def _apply_preprocessor(func, s, where_or_changes, changes=None) -> ApplyArgs:
    if changes is None:
        return ApplyArgs(s=s, changes=where_or_changes)
    else:
        return ApplyArgs(s=s, where=where_or_changes, changes=changes)


@semantipy_op(preprocessor=_apply_preprocessor)
def apply(s, where_or_changes, changes=None, /):
    raise NotImplementedError()


class ResolveArgs(SemanticModel):
    s: TextOrSemantics
    target_type: type[Semantics]


@overload
def resolve(s: Semantics | str, target_type: type[SemanticTypeA]) -> SemanticTypeA: ...


@overload
def resolve(s: Semantics | str) -> Semantics: ...


@semantipy_op(standard_param_type=ResolveArgs)
def resolve(s: Semantics, target_type: type[SemanticTypeA] | None = None) -> SemanticTypeA:
    """Compute the value of a semantic expression.

    Examples of semantic expressions:

    1. Constructing a unit test for a specific function.
    2. Computing the value of a mathematical expression.
    3. Answering the factual question, e.g., "What is the birth date of George Washington?"
    4. Generating a report based on a set of data.
    """
    raise NotImplementedError()


class CastArgs(SemanticModel):
    s: TextOrSemantics
    target_type: type[Semantics]


@semantipy_op(standard_param_type=CastArgs)
def cast(s: Semantics | str, target_type: type[SemanticTypeA]) -> SemanticTypeA:
    """Cast a semantic object to a different type.
    The operation does not change the semantics of the object.

    Based on the implementation, it may add or change some information to the original object.
    For example, casting a `Text` object to a `PythonFunction` object may generate code solely based on little information.
    It's recommended to use `evaluate` in this case for clarity.
    It's up to the implementation to decide the extent to which the object can be changed.
    """
    raise NotImplementedError()


class DiffArgs(SemanticModel):
    s: TextOrSemantics
    t: TextOrSemantics


@semantipy_op(standard_param_type=DiffArgs)
def diff(s: Semantics | str, t: Semantics | str) -> Semantics:
    """Compute the difference between two semantic objects."""
    raise NotImplementedError()
