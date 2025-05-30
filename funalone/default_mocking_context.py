from __future__ import annotations

import builtins
from enum import Enum
from typing import Any
from collections.abc import Iterable
from unittest.mock import MagicMock, Mock, create_autospec

from funalone.types import (
    MockOrigin,
    NamedObject,
    Name,
    MockItem,
    MockMetadata,
    is_exception,
    normalize_name,
)

BUILTIN_NAMES = dir(builtins)


class ContextStates(Enum):
    """The posible states in which a DefaultMockingContext might be."""

    SETUP = 0
    SETUP_ORIGINALS = 1
    ACTIVE = 2
    ENDED = 3


class DefaultMockingContext(dict):
    """A dict-like object that creates MagicMocks on not-found key lookups.

    A collection of key value pairs that returns a new named MagicMock object when
    accesing a key that doesn't exist. For use in a namespaced function for testing
    purposes. It also keeps track of access counts for these objects, to help with
    debugging and allows specification of custom Mock objects for certain keys.

    Attributes:
        allow_builtins: Whether the context mocks builtin names automatically or
            keeps default builtins.
        allow_exceptions: Whether the context mocks builtin exceptions automatically or
            keeps default exceptions.
        state: The current state of the context. It can be one of the following:
            - SETUP: The context is being set up.
            - ACTIVE: The context is active and can be used.
            - ENDED: The context has ended and should not be used.
    """

    state: ContextStates
    allow_builtins: bool
    allow_exceptions: bool
    specs: dict[str, Any]

    def __init__(
        self,
        custom_mocked_objects: dict[Name, Mock | Any]
        | Iterable[tuple[Name, Mock | Any]]
        | None = None,
        allow_builtins: bool = True,
        allow_exceptions: bool = True,
        specs: dict[str, Any] | None = None,
        **kw_custom_mocked_objects,
    ):
        object.__setattr__(self, "state", ContextStates.SETUP)
        object.__setattr__(self, "allow_builtins", allow_builtins)
        object.__setattr__(self, "allow_exceptions", allow_exceptions)
        object.__setattr__(self, "specs", specs or {})

        processed_custom_mocked_objects: dict[str, Mock | Any] = _process_custom_mocks(
            custom_mocked_objects, **kw_custom_mocked_objects
        )
        mocks = {
            name: MockItem(value, MockMetadata(self.state_to_mock_origin(), 0, 0))
            for name, value in processed_custom_mocked_objects.items()
        }

        super().__init__(mocks)

    def _get_mock(self, name: str | NamedObject) -> Any:
        name = normalize_name(name)

        if name in BUILTIN_NAMES:
            builtin = getattr(builtins, name)
            if self.allow_builtins:
                return builtin
            elif self.allow_exceptions and is_exception(builtin):
                return builtin

        active_access = 1 if self.state == ContextStates.ACTIVE else 0
        if result := super().get(name):
            result.metadata.total_access_count += 1
            result.metadata.active_access_count += active_access
            return result.object

        spec = self.specs.get(name)
        result = auto_create_mock_from_spec(name, spec)

        super().__setitem__(
            name,
            MockItem(
                result,
                MockMetadata(
                    self.state_to_mock_origin(is_generated=True),
                    1,
                    active_access,
                ),
            ),
        )
        return result

    def _set_mock(self, name: Name, value: Any) -> None:
        if not isinstance(name, str):
            name = name.__name__

        super().__setitem__(
            name, MockItem(value, MockMetadata(self.state_to_mock_origin(), 1, 0))
        )

    def setdefault(self, name: Any, value: Any | None = None, /) -> Any | None:
        """Set a default value for a key in the context.

        If the key already exists, it does nothing. Otherwise, it sets the
        default value and returns it.
        """
        if not isinstance(name, str) and not hasattr(name, "__name__"):
            raise TypeError(f"Expected str or NamedObject, got {type(name)}")

        return self._setdefault_typed(normalize_name(name), value)

    def _setdefault_typed(self, name: str, value: Mock | Any | None, /) -> Any | None:
        return super().setdefault(
            name, MockItem(value, MockMetadata(self.state_to_mock_origin(), 1, 0))
        )

    def reset(self):
        for mock_item in self.values():
            mock_item.metadata.total_access_count = 0
            mock_item.metadata.active_access_count = 0
            if isinstance(mock_item.object, Mock):
                mock_item.object.reset_mock()

    def set_state(self, new_state: ContextStates):
        object.__setattr__(self, "state", new_state)

    def state_to_mock_origin(self, is_generated: bool = False) -> MockOrigin:
        match self.state:
            case ContextStates.SETUP_ORIGINALS:
                return MockOrigin.FUNCTION_ORIGINAL
            case ContextStates.ACTIVE:
                return MockOrigin.GENERATED_WHILE_ACTIVE
            case _:
                return (
                    MockOrigin.GENERATED_WHILE_INACTIVE
                    if is_generated
                    else MockOrigin.CUSTOM
                )

    def to_debug_dict(self) -> dict[str, MockItem]:
        """Return a debug dictionary with the current state of the context."""
        return {key: value for key, value in super().items()}

    __getattr__ = _get_mock
    __setattr__ = _set_mock
    __getitem__ = _get_mock
    __setitem__ = _set_mock


def _process_custom_mocks(
    custom_mocked_objects: dict[str | NamedObject, Mock | Any]
    | Iterable[tuple[str | NamedObject, Mock | Any]]
    | None = None,
    **kw_custom_mocked_objects,
) -> dict[str, Mock | Any]:
    result: dict[str, Mock | Any] = {}
    if custom_mocked_objects is None:
        # Included to appease mypy.
        pass
    elif isinstance(custom_mocked_objects, dict):
        result = {}
        for name, mock in custom_mocked_objects.items():
            result[normalize_name(name)] = mock
    elif hasattr(custom_mocked_objects, "__iter__"):
        result = {}
        for name, mock in custom_mocked_objects:
            result[normalize_name(name)] = mock
    else:
        raise TypeError(
            f"Expected dict or iterable of tuples, got {type(custom_mocked_objects)}"
        )

    result |= kw_custom_mocked_objects
    return result


def auto_create_mock_from_spec(name: str, spec: Any | None = None) -> Mock:
    """Create a Mock object with the given spec.

    If the spec is a type, it creates a MagicMock with that spec.
    Otherwise, it creates a regular Mock with the spec as its return value.
    """
    if spec is None or isinstance(spec, Mock):
        return MagicMock(name=name)

    if isinstance(spec, type):
        return MagicMock(name=name, spec=spec, return_value=MagicMock(spec=spec))

    return create_autospec(spec=spec)
