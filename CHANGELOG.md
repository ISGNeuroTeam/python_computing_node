All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.1] - 2023-01-31
### Changed
- Stop launching workers agter 3 retries
### Fixed
- Test execution environment accepts platform_envs

## [1.2.0] - 2022-12-02
### Added
- Pass user guid to command executor
- Add logger config for execution environment

## [1.1.0] - 2022-11-22
### Added
- Added projects virtual environments
- Logging error while initialization
- Configuration script for project virtual environment
### Fixed
- Fixed get_command_syntax invoked before socket file exist
### Changed
- Workers errors in one file
- Downloading conda in local directory while building project

## [1.0.0] - 2022-04-25
### Added
- Logger configuration for every execution environment
- Add python virtual environment to test execution environment

## [0.1.0] - 2022-03-29
### Added
- Changelog.md.

### Changed
- Start using "changelog".