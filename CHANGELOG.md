# Changelog

All notable changes to this project will be automatically documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### Breaking Changes
- Replaced MD5 with SHA-256 for password hashing in token revocation
- Renamed `ModelBackend` to `RemoteAuthBackend` to avoid confusion with Django's built-in backend
- Changed `on_delete=models.SET_NULL` to `CASCADE` for OutstandingToken to prevent orphan tokens

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
