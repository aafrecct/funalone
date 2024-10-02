from unittest import TestCase
from unittest.mock import Mock, MagicMock

from funalone import isolated_test_for

do_something = Mock(name="do_something")
do_something_else = Mock(name="do_something_else")
do_something_with_args = Mock(name="do_something_with_args")
ext_variable = Mock()


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
    def test_isolated_test_for(self):
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
        ]
        for case in test_cases:
            with self.subTest(case):

                @isolated_test_for(
                    case["function"],
                    custom_mocked_objects=case["custom_mocks"],
                    mock_builtins=case.get("mock_builtins", False),
                )
                def tester_function(fn):
                    result = fn(*case["args"])

                    if "expected" in case:
                        self.assertEqual(case["expected"], result)
                    elif "expected_type" in case:
                        self.assertIsInstance(result, case["expected_type"])

                tester_function()
                do_something.assert_not_called()
                do_something_else.assert_not_called()
                do_something_with_args.assert_not_called()

    def test_isolated_test_for_with_args(self):
        test_cases = [
            {
                "function": example_function_one,
                "args": (1, 1),
                "test_args": (1, 2, 3),
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
                "test_args": ("a", "b", "c"),
                "custom_mocks": {"do_something_with_args": Mock(return_value=2)},
                "expected": 2,
            },
        ]
        for case in test_cases:
            with self.subTest(case):

                @isolated_test_for(
                    case["function"], custom_mocked_objects=case["custom_mocks"]
                )
                def tester_function(fn, arg1, arg2, /, *, arg3):
                    self.assertEqual(arg1, case["test_args"][0])
                    self.assertEqual(arg2, case["test_args"][1])
                    self.assertEqual(arg3, case["test_args"][2])
                    result = fn(*case["args"])
                    self.assertEqual(case["expected"], result)

                tester_function(
                    case["test_args"][0],
                    case["test_args"][1],
                    arg3=case["test_args"][2],
                )
                do_something.assert_not_called()
                do_something_else.assert_not_called()
                do_something_with_args.assert_not_called()

    @isolated_test_for(
        example_function_one,
        is_method=True,
    )
    def test_isolated_test_in_method(self, example_function_one):
        example_function_one(1, 1)

        do_something.assert_not_called()
        do_something_else.assert_not_called()
        do_something_with_args.assert_not_called()
