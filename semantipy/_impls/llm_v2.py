import ast
import inspect
import re
import textwrap
from typing import Type, Union, Literal, Dict, Any, Optional, TypeVar, Callable, Generic

from pydantic import ConfigDict, Field
from langchain.chat_models.base import BaseChatModel
from langchain_openai import ChatOpenAI

from semantipy.ops.base import Dispatcher, SupportsSemanticFunction
from semantipy.ops import context_enter, context_exit, resolve
from semantipy.semantics import (
    Semantics,
    SemanticModel,
    Text,
    Exemplar,
    Exemplars,
    ChatLogs,
    ChatMessage,
    Strategy,
    Guards,
    Guard,
    RoleContext,
)
from semantipy.renderer import Renderer

from jinja2 import Template as JinjaTemplate

from .base import BaseBackend, BaseExecutionPlan, BackendNotImplemented, DummyPlan, register


_lm: BaseChatModel | None = None


def _get_or_load_global_lm() -> BaseChatModel:
    global _lm

    if _lm is None:
        _lm = ChatOpenAI(model="gpt-4o", temperature=0.0)

    return _lm


class TemplateRenderer(SemanticModel, Renderer[Union[Dict[str, Any], SemanticModel], Text]):

    template_string: str
    template_type: Literal["f-string", "jinja"]

    def render(self, context: Dict[str, Any] | SemanticModel) -> Text:
        if isinstance(context, SemanticModel):
            context = context.model_dump()
        if self.template_type == "jinja":
            return Text(JinjaTemplate(self.template_string).render(context))
        else:
            return Text(self.template_string.format(**context))

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(template_string={self.template_string!r}, template_type={self.template_type!r})"
        )


ParsedType = TypeVar("ParsedType", Text, Dict[str, Any], SemanticModel)


class TemplateParser(Renderer[Text, ParsedType]):

    def render(self, text: Text, target_type: Type[ParsedType] | None = None) -> ParsedType:
        raise NotImplementedError()


class RegexTemplateParser(SemanticModel, TemplateParser):

    regex: str
    """The regex to use to parse the output."""
    with_fallback: bool = Field(default=False)
    """If True, the parser will fallback to the original text if the regex does not match."""

    def render(self, text: Text, target_type: Type[ParsedType] | None = None) -> ParsedType:
        match = re.search(self.regex, text)
        if match:
            if target_type is None or target_type == Text:
                return Text(match.group())  # type: ignore
            elif target_type == dict or str(target_type).startswith("typing.Dict"):
                return dict(match.groupdict())  # type: ignore
            elif issubclass(target_type, SemanticModel):
                return target_type(**match.groupdict())
            else:
                raise ValueError(f"Unsupported target type: {target_type}")
        elif self.with_fallback:
            return text  # type: ignore
        else:
            raise ValueError(f"Could not parse output: {text} [regex: {self.regex}]")


class TypeTemplateParser(SemanticModel, TemplateParser):

    target_type: type

    def render(self, text: Text, target_type: type | None = None) -> ParsedType:
        if target_type is not None and target_type != self.target_type:
            raise ValueError(f"Target type mismatch: {target_type} != {self.target_type}")
        if self.target_type in [int, float, bool, str]:
            val = ast.literal_eval(text)
            return self.target_type(val)
        else:
            return self.target_type(text)  # type: ignore


class ChainTemplateParser(SemanticModel, TemplateParser):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    parsers: list[TemplateParser]

    def _attempt_augmented_error_message(self, error, append_message):
        """Attempt to recreate an error with an appended message."""
        try:
            return type(error)(error.args[0] + append_message, *error.args[1:])
        except Exception:
            return error

    def render(self, text: Text, target_type: Type[ParsedType] | None = None) -> ParsedType:
        resp = text
        for parser in self.parsers:
            try:
                resp = parser.render(resp, target_type=target_type)
            except Exception as e:
                new_error = self._attempt_augmented_error_message(e, f" [parser: {parser}]")
                raise new_error.with_traceback(e.__traceback__) from None
        return resp  # type: ignore


class SeparatorTemplateParser(SemanticModel, TemplateParser):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    separator: str
    """The separator to use to parse the output."""
    inner_parser: TemplateParser | None = Field(default=None)
    """The parser to use for each part of the separated text."""

    def render(self, text: Text, target_type: Type[list[ParsedType]] | None = None) -> list[ParsedType]:
        parts = text.split(self.separator)
        if self.inner_parser is not None:
            if target_type is not None and str(target_type).startswith("typing.List"):
                inner_target_type = target_type.__args__[0]
            else:
                inner_target_type = None
            ret = []
            for part in parts:
                ret.append(self.inner_parser.render(Text(part), target_type=inner_target_type))
            return ret
        else:
            return [Text(part) for part in parts]  # type: ignore


class ExemplarsRenderer(Renderer[Exemplars, ChatLogs]):

    def __init__(
        self,
        input_renderer: TemplateRenderer | None = None,
        output_renderer: TemplateRenderer | None = None,
    ):
        self.input_renderer = input_renderer
        self.output_renderer = output_renderer

    def render(self, exemplars: Exemplars) -> ChatLogs:
        chat_logs: list[ChatMessage] = []
        for exemplar in exemplars:
            if self.input_renderer is not None and isinstance(exemplar.input, (dict, SemanticModel)):
                input = self.input_renderer.render(exemplar.input)
            else:
                input = Text(str(exemplar.input))
            if self.output_renderer is not None and isinstance(exemplar.output, (dict, SemanticModel)):
                output = self.output_renderer.render(exemplar.output)
            else:
                output = Text(str(exemplar.output))
            chat_logs.append(ChatMessage(role="human", content=input))
            chat_logs.append(ChatMessage(role="ai", content=output))
        return ChatLogs(chat_logs)


class LMPromptRenderer(SemanticModel, Renderer[Dict[str, Any], ChatLogs]):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    instruction: Text
    exemplars: Exemplars | None = Field(default=None)
    input_renderer: TemplateRenderer | None = Field(default=None)
    output_renderer: TemplateRenderer | None = Field(default=None)
    output_renderer_reverse: TemplateParser | None = Field(default=None)

    def render(self, user_input: Dict[str, Any]) -> ChatLogs:
        # System message
        chat_logs = ChatLogs([ChatMessage(role="system", content=self.instruction)])
        # Examples as interactions
        if self.exemplars is not None:
            chat_logs += ExemplarsRenderer(self.input_renderer, self.output_renderer).render(self.exemplars)
        # User input
        chat_logs.append(ChatMessage(role="human", content=self.input_renderer.render(user_input)))
        return chat_logs


class LLMCallExecutionPlan(BaseExecutionPlan, SemanticModel):
    prompt_renderer: LMPromptRenderer
    user_input: Dict[str, Any]
    guards: Guards | None = Field(default=None)

    def validate(self) -> None:
        if self.guards is not None:
            for guard in self.guards.root:
                forked_plan = self.model_copy(update={"user_input": guard.input, "guards": None})
                output = forked_plan.execute()
                if not guard.check(output):
                    raise ValueError(f"Invalid plan because guard failed\nGuard: {guard}\nOutput: {output}")

    def execute(self) -> Text | Any:
        self.validate()

        chat_logs = self.prompt_renderer.render(self.user_input)
        llm = _get_or_load_global_lm()
        response = llm(chat_logs.to_langchain())
        if response is None or response.content is None:
            raise ValueError("No response from the language model.")
        # TODO: support target type
        response_content = Text(response.content)
        if self.prompt_renderer.output_renderer_reverse is not None:
            return self.prompt_renderer.output_renderer_reverse.render(response_content)
        else:
            return response_content


@register
class LLMBackend(BaseBackend):

    @classmethod
    def select_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            "Please extract the desired information (specified via index) from the text.\n\nOutput nothing else other than the extracted information."
        )

        user_msg_template = "Text:\n\n{s}\n\nIndex: {selector}"

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="f-string"),
        )

    @classmethod
    def select_iter_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            "Please extract the desired information (specified via index) from the text.\n\n"
            "If multiple matches are found, separate them with `###`."
        )

        user_msg_template = "Text:\n\n{s}\n\nIndex: {selector}"

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="f-string"),
            output_renderer=TemplateRenderer(
                template_string="{% for item in output %}{{ item }}{% if not loop.last %}\n###\n{% endif %}{% endfor %}",
                template_type="jinja",
            ),
            output_renderer_reverse=SeparatorTemplateParser(separator="###"),
        )

    @classmethod
    def split_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            "Please split the text into multiple parts based on the given separator.\n\n"
            "Output each part separated by `###`."
        )

        user_msg_template = "Text:\n\n{s}\n\nSeparator: {selector}"

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="f-string"),
            output_renderer=TemplateRenderer(
                template_string="{% for item in output %}{{ item }}{% if not loop.last %}\n###\n{% endif %}{% endfor %}",
                template_type="jinja",
            ),
            output_renderer_reverse=SeparatorTemplateParser(separator="\n"),
        )

    @classmethod
    def combine_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            "Please combine the provided contents, and output a single paragraph.\n"
            + "If the original contents are repetitive, please remove the redundant contents.\n\n"
            + "Output the combined text with nothing else."
        )

        user_msg_template = (
            "Texts:\n\n{% for item in semantics %}{{ item }}{% if not loop.last %}\n\n{% endif %}{% endfor %}"
        )

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="jinja"),
        )

    @classmethod
    def logical_unary_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            "Given an unary logic operator and an input data, please output 1 (for TRUE) or 0 (for FALSE) "
            "as the result when the operator is applied on the input data. "
            "Please do not output anything else other than 0/1."
        )

        user_msg_template = "Operator: {operator}\n\nData: {s}"

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="f-string"),
        )

    @classmethod
    def logical_binary_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            "Given a binary logic operator and two input data, please output 1 (for TRUE) or 0 (for FALSE) "
            "as the result when the operator is applied on the input data. "
            "Please do not output anything else other than 0/1."
        )
        user_msg_template = "Operator: {operator}\n\nData 1: {s}\n\nData 2: {t}"

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="f-string"),
            output_renderer_reverse=TypeTemplateParser(target_type=bool),
        )

    @classmethod
    def apply_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            textwrap.dedent(
                """
            Please apply the changes to the following content.

            Modify the contents according to the changes provided. Update the title if necessary.

            Respond in the same format as the original content, with the changes applied.
            Do not include anything other than the modified content in your response.
            """
            ).strip()
        )

        user_msg_template = "Text:\n\n{s}\n\nChanges Wanted:\n\n{changes}"

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="f-string"),
        )

    @classmethod
    def resolve_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            textwrap.dedent(
                """
            You may see a request, an expression or a question. Please resolve it with the best of your knowledge.

            For simple questions, please write the answer directly without any additional texts in the response.
            For complex questions (e.g., mathematical problems or reasoning tasks), you should think about it step by step first.
            Then write the answer after `### Answer ###`.

            If the request contains a specific data type, please write your answer in that type.
            That means, the answer should be evaluatable to the desired data type with `ast.literal_eval`.
            """
            ).strip()
        )

        user_msg_template = "{{ s }}{% if target_type %}\n\nData Type: {{ target_type }}{% endif %}"
        ai_template = "{% if reasoning %}{{ reasoning }}\n\n### Answer ###\n{% endif %}{{ answer }}"

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="jinja"),
            output_renderer=TemplateRenderer(template_string=ai_template, template_type="jinja"),
            exemplars=Exemplars(
                [
                    Exemplar(input={"s": Text("What is the capital of France?")}, output={"answer": Text("Paris")}),
                    Exemplar(
                        input={
                            "s": Text(
                                "Which is a faster way to get to work?\n"
                                "Option 1: Take a 1000 minute bus, then a half hour train, and finally a 10 minute bike ride.\n"
                                "Option 2: Take an 800 minute bus, then an hour train, and finally a 30 minute bike ride."
                            ),
                            "target_type": int,
                        },
                        output={
                            "reasoning": Text(
                                "Option 1 will take 1000+30+10 = 1040 minutes.\n"
                                "Option 2 will take 800+60+30 = 890 minutes.\n"
                                "Since Option 2 takes 890 minutes and Option 1 takes 1040 minutes, Option 2 is faster."
                            ),
                            "answer": 2,
                        },
                    ),
                    Exemplar(
                        input={
                            "s": Text(
                                "A coin is heads up. Maybelle flips the coin. "
                                "Shalonda does not flip the coin. Is the coin still heads up?"
                            ),
                            "target_type": bool,
                        },
                        output={
                            "reasoning": Text(
                                "The coin was flipped by Maybelle. "
                                "So the coin was flipped 1 time, which is an odd number. "
                                "The coin started heads up, so after an odd number of flips, it will be tails up."
                            ),
                            "answer": False,
                        },
                    ),
                ]
            ),
            output_renderer_reverse=RegexTemplateParser(
                regex=r"\#\#\# Answer \#\#\#\s*(?P<answer>.*)", with_fallback=True
            ),
        )

    @classmethod
    def diff_prompt(cls) -> LMPromptRenderer:
        instruction = Text(
            textwrap.dedent(
                """
            Please compare the two texts and provide the differences.

            Respond with only the differences but nothing else.
            """
            ).strip()
        )

        user_msg_template = "Text 1:\n\n{s}\n\nText 2:\n\n{t}"

        return LMPromptRenderer(
            instruction=instruction,
            input_renderer=TemplateRenderer(template_string=user_msg_template, template_type="f-string"),
        )

    @classmethod
    def __semantic_function__(
        cls,
        func: Callable,
        kwargs: dict,
        dispatcher: Dispatcher | None = None,
        plan: BaseExecutionPlan | None = None,
    ) -> LLMCallExecutionPlan:
        """Get the proper prompt template from `<func_name>_prompt` and put it in a LLMCallExecutionPlan."""
        func_name = func.__name__ + "_prompt"
        if not hasattr(cls, func_name):
            raise BackendNotImplemented(f"Backend {cls.__name__} does not implement {func_name}")

        prompt_renderer = getattr(cls, func_name)()

        # patch of resolve
        if func == resolve and "target_type" in kwargs:
            prompt_renderer.output_renderer_reverse = ChainTemplateParser(
                parsers=[
                    prompt_renderer.output_renderer_reverse,
                    TypeTemplateParser(target_type=kwargs["target_type"]),
                ]
            )

        plan = LLMCallExecutionPlan(
            prompt_renderer=prompt_renderer,
            user_input=kwargs,
        )
        plan.sign(cls.__name__, "created")
        return plan


ContextType = TypeVar("ContextType", bound=Semantics)


@register
class ContextBackend(BaseBackend, Generic[ContextType]):

    _context_stack: list[ContextType] = []

    @classmethod
    def __semantic_dependencies__(cls):
        return [LLMBackend]

    @classmethod
    def __semantic_function__(
        cls, func: Callable, kwargs: dict, dispatcher: Dispatcher | None = None, plan: BaseExecutionPlan | None = None
    ) -> BaseExecutionPlan:
        """The backup backend that handles contexts."""
        if func == context_enter:
            cls._context_stack.append(kwargs["ctx"])
            return DummyPlan(signer=cls.__name__) if plan is None else plan

        if func == context_exit:
            cls._context_stack.pop()
            return DummyPlan(signer=cls.__name__) if plan is None else plan

        if not isinstance(plan, LLMCallExecutionPlan):
            return NotImplemented

        # Gather everything from the stack and add to the plan.
        if cls._context_stack:
            contexts: list[str] = []
            for layer in cls._context_stack:
                if isinstance(layer, RoleContext):
                    contexts.append("- " + str(layer.role) + ": " + str(layer.content))
                else:
                    contexts.append("- " + str(layer))
            plan.prompt_renderer.instruction = Text(
                f"{plan.prompt_renderer.instruction}\n\n"
                + f"Please consider the following contexts before responding:\n\n"
                + "\n".join(contexts)
            )
            plan.sign(cls.__name__, f"adding {len(cls._context_stack)} context")

        return plan


@register
class ExemplarBackend(ContextBackend[Exemplars]):

    _context_stack: list[Exemplars] = []

    @classmethod
    def __semantic_dependencies__(cls):
        return [LLMBackend]

    @classmethod
    def __semantic_function__(
        cls,
        func: Callable,
        kwargs: dict,
        dispatcher: Dispatcher | None = None,
        plan: BaseExecutionPlan | None = None,
    ) -> BaseExecutionPlan:
        """The backend is responsive to three things:

        1. Examples are set up via `context_enter`.
        2. Any semantic function that can be exemplified with a example.
        3. Examples are cleared via `context_exit`.
        """
        if func == context_enter and isinstance(kwargs["ctx"], Exemplars):
            cls._context_stack.append(kwargs["ctx"])
            return DummyPlan(signer=cls.__name__, final=True) if plan is None else plan

        if func == context_exit and isinstance(kwargs["ctx"], Exemplars):
            cls._context_stack.pop()
            return DummyPlan(signer=cls.__name__, final=True) if plan is None else plan

        if not isinstance(plan, LLMCallExecutionPlan):
            return NotImplemented

        # Gather everything from the stack and add to the plan.
        if cls._context_stack:
            if plan.prompt_renderer.exemplars is None:
                exemplars = []
            else:
                exemplars = plan.prompt_renderer.exemplars.root
            for layer in cls._context_stack:
                exemplars.extend(layer.root)
            plan.prompt_renderer.exemplars = Exemplars(exemplars)
            plan.sign(cls.__name__, f"adding {len(cls._context_stack)} exemplars")

        return plan


@register
class StrategyBackend(ContextBackend[Strategy]):
    """The backend is responsive to `Strategy` semantics."""

    _context_stack: list[Strategy] = []

    @classmethod
    def __semantic_dependencies__(cls) -> list[type[SupportsSemanticFunction]]:
        return [LLMBackend]

    @classmethod
    def __semantic_function__(
        cls,
        func: Callable[..., Any],
        kwargs: Dict,
        dispatcher: Dispatcher | None = None,
        plan: BaseExecutionPlan | None = None,
    ) -> BaseExecutionPlan:
        """The backend recognizes strategy in the context and applies it to the plan.
        It's only applicable to LLMCallExecutionPlan.
        """
        if func == context_enter and isinstance(kwargs["ctx"], Strategy):
            cls._context_stack.append(kwargs["ctx"])
            return DummyPlan(signer=cls.__name__, final=True) if plan is None else plan

        if func == context_exit and isinstance(kwargs["ctx"], Strategy):
            cls._context_stack.pop()
            return DummyPlan(signer=cls.__name__, final=True) if plan is None else plan

        if not isinstance(plan, LLMCallExecutionPlan):
            return NotImplemented

        # Gather everything from the stack and add to the plan.
        if cls._context_stack:
            strategies = "\n".join(str(strategy) for strategy in cls._context_stack)
            plan.prompt_renderer.instruction = Text(
                f"{plan.prompt_renderer.instruction}\n\n"
                f"Please follow the following strategies when responding:\n\n{strategies}"
            )
            plan.sign(cls.__name__, f"adding {len(cls._context_stack)} strategies")

        return plan


@register
class GuardBackend(ContextBackend[Guards]):
    """The backend is responsive to `Guard` semantics."""

    _context_stack: list[Guards] = []

    @classmethod
    def __semantic_dependencies__(cls) -> list[type[SupportsSemanticFunction]]:
        return [LLMBackend]

    @classmethod
    def __semantic_function__(
        cls,
        func: Callable[..., Any],
        kwargs: Dict,
        dispatcher: Dispatcher | None = None,
        plan: BaseExecutionPlan | None = None,
    ) -> BaseExecutionPlan:
        """The backend recognizes guard in the context and applies it to the plan.
        It's only applicable to LLMCallExecutionPlan.
        """
        if func == context_enter and isinstance(kwargs["ctx"], Guards):
            cls._context_stack.append(kwargs["ctx"])
            return DummyPlan(signer=cls.__name__, final=True) if plan is None else plan

        if func == context_exit and isinstance(kwargs["ctx"], Guards):
            cls._context_stack.pop()
            return DummyPlan(signer=cls.__name__, final=True) if plan is None else plan

        if not isinstance(plan, LLMCallExecutionPlan):
            return NotImplemented

        # Gather everything from the stack and add to the plan.
        if cls._context_stack:
            if plan.guards is None:
                guards = []
            else:
                guards = plan.guards.root
            for layer in cls._context_stack:
                guards.extend(layer.root)
            plan.guards = Guards(guards)
            plan.sign(cls.__name__, f"adding {len(cls._context_stack)} guards")

        return plan
