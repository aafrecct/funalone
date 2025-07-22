# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].

## [0.7.1] - 2025-05-30

### Changed
- Mocks will not be speced if spec-ing them fails. This avoids problems with some request objects.
- Changed type hints so that IsolatedFunctionClone instances now show the original function's type signature when called.

### Deprecated
- `with_isolated_function_clone` decorator is now deprecated because it adds unnecessary complexity in keeping the tested function's
type signature.

## [0.7.0] -  2025-05-30

### Added
- Mocks automatically created by the context are now, by default, autospec-ed with the functions initial globals.
- Contexts can now be reset, returning all metrics to 0.
- Isolated funtion clones can now be created with a decorator. Creating them once through this method and resetting them for every sub-test should be faster than repeatedly using the context manager.
- A new `allow_exceptions` paramenter prevents exception objects from being mocked and therefore not throwable.

### Deprecated
- Python 3.9 support has been dropped.

### Changed
- `create_namespaced_function_clone` now recieves a Callable instead of an Iterable for `keep_original_globals`. This callable will be called with all the functions original globals and the function will keep those that evaluate to True.
- Several changes to type hints. Hopefully now mypy won't complain as much when using the library.
- Changes to the whole test suite. Right now the new test suite barely reaches 100% coverage, but everything has been refatored so that new tests can be easily added almost declaratively. More tests might be added in a minor release in the future.
- The `mock_builtins` parameter has been reversed and is now `allow_builtins`.
- Minor improvements.

### Removed
- `DefaultMockingContext` is now not exported from the main module because it's usecases are limited and it's mostly built to work as part of IsolatedFunctionClone. (Making a fully working dict-like object that may be useful may be done for future updates.)

## [0.6.0] - 2025-01-14
- Breaking

### Added
- New `DefaultMockingContext` now has the functionality of old `MockCollection` and `IsolatedContext`, removing the extra unnecessary depth.

### Changed
- Context manager renamed to `IsolatedFunctionClone`
- Context manager is now a callable that will act as the isolated function.
- The custom `globals` context of the cloned function can now be accessed though the `context` attribute of `IsolatedFunctionClone`.
- Type hints

### Removed
- Intermediary object `MockCollection`. (Replaced, see 'Added')
- Intermediary object `IsolatedContext`. (Replaced, see 'Added')


## [0.5.1] - 2024-10-30

### Added
- Defaults can now be striped from the cloned function.
- Added some documentation. (Much missing still)

### Fixed
- Fixed missing import.
- Minor fixes.


## [0.5.0] - 2024-10-30

### Added
- Functions can now keep original globals and only override certain ones.
- Functions can now keep default arguments.
- Kept globals can be specified with a list of strings.
- Mocks can now be created and modified like attributes in the collection.

### Changed
- Refactored functionality into two files.
- Reworked how mocks are created and stored.

### Fixed
- Minor fixes


## [0.4.0] - 2024-10-17

### Changed
- Changed from a function decorator to a context manager for versatility.
- Made dependency logging optional


## 0.0.1 - 2024-09-27

- initial release


<!------------------------------------->

<!-- Links -->
[keep a changelog]: https://keepachangelog.com/en/1.0.0/
[semantic versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[0.7.0]: https://github.com/aafrecct/funalone/releases/tag/0.7.0
[0.6.0]: https://github.com/aafrecct/funalone/releases/tag/0.6.0
[0.5.1]: https://github.com/aafrecct/funalone/releases/tag/0.5.1
[0.5.0]: https://github.com/aafrecct/funalone/releases/tag/0.5.0
[0.4.0]: https://github.com/aafrecct/funalone/releases/tag/0.4.0