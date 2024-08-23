from typing import Callable, TypeVar, Any

from semantipy._impls.base import BaseExecutionPlan
from semantipy.ops.base import Dispatcher
from semantipy.semantics import Semantics, Text
from semantipy.ops import logical_binary, equals, contains

from .base import BaseBackend, LambdaExecutionPlan, register

SemanticType = TypeVar("SemanticType", bound=Semantics)


@register
class RedirectBackend(BaseBackend):
    """Redirects the implementation to a smaller set of operations.
    """

    @classmethod
    def equals(cls, s: Semantics, t: Semantics) -> bool:
        # TODO: inject this logic into dispatcher
        return logical_binary(Text("equals"), s, t)

    @classmethod
    def contains(cls, s: Semantics, t: Semantics) -> bool:
        return logical_binary(Text("contains"), s, t)

    @classmethod
    def __semantic_function__(cls, func: Callable[..., Any], kwargs: dict, dispatcher: Dispatcher | None = None, plan: BaseExecutionPlan | None = None) -> BaseExecutionPlan:
        if func == equals:
            return LambdaExecutionPlan(lambda: cls.equals(**kwargs))
        elif func == contains:
            return LambdaExecutionPlan(lambda: cls.contains(**kwargs))
        return NotImplemented
