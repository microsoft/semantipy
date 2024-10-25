__all__ = [
    "configure_lm",
    "LMExecutionPlan",
    "LMContextPlan",
    "LMBackend",
]

from pathlib import Path
from typing import Any

from pydantic import ConfigDict
from langchain.schema import BaseMessage
from langchain.chat_models.base import BaseChatModel
from semantipy.impls.base import BaseExecutionPlan, register, BaseBackend
from semantipy.ops.base import SemanticOperationRequest, Dispatcher
from semantipy.ops import context_enter, context_exit
from semantipy.semantics import SemanticModel, Text, Semantics

from .template import SemantipyPromptTemplate

_lm: BaseChatModel | None = None


def _get_or_load_global_lm() -> BaseChatModel:
    global _lm

    if _lm is None:
        from langchain_openai import ChatOpenAI

        _lm = ChatOpenAI(model="gpt-4o", temperature=0.0)

    return _lm


def configure_lm(lm: BaseChatModel) -> None:
    """An approach to configure the language model globally."""
    global _lm
    if not isinstance(lm, BaseChatModel):
        raise TypeError("lm must be an instance of BaseChatModel")
    _lm = lm


class LMExecutionPlan(BaseExecutionPlan, SemanticModel):
    """A plan to execute a language model operation."""

    prompt: SemantipyPromptTemplate

    def parse_output(self, output: Any) -> Any:
        if self.prompt.parser is None:
            return Text(output)
        return self.prompt.parser.parse(output)

    def lm_input(self) -> list[BaseMessage]:
        """Use this method to debug the input to the language model."""
        return self.prompt.render()

    def lm_output(self) -> Text:
        """Use this method to debug the output from the language model."""
        llm = _get_or_load_global_lm()
        response = llm.invoke(self.lm_input())
        if response is None or response.content is None:
            raise ValueError("No response from the language model.")
        return Text(response.content)  # type: ignore

    def execute(self) -> Any:
        return self.parse_output(self.lm_output())


_contexts: list[Semantics] = []


class LMContextPlan(BaseExecutionPlan, SemanticModel):
    context: Semantics
    pop: bool

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def execute(self) -> Any:
        if not self.pop:
            _contexts.append(self.context)
        else:
            _contexts.remove(self.context)


@register
class LMBackend(BaseBackend):

    _contexts: list[Semantics] = []

    @classmethod
    def __semantic_function__(
        cls,
        request: SemanticOperationRequest,
        dispatcher: Dispatcher | None = None,
        plan: BaseExecutionPlan | None = None,
    ) -> LMExecutionPlan | LMContextPlan:
        """Get the proper prompt template from `<func_name>_prompt` and put it in a LMExecutionPlan."""

        # Handle contexts
        if request.operator == context_enter:
            plan = LMContextPlan(context=request.operand, pop=False)
            plan.sign(cls.__name__, "context created")
            return plan
        if request.operator == context_exit:
            plan = LMContextPlan(context=request.operand, pop=True)
            plan.sign(cls.__name__, "context created")
            return plan

        if _contexts:
            request = request.model_copy(update={"contexts": request.contexts + _contexts})

        if hasattr(request.operator, "__name__"):
            func_name = request.operator.__name__
            prompt_config_path = Path(__file__).parent / "prompts" / f"{func_name}.yaml"
            if not prompt_config_path.exists():
                # fallback to universal prompt
                prompt_config_path = Path(__file__).parent / "prompts" / "universal.yaml"
        else:
            prompt_config_path = Path(__file__).parent / "prompts" / "universal.yaml"
        prompt = SemantipyPromptTemplate.from_file(prompt_config_path).input(request)
        plan = LMExecutionPlan(prompt=prompt)
        plan.sign(cls.__name__, "created")
        return plan
