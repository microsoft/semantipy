from __future__ import annotations

__all__ = [
    "SemanticModel",
    "SemanticRootModel",
    "SemanticContent",
    "Exemplar",
    "Exemplars",
    "StructuredDocument",
    "ChatMessage",
    "ChatLogs",
    "PythonFunction",
]

import inspect
import typing
from tempfile import NamedTemporaryFile
from typing import Generic, TypeVar, Any, List, Dict, Union, Optional, OrderedDict, Callable, Literal

from pydantic import BaseModel, RootModel, ConfigDict, model_serializer

from .base import Semantics
from .element import Text


class SemanticModel(Semantics, BaseModel):

    def __getitem__(self, index: Any) -> Any:
        if isinstance(index, str) and index in self.model_fields_set:
            return getattr(self, index)
        else:
            raise AttributeError(f"{self.__class__.__name__} has no attribute '{index}'")


class SemanticRootModel(SemanticModel, RootModel):

    def __getitem__(self, index):
        return self.root[index]


ContentType = TypeVar("ContentType")


class SemanticContent(SemanticModel, Generic[ContentType]):
    """Attributed content.

    Subclass this to create a content that is attached with attributes.
    Content is the most important part in this model.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    content: ContentType

    def __getitem__(self, index):
        try:
            return super().__getitem__(index)
        except AttributeError:
            return self.content[index]  # type: ignore


class Exemplar(SemanticModel):
    input: Dict[str, Any] | SemanticModel | Any
    output: Dict[str, Any] | SemanticModel | Any


class Exemplars(SemanticRootModel):
    root: List[Exemplar]

    def append(self, exemplar: Exemplar):
        if not isinstance(exemplar, Exemplar):
            raise TypeError(f"Expected Exemplar, but got {type(exemplar)}")
        self.root.append(exemplar)
        return self

    def extend(self, exemplars: List[Exemplar] | Exemplars):
        if isinstance(exemplars, Exemplars):
            exemplars = exemplars.root
        if not isinstance(exemplars, list):
            raise TypeError(f"Expected List[Exemplar], but got {type(exemplars)}")
        if not all(isinstance(exemplar, Exemplar) for exemplar in exemplars):
            raise TypeError(f"Expected input to be a list of Exemplar")
        self.root.extend(exemplars)
        return self

    def __iter__(self):
        return iter(self.root)


TextOrStructuredDocumentOrAnySemantics = Union["Text", "StructuredDocument", Semantics]
"""The basic element used in structured document.
Text / StructuredDocument is one kind of Semantics.
It's separatedly handled for auto conversion (e.g., from str to Text).
"""


class StructuredDocument(
    SemanticContent[
        Union[
            TextOrStructuredDocumentOrAnySemantics,
            List[TextOrStructuredDocumentOrAnySemantics],
            OrderedDict[str, TextOrStructuredDocumentOrAnySemantics],
        ]
    ]
):
    title: Optional[Text] = None

    # def __semantic_function__(self, func, types, args, kwargs):
    #     from semantipy.ops.manipulate import _apply

    #     if func == _apply:
    #         from semantipy._impls.llm import _lm_structured_document_apply

    #         return _lm_structured_document_apply(*args, **kwargs)
    #     return super().__semantic_function__(func, types, args, kwargs)

    @model_serializer
    def serialize_model(self) -> dict:
        # first title and then others
        if self.title is None:
            ret: dict = {}
        else:
            ret = {"title": self.title}
        ret.update({k: getattr(self, k) for k in self.model_fields_set if k != "title"})
        return ret


StructuredDocument.model_rebuild()


class ChatMessage(SemanticContent[Text]):
    role: Literal["system", "human", "ai"]

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

class ChatLogs(SemanticRootModel):
    root: List[ChatMessage]

    def append(self, message: ChatMessage):
        if not isinstance(message, ChatMessage):
            raise TypeError(f"Expected ChatMessage, but got {type(message)}")
        self.root.append(message)

    def extend(self, messages: List[ChatMessage] | ChatLogs):
        if isinstance(messages, ChatLogs):
            messages = messages.root
        if not isinstance(messages, list):
            raise TypeError(f"Expected List[ChatMessage], but got {type(messages)}")
        for message in messages:
            self.append(message)

    def __iter__(self):
        return iter(self.root)

    def __iadd__(self, messages: List[ChatMessage] | ChatLogs):
        self.extend(messages)
        return self

    def to_langchain(self):
        return [message.to_langchain() for message in self]


class PythonFunction(SemanticContent[Text]):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    entrypoint: Text
    intent: Optional[Union[Text, Semantics]] = None

    @staticmethod
    def _execute_code(code: str, fn_name: str) -> Callable[..., Any]:
        """Execute the code and return the defined function within the code."""
        globals_ = {}

        globals_.update({"typing": typing})
        globals_.update({name: getattr(typing, name) for name in dir(typing)})

        with NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp:
            temp.write(code)

        compiled = compile(code, temp.name, "exec")
        exec(compiled, globals_)

        if fn_name not in globals_:
            raise NameError(f"Function '{fn_name}' not found in the code execution result.")
        return globals_[fn_name]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(content={self.content!r}, entrypoint={self.entrypoint!r}, intent={self.intent!r})"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, PythonFunction)
            and self.content == other.content
            and self.entrypoint == other.entrypoint
            and self.intent == other.intent
        )

    def signature(self) -> inspect.Signature:
        return inspect.signature(self._execute_code(self.content, self.entrypoint))

    def __call__(self, *args, **kwargs):
        program = self._execute_code(self.content, self.entrypoint)
        return program(*args, **kwargs)

    def __semantic_function__(self, func, types, args, kwargs):
        from semantipy.ops.manipulate import _apply

        if func == _apply:
            from semantipy._impls.llm import _lm_python_function_apply

            return _lm_python_function_apply(*args, **kwargs)
        return super().__semantic_function__(func, types, args, kwargs)
