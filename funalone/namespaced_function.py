from types import FunctionType
from typing import Iterable


def create_namespaced_function_clone(
    function: FunctionType,
    globals: dict,
    name_override: str | None = None,
    closure: tuple | None = None,
    *,
    keep_original_globals: bool | Iterable[str] = False,
) -> FunctionType:
    clone_name = name_override if name_override else f"__cloned_{function.__name__}"
    clone_closure = closure if closure else function.__closure__

    if isinstance(keep_original_globals, bool):
        if keep_original_globals:
            keep_original_globals = function.__globals__.keys()
        else:
            keep_original_globals = []

    for g_varname in keep_original_globals:
        globals.setdefault(g_varname, function.__globals__[g_varname])

    clone_function = FunctionType(
        function.__code__,
        globals,
        name=clone_name,
        closure=clone_closure,
    )

    clone_function.__defaults__ = function.__defaults__
    clone_function.__kwdefaults__ = function.__kwdefaults__

    return clone_function
