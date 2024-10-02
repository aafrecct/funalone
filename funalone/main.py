from __future__ import annotations

from sys import stderr
from typing import Callable
from unittest.mock import MagicMock
from inspect import ismethod
import builtins

BUILTIN_NAMES = dir(builtins)


def isolated_test_for(
    tested_function: Callable,
    *,
    is_method: bool = False,
    mock_builtins: bool = False,
    alert_on_default_mock: bool = False,
    custom_mocked_objects: dict | None = None,
    **kw_custom_mocked_objects,
):
    if custom_mocked_objects is None:
        custom_mocked_objects = {}
    custom_mocked_objects |= kw_custom_mocked_objects
    global_context = IsolatedContext(custom_mocked_objects, mock_builtins)

    def isolated_fn():
        return type(tested_function)(tested_function.__code__, global_context)

    def wrapper(test_fn):
        def wrapped(*args, **kwargs):
            if is_method:
                new_args = (args[0], isolated_fn(), *args[1:])
            else:
                new_args = (isolated_fn(), *args)

            result = test_fn(*new_args, **kwargs)
            print(global_context, file=stderr)

            for key in global_context.object_access_count:
                if alert_on_default_mock and key not in custom_mocked_objects:
                    print(
                        f"`{key}` is not properly mocked and uses a default Mock.",
                        file=stderr,
                    )

            return result

        return wrapped

    return wrapper


class IsolatedContext(dict):
    def __init__(self, mocked_objects: dict, mock_builtins: bool = False) -> None:
        self.object_access_count = {}
        self.mocked_objects = mocked_objects
        self.mock_builtins = mock_builtins

    def get(self, item: str, default=None):
        if default is not None:
            return default
        if not self.mock_builtins and item in BUILTIN_NAMES:
            raise KeyError(item)

        self.object_access_count.setdefault(item, 0)
        self.object_access_count[item] += 1
        if result := self.mocked_objects.get(item):
            return result

        return MagicMock(name=item)

    def __str__(self) -> str:
        accessct_str = "\n\t".join(
            f"{k}: {v}" for k, v in self.object_access_count.items()
        )
        if not accessct_str.strip():
            accessct_str = "<No external dependencies>"
        return "Dependency access count: \n" f"\t{accessct_str}"

    def __getitem__(self, item: str):
        return self.get(item)
