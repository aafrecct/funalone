from __future__ import annotations

from typing import Any
from collections.abc import Callable

from funalone.types import F


def create_namespaced_function_clone(
    function: F,
    globals: dict[str, Any] | None = None,
    name_override: str | None = None,
    closure: tuple | None = None,
    *,
    keep_original_globals: bool | Callable[[str, Any], bool] = False,
    strip_original_defaults: bool = False,
) -> F:
    """Return a clone of the fuction given with overwritten globals.

    Creates a clone of a function for testing purposes while overwriting it's
    globals so it doesn't have access to it's external dependencies. These
    external dependencies can be replaced with Mock objects for unittesting.
    It also allows overwriting of the functions name, closure, and the erasure
    of default values for arguments, so that all arguments have to be specified
    in tests.

    Args:
        function: The function to clone.
        globals: A dict or dict-like object with the globals to override.
        name_override: Optional name to change name of clone.
        closure: Optional closure override.

        keep_original_globals:
            The globals of the original function that have to be kept, or
            `True` to keep all globals.
        strip_original_defaults: Whether to strip the fuction of defaults or
            keep the original ones.

    Returns:
        A function object with the same __code__ as the original function.
    """

    clone_name = name_override if name_override else f"__cloned_{function.__name__}"
    clone_closure = closure if closure else function.__closure__

    if globals is None:
        globals = {}
    globals = _process_globals(function, globals, keep_original_globals)

    clone_function = type(function)(
        function.__code__,
        globals,
        name=clone_name,
        closure=clone_closure,
    )

    if not strip_original_defaults:
        clone_function.__defaults__ = function.__defaults__
        clone_function.__kwdefaults__ = function.__kwdefaults__

    return clone_function


def _process_globals(
    function: F,
    globals: dict[str, Any],
    keep_original_globals: bool | Callable[[str, Any], bool],
) -> dict[str, Any]:
    """Process the globals of a function to remove unwanted globals.

    Args:
        function: The function to process.
        keep_original_globals: The globals to keep.

    Returns:
        A dict with the processed globals."""

    if isinstance(keep_original_globals, bool):
        if keep_original_globals:
            for key, value in function.__globals__.items():
                globals.setdefault(key, value)
        return globals

    function_used_globals = {
        name: function.__globals__[name]
        for name in function.__code__.co_names
        if name in function.__globals__
    }
    for key, value in function_used_globals.items():
        if keep_original_globals(key, value):
            globals.setdefault(key, value)

    return globals
