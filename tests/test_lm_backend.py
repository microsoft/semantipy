from semantipy.impls.base import SemanticOperationRequest
from semantipy.impls.lm.backend import configure_lm, LMBackend
from semantipy.ops import apply
from semantipy.semantics import Text

from _llm import llm


def test_lm_backend(llm):
    configure_lm(llm)

    plan = LMBackend.__semantic_function__(
        request=apply.bind("test_lm_backend", "Convert to Camel case"),
    )
    assert isinstance(plan._prompt(), list)
    assert plan.execute() == "TestLmBackend"


def test_lm_backend_anonymous(llm):
    configure_lm(llm)

    plan = LMBackend.__semantic_function__(
        request=SemanticOperationRequest(
            operator=Text("Convert to Camel case. First letter of each word should be capitalized."),
            operand=Text("apple_banana_cherry"),
        )
    )
    assert isinstance(plan._prompt(), list)
    assert plan.execute() == "AppleBananaCherry"
