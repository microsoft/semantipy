__all__ = ["logical_unary", "logical_binary", "equals", "contains"]

from semantipy.semantics import Semantics

from .base import semantipy_op


@semantipy_op
def logical_unary(operator: Semantics, s: Semantics) -> bool:
    raise NotImplementedError()


@semantipy_op
def logical_binary(operator: Semantics, s: Semantics, t: Semantics) -> bool:
    raise NotImplementedError()


@semantipy_op
def equals(s: Semantics, t: Semantics) -> bool:
    raise NotImplementedError()


@semantipy_op
def contains(s: Semantics, t: Semantics) -> bool:
    raise NotImplementedError()
