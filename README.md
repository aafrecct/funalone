# FunAlone

A small python library that makes it easy to test a function alone, that is, mocking all
dependencies. True unittests, without having to manually look and add every called function to an
increasing list of @mock.patch decorators.

## Changelog

### 0.5.1
- Defaults can now be striped from the cloned function.
- Added some documentation. (Much missing still)
- Fixed missing import.
- Minor fixes.

### 0.5.0
- Separated functionality into two different files.
- Functions can now keep original globals and only override certain ones.
- Functions can now keep default arguments.
- Kept globals can be specified with a list of strings.
- Reworked how mocks are created and stored.
- Mocks can now be created and modified like attributes in the collection.
- Minor fixes

### 0.4.0
- Changed from a function decorator to a context manager for versatility.
- Made dependency logging optional

