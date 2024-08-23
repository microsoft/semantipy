import dotenv

from semantipy import Text, TypedSelector, TextualStrategy, select, combine

dotenv.load_dotenv()


def test_guard():
    print(select.guard(input={"s": Text("Amanda has 24 apples."), "selector": TypedSelector(selector="number", type=int)}, expected=24)(
        Text("Natalia sold 48/2 = <<48/2=24>>24 clips in May. Natalia sold 48+24 = <<48+24=72>>72 clips altogether in April and May. #### 72"),
        TypedSelector(type=int)
    ))

def test_strategy():
    assert (select.context(TextualStrategy("Please pay attention to person names and output only the person names in the text."))(
        Text("Natalia sold clips in May."),
        TypedSelector(type=str)
    )) == "Natalia"

def test_combine():
    print(combine(
        Text("Natalia sold clips in May."),
        Text("Natalia sold clips in June."),
    ))

test_guard()

test_strategy()

test_combine()