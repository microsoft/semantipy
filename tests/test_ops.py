import pytest

from semantipy.impls import configure_lm
from semantipy.ops import *
from semantipy.semantics import Text, Exemplar

from _llm import llm


@pytest.fixture(autouse=True, scope="module")
def setup(llm):
    configure_lm(llm)


def test_apply():
    assert apply("apple_banana_cherry", "banana", "replace with grape") == "apple_grape_cherry"
    assert apply("苹果", "translate to English").lower() == "apple"


def test_resolve():
    assert resolve("What's the capital of Russia?") == "Moscow"
    assert resolve("Would a pear sink in water?", bool) == False


def test_cast():
    assert "{'input': 'see otter', 'output': 'loutre de mer'}" in cast(
        Exemplar(input=Text("see otter"), output=Text("loutre de mer")), Text
    )


def test_diff():
    d = diff("iPad is produced by Apple.", "iPhone is produced by Apple.")
    assert isinstance(d, Text)
    assert "Phone" in d

    with context(
        Exemplar(input=diff.bind("iPad is produced by Apple.", "iPhone is produced by Apple"), output="iPad vs. iPhone")
    ):
        assert diff("Windows is published by Microsoft.", "Office is published by Microsoft.") == "Windows vs. Office"


def test_select():
    assert (
        select(
            "Natalia sold 48/2 = <<48/2=24>>24 clips in May. Natalia sold 48+24 = <<48+24=72>>72 clips altogether in April and May. #### 72",
            int,
        )
        == 72
    )

    with context(Exemplar(input=select.bind("Amanda has 24 apples.", "Person name"), output="Amanda")):
        text = Text(
            "Natalia sold 48/2 = <<48/2=24>>24 clips in May. Natalia sold 48+24 = <<48+24=72>>72 clips altogether in April and May. #### 72"
        )
        assert select(text, "The sold object") == "clips"


def test_select_iter():
    with pytest.raises(ValueError):
        assert select_iter("Amanda has 1 apple, 2 bananas and 3 pineapples.", int) == [1, 2, 3]

    assert select_iter("Amanda has 1 apple, 2 bananas and 3 pineapples.", "all numbers", int) == [1, 2, 3]


def test_split():
    assert split("apple, banana, cherry", "comma") == ["apple", "banana", "cherry"]


def test_combine():
    assert (
        combine("Microsoft - AI, Cloud, Productivity", "Computing, Gaming & Apps")
        == "Microsoft - AI, Cloud, Productivity, Computing, Gaming & Apps"
    )


def test_contains():
    assert contains("intention to order a flight", "I want to book a flight from Seattle to London") is True
    assert contains("intention to order a flight", "I want to book a hotel in London") is False


def test_equals():
    assert equals("banana", "香蕉") is True
    assert equals("Microsoft", "Apple") is False

    with context("All tech companies are considered equal."):
        assert equals("Microsoft", "Apple") is True


def test_logical_unary():
    assert logical_unary("check whether the statement is the truth", "Sun rises from the west.") == False
    assert logical_unary("check whether the statement is the truth", "Sun rises from the east.") == True


def test_logical_binary():
    assert logical_binary("Check whether statements have overlaps.", "Apple is a fruit.", "Banana is a fruit.") == True
    assert (
        logical_binary("Check whether statements have overlaps.", "Apple is a fruit.", "Microsoft is a company.")
        == False
    )