from sys import stderr
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
ext_variable = MagicMock(
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
    def setUp(self) -> None:
        do_something.reset_mock()
        do_something_else.reset_mock()
        do_something_with_args.reset_mock()
        ext_variable.reset_mock()

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
                mock_builtins=case.get("mock_builtins", False),
                custom_mocked_objects=case["custom_mocks"],
            ) as subtest, self.subTest(case):
                result = subtest.isolated_function(*case["args"])

                if "expected" in case:
                    self.assertEqual(case["expected"], result)
                elif "expected_type" in case:
                    self.assertIsInstance(result, case["expected_type"])

                do_something.assert_not_called()
                do_something_else.assert_not_called()
                do_something_with_args.assert_not_called()

    def test_isolated_context_manager_logging_coverage(self):
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
                mock_builtins=False,
                log_dependency_access_count=True,
                alert_on_default_mock=True,
                name_allow_list=case.get("name_allow_list", False),
            ) as subtest, self.subTest(case):
                result = subtest.isolated_function(*case["args"])

                self.assertIsInstance(result, case["expected_type"])

                do_something.assert_not_called()
                do_something_else.assert_not_called()
                do_something_with_args.assert_not_called()
                self.assertIsNotNone(str(subtest.context))

    def test_isolated_context_manager_set_mocks_after_manager_entry(self):
        test_cases = [
            {
                "function": example_function_one,
                "ext_variable": 2,
                "expected_type": MagicMock,
            },
        ]
        for case in test_cases:
            with IsolatedContextManager(
                case["function"],
                mock_builtins=case.get("mock_builtins", False),
            ) as subtest, self.subTest(case):
                subtest.mocked_objects.do_something = Mock(side_effect=lambda: 0)
                subtest.mocked_objects.do_something_else = Mock(side_effect=lambda: 0)
                subtest.mocked_objects.ext_variable = case["ext_variable"]

                result = subtest.isolated_function(0, 0)

                self.assertEqual(result, case["ext_variable"])
                do_something.assert_not_called()
                do_something_else.assert_not_called()
                do_something_with_args.assert_not_called()
                subtest.mocked_objects.do_something.assert_called()
                subtest.mocked_objects.do_something_else.assert_called()

    def test_isolated_context_manager_keep_globals(self):
        test_cases = [
            {
                "function": example_function_one,
                "name_allow_list": [do_something],
                "expected_type": MagicMock,
            },
            {
                "function": example_function_one,
                "name_allow_list": [do_something, do_something_else],
                "custom_mocks": [(do_something, MagicMock())],
                "expected_not_called": ["do_something"],
                "expected_type": MagicMock,
            },
            {
                "function": example_function_one,
                "name_allow_list": [do_something, do_something_else],
                "expected_type": MagicMock,
            },
            {
                "function": example_function_one,
                "name_allow_list": ["do_something", "do_something_else"],
                "expected_type": MagicMock,
            },
            {
                "function": example_function_one,
                "name_allow_list": True,
                "expected_type": MagicMock,
            },
        ]

        functions = [
            do_something,
            do_something_else,
        ]

        for case in test_cases:
            with IsolatedContextManager(
                case["function"],
                custom_mocked_objects=case.get("custom_mocks"),
                mock_builtins=case.get("mock_builtins", False),
                name_allow_list=case["name_allow_list"],
            ) as subtest, self.subTest(case):
                result = subtest.isolated_function(0, 0)

                self.assertIsInstance(result, Mock)

                for fun in functions:
                    if (
                        isinstance(case["name_allow_list"], bool)
                        and case["name_allow_list"]
                    ) or (
                        fun.__name__ in case["name_allow_list"]
                        and fun.__name__ not in case.get("expected_not_called", [])
                    ):
                        fun.assert_called()
                    fun.reset_mock()

    def test_isolated_context_manager_reset_access_counts(self):
        test_cases = [
            {
                "function": example_function_one,
                "ext_variable": 2,
                "expected_type": MagicMock,
            },
        ]
        for case in test_cases:
            with IsolatedContextManager(
                case["function"],
                mock_builtins=case.get("mock_builtins", False),
            ) as subtest, self.subTest(case):
                subtest.mocked_objects.do_something = Mock(side_effect=lambda: 0)
                subtest.mocked_objects.do_something_else = Mock(side_effect=lambda: 0)
                subtest.mocked_objects.ext_variable = case["ext_variable"]

                result = subtest.isolated_function(0, 0)
                subtest.context.mocked_objects.reset_access_counts()

                self.assertEqual(result, case["ext_variable"])
                for object in subtest.context.mocked_objects:
                    print(object, file=stderr)
