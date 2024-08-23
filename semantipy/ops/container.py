__all__ = ["select", "select_iter", "split", "combine"]

from typing import Iterable

from semantipy.dispatch_utils import semantic_function_dispatch
from semantipy.semantics import Semantics, TypedSelector

from .base import semantipy_op


@semantipy_op
def select(s: Semantics, selector: Semantics) -> Semantics:
    raise NotImplementedError()


@semantipy_op
def select_iter(s: Semantics, selector: Semantics) -> Iterable[Semantics]:
    raise NotImplementedError()


@semantipy_op
def split(s: Semantics, selector: Semantics) -> Iterable[Semantics]:
    raise NotImplementedError()


@semantipy_op
def combine(*semantics: Semantics) -> Semantics:
    raise NotImplementedError()
