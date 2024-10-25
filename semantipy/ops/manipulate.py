from __future__ import annotations

__all__ = ["apply", "resolve", "cast", "diff", "select", "select_iter", "split", "combine"]

import functools
from typing import TypeVar, Callable, Iterable, overload

from semantipy.semantics import Text, Semantics

from .base import semantipy_op, SemanticOperationRequest


SemanticTypeA = TypeVar("SemanticTypeA", bound=Semantics)
SemanticTypeB = TypeVar("SemanticTypeB", bound=Semantics)


@overload
def apply(s: SemanticTypeA, changes: Semantics | str, /) -> SemanticTypeA: ...


@overload
def apply(s: SemanticTypeA, where: Semantics | str, changes: Semantics | str, /) -> SemanticTypeA: ...


@overload
def apply(s: str, changes: Semantics | str, /) -> Text: ...


@overload
def apply(s: str, where: Semantics | str, changes: Semantics | str, /) -> Text: ...


def _apply_preprocessor(func, s, where_or_changes, changes=None) -> SemanticOperationRequest:
    if changes is None:
        return SemanticOperationRequest(operator=func, operand=s, guest_operand=where_or_changes)
    else:
        return SemanticOperationRequest(operator=func, operand=s, guest_operand=changes, index=where_or_changes)


@semantipy_op(preprocessor=_apply_preprocessor)
def apply(s, where_or_changes, changes=None, /):
    """Apply changes to a semantic object.

    Apply comes with two signatures:

    1. `apply(s: SemanticType, changes: Semantics | str) -> SemanticType`
    2. `apply(s: SemanticType, where: Semantics | str, changes: Semantics | str) -> SemanticType`
    """
    raise NotImplementedError()


@overload
def resolve(s: Semantics | str, return_type: type[SemanticTypeA]) -> SemanticTypeA: ...


@overload
def resolve(s: Semantics | str) -> Semantics: ...


def _s_and_return_type_preprocessor(func, s, return_type=None) -> SemanticOperationRequest:
    return SemanticOperationRequest(operator=func, operand=s, return_type=return_type)


@semantipy_op(preprocessor=_s_and_return_type_preprocessor)
def resolve(s: Semantics, return_type: type[SemanticTypeA] | None = None) -> SemanticTypeA:
    """Compute the value of a semantic expression.

    Examples of semantic expressions:

    1. Constructing a unit test for a specific function.
    2. Computing the value of a mathematical expression.
    3. Answering the factual question, e.g., "What is the birth date of George Washington?"
    4. Generating a report based on a set of data.
    """
    raise NotImplementedError()


@semantipy_op(preprocessor=_s_and_return_type_preprocessor)
def cast(s: Semantics | str, return_type: type[SemanticTypeA]) -> SemanticTypeA:
    """Cast a semantic object to a different type.
    The operation does not change the semantics of the object.

    Based on the implementation, it may add or change some information to the original object.
    For example, casting a `Text` object to a `PythonFunction` object may generate code solely based on little information.
    It's recommended to use `evaluate` in this case for clarity.
    It's up to the implementation to decide the extent to which the object can be changed.
    """
    raise NotImplementedError()


@semantipy_op
def diff(s: Semantics | str, t: Semantics | str) -> Semantics:
    """Compute the difference between two semantic objects."""
    raise NotImplementedError()


def _select_preprocessor(
    func, s, selector_or_return_type, return_type=None, return_iterable=False
) -> SemanticOperationRequest:
    if return_type is not None:
        return SemanticOperationRequest(
            operator=func,
            operand=s,
            guest_operand=selector_or_return_type,
            return_type=return_type,
            return_iterable=return_iterable,
        )
    elif isinstance(selector_or_return_type, type):
        if return_iterable:
            raise ValueError("Selector cannot be a return type when return_iterable is True.")
        return SemanticOperationRequest(
            operator=func, operand=s, return_type=selector_or_return_type, return_iterable=return_iterable
        )
    else:
        return SemanticOperationRequest(
            operator=func, operand=s, guest_operand=selector_or_return_type, return_iterable=return_iterable
        )


@overload
def select(s: Semantics | str, return_type: type[SemanticTypeA]) -> SemanticTypeA: ...


@overload
def select(s: Semantics | str, selector: Semantics | str) -> Semantics: ...


@overload
def select(s: Semantics | str, selector: Semantics | str, return_type: type[SemanticTypeA]) -> SemanticTypeA: ...


@semantipy_op(preprocessor=_select_preprocessor)
def select(s, selector_or_return_type, return_type=None, /) -> Semantics:
    """
    Selects elements from the given input based on the provided selector or return type.

    The selector can be a semantic object or a string that specifies the criteria for selection.
    Alternatively, a return type can be provided to indicate the type of elements to be selected.
    If both a selector and a return type are provided, the function will use the selector to find
    the elements and then return them in the specified return type.
    """
    raise NotImplementedError()


@overload
def select_iter(s: Semantics | str, selector: Semantics | str) -> Iterable[Semantics]: ...


@overload
def select_iter(
    s: Semantics | str, selector: Semantics | str, return_type: type[SemanticTypeA]
) -> Iterable[SemanticTypeA]: ...


@semantipy_op(preprocessor=functools.partial(_select_preprocessor, return_iterable=True))
def select_iter(s, selector, return_type=None, /) -> Iterable[Semantics]:
    """
    Selects and iterates over elements based on a selector or return type.

    Similar to `select`, but returns an iterable of elements instead of a single element.
    """
    raise NotImplementedError()


@overload
def split(s: Semantics | str, selector: Semantics | str) -> Iterable[Semantics]: ...


@overload
def split(
    s: Semantics | str, selector: Semantics | str, return_type: type[SemanticTypeA]
) -> Iterable[SemanticTypeA]: ...


@semantipy_op(preprocessor=functools.partial(_select_preprocessor, return_iterable=True))
def split(s, selector, return_type=None, /) -> Iterable[Semantics]:
    """Split the input into multiple elements based on the provided selector or return type.

    This function is similar to `select_iter`, but the selector is used to match the cutted parts rather than the chosen parts.
    """
    raise NotImplementedError()


@semantipy_op
def combine(*semantics: Semantics | str) -> Semantics:
    """
    This function takes multiple semantic objects or strings and combines them into a single semantic object.
    The input can be a mix of `Semantics` objects and strings.
    The function  is designed to handle various types of semantic inputs and merge them into a cohesive whole.
    """
    raise NotImplementedError()
