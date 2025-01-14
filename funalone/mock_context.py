from __future__ import annotations

import builtins
from contextlib import ContextDecorator
from dataclasses import dataclass
from enum import Enum
from sys import stderr
from types import FunctionType
from typing import Any, Iterable, Protocol
from unittest.mock import MagicMock, Mock

from funalone.namespaced_function import create_namespaced_function_clone

BUILTIN_NAMES = dir(builtins)


class NamedObject(Protocol):
    def __name__(self) -> str: ...


class IsolatedFunctionClone(ContextDecorator):
    """A context manager that creates a namespaced clone of a function with
    access to a dummy `globals` object that creates mocks on the fly or serves
    custom ones for the missing external dependencies, while keeping track of
    statistics like access counts.

    Attributes:
        original_function: A reference to the original function..
        context: A reference to the `globals` context of the isolated function.
        mocked_objects: A shortcut reference to the `MockCollection` used by the
            context. Same as `self.context.mocked_objects`.
    """

    def __init__(
        self,
        tested_function: FunctionType,
        *,
        mock_builtins: bool = False,
        log_dependency_access_count: bool = False,
        alert_on_default_mock: bool = False,
        custom_mocked_objects: dict | Iterable[tuple[NamedObject, Mock]] | None = None,
        name_allow_list: Iterable[NamedObject] | bool = False,
        strip_function_defaults: bool = False,
        **kw_custom_mocked_objects,
    ):
        self.context = DefaultMockingContext(
            custom_mocked_objects,
            mock_builtins,
            **kw_custom_mocked_objects,
        )
        self._namespaced_function_clone = create_namespaced_function_clone(
            tested_function,
            self.context,
            keep_original_globals=_process_name_allow_list(name_allow_list),
            strip_original_defaults=strip_function_defaults,
        )
        self.original_function = tested_function
        self.log_dependency_access_count = log_dependency_access_count
        self.alert_on_default_mock = alert_on_default_mock

    def __call__(self, *args, **kwargs):
        self.activate()
        result = self._namespaced_function_clone(*args, **kwargs)
        self.deactivate()
        return result

    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.log_dependency_access_count:
            print(self.dependency_access_count_message(), file=stderr)

        if self.alert_on_default_mock:
            print(self.default_mock_alert_message(), file=stderr)

        self.deactivate()

    def activate(self):
        self.context.set_state(ContextStates.ACTIVE)

    def deactivate(self):
        self.context.set_state(ContextStates.ENDED)

    def dependency_access_count_message(self) -> str:
        accessct_str = "\n\t".join(
            f"{name}: {mock_item.metadata.active_access_count}"
            for name, mock_item in self.context.items()
        )
        if not accessct_str.strip():
            accessct_str = "<No external dependencies>"
        return f"Dependency access count: \n\t{accessct_str}"

    def default_mock_alert_message(self) -> str:
        default_mocks = [
            name
            for name, mock_item in self.context.items()
            if not mock_item.metadata.is_custom
        ]
        return "\n".join(
            f"`{key}` is not properly mocked and uses a default Mock."
            for key in default_mocks
        )


@dataclass
class MockMetadata:
    """A dataclass to track the metadata of a MockItem"""

    is_custom: bool
    total_access_count: int
    active_access_count: int


@dataclass
class MockItem:
    """A pair used by DefaultMockingContext to keep custom mocks along with
    metadata for them."""

    object: Any
    metadata: MockMetadata


class ContextStates(Enum):
    """The posible states in which a DefaultMockingContext might be."""

    SETUP = 0
    ACTIVE = 1
    ENDED = 2


class DefaultMockingContext(dict):
    """A dict-like object that creates MagicMocks on not-found key lookups.

    A collection of key value pairs that returns a new named MagicMock object when
    accesing a key that doesn't exist. For use in a namespaced function for testing
    purposes. It also keeps track of access counts for these objects, to help with
    debugging and allows specification of custom Mock objects for certain keys.

    Attributes:
        mock_builtins: Whether the context mocks builtin names automatically or
            keeps default builtins.
    """

    def __init__(
        self,
        custom_mocked_objects: dict | Iterable[tuple[NamedObject, Mock]] | None = None,
        mock_builtins: bool = False,
        **kw_custom_mocked_objects,
    ):
        object.__setattr__(self, "state", ContextStates.SETUP)
        object.__setattr__(self, "mock_builtins", mock_builtins)

        custom_mocked_objects = _process_custom_mocks(
            custom_mocked_objects, **kw_custom_mocked_objects
        )
        mocks = {
            k: MockItem(v, MockMetadata(True, 0, 0))
            for k, v in custom_mocked_objects.items()
        }

        super(__class__, self).__init__(mocks)

    def _get_mock(self, name: str | NamedObject) -> Any:
        if not isinstance(name, str):
            name = name.__name__

        if not self.mock_builtins and name in BUILTIN_NAMES:
            return getattr(builtins, name)

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

    def _set_mock(self, name: str | NamedObject, value: Any) -> None:
        if not isinstance(name, str):
            name = name.__name__

        super(__class__, self).__setitem__(
            name, MockItem(value, MockMetadata(True, 1, 0))
        )

    def setdefault(self, name: str | NamedObject, value: Any) -> None:
        if not isinstance(name, str):
            name = name.__name__

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
    | Iterable[tuple[NamedObject, Mock]]
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
