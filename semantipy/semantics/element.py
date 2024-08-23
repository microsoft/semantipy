from __future__ import annotations

__all__ = ["SemanticElement", "empty", "Text", "PathIndex", "Image"]

from typing import Any, TYPE_CHECKING

from pydantic import GetCoreSchemaHandler
from pydantic_core import CoreSchema, core_schema

from .base import Semantics

if TYPE_CHECKING:
    from .container import SemanticModel


class SemanticElement(Semantics):
    pass


class _Empty(SemanticElement):

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(None))
    
    def __str__(self) -> str:
        return ""


empty = _Empty()


class Text(str, SemanticElement):
    """Semantics that are represented with a pure textual string."""

    def __new__(cls, text: str) -> Text:
        obj = str.__new__(cls, text)
        return obj

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type: Any, handler: GetCoreSchemaHandler) -> CoreSchema:
        return core_schema.no_info_after_validator_function(cls, handler(str))


class PathIndex(SemanticElement):
    def __init__(self, paths: list[str | int] | str | int):
        if isinstance(paths, (str, int)):
            self.paths = [paths]
        elif not all(isinstance(p, (str, int)) for p in paths):
            raise ValueError("Paths must be a list of strings or integers.")
        else:
            self.paths = paths

    def index_on(self, model: SemanticModel) -> Any:
        current = model
        for path in self.paths:
            current = current[path]
        return current

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.paths!r})"


class Image(SemanticElement):
    pass
