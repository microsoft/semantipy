import textwrap

from semantipy import PythonFunction, SemanticModel, Text, ChatLogs, StructuredDocument, TypedSelector, apply, select, empty, context
from semantipy.renderer import TextRenderer, StructuredDocumentRenderer, CodeRenderer


def test_python_function_apply():
    fn = PythonFunction(
        content=textwrap.dedent(
            """
        def add(a: int, b: int) -> int:
            return a + b
        """
        ).strip(),
        entrypoint="add",
        intent=Text("Add two numbers"),
    )

    changes = Text("Change the function to subtract two numbers")
    updated_fn = apply(fn, changes)
    assert updated_fn(5, 3) == 2

    fn = PythonFunction(
        content=textwrap.dedent(
            """
        def fibbonaci(n: int) -> int:
            if n <= 1:
                return n
            else:
                return fibbonaci(n - 1) + fibbonaci(n - 2)
        """
        ).strip(),
        entrypoint="fibbonaci",
        intent=None,
    )
    changes = Text("Optimize the performance of the function")
    updated_fn = apply(fn, changes)
    assert updated_fn(10) == fn(10)
    assert updated_fn(40) == 102334155


def test_python_function_write():
    fn = PythonFunction(
        content=textwrap.dedent(
            """
        def add(a: int, b: int) -> int:
            return a + b
        """
        ).strip(),
        entrypoint="add",
        intent=Text("Add two numbers"),
    )

    intent = Text("unit test")
    with context(intent):
        print(CodeRenderer().render(intent))



def test_semantic_model():
    class AnyModel(SemanticModel):
        a: int
        b: int

    AnyModel(a=1, b=2)

    chat_logs = ChatLogs(
        [
            {"role": "human", "content": "Hello!"},
            {"role": "ai", "content": "Hi! How can I help you?"},
        ]
    )
    assert (
        repr(chat_logs)
        == "ChatLogs(root=[ChatMessage(content='Hello!', role='human'), ChatMessage(content='Hi! How can I help you?', role='ai')])"
    )
    assert isinstance(chat_logs.root[0].content, Text)
    assert ChatLogs.model_validate_json(chat_logs.model_dump_json()) == chat_logs

    document = StructuredDocument(
        title="Hello", content=[Text("World"), StructuredDocument(title="Nested", content="Document")]
    )
    assert (
        repr(document)
        == "StructuredDocument(content=['World', StructuredDocument(content='Document', title='Nested')], title='Hello')"
    )
    assert document[1]["title"] == "Nested"
    assert isinstance(document[1]["content"], Text)

    document = StructuredDocument(title="Hello", content="World")

    # FIXME: json dump raises Cannot check isinstance when validating from json, use a JsonOrPython validator instead.
    json = document.model_dump()
    assert document == StructuredDocument.model_validate(json)

    document = StructuredDocument(title="Hello", content={"nested": "Document", "other": Text("Content")})
    assert (
        repr(document)
        == "StructuredDocument(content=OrderedDict([('nested', 'Document'), ('other', 'Content')]), title='Hello')"
    )


def test_structured_document_apply():
    document = StructuredDocument(
        title="Mastering ChatGPT Prompting: The RTF Framework",
        content=[
            {
                "title": "Breaking Down the RTF Framework",
                "content": {
                    "role": {
                        "title": "Role (R): Defining the “Character” of the AI",
                        "content": "The Role aspect of the RTF framework is all about setting the stage for ChatGPT. By specifying a role, you’re essentially telling the AI what perspective to take when answering your question. This can range from a scientist, chef, writer, or any other persona you desire. The role sets the context for the AI’s response.",
                    },
                    "task": {
                        "title": "Task (T): Outlining the Desired Action",
                        "content": "Task represents the action you want ChatGPT to perform. It defines what you want the AI to do in response to your query. Tasks can be diverse, from researching a topic to generating a story, planning a schedule, or solving a problem. Clearly articulating the task helps ChatGPT understand your intentions and deliver relevant responses.",
                    },
                    "format": {
                        "title": "Format (F): Structuring the Response",
                        "content": "The Format component of the RTF framework deals with how you want ChatGPT’s response to be presented. You can specify the format as a list, table, story, diagram, or any other suitable structure. This aspect ensures that the information is delivered in a manner that aligns with your needs.",
                    },
                },
            },
            {
                "title": "Combining RTF Elements for Effective Prompts",
                "content": "To create a powerful prompt using the RTF framework, combine these three elements: Role, Task, and Format. For example: “Act as a Veterinarian, Research different types of dog breeds, Show in a Presentation.” With this prompt, ChatGPT will provide you with a presentation-style report on various dog breeds, adopting the perspective of a veterinarian."
            }
        ],
    )

    changes = Text("Adjust the tone of the content so that it teaches ChatGPT how to write a RTF prompt.")
    document_new = apply(document, changes)

    print(document_new)

    renderer = TextRenderer()
    rendered_old = renderer.render(document)
    rendered_new = renderer.render(document_new)
    assert rendered_old != rendered_new


def test_structurize_document():
    text = Text("Using AI platforms like chat GPTs as prompt generators for various other AI platforms, is akin to learning a new language. While you can certainly stumble through without a clear plan, a structured approach dramatically improves your ability to harness the full potential of chat GPT as prompt generator. This is because AI systems thrive on clarity and precision – the better your input, the more useful and on-target the output.")

    renderer = StructuredDocumentRenderer()
    rendered_text = renderer.render(text)
    assert isinstance(rendered_text, StructuredDocument)


def test_extract():
    text = Text("Natalia sold 48/2 = <<48/2=24>>24 clips in May. Natalia sold 48+24 = <<48+24=72>>72 clips altogether in April and May. #### 72")
    assert select(text, TypedSelector(type=int)) == 72


test_semantic_model()
test_structurize_document()
test_structured_document_apply()
test_python_function_apply()

test_extract()
test_python_function_write()
