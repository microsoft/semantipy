"""WIP: Document related semantics and semantic operations."""

from __future__ import annotations

__all__ = [
    "StructuredDocument",
]

from typing import List, Union, Literal

from semantipy.semantics import SemanticModel, Text


class StructuredDocument(SemanticModel):
    tag: Literal["header", "paragraph", "block"] = "block"
    children: List[Union[StructuredDocument, Text]]
