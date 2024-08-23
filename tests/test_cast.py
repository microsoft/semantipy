from semantipy import cast, Text, StructuredDocument

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

    print(cast(document, Text))

    # changes = Text("Adjust the tone of the content so that it teaches ChatGPT how to write a RTF prompt.")
    # document_new = apply(document, changes)

    # print(document_new)

    # renderer = TextRenderer()
    # rendered_old = renderer.render(document)
    # rendered_new = renderer.render(document_new)
    # assert rendered_old != rendered_new

test_structured_document_apply()