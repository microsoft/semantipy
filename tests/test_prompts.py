from jinja2 import Template, Environment, PackageLoader

env = Environment(loader=PackageLoader('semantipy', 'impls/lm/prompts'), trim_blocks=True, lstrip_blocks=True)
template = env.get_template("main.jinja2")
assert template.render(
    task="Sum two numbers",
    instructions=["Sum two numbers", "Provide the sum of two numbers"],
    formatting="Return the number with nothing else.",
    exemplars=[{"input": "1 2", "output": "3"}, {"input": "3 4", "output": "7"}],
    user_input="5 6",
    user_contexts=["I want to sum two numbers."]
) == """<|semantipy_chat_system|>
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

assert template.render(
    task="Sum two numbers",
    formatting="Return the number with nothing else.",
    exemplars=[{"input": "1 2", "output": "3"}, {"input": "3 4", "output": "7"}],
    user_exemplars=[{"input": "5 6", "output": "11"}],
    user_input="7 8",
) == """<|semantipy_chat_system|>
Sum two numbers

### Formatting Instructions ###

Return the number with nothing else.

### Exemplars ###

**Exemplar 1:**
Human: 1 2
AI: 3

**Exemplar 2:**
Human: 3 4
AI: 7

The exemplars above are provided by the system as examples of how to complete the task.
You can use them as a reference when completing the task.
<|semantipy_chat_human|>
5 6
<|semantipy_chat_ai|>
11
<|semantipy_chat_human|>
7 8"""

assert template.render(
    task="Sum two numbers",
    user_input="5 6"
) == """<|semantipy_chat_system|>
Sum two numbers

<|semantipy_chat_human|>
5 6"""
