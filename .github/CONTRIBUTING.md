# Contributing to Django-EasyJWT

## Commit Message Convention

This project uses [Conventional Commits](https://www.conventionalcommits.org/) for automated versioning and changelog generation.

### Commit Types

- `feat:` - New feature (triggers MINOR version bump,1.0.0 → 1.1.0)
- `fix:` - Bug fix (triggers PATCH version bump, 1.0.0 → 1.0.1)
- `perf:` - Performance improvement (1.0.0 → 1.0.1)
- `docs:` - Documentation changes (no version bump)
- `style:` - Code style changes (no version bump)
- `refactor:` - Code refactoring (no version bump)
- `test:` - Adding or updating tests (no version bump)
- `chore:` - Maintenance tasks (no version bump)
- `ci:` - CI/CD changes (no version bump)

### Examples

```bash
feat: add token rotation support
fix: resolve timeout issue in remote auth
perf: optimize token validation
docs: update installation instructions
```

### Breaking Changes

For breaking changes, add `BREAKING CHANGE:` in the commit body:

```bash
feat: redesign authentication API

BREAKING CHANGE: The authenticate() method now requires a request parameter
```

This triggers a MAJOR version bump (1.0.0 → 2.0.0).

## Release Process

Releases are **fully automated** via python-semantic-release:

1. **Push to master** - Make your changes and push to themaster` branch
2. **Automated analysis** - Semantic-release scans commits since last release
3. **Automatic release** (if warranted):
   - Version bumped automatically
   - CHANGELOG.md updated
   - Git tag created
   - GitHub release published
   - Package built and published to PyPI

**No manual version bumping, tagging, or PyPI uploads required!**

## Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes following conventional commits
4. Run tests: `pytest tests/ -v`
5. Push to your fork
6. Create Pull Request to `master`
7. Wait for review and merge

## Code Style

- Line length: 110 characters max
- Use type hints where appropriate
- Write tests for new features
- Update documentation as needed

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=easyjwt_auth --cov=easyjwt_client

# Run specific test file
pytest tests/test_auth/test_tokens.py -v
```
