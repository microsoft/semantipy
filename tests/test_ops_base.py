import re
import pytest

import semantipy.impls.base
from semantipy.impls.base import (
    BaseBackend,
    BaseExecutionPlan,
    register_backend,
    unregister_backend,
)
from semantipy.ops.base import Dispatcher, SemanticOperationRequest, semantipy_op
from semantipy.semantics import Text


_registered_backends = semantipy.impls.base._registered_backends.copy()


def setup_module():
    semantipy.impls.base._registered_backends.clear()


def teardown_module():
    semantipy.impls.base._registered_backends.extend(_registered_backends)


class DummyPlan(BaseExecutionPlan):

    def __init__(self, value):
        self.value = value

    def execute(self):
        if self.value == 6:
            raise RuntimeError("Value cannot be 6")
        return self.value


class BackendA(BaseBackend):

    @classmethod
    def __semantic_function__(cls, request, dispatcher, plan):
        plan = DummyPlan(2)
        plan.sign("A", "created")
        return plan


class BackendB(BaseBackend):

    @classmethod
    def __semantic_dependencies__(cls):
        return [BackendA]

    @classmethod
    def __semantic_function__(cls, request, dispatcher, plan):
        assert isinstance(plan, DummyPlan)
        plan.value += 5
        plan.sign("B", "modified")
        return plan


class BackendC(BaseBackend):

    @classmethod
    def __semantic_function__(cls, request, dispatcher, plan):
        plan = DummyPlan(10)
        plan.sign("C", "created")
        return plan


class BackendD(BaseBackend):

    @classmethod
    def __semantic_dependencies__(cls):
        return [BackendA, BackendC]

    @classmethod
    def __semantic_function__(cls, request, dispatcher, plan):
        assert isinstance(plan, DummyPlan)
        if plan.value == 6:
            return plan
        raise ValueError("This should not be called")


class BackendE(BaseBackend):

    @classmethod
    def __semantic_dependencies__(cls):
        return [BackendA]

    @classmethod
    def __semantic_function__(cls, request, dispatcher, plan):
        assert isinstance(plan, DummyPlan)
        plan.value = 1
        plan.sign("E", "modified to 1")
        return plan


def test_dispatcher():
    dummy_request = SemanticOperationRequest(
        operator=Text("dummy"),
        operand=Text("dummy"),
    )

    register_backend(BackendA)

    dispatcher = Dispatcher(dummy_request)
    plan = dispatcher.dispatch()
    assert plan.execute() == 2

    register_backend(BackendB)
    plan = dispatcher.dispatch()
    assert plan.execute() == 7

    unregister_backend(BackendA)
    with pytest.raises(AssertionError):
        dispatcher.dispatch()

    register_backend(BackendC)
    plan = dispatcher.dispatch()
    assert plan.execute() == 15
    assert plan.list_signs() == ["[C] created", "[B] modified"]

    register_backend(BackendA)
    plan = dispatcher.dispatch()
    assert plan.execute() == 15

    register_backend(BackendD)
    with pytest.raises(
        ValueError,
        match=re.escape(
            "This should not be called [while dispatching 'dummy']\n"
            "Full dispatch log:\n"
            "  handler BackendA invoked\n"
            "  handler BackendC invoked\n"
            "  handler BackendB invoked\n"
            "  handler BackendD invoked",
        ),
    ):
        dispatcher.dispatch()

    register_backend(BackendE)
    plan = dispatcher.dispatch()
    with pytest.raises(
        RuntimeError,
        match=re.escape(
            "Value cannot be 6 [while executing the generated plan for 'dummy']\n"
            "Full dispatch log:\n"
            "  [C] created\n"
            "  [E] modified to 1\n"
            "  [B] modified"
        ),
    ):
        dispatcher.execute(plan)

    unregister_backend(BackendA)
    unregister_backend(BackendB)
    unregister_backend(BackendC)
    unregister_backend(BackendD)
    unregister_backend(BackendE)


@semantipy_op
def dummy_op(a: Text, b: Text):
    raise NotImplementedError()


class BackendF(BaseBackend):

    @classmethod
    def __semantic_function__(cls, request, dispatcher, plan):
        return DummyPlan(request.operator.__name__)


def test_semantipy_op():
    register_backend(BackendF)
    assert dummy_op(Text("a"), Text("b")) == "dummy_op"

    unregister_backend(BackendF)
