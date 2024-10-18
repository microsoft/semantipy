import difflib

from pathlib import Path
from jinja2 import Template, Environment, PackageLoader
from semantipy.semantics import Exemplar
from semantipy.ops import *
from semantipy.impls.lm.template import SemantipyPromptTemplate

WRITE_MODE = False


def _diff(a: str, b: str):
    diff = difflib.ndiff(a.splitlines(keepends=True), b.splitlines(keepends=True))
    return "".join([d for d in diff if not d.startswith('  ')])


def _diff_with_ref(a: str, b_file: str):
    if not WRITE_MODE:
        b = (Path(__file__).parent / "refs" / b_file).read_text()
        return _diff(a, b)

    else:
        # Write mode
        (Path(__file__).parent / "refs" / b_file).write_text(a)


def test_main_jinja2():
    env = Environment(
        loader=PackageLoader("semantipy", "impls/lm/prompts"),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("main.jinja2")
    assert not _diff_with_ref(
        template.render(
            task="Sum two numbers",
            instructions=["Sum two numbers", "Provide the sum of two numbers"],
            formatting="Return the number with nothing else.",
            exemplars=[
                {"input": "1 2", "output": "3"},
                {"input": "3 4", "output": "7"},
            ],
            user_input="5 6",
            user_contexts=["I want to sum two numbers."],
        ),
        "main_01.txt"
    )

    assert not _diff_with_ref(
        template.render(
            task="Sum two numbers",
            formatting="Return the number with nothing else.",
            exemplars=[
                {"input": "1 2", "output": "3"},
                {"input": "3 4", "output": "7"},
            ],
            user_exemplars=[{"input": "5 6", "output": "11"}],
            user_input="7 8",
        ),
        "main_02.txt"
    )

    assert not _diff_with_ref(
        template.render(task="Sum two numbers", user_input="5 6"),
        "main_03.txt"
    )


def _generate_prompt_to_compare(
    filename: str, input: str | SemanticOperationRequest
) -> str:
    return "\n\n---\n\n".join(
        [
            message.content
            for message in SemantipyPromptTemplate.from_file(filename)
            .input(input)
            .render()
        ]  # type: ignore
    )  # type: ignore


def test_yamls():
    assert not _diff_with_ref(
        _generate_prompt_to_compare("resolve.yaml", "What's an apple?"),
        "resolve.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "apply.yaml",
            SemanticOperationRequest(
                operator="test",
                operand="some content",
                guest_operand="some modification",
            ),
        ),
        "apply_01.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "apply.yaml",
            SemanticOperationRequest(
                operator="test",
                operand="some content",
                guest_operand="some modification",
                contexts=[
                    Exemplar(
                        input=apply.bind("content 1", "modification 1"),
                        output="result 1",
                    ),
                    "some additional context",
                ],
            ),
        ),
        "apply_02.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "universal.yaml",
            logical_binary.bind("one of the operator is true", "0", "positive")
        ),
        "universal.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "cast.yaml",
            cast.bind("123.0", int)
        ),
        "cast_01.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "diff.yaml",
            SemanticOperationRequest(
                operator=diff,
                operand="some content",
                guest_operand="other content",
                contexts=[
                    "i'm a context",
                    "some additional context",
                ]
            )
        ),
        "diff_01.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "select.yaml",
            select.bind("some content", "some selection")
        ),
        "select_01.txt"
    )
    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "select.yaml",
            select.bind("some content", "some selection", int)
        ),
        "select_02.txt"
    )
    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "select.yaml",
            select.bind("some content", int)
        ),
        "select_03.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "select_iter.yaml",
            select_iter.bind("some content", "some selection")
        ),
        "select_iter_01.txt"
    )
    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "select_iter.yaml",
            select_iter.bind("some content", "some selection", int)
        ),
        "select_iter_02.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "split.yaml",
            split.bind("some content", "some delimiter")
        ),
        "split_01.txt"
    )
    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "split.yaml",
            split.bind("some content", "some delimiter", int)
        ),
        "split_02.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "combine.yaml",
            combine.bind("some content", "some other content", "more content")
        ),
        "combine_01.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "equals.yaml",
            equals.bind("some content", "some other content")
        ),
        "equals_01.txt"
    )

    assert not _diff_with_ref(
        _generate_prompt_to_compare(
            "contains.yaml",
            contains.bind("some content", "some container")
        ),
        "contains_01.txt"
    )


test_main_jinja2()
test_yamls()
