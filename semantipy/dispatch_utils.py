# Copied from https://nbviewer.org/gist/shoyer/1f0a308a06cd96df20879a1ddb8f0006

import functools


def get_overloaded_types_and_args(relevant_args):
    """Returns a list of arguments on which to call __semantic_function__.

    __semantic_function__ implementations should be called in order on the return
    values from this function.
    """
    from .semantics.base import Semantics

    # Runtime is O(num_arguments * num_unique_types)
    overloaded_types = []
    overloaded_args = []
    for arg in relevant_args:
        arg_type = type(arg)
        if arg_type not in overloaded_types:
            try:
                semantic_function = arg_type.__semantic_function__
            except AttributeError:
                continue

            overloaded_types.append(arg_type)

            if semantic_function is not Semantics.__semantic_function__:
                index = len(overloaded_args)
                for i, old_arg in enumerate(overloaded_args):
                    if issubclass(arg_type, type(old_arg)):
                        index = i
                        break
                overloaded_args.insert(index, arg)

    return overloaded_types, overloaded_args


def full_name(obj):
    return f"{obj.__module__}.{obj.__qualname__}"


def attempt_augmented_error_message(error, append_message):
    """Attempt to recreate an error with an appended message."""
    try:
        return type(error)(error.args[0] + append_message, *error.args[1:])
    except Exception:
        return error


def try_semantic_function_override(func, relevant_arguments, args, kwargs):
    # TODO: consider simplifying the interface, to only require either `types`
    # (by calling __semantic_function__ a classmethod) or `overloaded_args` (by
    # dropping `types` from the signature of __semantic_function__)
    types, overloaded_args = get_overloaded_types_and_args(relevant_arguments)
    if not overloaded_args:
        return False, None

    for overloaded_arg in overloaded_args:
        # Note that we're only calling __semantic_function__ on the *first*
        # occurrence of each argument type. This is necessary for reasonable
        # performance with a possibly long list of overloaded arguments, for
        # which each __semantic_function__ implementation might reasonably need to
        # check all argument types.
        try:
            result = overloaded_arg.__semantic_function__(func, types, args, kwargs)
        except Exception as error:
            # Ensure the type of the overloaded argument ends up in the
            # traceback
            message = " [while calling {!r} implementation of {!r}]".format(
                full_name(type(overloaded_arg)), full_name(func)
            )
            new_error = attempt_augmented_error_message(error, message)
            # Would probably need to use six to do this sanely on Python 2:
            # https://stackoverflow.com/questions/9157210/
            raise new_error.with_traceback(error.__traceback__) from None

        if result is not NotImplemented:
            return True, result

    raise TypeError(
        "no implementation found for {} on types that implement "
        "__semantic_function__: {}".format(func, list(map(type, overloaded_args)))
    )


def semantic_function_dispatch(dispatcher):
    """Wrap a function for dispatch with the __semantic_function__ protocol."""

    def decorator(func):
        @functools.wraps(func)
        def new_func(*args, **kwargs):
            relevant_arguments = dispatcher(*args, **kwargs)
            success, value = try_semantic_function_override(new_func, relevant_arguments, args, kwargs)
            if success:
                return value
            return func(*args, **kwargs)

        return new_func

    return decorator
