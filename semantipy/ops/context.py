from contextlib import ExitStack, contextmanager

__all__ = ["context", "context_enter", "context_exit"]

from semantipy.semantics import Semantics

from .base import semantipy_op, SemanticOperationRequest


def _context_preprocessor(func, ctx) -> SemanticOperationRequest:
    return SemanticOperationRequest(operator=func, operand=ctx)


@semantipy_op(preprocessor=_context_preprocessor)
def context_enter(ctx: Semantics):
    raise NotImplementedError()


@semantipy_op(preprocessor=_context_preprocessor)
def context_exit(ctx: Semantics):
    raise NotImplementedError()


@contextmanager
def context(*ctx: Semantics):
    # use request object to cast the input parameters
    casted_ctx = SemanticOperationRequest(
        operator=context_enter, operand=ctx[0], other_operands=list(ctx[1:])
    ).operands()
    with ExitStack() as es:
        for c in casted_ctx:
            es.enter_context(c)
        yield
