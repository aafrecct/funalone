from typing import Literal
from unittest import TestCase
from unittest.mock import MagicMock, Mock

from funalone.isolated_function_clone import (
    IsolatedFunctionClone,
    with_isolated_function_clone,
)
from test.declarative_test_case import DeclarativeTestCase
from test.utils import (
    StrangeObject,
    bad_use_of_a_strange_object,
    basic_two_int_function,
    check_one,
    check_two,
    do_nothing,
    ext_variable,
    if_else_function,
    raise_and_catch_a_value_error,
    raise_and_catch_custom_exception,
    return_external_variable,
    use_of_a_strange_object,
    use_of_str_builtin_function,
    basic_wrapper_function_with_error,
)


class IsolatedFunctionCloneTests(DeclarativeTestCase, TestCase):
    """Test case for the isolated function clone."""

    mocks_used = {
        "check_one": check_one,
        "check_two": check_two,
        "ext_variable": ext_variable,
        "custom_mock_one": MagicMock(
            name="custom_mock_one", side_effect=lambda *a: a if len(a) != 1 else a[0]
        ),
        "custom_mock_two": MagicMock(
            name="custom_mock_two", side_effect=lambda *a: a if len(a) != 1 else a[0]
        ),
    }
    # This variable controls the test cases that will be run.
    run_test_cases: list[str | int] | Literal["all"] = "all"

    test_cases = [
        {
            "message": "Test basic",
            "function": basic_two_int_function,
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
            },
        },
        {
            "message": "Cover logging functionality",
            "function": basic_two_int_function,
            "config": {
                "log_dependency_access_count": True,
                "alert_on_default_mock": True,
            },
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
            },
        },
        {
            "message": "Cover logging functionality, no dependencies",
            "function": do_nothing,
            "config": {
                "log_dependency_access_count": True,
                "alert_on_default_mock": True,
                "mock_builtins": True,
            },
            "args": (),
            "checks": {},
        },
        {
            "message": "Test basic with custom mock",
            "function": basic_two_int_function,
            "config": {
                "custom_mocks": {"check_one": mocks_used["custom_mock_one"]},
            },
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
                "called": [mocks_used["custom_mock_one"]],
            },
        },
        {
            "message": "Test basic with custom mock as keyword argument",
            "function": basic_two_int_function,
            "config": {
                "custom_mocks_kw": {"check_one": mocks_used["custom_mock_one"]},
            },
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
                "called": [mocks_used["custom_mock_one"]],
            },
        },
        {
            "message": "Test basic with custom mock given as object in pair iterable",
            "function": basic_two_int_function,
            "config": {
                "custom_mocks": [(check_one, mocks_used["custom_mock_one"])],
            },
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
                "called": [mocks_used["custom_mock_one"]],
            },
        },
        {
            "message": "Test basic with invalid custom mocks type",
            "function": basic_two_int_function,
            "config": {
                "custom_mocks": ...,
            },
            "args": (1, 2),
            "checks": {
                "raises": TypeError,
            },
        },
        {
            "message": "Test basic with custom mock given as object",
            "function": basic_two_int_function,
            "config": {
                "custom_mocks": {check_one: mocks_used["custom_mock_one"]},
            },
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
                "called": [mocks_used["custom_mock_one"]],
            },
        },
        {
            "message": "Test basic with name allow",
            "function": basic_two_int_function,
            "config": {
                "name_allow_list": ["check_one"],
            },
            "args": (1, 2),
            "checks": {
                "called_with": [(check_one, 1, 2)],
            },
        },
        {
            "message": "Test basic with name allow for variable",
            "function": return_external_variable,
            "config": {
                "name_allow_list": ["ext_variable"],
            },
            "args": (),
            "checks": {
                "result": ext_variable,
            },
        },
        {
            "message": "Test basic with allow all names",
            "function": basic_two_int_function,
            "config": {
                "allow_all_names": True,
            },
            "args": (1, 2),
            "checks": {
                "called_with": [(check_one, 1, 2)],
            },
        },
        {
            "message": "Test basic with allow condition hit",
            "function": basic_two_int_function,
            "config": {
                "name_allow_condition": lambda _n, v: v == check_one,
            },
            "args": (1, 2),
            "checks": {
                "called_with": [(check_one, 1, 2)],
            },
        },
        {
            "message": "Test basic with allow condition miss",
            "function": basic_two_int_function,
            "config": {
                "name_allow_condition": lambda n, _v: n == "check_two",
            },
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
            },
        },
        {
            "message": "Test basic with custom setup mock",
            "function": basic_two_int_function,
            "setup_actions": [
                lambda f: f.setdefault(check_one, MagicMock(name="fake_check_one")),
            ],
            "config": {},
            "args": (1, 2),
            "checks": {
                "not_called": [check_one],
            },
        },
        {
            "message": "Test default exception behaviour",
            "function": raise_and_catch_a_value_error,
            "config": {
                "name_allow_list": [check_one],
            },
            "args": (1,),
            "checks": {
                "called": [check_one],
            },
        },
        {
            "message": "Test not mocking builtins",
            "function": use_of_str_builtin_function,
            "config": {
                "allow_builtins": True,
                "custom_mocks": {
                    check_one: mocks_used["custom_mock_one"],
                },
            },
            "args": (1,),
            "checks": {
                "called": [mocks_used["custom_mock_one"]],
                "not_called": [check_one],
                "result": "1",
            },
        },
        {
            "message": "Test mock builtins",
            "function": use_of_str_builtin_function,
            "config": {
                "allow_builtins": False,
                "custom_mocks": {
                    check_one: mocks_used["custom_mock_one"],
                },
            },
            "args": (1,),
            "checks": {
                "called": [mocks_used["custom_mock_one"]],
                "not_called": [check_one],
                "result_class": Mock,
            },
        },
        {
            "message": "Test mock builtins not exceptions, builtin exception is raised",
            "function": raise_and_catch_a_value_error,
            "config": {
                "allow_builtins": False,
                "allow_exceptions": True,
                "name_allow_list": [check_one],
            },
            "args": (1,),
            "checks": {
                "called": [check_one],
            },
        },
        {
            "message": "Test mock builtins and exceptions, builtin exception is raised",
            "function": raise_and_catch_a_value_error,
            "config": {
                "allow_builtins": False,
                "allow_exceptions": False,
            },
            "args": (1,),
            "checks": {
                "raises": TypeError,
            },
        },
        {
            "message": "Test mock builtins not exceptions, custom exception is raised",
            "function": raise_and_catch_custom_exception,
            "config": {
                "allow_builtins": False,
                "allow_exceptions": True,
                "name_allow_list": [check_one],
            },
            "args": (1,),
            "checks": {
                "called": [check_one],
            },
        },
        {
            "message": "Test mock builtins and exceptions, custom exception is raised",
            "function": raise_and_catch_custom_exception,
            "config": {
                "allow_builtins": False,
                "allow_exceptions": False,
            },
            "args": (1,),
            "checks": {
                "raises": TypeError,
            },
        },
        {
            "message": "Test mock builtins and exceptions, custom exception is raised",
            "function": raise_and_catch_custom_exception,
            "config": {
                "allow_builtins": False,
                "allow_exceptions": False,
            },
            "args": (1,),
            "checks": {
                "raises": TypeError,
            },
        },
        {
            "message": "Test reset functionality",
            "function": if_else_function,
            "config": {
                "custom_mocks": {
                    check_one: mocks_used["custom_mock_one"],
                    check_two: lambda *a: True,
                }
            },
            "args": (1, 2),
            "reset": True,
            "checks": {
                "not_called": [check_one, mocks_used["custom_mock_one"]],
            },
        },
        {
            "message": "Test strange object, allowed",
            "function": use_of_a_strange_object,
            "config": {
                "name_allow_list": [StrangeObject],
            },
            "args": (1,),
            "checks": {
                # Default behaviour of the function.
                "result": "Done: 1",
            },
        },
        {
            "message": "Test weird object, auto mocked",
            "function": use_of_a_strange_object,
            "config": {},
            "args": (1,),
            "checks": {
                # Default behaviour of the function.
                "result_class": Mock,
            },
        },
        {
            "message": "Test weird object, custom mocked",
            "function": use_of_a_strange_object,
            "config": {
                "custom_mocks": {
                    StrangeObject: Mock(
                        return_value=Mock(do=lambda x: f"Custom: {x}"),
                    ),
                }
            },
            "args": (1,),
            "checks": {
                # Default behaviour of the function.
                "result": "Custom: 1",
            },
        },
        {
            "message": "Test autospec",
            "function": bad_use_of_a_strange_object,
            "config": {
                "autospec_mocks": True,
            },
            "args": (1,),
            "checks": {
                # Default behaviour of the function.
                "raises": AttributeError,
            },
        },
        {
            "message": "Test autospec with class",
            "function": bad_use_of_a_strange_object,
            "config": {
                "autospec_mocks": True,
            },
            "args": (1,),
            "checks": {
                # Default behaviour of the function.
                "raises": AttributeError,
            },
        },
        {
            "message": "Test autospec with function",
            "function": basic_wrapper_function_with_error,
            "config": {
                "autospec_mocks": True,
            },
            "args": (),
            "checks": {
                # Default behaviour of the function.
                "raises": TypeError,
            },
        },
        {
            "message": "Test with with ",
            "function": basic_two_int_function,
            "config": {
                "name_allow_list": ["check_one"],
            },
            "args": (1, 2),
            "checks": {
                "called_with": [(check_one, 1, 2)],
            },
        },
    ]

    def action(self, case):
        config = case.get("config", {})
        with (
            IsolatedFunctionClone(
                case["function"],
                custom_mocked_objects=config.get("custom_mocks"),
                name_allow_list=config.get("name_allow_list"),
                name_allow_condition=config.get("name_allow_condition"),
                allow_all_names=config.get("allow_all_names", False),
                allow_builtins=config.get("allow_builtins", True),
                allow_exceptions=config.get("allow_exceptions", True),
                autospec_mocks=config.get("autospec_mocks", False),
                strip_function_defaults=config.get("strip_function_defaults", False),
                log_dependency_access_count=config.get(
                    "log_dependency_access_count", False
                ),
                alert_on_default_mock=config.get("alert_on_default_mock", False),
                **config.get("custom_mocks_kw", {}),
            ) as function,
        ):
            for action in config.get("setup_actions", []):
                action(function)

            result = function(*case["args"])

            if case.get("reset", False):
                function.reset()

            return result


class IsolatedFunctionCloneDecoratorTests(DeclarativeTestCase, TestCase):
    mocks_used = IsolatedFunctionCloneTests.mocks_used

    # This variable controls the test cases that will be run.
    run_test_cases: list[str | int] | Literal["all"] = "all"

    test_cases = IsolatedFunctionCloneTests.test_cases

    def action(self, case):
        config = case.get("config", {})

        @with_isolated_function_clone(
            case["function"],
            custom_mocked_objects=config.get("custom_mocks"),
            name_allow_list=config.get("name_allow_list"),
            name_allow_condition=config.get("name_allow_condition"),
            allow_all_names=config.get("allow_all_names", False),
            allow_builtins=config.get("allow_builtins", True),
            allow_exceptions=config.get("allow_exceptions", True),
            autospec_mocks=config.get("autospec_mocks", False),
            strip_function_defaults=config.get("strip_function_defaults", False),
            log_dependency_access_count=config.get(
                "log_dependency_access_count", False
            ),
            alert_on_default_mock=config.get("alert_on_default_mock", False),
            **config.get("custom_mocks_kw", {}),
        )
        def test(function):
            result = function(*case["args"])

            if case.get("reset", False):
                function.reset()

            return result

        return test()  # Call the decorated function
