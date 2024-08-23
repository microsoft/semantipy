from __future__ import annotations

import inspect
import functools
import textwrap
from collections import defaultdict
from typing import Callable, Protocol, Dict, Any, TYPE_CHECKING, overload, Generic, TypeVar
from typing_extensions import Self, ParamSpec

from semantipy.semantics import Semantics, Guard, Guards, Exemplar, Exemplars

if TYPE_CHECKING:
    from semantipy._impls.base import BaseExecutionPlan


ParamSpecType = ParamSpec("ParamSpecType")
ReturnType = TypeVar("ReturnType")


class SemanticOperator(Semantics, Generic[ParamSpecType, ReturnType]):

    def __init__(self, func: Callable, preprocessor: Callable[..., dict] | None = None):
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

    def compile(self, *args, **kwargs) -> BaseExecutionPlan:
        # bind the arguments to the function
        if self.preprocessor is not None:
            arguments = self.preprocessor(self.func, *args, **kwargs)
        else:
            arguments = _bind_arguments(self.func, args, kwargs)
        dispatcher = Dispatcher(self.identifier, arguments)
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

    def guard(
        self,
        input: Dict[str, Any],
        expected: Dict[str, Any] | None = None,
        checker: Callable[[Any, Guard], bool] | None = None,
    ) -> SemanticOperator[ParamSpecType, ReturnType]:
        guard = Guard(input=input, expected=expected, checker=checker)
        op = self.fork()
        if len(op._contexts) > 0 and isinstance(op._contexts[-1], Guards):
            op._contexts[-1].append(guard)
        else:
            op._contexts.append(Guards([guard]))
        return op

    def exemplar(self, input: Any, output: Any) -> SemanticOperator[ParamSpecType, ReturnType]:
        exemplar = Exemplar(input=input, output=output)
        op = self.fork()
        if len(op._contexts) > 0 and isinstance(op._contexts[-1], Exemplars):
            op._contexts[-1].append(exemplar)
        else:
            op._contexts.append(Exemplars([exemplar]))
        return op

    def __call__(self, *args, **kwargs):  # type: ignore
        plan = self.compile(*args, **kwargs)
        return plan.execute()

    if TYPE_CHECKING:

        def compile(self, *args: ParamSpecType.args, **kwargs: ParamSpecType.kwargs) -> BaseExecutionPlan: ...

        def __call__(self, *args: ParamSpecType.args, **kwargs: ParamSpecType.kwargs) -> ReturnType: ...

    def __repr__(self) -> str:
        return f"<operator {self.func.__module__}.{self.func.__name__}>"


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
        func: Callable,
        kwargs: dict,
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
    *, preprocessor: Callable[..., dict] | None = None
) -> Callable[[Callable[ParamSpecType, ReturnType]], SemanticOperator[ParamSpecType, ReturnType]]: ...


def semantipy_op(func=None, *, preprocessor=None) -> Any:
    """Wrap a function for dispatch with the __semantic_function__ protocol."""

    def decorator(func):
        op = SemanticOperator(func, preprocessor)
        return functools.wraps(func)(op)

    if func is not None:
        return decorator(func)
    return decorator


class Dispatcher:

    def __init__(self, func, args):
        self.func = func
        self.args = args

        self.handlers: list[type[SupportsSemanticFunction]] = []

    def _init_handler_list(self) -> None:
        from semantipy._impls.base import list_backends, BaseBackend, BaseExecutionPlan

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
        from semantipy._impls.base import BackendNotImplemented, DummyPlan

        self._init_handler_list()

        plan: BaseExecutionPlan | None = None
        dispatch_logs: list[str] = []
        while self.handlers:
            self._sort_dependencies()
            handler = self.handlers.pop(0)

            try:
                dispatch_logs.append(f"handler {handler.__name__} invoked")
                candidate_plan = handler.__semantic_function__(self.func, self.args, self, plan)

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
                message = " [while dispatching {!r}]\n{}".format(self.func, self._render_dispatch_log(dispatch_logs))
                new_error = self._attempt_augmented_error_message(error, message)
                raise new_error.with_traceback(error.__traceback__) from None

            if plan is not None and plan.final:
                dispatch_logs.append(", final plan found")
                break

        if plan is None:
            msg = "No implementation found for {}\n{}".format(self.func, self._render_dispatch_log(dispatch_logs))
            raise NotImplementedError(msg)

        return plan

    def execute(self, plan: BaseExecutionPlan) -> Any:
        # TODO: this should be moved outside
        try:
            return plan.execute()
        except Exception as error:
            # Make sure the dispatch log is included in the traceback
            message = " [while executing the generated plan for {!r}]\n{}".format(
                self.func, self._render_dispatch_log(plan.list_signs())
            )
            new_error = self._attempt_augmented_error_message(error, message)
            raise new_error.with_traceback(error.__traceback__) from None

    def _render_dispatch_log(self, dispatch_logs: list[str]) -> str:
        return "Full dispatch log:\n" + "\n".join([textwrap.indent(l, "  ") for l in dispatch_logs])

    def _attempt_augmented_error_message(self, error, append_message):
        """Attempt to recreate an error with an appended message."""
        try:
            return type(error)(error.args[0] + append_message, *error.args[1:])
        except Exception:
            return error


def full_name(obj):
    return f"{obj.__module__}.{obj.__qualname__}"


def _bind_arguments(func, args, kwargs) -> dict:
    """This is to formulate the arguments as a dictionary."""

    # Match arguments with given arguments, so that we can use keyword arguments as much as possible.
    # Mutators don't like positional arguments. Positional arguments might not supply enough information.

    # get arguments passed to a function, and save it as a dict
    func_signature = inspect.signature(func)
    bound_arguments = func_signature.bind(*args, **kwargs)
    return dict(bound_arguments.arguments)

    # insp_parameters = inspect.signature(func).parameters
    # argname_list = list(insp_parameters.keys())
    # positional_args = []
    # keyword_args = {}

    # # According to https://docs.python.org/3/library/inspect.html#inspect.Parameter, there are five kinds of parameters
    # # in Python. We only try to handle POSITIONAL_ONLY and POSITIONAL_OR_KEYWORD here.

    # # Example:
    # # For foo(a, b, *c, **d), a and b and c should be kept.
    # # For foo(a, b, /, d), a and b should be kept.

    # for i, value in enumerate(args):
    #     if i >= len(argname_list):
    #         raise ValueError(f"{func} receives extra argument: {value}.")

    #     argname = argname_list[i]
    #     if insp_parameters[argname].kind == inspect.Parameter.POSITIONAL_ONLY:
    #         # positional only. have to be kept.
    #         positional_args.append(value)

    #     elif insp_parameters[argname].kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
    #         # this should be the most common case
    #         keyword_args[argname] = value

    #     elif insp_parameters[argname].kind == inspect.Parameter.VAR_POSITIONAL:
    #         # Any previous preprocessing might be wrong. Clean them all.
    #         # Any parameters that appear before a VAR_POSITIONAL should be kept positional.
    #         # Otherwise, VAR_POSITIONAL might not work.
    #         # For the cases I've tested, any parameters that appear after a VAR_POSITIONAL are considered keyword only.
    #         # But, if args is not long enough for VAR_POSITIONAL to be encountered, they should be handled by other if-branches.
    #         positional_args = args
    #         keyword_args = {}
    #         break

    #     else:
    #         # kind has to be one of `KEYWORD_ONLY` and `VAR_KEYWORD`
    #         raise ValueError(
    #             f"{func} receives positional argument: {value}, but the parameter type is found to be keyword only."
    #         )

    # # use kwargs to override
    # keyword_args.update(kwargs)

    # if positional_args:
    #     raise ValueError(f"Positional arguments unable to be parsed: {positional_args}")

    # return keyword_args
