from contextlib import ExitStack, contextmanager

__all__ = ["context", "grab_context", "context_enter", "context_exit"]

from semantipy.semantics import Semantics, Text, RoleContext, empty
from semantipy.renderer import TextRenderer

from .base import semantipy_op


_context_stack: list[Semantics] = []


@semantipy_op
def context_enter(ctx: Semantics):
    raise NotImplementedError()


@semantipy_op
def context_exit(ctx: Semantics):
    raise NotImplementedError()


@contextmanager
def context(*ctx: Semantics, **named_ctx: Semantics):
    ctx_ = list(ctx)
    for name, c in named_ctx.items():
        ctx_.append(RoleContext(role=Text(name), content=c))
    with ExitStack() as es:
        for c in ctx:
            es.enter_context(c)
        yield


def grab_context() -> Semantics:
    # TODO: a better implementation
    if not _context_stack:
        return empty
    text_renderer = TextRenderer()
    return Text("\n\n".join(text_renderer.render(ctx) for ctx in _context_stack))
