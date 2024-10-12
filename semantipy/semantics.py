from __future__ import annotations

__all__ = [
    "Semantics",
    "Text",
    "TextOrSemantics",
    "SemanticList",
    "SemanticDict",
    "SemanticModel",
    "Exemplar",
    "ChatMessage",
]

from typing import Callable, TYPE_CHECKING, Any, Union, Literal
from typing_extensions import Self

from pydantic import GetCoreSchemaHandler, BaseModel
from pydantic_core import CoreSchema, core_schema

if TYPE_CHECKING:
    from semantipy.ops.base import Dispatcher, BaseExecutionPlan, SupportsSemanticFunction, SemanticOperationRequest


class Semantics:

    @classmethod
    def __semantic_dependencies__(cls) -> list[type[SupportsSemanticFunction]]:
        """Return a list of backends that this backend depends on."""
        return []

    @classmethod
    def __semantic_function__(
        cls,
        request: SemanticOperationRequest,
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


class Text(str, Semantics):
    """Semantics that are represented with a pure textual string."""

    def __new__(cls, text: str) -> Text:
        obj = str.__new__(cls, text)
        return obj

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))



class SemanticList(list, Semantics):
    """Semantics that are represented with a list."""

    pass


class SemanticDict(dict, Semantics):
    """Semantics that are represented with a dictionary."""

    pass


class SemanticModel(Semantics, BaseModel):
    """Semantics that are inherit a Pydantic model."""

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, str) and index in self.model_fields_set:
            return getattr(self, index)
        else:
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{index}'")


class Exemplar(SemanticModel):
    """An example input-output pair."""

    input: Union[Text, Semantics]
    output: Union[Text, Semantics]


class ChatMessage(SemanticModel):
    """A message in a chat."""

    role: Literal["system", "human", "ai"]
    content: Text

    def to_langchain(self):
        from langchain.schema import SystemMessage, HumanMessage, AIMessage

        if self.role == "system":
            return SystemMessage(content=self.content)
        elif self.role == "human":
            return HumanMessage(content=self.content)
        elif self.role == "ai":
            return AIMessage(content=self.content)
        else:
            raise ValueError(f"Unsupported role: {self.role}")
