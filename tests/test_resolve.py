from semantipy import Text, resolve, equals, context, Exemplar, Exemplars

import dotenv

dotenv.load_dotenv()


def test_resolve():
    print(resolve(Text("Would a pear sink in water?"), bool))


def test_equals():
    with context(
        Text("ignore the differences in languages and only consider the meanings"),
        Exemplars([
            Exemplar(input={"operator": "equals", "s": "你好", "t": "hello"}, output="1")
        ])
    ):
        print(equals.compile(Text("你好"), Text("hello")))
        assert equals("苹果", "apple")


test_resolve()

test_equals()