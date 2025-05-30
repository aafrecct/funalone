

from typing import Generator, Literal
from unittest.mock import MagicMock


class DeclarativeTestCase:
    maxDiff = None

    custom_mock_one = MagicMock(name="custom_mock_one")
    custom_mock_two = MagicMock(name="custom_mock_two")

    # This variable controls the test cases that will be run.
    run_test_cases: list[str | int] | Literal["all"] = "all"
    test_cases: list[dict]

    def setUp(self) -> None:
        # Reset the mocks before each test
        global check_one, check_two, ext_variable
        for _name, mock in self.mocks_used.items():
            mock.reset_mock()

    def test(self) -> None:
        """Run the tests."""

        test_cases = self._get_tests(self.run_test_cases)

        for case in test_cases:
            self.setUp()
            with self.subTest(case["message"]):
                try:
                    result = self.action(case)

                except Exception as e:
                    self.assertIn(
                        "raises",
                        case["checks"],
                        "Didn't expect an exception to be raised",
                    )
                    self.assertIsInstance(
                        e,
                        case["checks"]["raises"],
                        f"Expected exception of type: {case['checks']['raises']}\n Got: {e}",
                    )
                else:
                    self.assertNotIn(
                        "raises",
                        case["checks"],
                        "Expected an exception to be raised",
                    )
                finally:
                    # Checks
                    for mock in case["checks"].get("called", []):
                        mock.assert_called()
                    for mock in case["checks"].get("not_called", []):
                        mock.assert_not_called()
                    for mock, *args in case["checks"].get("called_with", []):
                        mock.assert_called_with(*args)
                    if "result" in case["checks"]:
                        self.assertEqual(
                            case["checks"]["result"],
                            result,
                        )
                    elif "result_class" in case["checks"]:
                        self.assertIsInstance(
                            result,
                            case["checks"]["result_class"],
                            f"Expected result of type: {case['checks']['result_class']}\n Got: {result} (type: {type(result)})",
                        )

    def _get_tests(
        self, tests_to_run: set[str | int] | Literal["all"]
    ) -> Generator[dict, None, None]:
        """Filter the tests based on the provided list of test names."""
        run_all = tests_to_run == "all"

        for i, test in enumerate(self.test_cases):
            test_this = run_all or i in tests_to_run or test["message"] in tests_to_run
            if test_this:
                yield test | {"message": f"Test {i:0>2}: {test['message']}"}
