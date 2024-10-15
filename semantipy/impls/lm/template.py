from __future__ import annotations

import re
from typing import List, Optional

from jinja2 import Template, Environment, PackageLoader
from pydantic import Field

from langchain.prompts import ChatPromptTemplate
from langchain.schema import ChatMessage

from semantipy.ops.base import SemanticOperationRequest
from semantipy.semantics import SemanticModel, Text, Exemplar

def get_template(name: str) -> Template:
    env = Environment(loader=PackageLoader('semantipy', 'impls/lm/prompts'), trim_blocks=True, lstrip_blocks=True)
    return env.get_template(name)

class SemantipyOutputParser(SemanticModel):
    """The general output parser used by semantipy to extract the results."""

    return_type: type = Field(default=str)


class ExemplarTemplate(SemanticModel):

    source_file: str

    def render(self, request: SemanticOperationRequest) -> Text:
        return Text(get_template(self.source_file).render(request.model_dump()))



class SemantipyPromptTemplate(SemanticModel):
    """The general prompt template used by semantipy to implement the operators."""

    # Task requirements that are specified by developers.
    task: Text
    instructions: Optional[List[Text]] = Field(default=None)
    formatting: Optional[Text] = Field(default=None)
    exemplars: Optional[List[Exemplar]] = Field(default=None)

    exemplar_renderer: Optional[ExemplarTemplate] = Field(default=None)
    parser: Optional[SemantipyOutputParser] = Field(default=None)

    # User inputs provided by users.
    user_input: Text
    user_exemplars: Optional[List[Exemplar]] = Field(default=None)
    user_contexts: Optional[List[Text]] = Field(default=None)

    def input(self, input: Text | str, exemplars: Optional[List[Exemplar]] = None, contexts: Optional[List[str]] = None) -> SemantipyPromptTemplate:
        # Fork the current prompt template with the new user input.
        return self.model_copy(update={"user_input": input, "user_exemplars": exemplars, "user_contexts": contexts})

    def render(self) -> List[ChatMessage]:
        regex = re.compile(r"<\|semantipy_chat_(?P<role>system|human|ai)\|>\s*(?P<content>.*?)(?=\s*<\|semantipy_chat_\w+\|>|$)", re.DOTALL)
        return [ChatMessage(role=match.group("role"), content=match.group("content")) for match in regex.finditer(string)]


RESOLVE_TEMPLATE = SemantipyPromptTemplate(
    task="You may see a request, an expression or a question. Please resolve it with the best of your knowledge.",
    instructions=[
        "For simple questions, please write the answer directly without any additional texts in the response.",
        "For complex questions (e.g., mathematical problems or reasoning tasks), you should think about it step by step first. " +
        "Then write the answer after `### Answer ###`.",
        "If the request contains a specific data type, please write your answer in that type. " +
        "That means, the answer should be evaluatable to the desired data type with `ast.literal_eval`."
    ],
    formatting="For simple questions, output the answer with nothing else. For complex questions, output the answer after `### Answer ###`.",
    exemplars=
)