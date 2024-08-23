from __future__ import annotations

__all__ = ["Semantics"]

from typing import Callable, TYPE_CHECKING, Any
from typing_extensions import Self

if TYPE_CHECKING:
    from semantipy.ops.base import Dispatcher, BaseExecutionPlan, SupportsSemanticFunction


class Semantics:

    @classmethod
    def __semantic_dependencies__(cls) -> list[type[SupportsSemanticFunction]]:
        """Return a list of backends that this backend depends on."""
        return []

    @classmethod
    def __semantic_function__(
        cls,
        func: Callable,
        kwargs: dict,
        dispatcher: Dispatcher | None = None,
        plan: BaseExecutionPlan | None = None,
    ) -> BaseExecutionPlan:
        return NotImplemented

    def __enter__(self: Self) -> Any:
        from semantipy.ops import context_enter
        return context_enter(self)

    def __exit__(self: Self, exc_type, exc_val, exc_tb) -> None:
        from semantipy.ops import context_exit
        return context_exit(self)

    # def apply(self: Self, changes: Semantics) -> Self:
    #     from semantipy.ops import apply
    #     return apply(self, changes)

    # def contains(self: Self, t: Semantics) -> bool:
    #     from semantipy.ops import contains
    #     return contains(self, t)
