# FunAlone

A small python library that makes it easy to test a **fun**ction **alone**, that is, mocking all
dependencies. True unittests, without having to manually look and add every called function to an
increasing list of @mock.patch decorators.

## Example

Say you have a function named `do_a_lot_of_stuff` and you want to test it with `unittest`, only testing the functions code, not the function that it calls within.

```python
def do_a_lot_of_stuff(arg: int):
    if arg > 5:
        result = do_this(arg)
    elif arg < 0:
        result = do_that(arg)
    else:
        result = do_nothing(arg)
    
    return result
```

In this case you might want to know which external function has been called, depending on the input, without having the code actually call that function (which could have side effects and should have it's own unit tests).

```python
class Test(unittest.TestCase):
    def test_do_a_lot_of_stuff_with_5(self):
        with IsolatedFunctionClone(
            do_a_lot_of_stuff
            ) as do_a_lot_of_stuff_clone:

            # This calls a function clone with an isolated context.
            # All external names are mocked.
            do_a_lot_of_stuff_clone(5)

            # You can access this context later to assert calls,
            # And you can use the original functions to do this,
            # so it's all refactor-friendly.
            do_a_lot_of_stuff_clone.context[do_this].assert_not_called()
            do_a_lot_of_stuff_clone.context[do_that].assert_not_called()
            do_a_lot_of_stuff_clone.context[do_nothing].assert_called_once()

```

There are more parameters and ways to use the library, this is only a basic example.

## Installation

You can install the latest version with pip:
```bash
pip install funalone
```

## Tests

There is a small collection of unittests in the `test` folder.
You can run them using unittest.

## Credits

This project is developed by Borja Martinena (borjamartinena[at]gmail.com).