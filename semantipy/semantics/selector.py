from __future__ import annotations

__all__ = ["TypedSelector", "PatternSelector"]

from typing import TypeVar, Generic, TYPE_CHECKING
from pydantic import Field

from .container import SemanticModel, Exemplars, Exemplar
from .element import Text, _Empty, empty
from .base import Semantics

if TYPE_CHECKING:
    from semantipy.ops.base import BaseExecutionPlan
    from semantipy._impls.llm_v2 import LLMCallExecutionPlan



SelectorType = TypeVar("SelectorType")
ParsedType = TypeVar("ParsedType")


class SemanticSelector(Semantics):

    @classmethod
    def select_impl(cls, plan: LLMCallExecutionPlan, s: Semantics, index: SemanticSelector) -> LLMCallExecutionPlan:
        """Subclass should implement this method to provide the logic for selecting the information from the input."""
        return NotImplemented

    @classmethod
    def __semantic_dependencies__(cls):
        from semantipy._impls.llm_v2 import LLMBackend
        return [LLMBackend]

    @classmethod
    def __semantic_function__(cls, func, kwargs, dispatcher, plan):
        from semantipy.ops.container import select
        from semantipy._impls.llm_v2 import LLMCallExecutionPlan

        if not isinstance(plan, LLMCallExecutionPlan):
            return NotImplemented

        if func == select:
            if "selector" not in kwargs:
                raise ValueError("selector not provided for select.")
            if "s" not in kwargs:
                raise ValueError("s not provided for select.")
            return cls.select_impl(plan, kwargs["s"], kwargs["selector"])
        return NotImplemented


class TypedSelector(SemanticSelector, SemanticModel, Generic[SelectorType]):
    selector: Text | _Empty = Field(default=empty)
    type: type[SelectorType]

    @classmethod
    def select_impl(cls, plan: LLMCallExecutionPlan, s: Semantics, index: TypedSelector) -> LLMCallExecutionPlan:
        from semantipy._impls.llm_v2 import TemplateRenderer, TemplateParser

        class TypeParser(SemanticModel, TemplateParser):
            dtype: type

            def render(
                self, text: Text, target_type: type | None = None
            ):
                if target_type is None:
                    target_type = self.dtype
                return target_type(text)

        plan.prompt_renderer.instruction = Text(
            plan.prompt_renderer.instruction + "\n" +
            "You may see an \"index\", which describes what information you should extract.\n" +
            "You may also see a \"dtype\", which describes the type of the extracted information.\n" +
            "The response should be evaluatable to the desired `dtype` with `ast.literal_eval`."
        )  # TODO use combine or apply operator

        plan.prompt_renderer.exemplars = Exemplars([
            Exemplar(input={
                "selector": TypedSelector(type=int),
                "s": Text("The answer to life, the universe, and everything is 42."),
            }, output=42)
        ])

        plan.prompt_renderer.input_renderer = TemplateRenderer(
            template_string=(
                "index: {% if selector.selector|string %}{{ selector.selector }}" +
                "{% else %}Not specified. You can extract the most important part of the text, " +
                "typically the final answer, or the main point.{% endif %}\n" +
                "dtype: {{ selector.dtype }}\n\nContent: {{ s }}"
            ),
            template_type="jinja"
        )
        plan.prompt_renderer.output_renderer = None
        plan.prompt_renderer.output_renderer_reverse = TypeParser(dtype=index.type)

        plan.sign(cls.__name__, "adding typed information")
        return plan


class PatternSelector(SemanticModel):
    pattern: Text
