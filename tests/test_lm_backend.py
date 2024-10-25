from semantipy.impls.base import SemanticOperationRequest
from semantipy.impls.lm.backend import configure_lm, LMBackend, LMExecutionPlan
from semantipy.ops import apply, context_enter, context_exit, resolve
from semantipy.semantics import Text

from _llm import llm


def test_lm_backend(llm):  # noqa: F811
    configure_lm(llm)

    plan = LMBackend.__semantic_function__(
        request=apply.bind("test_lm_backend", "Convert to Camel case"),
    )
    assert isinstance(plan, LMExecutionPlan)
    assert isinstance(plan.lm_input(), list)
    assert plan.execute() == "TestLmBackend"


def test_lm_backend_anonymous(llm):  # noqa: F811
    configure_lm(llm)

    plan = LMBackend.__semantic_function__(
        request=SemanticOperationRequest(
            operator=Text("Convert to Camel case. First letter of each word should be capitalized."),
            operand=Text("apple_banana_cherry"),
        )
    )
    assert isinstance(plan, LMExecutionPlan)
    assert isinstance(plan.lm_input(), list)
    assert plan.execute() == "AppleBananaCherry"


def test_contexts(llm):  # noqa: F811
    configure_lm(llm)

    context = Text("China has a population of 2 billion in 2050.")
    plan = LMBackend.__semantic_function__(request=SemanticOperationRequest(operator=context_enter, operand=context))
    assert plan.execute() is None
    plan = LMBackend.__semantic_function__(request=resolve.bind("What's the population of China in 2050?"))
    assert isinstance(plan, LMExecutionPlan)
    assert "China has a population of 2 billion in 2050" in plan.lm_input()[-1].content
    assert plan.execute() == "2 billion"
    plan = LMBackend.__semantic_function__(request=SemanticOperationRequest(operator=context_exit, operand=context))
    assert plan.execute() is None
