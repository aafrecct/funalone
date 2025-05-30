from enum import Enum
from types import FunctionType
from typing import Protocol, TypeVar, TypeAlias, Any
from dataclasses import dataclass


class NamedObject(Protocol):
    __name__: str


Name: TypeAlias = str | NamedObject

F = TypeVar("F", bound=FunctionType)


class MockOrigin(Enum):
    CUSTOM = 1
    FUNCTION_ORIGINAL = 2
    GENERATED_WHILE_ACTIVE = 3
    GENERATED_WHILE_INACTIVE = 4


@dataclass
class MockMetadata:
    """A dataclass to track the metadata of a MockItem"""

    origin: MockOrigin
    total_access_count: int
    active_access_count: int


@dataclass
class MockItem:
    """A pair used by DefaultMockingContext to keep custom mocks along with
    metadata for them."""

    object: Any
    metadata: MockMetadata


def normalize_name(name: Name) -> str:
    """Normalize a name to a string."""
    if isinstance(name, str):
        return name
    return name.__name__


def is_exception(obj: Any) -> bool:
    """Check if the object is an exception."""
    if isinstance(obj, type):
        return issubclass(obj, Exception)
    return isinstance(obj, Exception)
