from unittest import TestCase
from unittest.mock import ANY, Mock
from typing import Literal
from funalone.default_mocking_context import ContextStates, DefaultMockingContext
from funalone.types import MockItem as MI, MockMetadata as MM, MockOrigin as MO
from test.declarative_test_case import DeclarativeTestCase
from test.utils import (
    basic_two_int_function,
    check_one,
    ext_variable,
)


def dict_set(dict, key, value):
    """Set a key in a dict."""
    dict[key] = value


class DefaultMockingContestTests(DeclarativeTestCase, TestCase):
    """Test case for default mocking context."""

    mocks_used = {}
    # This variable controls the test cases that will be run.
    run_test_cases: list[str | int] | Literal["all"] = "all"

    test_cases = [
        {
            "message": "Test basic",
            "config": {},
            "actions": [
                lambda context: context["check_one"],
            ],
            "checks": {
                "result": {
                    "check_one": MI(ANY, MM(MO.GENERATED_WHILE_INACTIVE, 1, 0)),
                },
            },
        },
        {
            "message": "Defaults are not saved in the context",
            "config": {},
            "actions": [
                lambda context: context["str"],
            ],
            "checks": {
                "result": {},
            },
        },
        {
            "message": "Default exceptions are not saved in the context",
            "config": {
                "allow_builtins": True,
            },
            "actions": [
                lambda context: context["ValueError"],
            ],
            "checks": {
                "result": {},
            },
        },
        {
            "message": "Setting a value in the context",
            "config": {
                "allow_builtins": True,
            },
            "actions": [
                lambda context: dict_set(context, "ext_variable", ext_variable),
            ],
            "checks": {
                "result": {
                    "ext_variable": MI(ANY, MM(MO.CUSTOM, 1, 0)),
                },
            },
        },
        {
            "message": "Setting a value in the context passing the object directly",
            "config": {},
            "actions": [
                lambda context: dict_set(context, basic_two_int_function, check_one),
            ],
            "checks": {
                "result": {
                    "basic_two_int_function": MI(ANY, MM(MO.CUSTOM, 1, 0)),
                },
            },
        },
        {
            "message": "Setting a value in the context during function globals setup",
            "config": {
                "allow_builtins": True,
            },
            "actions": [
                lambda context: context.set_state(ContextStates.SETUP_ORIGINALS),
                lambda context: dict_set(context, "ext_variable", ext_variable),
            ],
            "checks": {
                "result": {
                    "ext_variable": MI(ANY, MM(MO.FUNCTION_ORIGINAL, 1, 0)),
                },
            },
        },
        {
            "message": "Setting a value with setdefault in the context",
            "config": {
                "allow_builtins": True,
            },
            "actions": [
                lambda context: context.setdefault("ext_variable", ext_variable),
            ],
            "checks": {
                "result": {
                    "ext_variable": MI(ANY, MM(MO.CUSTOM, 1, 0)),
                },
            },
        },
        {
            "message": "Setting a value with setdefault in the context during function globals setup",
            "config": {
                "allow_builtins": True,
            },
            "actions": [
                lambda context: context.set_state(ContextStates.SETUP_ORIGINALS),
                lambda context: context.setdefault("ext_variable", ext_variable),
            ],
            "checks": {
                "result": {
                    "ext_variable": MI(ANY, MM(MO.FUNCTION_ORIGINAL, 1, 0)),
                },
            },
        },
        {
            "message": "Getting a new value in the context",
            "config": {
                "allow_builtins": True,
            },
            "actions": [
                lambda context: context.set_state(ContextStates.ENDED),
                lambda context: context["ext_variable"],
            ],
            "checks": {
                "result": {
                    "ext_variable": MI(ANY, MM(MO.GENERATED_WHILE_INACTIVE, 1, 0)),
                },
            },
        },
        {
            "message": "Getting a new value in the context during function execution",
            "config": {
                "allow_builtins": True,
            },
            "actions": [
                lambda context: context.set_state(ContextStates.ACTIVE),
                lambda context: context["ext_variable"],
            ],
            "checks": {
                "result": {
                    "ext_variable": MI(ANY, MM(MO.GENERATED_WHILE_ACTIVE, 1, 1)),
                },
            },
        },
        {
            "message": "Setting custom mocks on init then accessing them",
            "config": {
                "custom_mocks": {
                    "ext_variable": ext_variable,
                },
                "allow_builtins": True,
            },
            "actions": [
                lambda context: context.set_state(ContextStates.ACTIVE),
                lambda context: context["ext_variable"],
            ],
            "checks": {
                "result": {
                    "ext_variable": MI(ANY, MM(MO.CUSTOM, 1, 1)),
                },
            },
        },
        {
            "message": "Set default with bad types",
            "config": {
                "custom_mocks": {
                    "ext_variable": ext_variable,
                },
                "allow_builtins": True,
            },
            "actions": [
                lambda context: context.setdefault(object(), Mock()),
            ],
            "checks": {
                "raises": TypeError,
            },
        },
    ]

    def action(self, case):
        config = case.get("config", {})

        context = DefaultMockingContext(
            custom_mocked_objects=config.get("custom_mocks", {}),
            allow_builtins=config.get("allow_builtins", True),
            allow_exceptions=config.get("allow_exceptions", True),
            specs=config.get("specs", {}),
            **config.get("custom_mocks_kw", {}),
        )

        for action in case.get("actions", []):
            action(context)

        return context.to_debug_dict()
