__all__ = ["logical_unary", "logical_binary", "equals", "contains"]

from semantipy.semantics import Semantics

from .base import semantipy_op, SemanticOperationRequest


def _logical_unary_preprocessor(func, operator, s) -> SemanticOperationRequest:
    return SemanticOperationRequest(operator=operator, operand=s, guest_operand=operator, return_type=bool)


@semantipy_op(preprocessor=_logical_unary_preprocessor)
def logical_unary(operator: Semantics, s: Semantics | str) -> bool:
    raise NotImplementedError()


def _logical_binary_preprocessor(func, operator, s, t) -> SemanticOperationRequest:
    return SemanticOperationRequest(operator=operator, operand=s, guest_operand=t, return_type=bool)


@semantipy_op(preprocessor=_logical_binary_preprocessor)
def logical_binary(operator: Semantics, s: Semantics | str, t: Semantics | str) -> bool:
    raise NotImplementedError()


def _binary_func_preprocessor(func, s, t) -> SemanticOperationRequest:
    return SemanticOperationRequest(operator=func, operand=s, guest_operand=t, return_type=bool)


@semantipy_op(preprocessor=_binary_func_preprocessor)
def equals(s: Semantics, t: Semantics) -> bool:
    raise NotImplementedError()


@semantipy_op(preprocessor=_binary_func_preprocessor)
def contains(s: Semantics, t: Semantics) -> bool:
    raise NotImplementedError()
