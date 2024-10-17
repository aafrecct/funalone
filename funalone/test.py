from unittest import TestCase
from unittest.mock import Mock, MagicMock

from funalone import IsolatedContextManager

do_something = Mock(
    name="do_something",
    __name__="do_something",
)
do_something_else = Mock(
    name="do_something_else",
    __name__="do_something_else",
)
do_something_with_args = Mock(
    name="do_something_with_args",
    __name__="do_something_with_args",
)
ext_variable = Mock(
    name="ext_variable",
    __name__="ext_variable",
)


def example_function_one(an_arg, another_arg):
    do_something()
    do_something_else()
    y = ext_variable
    y += an_arg
    y -= another_arg
    do_something()
    return y


def example_function_two(a_parameter, another_parameter):
    inn_variable = do_something_with_args(a_parameter, another_parameter, ext_variable)
    return inn_variable


def example_function_three(a_paramenter):
    return list((str(a_paramenter),))


class FunAloneTests(TestCase):
    def test_isolated_context_manager(self):
        test_cases = [
            {
                "function": example_function_one,
                "args": (0, 0),
                "custom_mocks": {},
                "expected_type": MagicMock,
            },
            {
                "function": example_function_one,
                "args": (0, 0),
                "custom_mocks": None,
                "expected_type": MagicMock,
            },
            {
                "function": example_function_one,
                "args": (0, 0),
                "custom_mocks": {"ext_variable": 1},
                "expected": 1,
            },
            {
                "function": example_function_one,
                "args": (1, 1),
                "custom_mocks": {"ext_variable": 1},
                "expected": 1,
            },
            {
                "function": example_function_one,
                "args": (1, 1),
                "custom_mocks": {
                    "ext_variable": 1,
                    "do_something": lambda: 0,
                    "do_something_else": lambda: 0,
                },
                "expected": 1,
            },
            {
                "function": example_function_two,
                "args": (0, 0),
                "custom_mocks": {"do_something_with_args": lambda a, b, c: 1},
                "expected": 1,
            },
            {
                "function": example_function_two,
                "args": (0, 0),
                "custom_mocks": {"do_something_with_args": Mock(return_value=2)},
                "expected": 2,
            },
            {
                "function": example_function_three,
                "args": (0,),
                "custom_mocks": {},
                "expected": ["0"],
            },
            {
                "function": example_function_three,
                "args": (0,),
                "custom_mocks": {},
                "mock_builtins": True,
                "expected_type": MagicMock,
            },
            {
                "function": example_function_one,
                "args": (1, 2),
                "custom_mocks": [
                    (do_something, lambda: 0),
                    (do_something_else, lambda: 0),
                    ("ext_variable", 0),
                ],
                "expected": -1,
            },
        ]
        for case in test_cases:
            with IsolatedContextManager(
                case["function"],
                custom_mocked_objects=case["custom_mocks"],
                mock_builtins=case.get("mock_builtins", False),
            ) as subtest, self.subTest(case):
                result = subtest.isolated_function(*case["args"])

                if "expected" in case:
                    self.assertEqual(case["expected"], result)
                elif "expected_type" in case:
                    self.assertIsInstance(result, case["expected_type"])

                do_something.assert_not_called()
                do_something_else.assert_not_called()
                do_something_with_args.assert_not_called()

    def test_isolated_context_manager_logs(self):
        test_cases = [
            {
                "function": example_function_one,
                "args": (0, 0),
                "custom_mocks": {},
                "expected_type": MagicMock,
            },
            {
                "function": example_function_three,
                "args": (0,),
                "custom_mocks": {},
                "expected_type": list,
            },
        ]
        for case in test_cases:
            with IsolatedContextManager(
                case["function"],
                custom_mocked_objects=case["custom_mocks"],
                mock_builtins=case.get("mock_builtins", False),
                log_dependency_access_count=True,
                alert_on_default_mock=True,
            ) as subtest, self.subTest(case):
                result = subtest.isolated_function(*case["args"])

                self.assertIsInstance(result, case["expected_type"])

                do_something.assert_not_called()
                do_something_else.assert_not_called()
                do_something_with_args.assert_not_called()
                self.assertIsNotNone(str(subtest.context))
