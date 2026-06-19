# Changelog

All notable changes to this project will be automatically documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!-- version list -->

## v1.0.12 (2026-06-19)

### Bug Fixes

- **easyjwt_client**: Validate required settings in ready() to prevent mypy/django-stubs crash
  ([`b0f1e18`](https://github.com/garrethcain/django-easyjwt/commit/b0f1e18d7dfb53f87e2ab2473348b34f88e6c338))


## v1.0.11 (2026-06-17)

### Bug Fixes

- Updated PSR config to match v10
  ([`c62088b`](https://github.com/garrethcain/django-easyjwt/commit/c62088bf598f5b2df2faa5406f6072c4f9abecb6))


## Unreleased

### Bug Fixes

- Move changelog_file to correct PSR v10 config section
  ([`1ccd088`](https://github.com/garrethcain/django-easyjwt/commit/1ccd08828b2dd9ae3fc0af81815c7e7adf75d985))


## v1.0.9 (2026-06-17)

### Bug Fixes

- Correct semantic-release config, backfill missing changelog entries
  ([`853e376`](https://github.com/garrethcain/django-easyjwt/commit/853e3761a4a327b4f3506e113f1d7ada363db1b8))


## [1.0.8] - 2026-06-17

### Fixed

- Include `easyjwt_auth.token_blacklist` subpackage (and its `management/commands` subpackages) in PyPI distribution. Previous releases used explicit package listing which omitted subpackages, causing `ModuleNotFoundError` on any install from PyPI since v1.0.0.

## [1.0.7] - 2026-06-16

### Fixed

- Fixed `TOKEN_USER_CLASS` default from `easyjwt_user.models.TokenUser` to `easyjwt_auth.models.TokenUser`
- `CreateUserSerializer.create()` now uses `create_user()` instead of `Manager.create()` + `set_password()`
- Added configurable `REMOTE_AUTH_SERVICE_PASSWORD_CHANGE_PATH` setting, removed hardcoded path
- `TokenViewBase._serializer_class` now stores setting key name, resolves at runtime via `getattr(api_settings, key)`
- Added catch-all `requests.RequestException` handler in client utils

### Changed

- Merged `release-publish.yml` into `release-version.yml` (single CI workflow)

### Docs

- Full README refresh: badges, features, config reference tables, API endpoints, security section, curl examples

## [1.0.6] - 2026-06-16

### Fixed

- Validate password confirmation in `CreateUserSerializer`
- Sanitize error responses to prevent information leakage
- Enforce authentication on `TokenUserDetailView`
- Resolve 7 bugs across client, user, and settings modules
- Add SSL verification warning, remove dead code, add error logging
- Enforce password validation in admin user creation form
- `RemoteAuthBackend` now inherits correct Django `BaseBackend`

### Changed

- Unify settings access pattern, remove dead `jwt_secret` field

### Tests

- Add comprehensive blacklist subsystem tests
- Add coverage for previously untested features
- Fix `InsecureKeyLengthWarning` in `TokenBackend` tests
- Add coverage for client views, user views, and known bug markers

### Chores

- Removed unreferenced file

## [1.0.5] - 2026-04-17

### Fixed

- Use `GenericAPIView` for `PasswordChangeView`
- Password change returns meaningful validation errors, password validator runs, validator errors bubble up to the client service

## [1.0.4] - 2026-04-17

### Fixed

- Password change returns validation error instead of 404

### Changed

- Corrected the semantic-release configuration

## [1.0.3] - 2026-03-05

### Fixed

- Separated the version and release steps for the CI pipeline
- Stopped building the package in the wrong CI step

### Build

- Added skip message to the PSR commit message to avoid duplicate runs

## [1.0.2] - 2026-03-05

### Fixed

- Updated the docs

## [1.0.1] - 2026-03-04

### Fixed

- Add environment and build step for PyPI trusted publishing
- Fixed CI authentication token

### Build

- Updated the CI environment configuration

## [1.0.0] - 2026-03-04

### Breaking Changes

- Replaced MD5 with SHA-256 for password hashing in token revocation
- Renamed `ModelBackend` to `RemoteAuthBackend` to avoid confusion with Django's built-in backend
- Changed `on_delete=models.SET_NULL` to `CASCADE` for `OutstandingToken` to prevent orphan tokens

### Fixed

- Fixed Bearer token parsing to use standard space delimiter instead of colon
- Added configurable timeout to all HTTP requests (default: 30 seconds)
- Made SSL verification configurable via `REMOTE_AUTH_SSL_VERIFY` setting
- Consolidated HTTP error handling across client modules
- Removed duplicate `BLACKLIST_AFTER_ROTATION` check in token verification
- Fixed inconsistent `AUTH_HEADER_NAME` usage

### Changed

- Removed unused `get_csrf_token()` method from `TokenManager`
- Removed verbose Django tutorial comments from `easyjwt_user/models.py`
- Added `__all__` exports to all public modules for better API documentation

### Security

- Replaced MD5 with SHA-256 for password hashing (function name kept for backwards compatibility)
