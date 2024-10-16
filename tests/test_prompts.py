from jinja2 import Template, Environment, PackageLoader
from semantipy.semantics import Exemplar
from semantipy.ops import SemanticOperationRequest, apply
from semantipy.impls.lm.template import SemantipyPromptTemplate


def test_main_jinja2():
    env = Environment(loader=PackageLoader("semantipy", "impls/lm/prompts"), trim_blocks=True, lstrip_blocks=True)
    template = env.get_template("main.jinja2")
    assert (
        template.render(
            task="Sum two numbers",
            instructions=["Sum two numbers", "Provide the sum of two numbers"],
            formatting="Return the number with nothing else.",
            exemplars=[{"input": "1 2", "output": "3"}, {"input": "3 4", "output": "7"}],
            user_input="5 6",
            user_contexts=["I want to sum two numbers."],
        )
        == """<|semantipy_chat_system|>
Sum two numbers

### Step-by-step Task Instructions ###

(1) Sum two numbers
(2) Provide the sum of two numbers

### Formatting Instructions ###

Return the number with nothing else.

<|semantipy_chat_human|>
1 2
<|semantipy_chat_ai|>
3
<|semantipy_chat_human|>
3 4
<|semantipy_chat_ai|>
7
<|semantipy_chat_human|>
### Context ###

Please consider the following information when completing the user task below:

- I want to sum two numbers.

### User Task ###

5 6"""
    )

    assert (
        template.render(
            task="Sum two numbers",
            formatting="Return the number with nothing else.",
            exemplars=[{"input": "1 2", "output": "3"}, {"input": "3 4", "output": "7"}],
            user_exemplars=[{"input": "5 6", "output": "11"}],
            user_input="7 8",
        )
        == """<|semantipy_chat_system|>
Sum two numbers

### Formatting Instructions ###

Return the number with nothing else.

### Exemplars ###

**Exemplar 1:**
**Human:**
1 2
**Assistant:**
3

**Exemplar 2:**
**Human:**
3 4
**Assistant:**
7

The exemplars above are provided by the system as examples of how to complete the task.
You can use them as a reference when completing the task.
<|semantipy_chat_human|>
5 6
<|semantipy_chat_ai|>
11
<|semantipy_chat_human|>
7 8"""
    )

    assert (
        template.render(task="Sum two numbers", user_input="5 6")
        == """<|semantipy_chat_system|>
Sum two numbers

<|semantipy_chat_human|>
5 6"""
    )


def test_yamls():
    assert (
        "\n\n---\n\n".join(
            [
                message.content
                for message in SemantipyPromptTemplate.from_file("resolve.yaml").input("What's an apple?").render()
            ]
        )
        == """You are a helpful assistant. You may see a request, an expression or a question. You will resolve it with the best of your knowledge.

### Step-by-step Task Instructions ###

(1) For simple questions, please write the answer directly without any additional texts in the response.
(2) For complex questions (e.g., mathematical problems or reasoning tasks), you should think about it step by step first. Then write the answer after `**Answer:**`.
(3) If the request contains a specific return type, please write your answer in that type. That means, the answer should be evaluatable to the desired return type with `ast.literal_eval`.

### Formatting Instructions ###

For simple questions, output the answer with nothing else. For complex questions, output the answer after `**Answer:**`.

---

**Request:**: What is the capital of France?

---

Paris

---

**Request:**: Which is a faster way to get to work?
Option 1: Take a 1000 minute bus, then a half hour train, and finally a 10 minute bike ride.
Option 2: Take an 800 minute bus, then an hour train, and finally a 30 minute bike ride."

**Return type**: <class 'int'>

---

Option 1 will take 1000+30+10 = 1040 minutes.
Option 2 will take 800+60+30 = 890 minutes.
Since Option 2 takes 890 minutes and Option 1 takes 1040 minutes, Option 2 is faster.

**Answer:** 2

---

**Request:**: A coin is heads up. Maybelle flips the coin. Shalonda does not flip the coin. Is the coin still heads up?

**Return type**: <class 'bool'>

---

The coin was flipped by Maybelle. So the coin was flipped 1 time, which is an odd number. The coin started heads up, so after an odd number of flips, it will be tails up.

**Answer:** False

---

What's an apple?"""
    )

    assert (
        "\n\n---\n\n".join(
            [
                message.content
                for message in SemantipyPromptTemplate.from_file("apply.yaml")
                .input(
                    SemanticOperationRequest(operator="test", operand="some content", guest_operand="some modification")
                )
                .render()
            ]
        )
    ) == """Please apply the changes to the following content.

### Step-by-step Task Instructions ###

(1) Modify the contents according to the changes provided.
(2) Do not touch the parts that are not mentioned in the changes.

### Formatting Instructions ###

Respond in the same format as the original content, with the changes applied. Do not include anything other than the modified content in your response.

---

**Original content:**: some content

**Changes**: some modification"""

    assert (
        "\n\n---\n\n".join(
            [
                message.content
                for message in SemantipyPromptTemplate.from_file("apply.yaml")
                .input(
                    SemanticOperationRequest(operator="test", operand="some content", guest_operand="some modification", contexts=[
                        Exemplar(input=apply.bind("content 1",  "modification 1"), output="result 1"),
                        "some additional context"
                    ])
                )
                .render()
            ]
        ) == """Please apply the changes to the following content.

### Step-by-step Task Instructions ###

(1) Modify the contents according to the changes provided.
(2) Do not touch the parts that are not mentioned in the changes.

### Formatting Instructions ###

Respond in the same format as the original content, with the changes applied. Do not include anything other than the modified content in your response.

---

**Original content:**: content 1

**Changes**: modification 1

---

result 1

---

### Context ###

Please consider the following information when completing the user task below:

- some additional context

### User Task ###

**Original content:**: some content

**Changes**: some modification""")


test_main_jinja2()
test_yamls()
