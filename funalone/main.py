from sys import stderr
from typing import Callable
from unittest.mock import MagicMock


def isolated_test_for(
    tested_function: Callable,
    *,
    alert_on_default_mock: bool = False,
    custom_mocked_objects: dict | None = None,
    **kw_custom_mocked_objects,
):
    if custom_mocked_objects is None:
        custom_mocked_objects = {}
    custom_mocked_objects |= kw_custom_mocked_objects
    global_context = IsolatedContext(custom_mocked_objects)

    def isolated_fn():
        return type(tested_function)(tested_function.__code__, global_context)

    def wrapper(test_fn):
        def wrapped():
            result = test_fn(isolated_fn())
            print(global_context, file=stderr)

            for key in global_context.object_access_count:
                if alert_on_default_mock and key not in custom_mocked_objects:
                    print(
                        f"`{key}` is not properly mocked and uses a default Mock.",
                        file=stderr,
                    )

            return result

        return wrapped

    return wrapper


class IsolatedContext(dict):
    def __init__(self, mocked_objects: dict) -> None:
        self.object_access_count = {}
        self.mocked_objects = mocked_objects

    def get(self, item: str, default=None):
        if default is not None:
            return default
        self.object_access_count.setdefault(item, 0)
        self.object_access_count[item] += 1
        if result := self.mocked_objects.get(item):
            return result
        return MagicMock(name=item)

    def __str__(self) -> str:
        accessct_ctr = "\n\t".join(
            f"{k}: {v}" for k, v in self.object_access_count.items()
        )
        return "Dependency access count: \n" f"\t{accessct_ctr}"

    def __getitem__(self, item: str):
        return self.get(item)
