# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog],
and this project adheres to [Semantic Versioning].


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


## [0.0.1] - 2024-09-27

- initial release


<!------------------------------------->

<!-- Links -->
[keep a changelog]: https://keepachangelog.com/en/1.0.0/
[semantic versioning]: https://semver.org/spec/v2.0.0.html

<!-- Versions -->
[unreleased]: https://github.com/Author/Repository/compare/v0.0.2...HEAD
[0.0.2]: https://github.com/Author/Repository/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/Author/Repository/releases/tag/v0.0.1