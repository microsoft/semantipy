from __future__ import annotations

from typing import TypeVar, Generic, Optional, Literal, List, Union, Any, Callable, TYPE_CHECKING

from semantipy.semantics import (
    Semantics,
    Text,
    SemanticContent,
    StructuredDocument,
    empty,
    SemanticModel,
    SemanticRootModel,
    PythonFunction
)

if TYPE_CHECKING:
    from semantipy.ops.base import Dispatcher, BaseExecutionPlan, SupportsSemanticFunction

InputType = TypeVar("InputType")
OutputType = TypeVar("OutputType")


class Renderer(Generic[InputType, OutputType]):
    """Renderer converts one type of semantics (or any type) into another semantic type,
    possibly with or without information addition or information loss.

    Renderer can be thought as an approach to modularize the type conversion of semantic objects.
    It's from a type view of semantics (rather than a semantic view).
    Operators may or may not use renderers as the implementation to process semantics.
    """

    def render_plan(self, semantics: InputType, target_type: type[OutputType] | None = None) -> BaseExecutionPlan:
        """Return the execution plan to render the semantics into the target type.

        Subclass can override this to provide a custom execution plan for deferred execution.
        Raising NotImplemented here to indicate that this renderer is not suitable for current arguments.
        """
        from semantipy._impls.base import LambdaExecutionPlan

        return LambdaExecutionPlan(lambda: self.render(semantics, target_type))

    def render(self, semantics: InputType, target_type: type[OutputType] | None = None) -> OutputType:
        """Render the semantics into the target type.
        
        Subclass can also override `render_plan` and write `render_plan().execute()` here.
        """
        raise NotImplementedError()


class _PureTextStructuredDocument(SemanticContent[List[Union[Text, "_PureTextStructuredDocument"]]]):
    """This class exists for rendering purposes only. It's not meant to be used directly."""

    name: Optional[Text]
    """Useful as XML tags."""
    title: Optional[Text]
    """Useful as Markdown headers."""


_PureTextStructuredDocument.model_rebuild()


class TextRenderer(Renderer[Semantics, Text]):

    def __init__(self, format: Literal["markdown", "xml"] = "markdown"):
        self.format = format

    def _recursively_render_markdown(self, semantics: Text | _PureTextStructuredDocument, level: int = 1) -> Text:
        if isinstance(semantics, Text):
            return semantics
        elif isinstance(semantics, _PureTextStructuredDocument):
            elements: list[str] = []
            if semantics.title is not None:
                elements.append(f"{'#' * level} {semantics.title} {'#' * level}")
            elements += [self._recursively_render_markdown(c, level + 1) for c in semantics.content]
            return Text("\n\n".join(elements))
        else:
            raise ValueError(f"Unsupported semantics: {semantics}")

    def _recursively_render_xml(self, semantics: Text | _PureTextStructuredDocument) -> Text:
        if isinstance(semantics, Text):
            return semantics
        elif isinstance(semantics, _PureTextStructuredDocument):
            elements: list[str] = [self._recursively_render_xml(c) for c in semantics.content]
            if semantics.name is not None:
                return Text(f"<{semantics.name}>\n" + "\n".join(elements) + f"\n</{semantics.name}>")
            else:
                return Text("\n".join(elements))
        else:
            raise ValueError(f"Unsupported semantics: {semantics}")

    def _assign_name(
        self, semantics: _PureTextStructuredDocument | Text, name: str | Text, title: str | Text | None = None
    ) -> _PureTextStructuredDocument:
        if isinstance(semantics, Text):
            return _PureTextStructuredDocument(
                name=Text(name), title=Text(title) if title is not None else None, content=[semantics]
            )
        elif isinstance(semantics, _PureTextStructuredDocument):
            semantics.name = Text(name)
            if title is not None:
                semantics.title = Text(title)
            return semantics
        else:
            raise ValueError(f"Unsupported semantics to assign name: {semantics}")

    def _any_to_text_or_structured_document(self, semantics: Semantics | Any) -> Text | _PureTextStructuredDocument:
        """Convert any semantics into Text or _PureTextStructuredDocument."""
        if isinstance(semantics, Text):
            return semantics
        elif semantics is empty:
            return Text("")
        elif isinstance(semantics, StructuredDocument):
            contents: list[Text | _PureTextStructuredDocument] = []
            if isinstance(semantics.content, Text):
                contents.append(semantics.content)
            elif isinstance(semantics.content, list):
                contents += [self._any_to_text_or_structured_document(c) for c in semantics.content]
            elif isinstance(semantics.content, dict):
                for k, v in semantics.content.items():
                    contents.append(self._assign_name(self._any_to_text_or_structured_document(v), k))
            return _PureTextStructuredDocument(name=semantics.title, title=semantics.title, content=contents)
        elif isinstance(semantics, SemanticRootModel):
            return self._any_to_text_or_structured_document(semantics.root)
        elif isinstance(semantics, SemanticModel):
            contents = []
            for k in semantics.model_fields_set:
                rv = self._any_to_text_or_structured_document(getattr(semantics, k))
                contents.append(self._assign_name(rv, k))
            return _PureTextStructuredDocument(name=None, title=None, content=contents)

        raise ValueError(f"Unsupported semantics: {semantics}")

    def render(self, semantics: Semantics, target_type: type[Text] | None = None) -> Text:
        semantics_converted = self._any_to_text_or_structured_document(semantics)
        if target_type is not None and target_type != Text:
            raise ValueError(f"Unsupported target type: {target_type}")
        if self.format == "markdown":
            return self._recursively_render_markdown(semantics_converted)
        elif self.format == "xml":
            return self._recursively_render_xml(semantics_converted)
        else:
            raise ValueError(f"Unsupported format: {self.format}")


class StructuredDocumentRenderer(Renderer[Text, StructuredDocument]):

    def render(self, semantics: Text, target_type: type[StructuredDocument] | None = None) -> StructuredDocument:
        from semantipy._impls.llm import _lm_structurize_document
        return _lm_structurize_document(semantics)


class CodeRenderer(Renderer[Text, PythonFunction]):

    def render(self, semantics: Text, target_type: type[PythonFunction] | None = None) -> PythonFunction:
        from semantipy._impls.llm import _lm_python_function_generate
        from semantipy.ops import grab_context
        return _lm_python_function_generate(
            Text(semantics + "\n\n**Context:** " + TextRenderer().render(grab_context()))
        )


RENDERER_REGISTRY: dict[tuple[type, type], type[Renderer]] = {
    (Semantics, Text): TextRenderer,
    (Text, StructuredDocument): StructuredDocumentRenderer,
    (Text, PythonFunction): CodeRenderer,
}


def list_renderers(input_type: type, output_type: type) -> List[type[Renderer]]:
    """Get all renderers that can convert input_type to output_type."""
    matches: list[tuple[int, type[Renderer]]] = []
    for (k1, k2), candidate in RENDERER_REGISTRY.items():
        score = 0
        if input_type == k1:
            score += 3
        elif issubclass(input_type, k1):
            score += 2
        if output_type == k2:
            score += 3
        elif issubclass(output_type, k2):
            score += 2
        if score > 3:
            matches.append((score, candidate))
    matches.sort(reverse=True)  # later added renderers have higher priority
    return [v for _, v in matches]
