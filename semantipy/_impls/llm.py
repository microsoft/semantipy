import json
import dotenv
from typing import TypeVar

dotenv.load_dotenv()

import textwrap
from langchain.prompts import ChatPromptTemplate, ChatMessagePromptTemplate
from langchain.schema import SystemMessage, StrOutputParser
from langchain.output_parsers import RegexParser, PydanticOutputParser
from langchain_openai import ChatOpenAI

from semantipy.semantics import PythonFunction, StructuredDocument, Semantics, Text, empty
from semantipy.renderer import TextRenderer

_lm = ChatOpenAI(model="gpt-4o", temperature=0.0)

ExtractType = TypeVar("ExtractType", bound=Semantics)


def _lm_python_function_apply(s: PythonFunction, changes: Semantics):
    if not isinstance(s, PythonFunction):
        return NotImplemented

    system_msg = """
        Please apply the changes to a Python function.

        Modify the code according to the changes provided. Update the intent if necessary.
        Please do not change the function name unless the changes specifically require it.
        If the name, intent, or code does not need to be changed, please write the original value in the response.

        Respond in the following format:

        **Updated Function Name**: <name>

        **Updated Function Intent**: <intent>

        **Updated Function Code**:

        ```python
        <code>
        ```
        """

    user_msg_template = """
        **Function Name**: {name}
        
        **Function Intent**: {intent}
        
        **Function Code**:
        
        ```python
        {code}
        ```

        **Changes Wanted**: {changes}
        """

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", textwrap.dedent(system_msg).strip()), ("user", textwrap.dedent(user_msg_template).strip())]
    )

    parser = RegexParser(
        regex=(
            r"\*\*Updated Function Name\*\*: (.*)\s+"
            r"\*\*Updated Function Intent\*\*: (.*)\s+"
            r"\*\*Updated Function Code\*\*:\s+```python\n([\s\S]+)\n```"
        ),
        output_keys=["name", "intent", "code"],
    )

    chain = prompt_template | _lm | parser

    output = chain.invoke({"name": s.entrypoint, "intent": s.intent, "code": s.content, "changes": changes})
    return PythonFunction(content=output["code"], entrypoint=output["name"], intent=output["intent"])


def _lm_python_function_generate(intent: Text) -> PythonFunction:
    system_msg = """
        Please generate a Python function that satisfies the following intent.
        The function should be complete and ready to use.

        Respond in the following format:

        **Function Name**: <name>

        **Function Intent**: <intent>

        **Function Code**:

        ```python
        <code>
        ```
        """

    user_msg_template = """
        **Function Intent**: {intent}
        """

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", textwrap.dedent(system_msg).strip()), ("user", textwrap.dedent(user_msg_template).strip())]
    )

    parser = RegexParser(
        regex=(
            r"\*\*Function Name\*\*: (.*)\s+"
            r"\*\*Function Intent\*\*: (.*)\s+"
            r"\*\*Function Code\*\*:\s+```python\n([\s\S]+)\n```"
        ),
        output_keys=["name", "intent", "code"],
    )

    chain = prompt_template | _lm | parser

    output = chain.invoke({"intent": intent})
    return PythonFunction(content=output["code"], entrypoint=output["name"], intent=output["intent"])


def _lm_structured_document_apply(s: StructuredDocument, changes: Semantics):
    if not isinstance(s, StructuredDocument):
        return NotImplemented

    system_msg = """
        Please apply the changes to the following document.

        Modify the contents according to the changes provided. Update the title if necessary.

        Respond in the same format as the original document, with the changes applied, wrapped in a JSON code block.
        Do not include anything other than the modified document in your response.

        Your response should look like:

        ```json
        <modified_document>
        ```
        """

    user_msg_template = """
        Document:

        ```json
        {document}
        ```

        Changes Wanted: {changes}
        """

    prompt_template = ChatPromptTemplate.from_messages(
        [("system", textwrap.dedent(system_msg).strip()), ("user", textwrap.dedent(user_msg_template).strip())]
    )

    parser = RegexParser(
        regex=r"```json\n([\s\S]+)\n```",
        output_keys=["document"],
    )

    chain = prompt_template | _lm | parser

    output = chain.invoke({"document": json.dumps(s.model_dump_json(), indent=2), "changes": changes})
    return StructuredDocument.model_validate(json.loads(output["document"]))


def _lm_select(s: Semantics, index: Semantics, dtype: type[ExtractType] | None = None) -> ExtractType:
    system_msg = "Please extract the desired information from the text."

    if index is not empty:
        system_msg += " The information to extract is: " + str(index)
    else:
        system_msg += " The desired information is the most important part of the text, typically the final answer, or the main point."

    if dtype is not None:
        system_msg += (
            "\n\nThe extracted information should be of type: "
            + str(dtype)
            + ". "
            + "The response should be evaluatable to the desired type with `ast.literal_eval`. "
            + "For example, if the extracted information is a string, you should respond with '<answer>'. "
            + "If the extracted information is a list of numbers, you should respond with [1, 2, 3]. "
        )

    system_msg += "\n\nOutput nothing else other than the extracted information."

    user_msg_template = "Text:\n\n{document}"

    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=system_msg.strip()),
            ChatMessagePromptTemplate.from_template(role="user", template=user_msg_template.strip()),
        ]
    )

    parser = StrOutputParser()

    chain = prompt_template | _lm | parser
    output = chain.invoke({"document": TextRenderer().render(s)})

    if dtype is not None:
        return dtype(output)  # type: ignore
    else:
        return output  # type: ignore


def _lm_structurize_document(s: Text) -> StructuredDocument:
    system_msg = """
        Please structure the following text into a document.

        Respond in the following format:

        ```json
        {
            "title": "<title>",
            "content": [<content>] or "<content>"
        }
        ```

        Here, content is a list of nested documents or a text string.
        """

    user_msg_template = """
        Text:

        {text}
        """

    prompt_template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=textwrap.dedent(system_msg).strip()),
            ChatMessagePromptTemplate.from_template(role="user", template=textwrap.dedent(user_msg_template).strip()),
        ]
    )

    parser = RegexParser(
        regex=r"```json\n([\s\S]+)\n```",
        output_keys=["document"],
    )

    chain = prompt_template | _lm | parser

    output = chain.invoke({"text": s})
    return StructuredDocument.model_validate(json.loads(output["document"]))
