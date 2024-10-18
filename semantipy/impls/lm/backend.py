from pathlib import Path
from typing import Any

from langchain.schema import BaseMessage
from langchain.chat_models.base import BaseChatModel
from semantipy.impls.base import BaseExecutionPlan, register, BaseBackend
from semantipy.ops.base import SemanticOperationRequest, Dispatcher
from semantipy.semantics import SemanticModel, Text

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
        raise TypeError('lm must be an instance of BaseChatModel')
    _lm = lm


class LMExecutionPlan(BaseExecutionPlan, SemanticModel):
    prompt: SemantipyPromptTemplate

    def _parse_output(self, output: Any) -> Any:
        if self.prompt.parser is None:
            return Text(output)
        return self.prompt.parser.parse(output)

    def _prompt(self) -> list[BaseMessage]:
        return self.prompt.render()

    def execute(self) -> Any:
        llm = _get_or_load_global_lm()
        response = llm(self._prompt())
        if response is None or response.content is None:
            raise ValueError("No response from the language model.")
        return self._parse_output(response.content)


@register
class LMBackend(BaseBackend):
    @classmethod
    def __semantic_function__(
        cls,
        request: SemanticOperationRequest,
        dispatcher: Dispatcher | None = None,
        plan: BaseExecutionPlan | None = None,
    ) -> LMExecutionPlan:
        """Get the proper prompt template from `<func_name>_prompt` and put it in a LMExecutionPlan."""
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
