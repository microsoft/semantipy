from semantipy.impls.lm.backend import LMBackend
from semantipy.ops import apply


def test_lm_backend():
    plan = LMBackend.__semantic_function__(
        request=apply.bind("test_lm_backend", "Convert to Camel case"),
    )
    print(plan._prompt())


test_lm_backend()