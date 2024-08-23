import dotenv

dotenv.load_dotenv()

from semantipy import Text, select, apply, context, Exemplars, Exemplar, TypedSelector

def test_select():
    text = Text("Natalia sold 48/2 = <<48/2=24>>24 clips in May. Natalia sold 48+24 = <<48+24=72>>72 clips altogether in April and May. #### 72")
    assert select(text, TypedSelector(type=int)) == 72

def test_select_with_context():
    with context(Exemplars([
        Exemplar(
            input={
                "s": Text("Amanda has 24 apples."),
                "selector": TypedSelector(type=str, selector=Text("Person name")),
            },
            output="Amanda"
        )
    ])):
        text = Text("Natalia sold 48/2 = <<48/2=24>>24 clips in May. Natalia sold 48+24 = <<48+24=72>>72 clips altogether in April and May. #### 72")
        assert select(text, TypedSelector(type=str, selector=Text("The sold object"))) == "clips"

def test_apply():
    text = Text("paris")
    assert apply(text, Text("Capitalize")) == Text("Paris")

test_select()
test_select_with_context()
test_apply()
