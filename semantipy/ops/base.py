from __future__ import annotations

__all__ = [
    "SemanticOperator",
    "semantipy_op",
    "SemanticOperationRequest",
    "Dispatcher",
    "SupportsSemanticFunction",
]

import functools
import textwrap
from collections import defaultdict
from typing import Callable, Protocol, Dict, List, Union, Any, TYPE_CHECKING, overload, Generic, TypeVar
from typing_extensions import Self, ParamSpec

from pydantic import Field, ConfigDict
from semantipy.semantics import Semantics, Exemplar, Text, SemanticModel

if TYPE_CHECKING:
    from semantipy.impls.base import BaseExecutionPlan


ParamSpecType = ParamSpec("ParamSpecType")
ReturnType = TypeVar("ReturnType")


class SemanticOperator(Semantics, Generic[ParamSpecType, ReturnType]):
    """A semantic operator is a callable object that can be dispatched to backends for execution.

    When operator is called, the arguments will be first preprocessed by the preprocessor.
    The interface of the preprocessor is `preprocessor(operator_self, *args, **kwargs) -> SemanticOperationRequest`.
    The request payload will then be sent to backends for execution.
    """

    def __init__(self, func: Callable, preprocessor: Callable[..., SemanticOperationRequest]):
        self.func = func
        self.preprocessor = preprocessor

        self._contexts: list[Semantics] = []

        # Identifier is used by backends to identify the operator.
        # It's currently the original operator object.
        self._identifier: SemanticOperator | None = None

    @property
    def identifier(self) -> SemanticOperator:
        return self._identifier or self

    def impl(self, implementation: Callable[ParamSpecType, ReturnType]) -> Callable[ParamSpecType, ReturnType]:
        # TODO: use context to implement this
        return implementation

    def bind(self, *args, **kwargs) -> SemanticOperationRequest:
        return self.preprocessor(self.identifier, *args, **kwargs)

    def compile(self, *args, **kwargs) -> BaseExecutionPlan:  # type: ignore
        arguments = self.bind(*args, **kwargs)
        dispatcher = Dispatcher(arguments)
        if not self._contexts:
            return dispatcher.dispatch()
        else:
            # Invoke contexts attached locally with the operator
            from .context import context

            with context(*self._contexts):
                return dispatcher.dispatch()

    def fork(self) -> SemanticOperator[ParamSpecType, ReturnType]:
        op = SemanticOperator(self.func, self.preprocessor)
        op._contexts = self._contexts.copy()
        if self._identifier is not None:
            op._identifier = self._identifier
        else:
            op._identifier = self
        return op

    def context(self, ctx: Semantics) -> SemanticOperator[ParamSpecType, ReturnType]:
        """Attach the operator with context. It's NOT in-place."""
        op = self.fork()
        op._contexts.append(ctx)
        return op

    def exemplar(self, input: Semantics, output: Semantics) -> SemanticOperator[ParamSpecType, ReturnType]:
        exemplar = Exemplar(input=input, output=output)
        return self.context(exemplar)

    def __call__(self, *args, **kwargs):  # type: ignore
        plan = self.compile(*args, **kwargs)
        return plan.execute()

    if TYPE_CHECKING:

        def compile(self, *args: ParamSpecType.args, **kwargs: ParamSpecType.kwargs) -> BaseExecutionPlan: ...  # noqa

        def __call__(self, *args: ParamSpecType.args, **kwargs: ParamSpecType.kwargs) -> ReturnType: ...  # noqa

    def __repr__(self) -> str:
        return f"<operator {self.func.__module__}.{self.func.__name__}>"


def _default_preprocessor(operator_self: SemanticOperator, *args, **kwargs) -> SemanticOperationRequest:
    # Dummy preprocessor that simply binds the arguments following the orders from args to kwargs.
    all_operands = list(args) + list(kwargs.values())
    if len(all_operands) == 0:
        raise ValueError("No operands provided for the operator")
    elif len(all_operands) == 1:
        return SemanticOperationRequest(operator=operator_self, operand=all_operands[0])
    elif len(all_operands) == 2:
        return SemanticOperationRequest(operator=operator_self, operand=all_operands[0], guest_operand=all_operands[1])
    else:
        return SemanticOperationRequest(
            operator=operator_self,
            operand=all_operands[0],
            guest_operand=all_operands[1],
            other_operands=all_operands[2:],
        )


class SemanticOperationRequest(SemanticModel):
    """All calls of semantic operators are finally converted into a request payload.

    In the payload, the operator can be either a SemanticOperator object or any Semantics object describing an action.
    Put the primary operand in the `operand` field, the secondary operand in the `guest_operand` field,
    and other operands in the `other_operands` field.
    In case of indexing operations like `apply` and `select`, the indexing is expected in the `index` field.

    The return type is optional, but can be used to hint the backend on the expected return type.
    Some operators imply that an iterable of the same type is returned,
    in which case the iterable should not explicitly be specified in the return type,
    but implied by the operator itself.

    Altogether, the request can be expressed in the form of ::

        return_val: return_type = operand[index].operator(guest_operand, *other_operands)

    That is the general form of all semantic operations supported currently.

    The reason to put all the semantic operation calls into one form of request are in two folds:

    1. We can leverage the type casting and elevation provided by pydantic to ensure the "semantic"-typing of the arguments.
       String will be automatically casted to Text, and other types can be validated.
    2. Implementations do not have to worry about wild arguments in dictionary,
       nor do the frontends need to define one argument specification for each operator type.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    operator: Union[Text, SemanticOperator, Semantics]
    operand: Union[Text, Semantics]
    guest_operand: Union[Text, Semantics] | None = Field(default=None)
    index: Union[Text, Semantics] | None = Field(default=None)
    other_operands: List[Union[Text, Semantics]] = Field(default_factory=list)
    return_type: type | Text | Semantics | None = Field(default=None)
    # return type should always be type except the cases of exemplars
    return_iterable: bool = Field(default=False)
    contexts: List[Union[Text, Semantics]] = Field(default_factory=list)

    def operands(self) -> List[Semantics]:
        operands = [self.operand]
        if self.guest_operand is not None:
            operands.append(self.guest_operand)
        operands.extend(self.other_operands)
        return operands


class SupportsSemanticFunction(Protocol):
    """A protocol for objects that support the __semantic_function__ protocol,
    which implements the logic of executing the operators on specific objects.

    In this project, two types of objects support such protocol.
    One is the subclasses of Semantics, for which the logics for specific types of semantics
    can be conveniently implemented.
    The other is the backends, which implements a general approach (or principle) on
    how the operators should be executed.
    """

    @classmethod
    def __semantic_function__(
        cls,
        request: SemanticOperationRequest,
        dispatcher: Dispatcher | None = None,
        plan: BaseExecutionPlan | None = None,
    ) -> BaseExecutionPlan: ...

    @classmethod
    def __semantic_dependencies__(cls) -> list[type[SupportsSemanticFunction]]:
        """Return a list of backends that this backend depends on."""
        ...


@overload
def semantipy_op(func: Callable[ParamSpecType, ReturnType]) -> SemanticOperator[ParamSpecType, ReturnType]: ...


@overload
def semantipy_op(
    *, preprocessor: Callable[..., SemanticOperationRequest] | None = None
) -> Callable[[Callable[ParamSpecType, ReturnType]], SemanticOperator[ParamSpecType, ReturnType]]: ...


def semantipy_op(func=None, *, preprocessor=None) -> Any:
    """Wrap a function for dispatch with the __semantic_function__ protocol.

    It can be used with `@semantipy_op` or `@semantipy_op(preprocessor=...)`.

    In case it's used with a specified preprocessor,
    the preprocessor will be used to preprocess the arguments before dispatching.
    The preprocessor is expected to return a `SemanticOperationRequest` object.
    The implementation will receive the backend object returned by the preprocessor.
    If no preprocessor is specified, the arguments will be parsed with a default dummy preprocessor.
    """
    if preprocessor is None:
        preprocessor = _default_preprocessor

    def decorator(func):
        op = SemanticOperator(func, preprocessor)
        return functools.wraps(func)(op)

    if func is not None:
        return decorator(func)

    return decorator


class Dispatcher:

    def __init__(self, request: SemanticOperationRequest):
        self.request = request

        self.handlers: list[type[SupportsSemanticFunction]] = []

    def _init_handler_list(self) -> None:
        from semantipy.impls.base import list_backends, BaseBackend, BaseExecutionPlan

        for backend in reversed(list_backends()):
            # Assume the later backends are more specific and should be executed first.
            # Execute the backends in reverse order.
            if backend not in self.handlers:
                self.handlers.append(backend)

    def _sort_dependencies(self) -> None:
        graph_forward = defaultdict(list)
        graph_backward = defaultdict(list)

        for handler in self.handlers:
            for dependency in handler.__semantic_dependencies__():
                if dependency in self.handlers:
                    graph_forward[dependency].append(handler)
                    graph_backward[handler].append(dependency)

        # Topological sort
        # (somewhat stable, for nodes with no dependencies)
        incoming_counts = defaultdict(lambda: 0)
        incoming_counts.update({node: len(dependency) for node, dependency in graph_backward.items()})
        sorted_nodes = []

        queue = [node for node in self.handlers if not incoming_counts[node]]
        while queue:
            node = queue.pop(0)
            sorted_nodes.append(node)
            for used_by in graph_forward[node]:
                incoming_counts[used_by] -= 1
                if not incoming_counts[used_by]:
                    queue.append(used_by)

        if not all(count == 0 for count in incoming_counts.values()):
            raise ValueError(
                "Circular dependency found in the backends: {}".format(
                    {type: count for type, count in incoming_counts.items() if count > 0}
                )
            )

        self.handlers = sorted_nodes

    def dispatch(self) -> BaseExecutionPlan:
        from semantipy.impls.base import BackendNotImplemented, DummyPlan

        self._init_handler_list()

        plan: BaseExecutionPlan | None = None
        dispatch_logs: list[str] = []
        while self.handlers:
            self._sort_dependencies()
            handler = self.handlers.pop(0)

            try:
                dispatch_logs.append(f"handler {handler.__name__} invoked")
                candidate_plan = handler.__semantic_function__(self.request, self, plan)

                if candidate_plan is NotImplemented:
                    # Returns not implemented is considered BackendNotImplemented
                    raise BackendNotImplemented()

                if isinstance(candidate_plan, DummyPlan):
                    # DummyPlan is used to indicate that the handler has handled the request,
                    # but didn't generate any useful plan.
                    dispatch_logs[-1] += ", handled but no plan generated"

                # Update the plan
                plan = candidate_plan

            except BackendNotImplemented as error:
                if len(error.args) > 0:
                    dispatch_logs[-1] += f", but raises not implemented: {error.args}"
                else:
                    dispatch_logs[-1] += ", but raises not implemented"

            except Exception as error:
                message = " [while dispatching {!r}]\n{}".format(
                    self.request.operator, self._render_dispatch_log(dispatch_logs)
                )
                new_error = self._attempt_augmented_error_message(error, message)
                raise new_error.with_traceback(error.__traceback__) from None

            if plan is not None and plan.final:
                dispatch_logs.append(", final plan found")
                break

        if plan is None:
            msg = "No implementation found for {}\n{}".format(
                self.request.operator, self._render_dispatch_log(dispatch_logs)
            )
            raise NotImplementedError(msg)

        return plan

    def execute(self, plan: BaseExecutionPlan) -> Any:
        # TODO: this should be moved outside
        try:
            return plan.execute()
        except Exception as error:
            # Make sure the dispatch log is included in the traceback
            message = " [while executing the generated plan for {!r}]\n{}".format(
                self.request.operator, self._render_dispatch_log(plan.list_signs())
            )
            new_error = self._attempt_augmented_error_message(error, message)
            raise new_error.with_traceback(error.__traceback__) from None

    def _render_dispatch_log(self, dispatch_logs: list[str]) -> str:
        return "Full dispatch log:\n" + "\n".join([textwrap.indent(log, "  ") for log in dispatch_logs])

    def _attempt_augmented_error_message(self, error, append_message):
        """Attempt to recreate an error with an appended message."""
        try:
            return type(error)(error.args[0] + append_message, *error.args[1:])
        except Exception:
            return error
