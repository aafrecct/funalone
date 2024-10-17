from __future__ import annotations

from sys import stderr
from typing import Callable, Iterable
import unittest
from unittest.mock import MagicMock, Mock
from contextlib import ContextDecorator
import builtins

BUILTIN_NAMES = dir(builtins)


def _process_custom_mocks(
    custom_mocked_objects: dict | Iterable[tuple[object, Mock]] | None = None,
    **kw_custom_mocked_objects,
) -> dict[str, Mock]:
    if custom_mocked_objects is None:
        result = {}
    elif not isinstance(custom_mocked_objects, dict) and hasattr(
        custom_mocked_objects, "__iter__"
    ):
        result = {}
        for obj, mock in custom_mocked_objects:
            if isinstance(obj, str):
                result[obj] = mock
            else:
                result[obj.__name__] = mock
    else:
        result = custom_mocked_objects
    result |= kw_custom_mocked_objects
    return result


class IsolatedContext(dict):
    def __init__(
        self, custom_mocked_objects: dict, mock_builtins: bool = False
    ) -> None:
        self.object_access_count = {}
        self.custom_mocked_objects = custom_mocked_objects
        self.mocked_objects = {}
        self.mock_builtins = mock_builtins

    def __getitem__(self, item: str):
        if not self.mock_builtins and item in BUILTIN_NAMES:
            raise KeyError(item)

        self.object_access_count.setdefault(item, 0)
        self.object_access_count[item] += 1
        if (result := self.custom_mocked_objects.get(item)) is not None:
            return result
        if (result := self.mocked_objects.get(item)) is not None:
            return result

        result = MagicMock(name=item)
        self.mocked_objects[item] = result
        return result

    def __str__(self) -> str:
        return str(self.custom_mocked_objects | self.mocked_objects)

    def dependency_access_count_str(self) -> str:
        accessct_str = "\n\t".join(
            f"{k}: {v}" for k, v in self.object_access_count.items()
        )
        if not accessct_str.strip():
            accessct_str = "<No external dependencies>"
        return "Dependency access count: \n" f"\t{accessct_str}"

    def default_mock_alert_str(self) -> str:
        default_mocks = [
            key
            for key in self.object_access_count
            if key not in self.custom_mocked_objects
        ]
        return "\n".join(
            f"`{key}` is not properly mocked and uses a default Mock."
            for key in default_mocks
        )


class IsolatedContextManager(ContextDecorator):
    def __init__(
        self,
        tested_function: Callable,
        *,
        mock_builtins: bool = False,
        log_dependency_access_count: bool = False,
        alert_on_default_mock: bool = False,
        unittest_testcase: unittest.TestCase = None,
        unittest_with_subtest: bool = False,
        custom_mocked_objects: dict | tuple[object, Mock] | None = None,
        **kw_custom_mocked_objects,
    ):
        custom_mocked_objects = _process_custom_mocks(
            custom_mocked_objects, **kw_custom_mocked_objects
        )
        global_context = IsolatedContext(custom_mocked_objects, mock_builtins)

        def isolated_fn():
            return type(tested_function)(tested_function.__code__, global_context)

        self.original_function = tested_function
        self.isolated_function = isolated_fn()
        self.context = global_context
        self.mock_builtins = mock_builtins
        self.log_dependency_access_count = log_dependency_access_count
        self.alert_on_default_mock = alert_on_default_mock

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.log_dependency_access_count:
            print(self.context.dependency_access_count_str(), file=stderr)

        if self.alert_on_default_mock:
            print(self.context.default_mock_alert_str(), file=stderr)
