from __future__ import annotations

from .base import semantipy_op


@semantipy_op
def guard(func, inputs, outputs):
    raise NotImplementedError()
