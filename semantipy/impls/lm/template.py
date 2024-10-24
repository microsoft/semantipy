from __future__ import annotations

__all__ = [
    "RegexOutputParser",
    "SemantipyPromptTemplate",
]

import ast
import re
from pathlib import Path
from typing import List, Optional, Any, Union

import yaml
from jinja2 import Template, Environment, PackageLoader
from pydantic import Field, ConfigDict

from langchain.prompts import ChatPromptTemplate
from langchain.schema import BaseMessage, ChatMessage, SystemMessage, HumanMessage, AIMessage

from semantipy.ops.base import SemanticOperationRequest
from semantipy.semantics import Semantics, SemanticModel, Text, Exemplar


def get_template(name: str) -> Template:
    env = Environment(loader=PackageLoader("semantipy", "impls/lm/prompts"), trim_blocks=True, lstrip_blocks=True)
    return env.get_template(name)


class RegexOutputParser(SemanticModel):
    """Use a regular expression to parse the output."""

    pattern: str
    return_type: Optional[type] = Field(default=None)
    multi: bool = Field(default=False)

    def to_return_type(self, value: Any) -> Any:
        if self.return_type is None:
            return value
        if isinstance(value, str) and not issubclass(self.return_type, str):
            value = ast.literal_eval(value)
        return self.return_type(value)  # type: ignore

    def parse(self, output: Text) -> Any:
        all_matches = []
        for match in re.finditer(self.pattern, output):
            if match is None:
                raise ValueError(f"Failed to parse the output with the pattern `{self.pattern}`: {output}")
            if not self.multi:
                return self.to_return_type(match.group(1))
            all_matches.append(self.to_return_type(match.group(1)))
        if not self.multi:
            raise ValueError(f"Failed to parse the output with the pattern `{self.pattern}`: {output}")
        return all_matches


class SemantipyPromptTemplate(SemanticModel):
    """The general prompt template used by semantipy to implement the operators."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # Task requirements that are specified by developers.

    task: Text
    instructions: Optional[List[Text]] = Field(default=None)
    formatting: Optional[Text] = Field(default=None)
    exemplars: Optional[List[Exemplar]] = Field(default=None)

    input_template: Optional[Text] = Field(default=None)
    parser: Optional[RegexOutputParser] = Field(default=None)

    # User inputs provided by users.
    user_input: Union[Text, Semantics, None] = Field(default=None)
    user_exemplars: Optional[List[Exemplar]] = Field(default=None)
    user_contexts: Optional[List[Text]] = Field(default=None)

    def input(self, request: SemanticOperationRequest | Text | str) -> SemantipyPromptTemplate:
        # Fork the current prompt template with the new user input.
        if isinstance(request, str):
            return self.model_copy(update={"user_input": Text(request)})
        return self.model_copy(
            update={
                "user_input": request.model_copy(update={"contexts": None}),
                "user_exemplars": [ctx for ctx in request.contexts if isinstance(ctx, Exemplar)],
                "user_contexts": [ctx for ctx in request.contexts if not isinstance(ctx, Exemplar)],
                "parser": (
                    self.parser.model_copy(
                        update={"return_type": request.return_type, "multi": request.return_iterable}
                    )
                    if self.parser is not None
                    else None
                ),
            }
        )

    def render_exemplar_or_user_input(self, request: Text | SemanticOperationRequest | Any) -> Text:
        if isinstance(request, str):
            return Text(request)
        elif isinstance(request, SemanticOperationRequest) and self.input_template is not None:
            return Text(Template(source=self.input_template).render(request.model_dump()))
        else:
            raise ValueError(f"Failed to render the input: {request}")

    def render(self) -> List[BaseMessage]:
        if self.user_input is None:
            raise ValueError("The user input is required to render the prompt.")
        copy = self.model_copy(
            update={
                "exemplars": (
                    [
                        Exemplar(input=self.render_exemplar_or_user_input(exemplar.input), output=exemplar.output)
                        for exemplar in self.exemplars
                    ]
                    if self.exemplars is not None
                    else None
                ),
                "user_exemplars": (
                    [
                        Exemplar(input=self.render_exemplar_or_user_input(exemplar.input), output=exemplar.output)
                        for exemplar in self.user_exemplars
                    ]
                    if self.user_exemplars is not None
                    else None
                ),
                "user_input": self.render_exemplar_or_user_input(self.user_input),
            }
        )
        string = get_template("main.jinja2").render(copy.model_dump())
        regex = re.compile(
            r"<\|semantipy_chat_(?P<role>system|human|ai)\|>\s*(?P<content>.*?)(?=\s*<\|semantipy_chat_\w+\|>|$)",
            re.DOTALL,
        )
        return [
            self._create_message(match.group("role"), match.group("content")) for match in regex.finditer(string)
        ]
    
    def _create_message(self, role: str, content: str) -> BaseMessage:
        if role == "system":
            return SystemMessage(content=content)
        elif role == "human":
            return HumanMessage(content=content)
        elif role == "ai":
            return AIMessage(content=content)
        else:
            raise TypeError(f"Unknown role: {role}")

    @classmethod
    def from_config(cls, config: dict) -> SemantipyPromptTemplate:
        config["parser"] = RegexOutputParser(**config["parser"]) if "parser" in config else None
        if "exemplars" in config:
            config["exemplars"] = [
                Exemplar(
                    input=SemanticOperationRequest(operator=Text("Exemplar. Operator unknown."), **exemplar["input"]),
                    output=Text(exemplar["output"]),
                )
                for exemplar in config["exemplars"]
            ]
        return cls(**config)

    @classmethod
    def from_file(cls, filename: Path | str) -> SemantipyPromptTemplate:
        # Treat the filename as a simple name if it is a string.
        if isinstance(filename, str):
            filename = Path(__file__).parent / "prompts" / filename
        with filename.open() as file:
            return cls.from_config(yaml.safe_load(file))
