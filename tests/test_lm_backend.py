from semantipy.impls.lm.backend import configure_lm, LMBackend
from semantipy.ops import apply
from _llm import llm


def test_lm_backend(llm):
    configure_lm(llm)

    plan = LMBackend.__semantic_function__(
        request=apply.bind("test_lm_backend", "Convert to Camel case"),
    )
    assert isinstance(plan._prompt(), list)
    assert plan.execute() == "TestLmBackend"
