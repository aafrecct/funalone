from typing import Literal
from unittest import TestCase
from unittest.mock import MagicMock

from funalone import create_namespaced_function_clone
from test.declarative_test_case import DeclarativeTestCase
from test.utils import (
    basic_two_int_function,
    check_one,
    check_two,
    ext_variable,
    function_with_default_arguments,
)


class NamespacedFunctionCloneTests(DeclarativeTestCase, TestCase):
    mocks_used = {
        "check_one": check_one,
        "check_two": check_two,
        "ext_variable": ext_variable,
        "custom_mock_one": MagicMock(name="custom_mock_one"),
        "custom_mock_two": MagicMock(name="custom_mock_two"),
    }
    # This variable controls the test cases that will be run.
    run_test_cases: list[str | int] | Literal["all"] = "all"
    test_cases = [
        {
            "message": "Test basic",
            "function": basic_two_int_function,
            "config": {
                "globals": {"check_one": lambda a, b: ...},
            },
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
            },
        },
        {
            "message": "Test None globals",
            "function": basic_two_int_function,
            "config": {
                "globals": None,
            },
            "args": (1, 2),
            "checks": {
                "raises": NameError,
            },
        },
        {
            "message": "Test keep original globals",
            "function": basic_two_int_function,
            "config": {
                "globals": {},
                "keep_original_globals": True,
            },
            "args": (1, 2),
            "checks": {
                "called": [check_one],
            },
        },
        {
            "message": "Test replace check_one",
            "function": basic_two_int_function,
            "config": {
                "globals": {"check_one": mocks_used["custom_mock_one"]},
            },
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
                "called": [mocks_used["custom_mock_one"]],
            },
        },
        {
            "message": "Test keep original defaults",
            "function": function_with_default_arguments,
            "config": {
                "globals": {"check_one": mocks_used["custom_mock_one"]},
            },
            "args": (1,),
            "checks": {
                "called_with": [
                    # a = 1  and the rest are the function's original defaults
                    (mocks_used["custom_mock_one"], 1, 1, 2, 3, 4)
                ],
            },
        },
        {
            "message": "Test strip original defaults",
            "function": function_with_default_arguments,
            "config": {
                "globals": {},
                "strip_original_defaults": True,
            },
            "args": (1),
            "checks": {
                "raises": TypeError,
            },
        },
    ]

    def action(self, case) -> None:
        # Clone the function
        cloned_function = create_namespaced_function_clone(
            case["function"], **case["config"]
        )

        # Call the cloned function with the provided arguments
        return cloned_function(*case["args"], **case.get("kwargs", {}))
