from unittest.mock import MagicMock


def test(tested_fn, **mocked_objects):
    global_context = IsolatedContext(mocked_objects)

    def isolated_fn():
        return type(tested_fn)(tested_fn.__code__, global_context)

    def wrapper(test_fn):
        def wrapped():
            result = test_fn(isolated_fn())
            print(global_context)

            for key in global_context.nameset:
                if key not in mocked_objects:
                    print(f"`{key}` is not properly mocked and uses a default Mock.")

            return result

        return wrapped

    return wrapper


class IsolatedContext(dict):
    def __init__(self, mocked_objects) -> None:
        self.nameset = set()
        self.access_count = {}
        self.mocked_objects = mocked_objects

    def get(self, item: str, default=None):
        if default is not None:
            return default
        self.nameset.add(item)
        self.access_count.setdefault(item, 0)
        self.access_count[item] += 1
        if result := self.mocked_objects.get(item):
            return result
        return MagicMock(name=item)

    def __str__(self) -> str:
        nameset_str = "\n\t".join(name for name in self.nameset)
        accessct_ctr = "\n\t".join(f"{k}: {v}" for k, v in self.access_count.items())
        return (
            "Nameset: \n" f"\t{nameset_str}" "\n\n" "Call count: \n" f"\t{accessct_ctr}"
        )

    def __getitem__(self, item: str):
        return self.get(item)


def a_function(a_parameter, another_parameter):
    do_something()
    do_something_else()
    y = x + 1
    y += a_parameter
    y -= another_parameter
    do_something()
    return y


@test(a_function, x=2, do_something=lambda: 0)
def test_a_function(a_function):
    a = a_function(1, 2)
    assert a == 2


if __name__ == "__main__":
    test_a_function()
