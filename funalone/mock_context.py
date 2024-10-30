import builtins
from contextlib import ContextDecorator
from dataclasses import dataclass
from enum import Enum
from sys import stderr
from types import FunctionType
from typing import Iterable
from unittest.mock import MagicMock, Mock

from funalone.namespaced_function import create_namespaced_function_clone

BUILTIN_NAMES = dir(builtins)


class IsolatedContextManager(ContextDecorator):
    def __init__(
        self,
        tested_function: FunctionType,
        *,
        mock_builtins: bool = False,
        log_dependency_access_count: bool = False,
        alert_on_default_mock: bool = False,
        custom_mocked_objects: dict | Iterable[tuple[object, Mock]] | None = None,
        name_allow_list: Iterable[object] | bool = False,
        **kw_custom_mocked_objects,
    ):
        global_context = IsolatedContext(
            mock_builtins,
            custom_mocked_objects,
            **kw_custom_mocked_objects,
        )

        self.original_function = tested_function
        self._namespaced_function_clone = create_namespaced_function_clone(
            tested_function,
            global_context,
            keep_original_globals=_process_name_allow_list(name_allow_list),
        )

        def exec_isolated_function(*args, **kwargs):
            self.context.start()
            return self._namespaced_function_clone(*args, **kwargs)

        self.isolated_function = exec_isolated_function
        setattr(self, tested_function.__name__, exec_isolated_function)

        self.context = global_context
        self.mocked_objects = self.context.mocked_objects
        self.log_dependency_access_count = log_dependency_access_count
        self.alert_on_default_mock = alert_on_default_mock

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.log_dependency_access_count:
            print(self.context.dependency_access_count_str(), file=stderr)

        if self.alert_on_default_mock:
            print(self.context.default_mock_alert_str(), file=stderr)

        self.context.end()


class IsolatedContext(dict):
    def __init__(
        self,
        mock_builtins: bool = False,
        custom_mocked_objects: dict | Iterable[tuple[object, Mock]] | None = None,
        **kw_custom_mocked_objects,
    ) -> None:
        custom_mocked_objects = _process_custom_mocks(
            custom_mocked_objects, **kw_custom_mocked_objects
        )

        self.mocked_objects = MockCollection(custom_mocked_objects)
        self.mock_builtins = mock_builtins

    def __getitem__(self, item: str):
        if not self.mock_builtins and item in BUILTIN_NAMES:
            raise KeyError(item)

        return self.mocked_objects._get_mock(item)

    def __str__(self) -> str:
        return str(self.mocked_objects)

    def setdefault(self, key, value) -> None:
        self.mocked_objects.setdefault(key, value)

    def dependency_access_count_str(self) -> str:
        accessct_str = "\n\t".join(
            f"{name}: {mock_item.metadata.active_access_count}"
            for name, mock_item in self.mocked_objects.items()
        )
        if not accessct_str.strip():
            accessct_str = "<No external dependencies>"
        return "Dependency access count: \n" f"\t{accessct_str}"

    def default_mock_alert_str(self) -> str:
        default_mocks = [
            name
            for name, mock_item in self.mocked_objects.items()
            if not mock_item.metadata.is_custom
        ]
        return "\n".join(
            f"`{key}` is not properly mocked and uses a default Mock."
            for key in default_mocks
        )

    def start(self):
        self.mocked_objects.set_state(ContextStates.ACTIVE)

    def end(self):
        self.mocked_objects.set_state(ContextStates.ENDED)


@dataclass
class MockMetadata:
    is_custom: bool
    total_access_count: int
    active_access_count: int


@dataclass
class MockItem:
    object: Mock
    metadata: MockMetadata


class ContextStates(Enum):
    SETUP = 0
    ACTIVE = 1
    ENDED = 2


class MockCollection(dict):
    def __init__(self, init: dict | None = None):
        object.__setattr__(self, "state", ContextStates.SETUP)
        mocks = (
            {k: MockItem(v, MockMetadata(True, 0, 0)) for k, v in init.items()}
            if init
            else {}
        )
        super(__class__, self).__init__(mocks)

    def _get_mock(self, name: str) -> builtins.Any:
        active_access = 1 if self.state == ContextStates.ACTIVE else 0
        if result := super(__class__, self).get(name):
            result.metadata.total_access_count += 1
            result.metadata.active_access_count += active_access
            return result.object

        result = MagicMock(name=name)
        super(__class__, self).__setitem__(
            name, MockItem(result, MockMetadata(False, 1, active_access))
        )
        return result

    def _set_mock(self, name: str, value: builtins.Any) -> None:
        super(__class__, self).__setitem__(
            name, MockItem(value, MockMetadata(True, 1, 0))
        )

    def setdefault(self, name, value) -> None:
        if super(__class__, self).get(name) is not None:
            return
        self._set_mock(name, value)

    def reset_access_counts(self):
        for mock_item in self.values():
            mock_item.metadata.total_access_count = 0
            mock_item.metadata.active_access_count = 0

    def set_state(self, new_state: ContextStates):
        object.__setattr__(self, "state", new_state)

    __getattr__ = _get_mock
    __setattr__ = _set_mock
    __getitem__ = _get_mock
    __setitem__ = _set_mock


def _process_custom_mocks(
    custom_mocked_objects: dict[str, Mock]
    | Iterable[tuple[object, Mock]]
    | None = None,
    **kw_custom_mocked_objects,
) -> dict[str, Mock]:
    if custom_mocked_objects is None:
        result: dict[str, Mock] = {}
    elif not isinstance(custom_mocked_objects, dict) and hasattr(
        custom_mocked_objects, "__iter__"
    ):
        result = {}
        for obj, mock in custom_mocked_objects:
            if isinstance(obj, str):
                result[obj] = mock
            else:
                result[obj.__name__] = mock
    elif isinstance(custom_mocked_objects, dict):
        result = custom_mocked_objects

    result |= kw_custom_mocked_objects
    return result


def _process_name_allow_list(
    name_allow_list: Iterable[object | str] | bool,
) -> list[str] | bool:
    if isinstance(name_allow_list, bool):
        return name_allow_list

    result = []
    for item in name_allow_list:
        if isinstance(item, str):
            result.append(item)
        else:
            result.append(item.__name__)
    return result
