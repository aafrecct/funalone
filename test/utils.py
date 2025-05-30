from unittest.mock import Mock
from typing import Any

check_one = Mock(
    name="check_one",
    __name__="check_one",
)
check_two = Mock(
    name="check_two",
    __name__="check_two",
)
ext_variable = Mock(
    name="ext_variable",
)


def do_nothing() -> None:
    """An example function that does nothing."""
    pass


def return_external_variable() -> None:
    """An example function that does nothing."""
    return ext_variable


def basic_two_int_function(a: int, b: int) -> int:
    """Example function.
    You can check if this fucntion has been called by checking the mock
    `check_one`."""
    return check_one(a, b)


def basic_wrapper_function_with_error():
    """Example function.
    Calls basic_two_int_function_call with the wrong number of arguments."""
    return basic_two_int_function(1, 2, 3, 4)


def complex_multi_argument_function(
    a: int, /, b: str, c: dict[str, int], *d: bool, e: bool, **f
):
    """Example function.
    You can check if this fucntion has been called by checking the mock
    `check_two`."""
    return check_two(a, b, c, *d, e, **f)


def function_with_default_arguments(
    a: int, b: int = 1, c: int = 2, d: int = 3, e: int = 4
):
    """Example function.
    You can check if this fucntion has been called by checking the mock
    `check_one`."""
    return check_one(a, b, c, d, e)


def if_else_function(a: int, b: int) -> int:
    """Example function.
    You can check if this fucntion has been called by checking the mocks
    `check_one` and `check_two`."""
    if a > b:
        return check_one(a, b)
    else:
        return check_two(a, b)


def use_of_str_builtin_function(a: int) -> str:
    """Example function.
    You can check if this fucntion has been called by checking the mock
    `check_one`."""
    return check_one(str(a))


class StrangeObject(Mock):
    """A strange object with a method that can be called."""

    def do(self, x: Any):
        return f"Done: {x}"


def use_of_a_strange_object(a: int) -> str:
    """Example function.
    This example calls the do method of a StrangeObject."""
    so = StrangeObject()
    return so.do(a)


def bad_use_of_a_strange_object(a: int) -> str:
    """Example function.
    This example calls the act method of a StrangeObject, which doesn't exist."""
    so = StrangeObject()
    return so.act(a)


def raise_a_value_error(a: int) -> None:
    """Example function."""
    raise ValueError(a)


def raise_and_catch_a_value_error(a: int) -> None:
    """Example function.
    `check_one` is called if the error is caught correctly with the error and `a` as parameters."""
    try:
        raise ValueError(a)
    except ValueError as e:
        return check_one(e, a)


def indirect_raise_and_catch_a_value_error(a: int) -> None:
    """Example function.
    `check_one` is called if the error is caught correctly with the error and `a` as parameters."""
    try:
        raise_a_value_error(a)
    except ValueError as e:
        return check_one(e, a)


class CustomException(Exception):
    """Custom exception for testing purposes."""

    def __init__(self, a: int) -> None:
        super().__init__(a)


def raise_custom_exception(a: int) -> None:
    """Example function."""
    raise CustomException(a)


def raise_and_catch_custom_exception(a: int) -> None:
    """Example function.
    `check_one` is called if the error is caught correctly with the error and `a` as parameters."""
    try:
        raise CustomException(a)
    except CustomException as e:
        check_one(e, a)
