# GitHub Actions CI/CD Workflow

## Overview

This directory contains the GitHub Actions workflows for continuous integration and deployment.

## CI Workflow (`ci.yml`)

The main CI workflow runs on every push to `main` and on all pull requests. It ensures code quality and prevents regressions by running comprehensive checks.

### Jobs

#### 1. Lint (Ruff)
- **Purpose**: Enforces code style and catches common errors
- **Tool**: Ruff (fast Python linter)
- **Command**: `ruff check . --output-format=github`
- **Python Version**: 3.10
- **Features**:
  - GitHub-formatted output for inline annotations
  - Minimal dependencies (ruff only) for fast execution
  - Cached pip dependencies

#### 2. Type Check (Mypy)
- **Purpose**: Enforces type safety and catches type-related bugs
- **Tool**: Mypy (static type checker)
- **Command**: `mypy src/ --strict`
- **Python Version**: 3.10
- **Features**:
  - Strict mode enabled (no untyped code allowed)
  - Full dependency installation for accurate type checking
  - Cached pip dependencies

#### 3. Test (Pytest)
- **Purpose**: Runs test suite and verifies code coverage
- **Tool**: Pytest with pytest-cov
- **Command**: `pytest --cov=src --cov-report=xml --cov-report=term --cov-fail-under=90`
- **Python Versions**: 3.10, 3.11, 3.12 (matrix)
- **Features**:
  - Tests on multiple Python versions simultaneously
  - Coverage threshold enforced (≥90%)
  - XML and terminal coverage reports
  - Coverage artifacts uploaded (Python 3.10 only)
  - Optional Codecov integration
  - Cached pip dependencies per Python version

### Performance Optimizations

1. **Dependency Caching**: Each job caches pip dependencies to speed up subsequent runs
2. **Minimal Dependencies**: Lint job only installs ruff (not full requirements)
3. **Parallel Execution**: All jobs run in parallel by default
4. **Fail-Fast Disabled**: Test matrix continues even if one Python version fails

### Expected Execution Time

- **First Run** (no cache): ~3-5 minutes
- **Subsequent Runs** (with cache): ~2-3 minutes
- **Lint Job**: ~30-60 seconds
- **Type Check Job**: ~60-90 seconds
- **Test Job** (per Python version): ~60-120 seconds

### Triggers

- **Push to main**: Runs full CI on all commits to main branch
- **Pull Requests**: Runs full CI on all PRs to main branch

### Artifacts

- **Coverage Reports**: Uploaded from Python 3.10 test run
  - `coverage.xml`: XML format (for Codecov, IDE integration)
  - `htmlcov/`: HTML format (for viewing in browser)
  - Retention: 30 days

### Failure Scenarios

The workflow will fail if:
1. ✅ Ruff detects linting errors
2. ✅ Mypy finds type errors (strict mode)
3. ✅ Any test fails
4. ✅ Code coverage is below 90%

### CI Badge

The README includes a CI status badge that shows the current status:
- ✅ Green: All checks passing
- ❌ Red: One or more checks failing
- ⚪ Gray: No workflow runs yet

## Local Testing

Before pushing, you can run the same checks locally:

```bash
# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# OR
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Run all checks (same as CI)
make lint        # Ruff check
make typecheck   # Mypy strict
make test        # Pytest with coverage

# Or run manually
ruff check . --output-format=github
mypy src/ --strict
pytest --cov=src --cov-report=xml --cov-report=term --cov-fail-under=90
```

## Codecov Integration (Optional)

The workflow includes optional Codecov integration. To enable:

1. Sign up at [codecov.io](https://codecov.io)
2. Add repository to Codecov
3. Add `CODECOV_TOKEN` to repository secrets (Settings → Secrets → Actions)
4. The workflow will automatically upload coverage reports

**Note**: Codecov upload is configured with `continue-on-error: true`, so CI won't fail if Codecov is unavailable.

## Best Practices

1. **Always run checks locally before pushing** to avoid CI failures
2. **Keep coverage at or above 90%** - add tests for new code
3. **Fix linting and type errors immediately** - don't ignore them
4. **Review coverage reports** - uploaded artifacts show which lines aren't covered
5. **Use descriptive commit messages** - they appear in CI logs

## Troubleshooting

### Workflow Fails on Lint
- Run `ruff check .` locally to see errors
- Fix with `ruff check . --fix` or `make format`

### Workflow Fails on Type Check
- Run `mypy src/ --strict` locally
- Add missing type hints or fix type errors
- Check mypy configuration in `pyproject.toml`

### Workflow Fails on Tests
- Run `pytest -v` locally to see which tests fail
- Check test output in CI logs
- Ensure all dependencies are in `requirements.txt`

### Workflow Fails on Coverage
- Run `pytest --cov=src --cov-report=term-missing` locally
- Identify uncovered lines and add tests
- Current threshold: 90% (configured in `pyproject.toml`)

### Slow Workflow Execution
- Check if caching is working (should see "Cache restored" in logs)
- First run is always slower (building cache)
- Expected time: 2-5 minutes total

## Maintenance

- **Action Versions**: Update to latest stable versions periodically
  - `actions/checkout@v4`
  - `actions/setup-python@v5`
  - `actions/cache@v4`
  - `actions/upload-artifact@v4`
  - `codecov/codecov-action@v4`

- **Python Versions**: Update matrix when dropping/adding Python versions
  - Currently: 3.10, 3.11, 3.12
  - Update in `ci.yml` line 76

- **Dependencies**: Keep in sync with `requirements.txt` and `requirements-dev.txt`

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python in GitHub Actions](https://docs.github.com/en/actions/automating-builds-and-tests/building-and-testing-python)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.io/)
