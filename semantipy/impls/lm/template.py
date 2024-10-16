from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import List, Optional, Any, Union

import yaml
from jinja2 import Template, Environment, PackageLoader
from pydantic import Field, ConfigDict

from langchain.prompts import ChatPromptTemplate
from langchain.schema import ChatMessage

from semantipy.ops.base import SemanticOperationRequest
from semantipy.semantics import Semantics, SemanticModel, Text, Exemplar


def get_template(name: str) -> Template:
    env = Environment(loader=PackageLoader("semantipy", "impls/lm/prompts"), trim_blocks=True, lstrip_blocks=True)
    return env.get_template(name)


class RegexOutputParser(SemanticModel):
    """Use a regular expression to parse the output."""

    pattern: str
    return_type: Optional[type] = Field(default=None)

    def to_return_type(self, value: Any) -> Any:
        if self.return_type is None:
            return value
        if isinstance(value, str) and not issubclass(self.return_type, str):
            value = ast.literal_eval(value)
        return self.return_type(value)  # type: ignore

    def parse(self, output: Text) -> Any:
        match = re.search(self.pattern, output)
        if match is None:
            raise ValueError(f"Failed to parse the output with the pattern `{self.pattern}`: {output}")
        return self.to_return_type(match.group(1))


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
                    self.parser.model_copy(update={"return_type": request.return_type})
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

    def render(self) -> List[ChatMessage]:
        if self.user_input is None:
            raise ValueError("The user input is required to render the prompt.")
        copy = self.model_copy(update={
            "exemplars": [
                Exemplar(input=self.render_exemplar_or_user_input(exemplar.input), output=exemplar.output)
                for exemplar in self.exemplars
            ] if self.exemplars is not None else None,
            "user_exemplars": [
                Exemplar(input=self.render_exemplar_or_user_input(exemplar.input), output=exemplar.output)
                for exemplar in self.user_exemplars
            ] if self.user_exemplars is not None else None,
            "user_input": self.render_exemplar_or_user_input(self.user_input),
        })
        string = get_template("main.jinja2").render(copy.model_dump())
        regex = re.compile(
            r"<\|semantipy_chat_(?P<role>system|human|ai)\|>\s*(?P<content>.*?)(?=\s*<\|semantipy_chat_\w+\|>|$)",
            re.DOTALL,
        )
        return [
            ChatMessage(role=match.group("role"), content=match.group("content")) for match in regex.finditer(string)
        ]

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
    def from_file(cls, filename: str) -> SemantipyPromptTemplate:
        path = Path(__file__).parent / "prompts" / filename
        with path.open() as file:
            return cls.from_config(yaml.safe_load(file))
