from typing import Any
from funalone.default_mocking_context import (
    ContextStates,
    DefaultMockingContext,
)
from funalone.namespaced_function import create_namespaced_function_clone
from funalone.types import (
    MockOrigin,
    Name,
    NamedObject,
    F,
    is_exception,
    normalize_name,
)


from collections.abc import Callable, Iterable
from contextlib import ContextDecorator
from unittest.mock import Mock
from sys import stderr


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
        tested_function: F,
        *,
        custom_mocked_objects: dict | Iterable[tuple[NamedObject, Mock]] | None = None,
        name_allow_list: Iterable[NamedObject] | None = None,
        name_allow_condition: Callable[[str, Any], bool] | None = None,
        allow_all_names: bool = False,
        allow_builtins: bool = True,
        allow_exceptions: bool = True,
        autospec_mocks: bool = True,
        strip_function_defaults: bool = False,
        log_dependency_access_count: bool = False,
        alert_on_default_mock: bool = False,
        **kw_custom_mocked_objects,
    ):
        self.context = DefaultMockingContext(
            custom_mocked_objects,
            allow_builtins,
            allow_exceptions,
            specs=tested_function.__globals__ if autospec_mocks else None,
            **kw_custom_mocked_objects,
        )

        self.context.set_state(ContextStates.SETUP_ORIGINALS)
        self._namespaced_function_clone = create_namespaced_function_clone(
            tested_function,
            self.context,
            keep_original_globals=_process_name_allows(
                allow_all_names, name_allow_list, name_allow_condition, allow_exceptions
            ),
            strip_original_defaults=strip_function_defaults,
        )

        self.context.set_state(ContextStates.SETUP)
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

    def reset(self):
        self.context.reset()

    def dependency_access_count_message(self) -> str:
        accessct_str = "\n\t".join(
            f"{name}: {mock_item.metadata.active_access_count}"
            for name, mock_item in self.context.to_debug_dict().items()
        )
        if not accessct_str.strip():
            accessct_str = "<No external dependencies>"
        return f"Dependency access count: \n\t{accessct_str}"

    def default_mock_alert_message(self) -> str:
        default_mocks = [
            name
            for name, mock_item in self.context.to_debug_dict().items()
            if mock_item.metadata.origin == MockOrigin.GENERATED_WHILE_ACTIVE
        ]
        return "\n".join(
            f"`{key}` is not properly mocked and uses a default Mock."
            for key in default_mocks
        )


def with_isolated_function_clone(
    tested_function: F,
    *,
    custom_mocked_objects: dict | Iterable[tuple[NamedObject, Mock]] | None = None,
    name_allow_list: Iterable[NamedObject] | None = None,
    name_allow_condition: Callable[[object], bool] | None = None,
    allow_all_names: bool = False,
    allow_builtins: bool = True,
    allow_exceptions: bool = True,
    autospec_mocks: bool = True,
    strip_function_defaults: bool = False,
    log_dependency_access_count: bool = False,
    alert_on_default_mock: bool = False,
    **kw_custom_mocked_objects,
):
    """A decorator for unittest functions that creates an isolated function clone
    for a given function and passes it to the decorated function as a parameter.
    """

    def wrapper(function: Callable):
        def wrapped_function(*args, **kwargs):
            with IsolatedFunctionClone(
                tested_function,
                custom_mocked_objects=custom_mocked_objects,
                name_allow_list=name_allow_list,
                name_allow_condition=name_allow_condition,
                allow_all_names=allow_all_names,
                autospec_mocks=autospec_mocks,
                allow_builtins=allow_builtins,
                allow_exceptions=allow_exceptions,
                strip_function_defaults=strip_function_defaults,
                log_dependency_access_count=log_dependency_access_count,
                alert_on_default_mock=alert_on_default_mock,
                **kw_custom_mocked_objects,
            ) as isolated_function:
                return function(isolated_function, *args, **kwargs)

        return wrapped_function

    return wrapper


def _process_name_allows(
    allow_all: bool = False,
    name_allow_list: Iterable[Name] | None = None,
    name_allow_condition: Callable[[str, Any], bool] | None = None,
    allow_exceptions: bool = True,
) -> Callable[[str, Any], bool] | bool:
    if allow_all:
        return allow_all

    checks: list[Callable[[str, Any], bool]] = []
    if name_allow_list:
        normalized_name_allow_set = (
            {normalize_name(name) for name in name_allow_list}
            if name_allow_list
            else set()
        )

        def name_is_in_list(name: str, _obj: Any) -> bool:
            return name in normalized_name_allow_set

        checks.append(name_is_in_list)

    if name_allow_condition:
        checks.append(name_allow_condition)

    if allow_exceptions:
        checks.append(lambda _n, o: is_exception(o))

    return (
        lambda name, object: any(check(name, object) for check in checks)
        if checks
        else False
    )
