# GitHub Issues for Google Photos Sync Application

Copy each issue below to GitHub. They are numbered for sequential implementation.

---

## Issue #1: Project Foundation - Setup pyproject.toml, Dependencies, and Development Tools

### Description
Set up the complete Python project structure with modern dependency management, ruff linting configuration, and development tooling following PEP standards.

### Context
This is a TDD-driven Flask + Streamlit application for syncing Google Photos. All code must follow PEP standards, clean code principles, and use ruff for linting.

### Acceptance Criteria
- [ ] Create `pyproject.toml` with project metadata following PEP 621
- [ ] Configure ruff with line-length 88, Python 3.10+, select rules: E, F, I, N, W, B, C90
- [ ] Add production dependencies: flask>=3.1.2, streamlit>=1.52.2, google-auth>=2.25.0, google-api-python-client>=2.110.0, requests>=2.31.0, python-dotenv>=1.0.0
- [ ] Add dev dependencies: pytest>=7.4.0, pytest-cov>=4.1.0, pytest-mock>=3.12.0, ruff>=0.1.9, mypy>=1.7.0, uv>=0.5.0
- [ ] Create `requirements.txt` and `requirements-dev.txt` from pyproject.toml
- [ ] Configure pytest with testpaths, coverage target 90%, and sensible defaults
- [ ] Create `.env.example` with placeholder environment variables
- [ ] Create `Makefile` with targets: venv, install, test, lint, format, coverage, run-api, run-ui, clean
- [ ] Create `.python-version` file specifying Python 3.10+
- [ ] All configuration files must be valid and properly formatted

### Technical Details
- Use `[project]` table in pyproject.toml (modern standard)
- Configure ruff's `[tool.ruff]` section with per-file-ignores for tests (allow S101 for assert)
- Configure pytest with `[tool.pytest.ini_options]` including coverage report settings
- **CRITICAL**: Always use virtual environment (venv). Use `uv` for fast package installation (10-100x faster than pip)
- Makefile should:
  - Use .PHONY targets
  - Include `venv` target: create virtual environment with `uv venv`
  - Include `install` target: install dependencies with `uv pip install`
  - Include `clean` target: remove `.venv/`, `__pycache__/`, `.pytest_cache/`, etc.
  - All targets should check if venv is activated or activate it automatically
- `.python-version` file helps tools like uv auto-detect Python version

### Testing Requirements
- Create fresh virtual environment: `uv venv`
- Activate venv and verify: `which python` or `where python` should point to `.venv/`
- Install dependencies: `uv pip install -r requirements.txt -r requirements-dev.txt`
- Verify ruff runs without errors on empty project: `ruff check .`
- Verify pytest configuration: `pytest --collect-only` should work
- Verify Makefile targets work: `make venv`, `make install`, `make test`
- Time the install with uv vs pip (uv should be significantly faster)

### Files to Create
- `pyproject.toml`
- `requirements.txt`
- `requirements-dev.txt`
- `.env.example`
- `Makefile`
- `.python-version` (contains: `3.10`)

### References
- PEP 621 (pyproject.toml metadata)
- PEP 518 (build system)
- Clean Code: Keep configuration files simple and well-documented

---

## Issue #2: Project Structure - Create Source and Test Directory Hierarchy

### Description
Create the complete directory structure for the application following Python packaging best practices with clear separation between API, core logic, Google Photos integration, and UI layers.

### Context
We're building an API-first application with Flask backend and Streamlit frontend. The structure must support TDD with clear test organization.

### Acceptance Criteria
- [ ] Create `src/google_photos_sync/` main package with `__init__.py`
- [ ] Create `src/google_photos_sync/api/` for Flask API layer
- [ ] Create `src/google_photos_sync/core/` for business logic (framework-agnostic)
- [ ] Create `src/google_photos_sync/google_photos/` for Google Photos API integration
- [ ] Create `src/google_photos_sync/ui/` for Streamlit GUI
- [ ] Create `src/google_photos_sync/ui/components/` for reusable UI components
- [ ] Create `src/google_photos_sync/utils/` for shared utilities
- [ ] Create `tests/unit/`, `tests/integration/`, `tests/e2e/` with `__init__.py` files
- [ ] Create `tests/conftest.py` for pytest fixtures
- [ ] All `__init__.py` files should have module docstrings

### Technical Details
- Use `src/` layout (PEP recommends this for distributable packages)
- Package name: `google_photos_sync` (underscores, not hyphens per PEP 8)
- Each `__init__.py` should contain a one-line docstring describing the module's purpose
- Test directory structure mirrors source structure for clarity

### Testing Requirements
- Verify package is importable: `python -c "import google_photos_sync"`
- Verify pytest discovers test directories: `pytest --collect-only`

### Files to Create
- `src/google_photos_sync/__init__.py`
- `src/google_photos_sync/api/__init__.py`
- `src/google_photos_sync/core/__init__.py`
- `src/google_photos_sync/google_photos/__init__.py`
- `src/google_photos_sync/ui/__init__.py`
- `src/google_photos_sync/ui/components/__init__.py`
- `src/google_photos_sync/utils/__init__.py`
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/e2e/__init__.py`
- `tests/conftest.py`

### References
- PEP 8 (package naming)
- Python Packaging Guide (src layout)

---

## Issue #3: TDD - Google Photos OAuth Authentication Module

### Description
Implement OAuth 2.0 authentication for Google Photos API following TDD. Write failing tests first, then implement the authentication flow with credential storage and refresh token handling.

### Context
We need to authenticate with Google Photos API for both source (read-only) and target (append-only) accounts. Must handle OAuth flow, token storage, and automatic refresh.

### Acceptance Criteria
- [ ] RED: Write failing tests in `tests/unit/test_google_photos_auth.py` for:
  - OAuth URL generation with correct scopes
  - Token exchange from authorization code
  - Credential storage and retrieval
  - Automatic token refresh when expired
  - Multiple account credential management (source vs target)
- [ ] GREEN: Implement `src/google_photos_sync/google_photos/auth.py` to pass all tests
- [ ] REFACTOR: Clean up code, ensure PEP 8 compliance, add type hints
- [ ] Test coverage ≥90% for auth module
- [ ] All docstrings follow Google or NumPy style
- [ ] Ruff linting passes with zero errors
- [ ] Use dependency injection (pass config/storage, don't hard-code paths)

### Technical Details
- Use `google.oauth2.credentials` and `google_auth_oauthlib.flow`
- Required scopes: 
  - Source account: `https://www.googleapis.com/auth/photoslibrary.readonly`
  - Target account: `https://www.googleapis.com/auth/photoslibrary.appendonly`
- Store credentials securely (encrypt tokens if possible)
- Handle credential refresh automatically using refresh tokens
- Support multiple accounts (source and target) simultaneously

### Testing Requirements
- Mock Google OAuth endpoints (don't make real API calls in tests)
- Test token expiry and refresh logic
- Test error handling (invalid auth code, network errors, expired refresh token)
- Use pytest fixtures for common test data (mock credentials, config)
- Run with coverage: `pytest tests/unit/test_google_photos_auth.py --cov=src/google_photos_sync/google_photos/auth --cov-report=term-missing`

### Files to Create
- `tests/unit/test_google_photos_auth.py` (RED phase - write first)
- `src/google_photos_sync/google_photos/auth.py` (GREEN phase - implement after tests)

### References
- Google Photos API Authentication: https://developers.google.com/photos/library/guides/authentication-authorization
- Clean Code: Single Responsibility Principle (auth module does only authentication)
- KISS: Keep the OAuth flow simple and understandable

---

## Issue #4: TDD - Google Photos API Client Wrapper

### Description
Create a wrapper around Google Photos API following TDD. Implement methods for listing photos, fetching photo metadata, downloading photos, and uploading photos with metadata preservation.

### Context
This client abstracts the Google Photos API complexity and provides clean methods for our sync operations. Must handle pagination, rate limiting, and metadata preservation.

### Acceptance Criteria
- [ ] RED: Write failing tests in `tests/unit/test_google_photos_client.py` for:
  - List all photos with pagination handling
  - Fetch photo metadata (filename, creation time, EXIF, location)
  - Download photo binary data (support streaming for memory efficiency)
  - Upload photo with metadata preservation
  - Handle rate limiting (respect 429 responses)
  - Error handling for common API errors
- [ ] GREEN: Implement `src/google_photos_sync/google_photos/client.py` to pass all tests
- [ ] Create `src/google_photos_sync/google_photos/models.py` for Photo data class
- [ ] REFACTOR: Ensure clean code, type hints, PEP 8 compliance
- [ ] Test coverage ≥90% for client module
- [ ] Ruff linting passes with zero errors

### Technical Details
- Use `google-api-python-client` library (`googleapiclient.discovery`)
- Implement pagination using `pageToken` for large photo libraries
- Rate limiting: implement exponential backoff for 429 errors (don't be aggressive)
- For downloads: use streaming to avoid loading entire files in memory
- For uploads: preserve all metadata (creation time, EXIF, location, description)
- Use dataclasses or Pydantic for Photo model (clean, typed data structures)

### Testing Requirements
- Mock Google Photos API responses (use `pytest-mock` or `unittest.mock`)
- Test pagination logic with mock paginated responses
- Test rate limiting with mock 429 responses and verify backoff behavior
- Test download streaming (verify file is not fully loaded in memory)
- Test metadata preservation in uploads
- Run with coverage: `pytest tests/unit/test_google_photos_client.py --cov=src/google_photos_sync/google_photos --cov-report=term-missing`

### Files to Create
- `tests/unit/test_google_photos_client.py` (RED phase - write first)
- `src/google_photos_sync/google_photos/client.py` (GREEN phase)
- `src/google_photos_sync/google_photos/models.py` (data models)

### References
- Google Photos API: https://developers.google.com/photos/library/reference/rest
- Clean Code: Encapsulation (hide API complexity)
- KISS: Simple, clear method names

---

## Issue #5: TDD - Compare Service for Account Comparison

### Description
Implement the compare feature following TDD. This service compares source and target Google Photos accounts and produces a JSON report of differences (missing photos, different metadata).

### Context
Compare is a read-only operation that helps users understand what will change during sync. Output should be clear, actionable, and optionally usable to speed up operations.

### Acceptance Criteria
- [ ] RED: Write failing tests in `tests/unit/test_compare_service.py` for:
  - Compare two accounts and identify missing photos on target
  - Identify photos with different metadata (e.g., different creation time)
  - Identify extra photos on target (that don't exist on source)
  - Generate JSON report with clear structure
  - Handle empty accounts gracefully
  - Handle identical accounts (no differences)
- [ ] GREEN: Implement `src/google_photos_sync/core/compare_service.py` to pass all tests
- [ ] REFACTOR: Clean code, type hints, docstrings
- [ ] Test coverage ≥90%
- [ ] Ruff linting passes with zero errors

### Technical Details
- Use Google Photos API client from Issue #4
- Compare photos by unique identifier (e.g., Google Photos media item ID)
- Also compare metadata: filename, creation time, file size
- JSON output format:
  ```json
  {
    "source_account": "user@example.com",
    "target_account": "backup@example.com",
    "comparison_date": "2025-12-21T10:30:00Z",
    "total_source_photos": 1500,
    "total_target_photos": 1450,
    "missing_on_target": [...],
    "different_metadata": [...],
    "extra_on_target": [...]
  }
  ```
- Use dependency injection: inject Google Photos client, don't instantiate internally

### Testing Requirements
- Mock Google Photos client responses
- Test various scenarios: empty accounts, identical accounts, partial sync, complete mismatch
- Verify JSON output structure and content
- Test performance with large mock datasets (1000+ photos)
- Run with coverage: `pytest tests/unit/test_compare_service.py --cov=src/google_photos_sync/core/compare_service --cov-report=term-missing`

### Files to Create
- `tests/unit/test_compare_service.py` (RED phase - write first)
- `src/google_photos_sync/core/compare_service.py` (GREEN phase)

### References
- Clean Code: Functions should do one thing well
- KISS: Simple comparison logic

---

## Issue #6: TDD - Memory-Efficient Transfer Manager

### Description
Implement a transfer manager following TDD that handles photo downloads and uploads efficiently without exhausting memory, using streaming and controlled buffering.

### Context
We need to transfer potentially thousands of photos without loading them all into RAM. The transfer manager should stream data from source to target with minimal memory footprint.

### Acceptance Criteria
- [ ] RED: Write failing tests in `tests/unit/test_transfer_manager.py` for:
  - Transfer single photo from source to target (streaming)
  - Memory usage remains bounded (test with mock large files)
  - Verify metadata is preserved during transfer
  - Handle transfer failures gracefully (retry logic)
  - Progress reporting (bytes transferred, photos completed)
  - Concurrent transfers with configurable max workers (default: 3-5 to respect API limits)
- [ ] GREEN: Implement `src/google_photos_sync/core/transfer_manager.py` to pass all tests
- [ ] REFACTOR: Clean code, type hints, efficient implementation
- [ ] Test coverage ≥90%
- [ ] Ruff linting passes with zero errors

### Technical Details
- Use streaming: download chunks, upload chunks (don't load full file in memory)
- Default chunk size: 8MB or configurable
- Support concurrent transfers using `concurrent.futures.ThreadPoolExecutor`
- Max concurrent transfers: 3-5 (conservative to avoid hitting Google API rate limits)
- Implement simple retry logic with exponential backoff (max 3 retries)
- Progress callback: `on_progress(photo_id, bytes_transferred, total_bytes)`
- Use dependency injection: inject Google Photos client

### Testing Requirements
- Mock large file transfers (100MB+) and verify memory doesn't grow proportionally
- Test concurrent transfer logic with mock photos
- Test retry mechanism with mock failures
- Test progress reporting callback
- Verify metadata preservation
- Run with coverage: `pytest tests/unit/test_transfer_manager.py --cov=src/google_photos_sync/core/transfer_manager --cov-report=term-missing`

### Files to Create
- `tests/unit/test_transfer_manager.py` (RED phase - write first)
- `src/google_photos_sync/core/transfer_manager.py` (GREEN phase)

### References
- Clean Code: Small functions, clear names
- KISS: Simple streaming logic, avoid premature optimization

---

## Issue #7: TDD - Idempotent Sync Service with Monodirectional Sync

### Description
Implement the core sync service following TDD. This service performs monodirectional sync from source to target, ensuring target becomes 100% identical to source (idempotent operation).

### Context
Sync is the main feature. It must be idempotent (safe to run multiple times), monodirectional (source → target only), and handle deletions on target if files don't exist on source.

### Acceptance Criteria
- [ ] RED: Write failing tests in `tests/unit/test_sync_service.py` for:
  - Sync empty source to non-empty target (target becomes empty)
  - Sync non-empty source to empty target (target gets all photos)
  - Sync with partial overlap (missing photos are added, extras are deleted)
  - Idempotency: running sync twice has same result as running once
  - Sync preserves all metadata
  - Sync respects dry-run mode (preview changes without executing)
  - Progress reporting during sync
- [ ] GREEN: Implement `src/google_photos_sync/core/sync_service.py` to pass all tests
- [ ] REFACTOR: Clean code, type hints, clear logic
- [ ] Test coverage ≥90%
- [ ] Ruff linting passes with zero errors

### Technical Details
- Use Compare service to identify differences
- Use Transfer manager for efficient photo transfers
- Deletion logic: delete photos on target that don't exist on source
- Dry-run mode: return list of planned actions without executing
- Progress reporting: `on_progress(action, photo_id, progress_pct)`
- Idempotency: if sync interrupted, re-running completes the work
- Use dependency injection: inject compare service, transfer manager

### Testing Requirements
- Test all sync scenarios with mock data
- Verify idempotency: run sync twice, verify second run does nothing
- Test dry-run mode returns correct action plan
- Test deletion logic (photos removed from target when missing on source)
- Verify metadata preservation
- Test progress reporting
- Run with coverage: `pytest tests/unit/test_sync_service.py --cov=src/google_photos_sync/core/sync_service --cov-report=term-missing`

### Files to Create
- `tests/unit/test_sync_service.py` (RED phase - write first)
- `src/google_photos_sync/core/sync_service.py` (GREEN phase)

### References
- Clean Code: Functions do one thing, SRP
- KISS: Clear, simple sync logic
- Idempotency is critical for user confidence

---

## Issue #8: Flask API - Application Factory and Configuration

### Description
Set up Flask application using the application factory pattern with proper configuration management, logging, and error handling middleware.

### Context
API-first design: Flask provides REST API consumed by Streamlit UI and potentially other clients. Must be production-ready with proper structure.

### Acceptance Criteria
- [ ] Create `src/google_photos_sync/config.py` with configuration classes (Dev, Prod, Test)
- [ ] Create `src/google_photos_sync/api/app.py` with Flask application factory
- [ ] Configure logging in `src/google_photos_sync/utils/logging_config.py`
- [ ] Create error handling middleware in `src/google_photos_sync/api/middleware.py`
- [ ] Configure CORS for Streamlit frontend
- [ ] Add health check endpoint `/health`
- [ ] All configuration loaded from environment variables (.env file)
- [ ] Ruff linting passes with zero errors
- [ ] Basic integration test verifying Flask app starts

### Technical Details
- Application factory pattern: `create_app(config_name='development')`
- Configuration: use classes (DevelopmentConfig, ProductionConfig, TestConfig)
- Load secrets from environment variables using `python-dotenv`
- Logging: structured logging with timestamps, log levels
- Error handlers: JSON responses for 400, 404, 500 errors
- CORS: allow Streamlit frontend origin (configure via env var)
- Health check returns: `{"status": "healthy", "version": "0.1.0"}`

### Testing Requirements
- Integration test in `tests/integration/test_flask_app.py`:
  - App creation with different configs
  - Health endpoint returns 200
  - Error handlers return correct JSON
  - CORS headers present
- Run: `pytest tests/integration/test_flask_app.py`

### Files to Create
- `src/google_photos_sync/config.py`
- `src/google_photos_sync/api/app.py`
- `src/google_photos_sync/utils/logging_config.py`
- `src/google_photos_sync/api/middleware.py`
- `tests/integration/test_flask_app.py`

### References
- Flask documentation: Application factory pattern
- PEP 8: Configuration as code
- Clean Code: Separation of concerns (config, app, middleware)

---

## Issue #9: Flask API - REST Endpoints for Sync and Compare

### Description
Implement Flask REST API endpoints for OAuth callback, compare, and sync operations with proper request validation, error handling, and JSON responses.

### Context
These endpoints are consumed by Streamlit UI. Must be well-documented, follow REST principles, and provide clear responses.

### Acceptance Criteria
- [ ] Implement `src/google_photos_sync/api/routes.py` with endpoints:
  - `POST /api/auth/google` - Initiate OAuth flow
  - `GET /api/auth/callback` - OAuth callback handler
  - `POST /api/compare` - Compare source and target accounts
  - `POST /api/sync` - Execute sync operation
  - `GET /api/sync/status/<task_id>` - Get sync progress (if async)
- [ ] Request validation using dataclasses or Pydantic
- [ ] Proper HTTP status codes (200, 201, 400, 401, 404, 500)
- [ ] JSON responses with clear error messages
- [ ] Integration tests in `tests/integration/test_api_routes.py`
- [ ] Test coverage ≥90% for routes
- [ ] Ruff linting passes with zero errors
- [ ] API documentation in docstrings

### Technical Details
- Use Flask blueprints for organization
- Request body validation (reject invalid requests with 400)
- Authentication: verify OAuth tokens in requests
- For long-running sync: consider background tasks (or keep simple synchronous for now)
- Response format:
  ```json
  {
    "success": true,
    "data": {...},
    "message": "Operation completed"
  }
  ```
- Error format:
  ```json
  {
    "success": false,
    "error": "Error description",
    "code": "ERROR_CODE"
  }
  ```

### Testing Requirements
- Integration tests with Flask test client
- Test happy paths: successful compare, successful sync
- Test error cases: invalid auth, missing parameters, API errors
- Mock Google Photos client in tests
- Verify response formats and status codes
- Run: `pytest tests/integration/test_api_routes.py --cov=src/google_photos_sync/api --cov-report=term-missing`

### Files to Create
- `src/google_photos_sync/api/routes.py`
- `tests/integration/test_api_routes.py`

### References
- REST API best practices
- Flask documentation: Blueprints, request handling
- Clean Code: Thin controllers (delegate to services)

---

## Issue #10: Streamlit UI - Foundation and Layout

### Description
Create the Streamlit application foundation with navigation, layout, and reusable UI components following clean code principles.

### Context
The UI must be extremely user-friendly for non-technical users. Clear, simple, with no room for mistakes.

### Acceptance Criteria
- [ ] Create `src/google_photos_sync/ui/app.py` as main Streamlit entry point
- [ ] Implement sidebar navigation (Home, Compare, Sync, Settings)
- [ ] Create session state management for user data
- [ ] Create reusable components in `src/google_photos_sync/ui/components/`:
  - `auth_component.py` - OAuth authentication UI
  - `status_component.py` - Status messages and progress bars
  - `confirmation_dialog.py` - Warning dialogs for destructive operations
- [ ] Implement basic styling (clean, professional)
- [ ] Add footer with version and documentation link
- [ ] Ruff linting passes with zero errors
- [ ] Manual testing: app runs and displays correctly

### Technical Details
- Use `st.sidebar` for navigation
- Session state keys: `source_auth`, `target_auth`, `comparison_result`, `sync_status`
- Components should be pure functions (no side effects)
- Use `st.error()`, `st.warning()`, `st.success()`, `st.info()` for messages
- Styling: use Streamlit's theming, keep it simple
- Entry point: `streamlit run src/google_photos_sync/ui/app.py`

### Testing Requirements
- Manual testing (Streamlit doesn't have easy unit testing)
- Verify navigation works
- Verify session state persists correctly
- Verify components render without errors
- Check responsive layout

### Files to Create
- `src/google_photos_sync/ui/app.py`
- `src/google_photos_sync/ui/components/__init__.py`
- `src/google_photos_sync/ui/components/auth_component.py`
- `src/google_photos_sync/ui/components/status_component.py`
- `src/google_photos_sync/ui/components/confirmation_dialog.py`

### References
- Streamlit documentation: Session state, components
- Clean Code: Reusable components
- KISS: Simple, clear UI

---

## Issue #11: Streamlit UI - Sync View with Safety Warnings

### Description
Implement the sync view in Streamlit with clear, prominent warnings before destructive operations, explaining exactly which account will be modified.

### Context
This is critical for user safety. Users must clearly understand that target account will be modified to match source (including deletions). No room for confusion.

### Acceptance Criteria
- [ ] Create `src/google_photos_sync/ui/components/sync_view.py`
- [ ] Display source and target account information clearly
- [ ] Show comparison summary before sync (X photos to add, Y to delete)
- [ ] Implement multi-step confirmation for sync:
  1. User reviews comparison
  2. User checks "I understand target will be modified" checkbox
  3. User clicks "Review Sync Plan" button
  4. Display detailed warning dialog explaining destructive nature
  5. User types account name to confirm
  6. User clicks "Execute Sync" button
- [ ] Show real-time progress during sync (progress bar, current photo, ETA)
- [ ] Display success/failure summary after sync
- [ ] Emergency stop button during sync
- [ ] Ruff linting passes with zero errors

### Technical Details
- Warning text example: "⚠️ DESTRUCTIVE OPERATION: The target account (backup@example.com) will be modified to exactly match the source account (main@example.com). This includes DELETING photos on target that don't exist on source. This cannot be undone."
- Confirmation: user must type target account name exactly to confirm
- Progress: use `st.progress()` and update in real-time
- Call Flask API `/api/sync` endpoint for execution
- Handle API errors gracefully with clear messages
- Store sync results in session state for review

### Testing Requirements
- Manual testing scenarios:
  - Verify warning messages are clear and prominent
  - Verify user cannot proceed without confirmations
  - Verify progress updates correctly
  - Verify error messages display clearly
  - Test emergency stop button
- User acceptance testing with non-technical person

### Files to Create
- `src/google_photos_sync/ui/components/sync_view.py`

### References
- UX best practices: Destructive operations require explicit confirmation
- Clean Code: Clear, descriptive text
- KISS: Simple, impossible-to-misunderstand UI

---

## Issue #12: Streamlit UI - Compare View

### Description
Implement the compare view in Streamlit that displays account comparison results in a clear, actionable format.

### Context
Compare is a read-only operation that helps users preview what sync will do. Should be easy to understand even for non-technical users.

### Acceptance Criteria
- [ ] Create `src/google_photos_sync/ui/components/compare_view.py`
- [ ] Display source and target account information
- [ ] Show comparison statistics:
  - Total photos on source
  - Total photos on target
  - Photos to be added to target
  - Photos to be deleted from target
  - Photos with metadata differences
- [ ] Display detailed lists (collapsible sections):
  - Missing photos on target (with thumbnails if possible)
  - Extra photos on target (will be deleted)
  - Metadata differences
- [ ] Export comparison as JSON (download button)
- [ ] Clear call-to-action: "Go to Sync" button
- [ ] Handle empty/identical accounts gracefully
- [ ] Ruff linting passes with zero errors

### Technical Details
- Call Flask API `/api/compare` endpoint
- Use `st.metric()` for statistics
- Use `st.expander()` for collapsible lists
- Use `st.download_button()` for JSON export
- Display photo thumbnails using `st.image()` (if URLs available)
- Color coding: red for deletions, green for additions, yellow for changes
- Cache comparison results in session state (avoid re-running on page refresh)

### Testing Requirements
- Manual testing:
  - Test with empty source/target
  - Test with identical accounts
  - Test with various differences
  - Verify JSON export is valid
  - Verify UI is clear and understandable
- User acceptance testing with non-technical person

### Files to Create
- `src/google_photos_sync/ui/components/compare_view.py`

### References
- Streamlit documentation: Metrics, expanders, downloads
- Clean Code: Clear presentation of data
- KISS: Simple, scannable UI

---

## Issue #13: Integration Tests - End-to-End Workflow

### Description
Create comprehensive end-to-end tests that verify the complete workflow from authentication through compare and sync operations.

### Context
E2E tests ensure all components work together correctly. These tests use real Flask app and services but mock external Google API calls.

### Acceptance Criteria
- [ ] Create `tests/e2e/test_sync_workflow.py` with tests for:
  - Complete OAuth flow (mock Google OAuth)
  - Full compare operation (mock Google Photos API)
  - Full sync operation (mock Google Photos API)
  - Error recovery scenarios
  - Idempotency verification
- [ ] Tests should cover the entire stack: Flask API → Services → Google Photos client
- [ ] Mock Google API responses realistically
- [ ] Verify database/state persistence if applicable
- [ ] Test coverage for E2E tests ≥80%
- [ ] All tests pass consistently
- [ ] Ruff linting passes with zero errors

### Technical Details
- Use Flask test client for API calls
- Use `pytest-mock` to mock Google API responses
- Create realistic test data (photos with metadata)
- Test complete workflows, not just individual endpoints
- Verify state changes after operations
- Test error scenarios (API failures, network issues)

### Testing Requirements
- Run E2E tests: `pytest tests/e2e/ -v`
- Verify tests are deterministic (pass consistently)
- Verify mock data is realistic
- Check test execution time (should be reasonable, <1 minute total)

### Files to Create
- `tests/e2e/test_sync_workflow.py`
- Additional fixtures in `tests/conftest.py` if needed

### References
- Pytest documentation: Fixtures, mocking
- Clean Code: Tests as documentation
- Integration testing best practices

---

## Issue #14: CI/CD - GitHub Actions Workflow

### Description
Set up GitHub Actions workflow for continuous integration: run tests, check coverage (≥90%), run linting, and verify code quality on every push and PR.

### Context
Automated CI ensures code quality and prevents regressions. All checks must pass before merging.

### Acceptance Criteria
- [ ] Create `.github/workflows/ci.yml` with jobs:
  - Lint (ruff check)
  - Type check (mypy)
  - Tests (pytest with coverage)
  - Coverage threshold check (≥90%)
- [ ] Run on: push to main, pull requests
- [ ] Use Python 3.10, 3.11, 3.12 matrix
- [ ] Cache dependencies for faster runs
- [ ] Upload coverage report as artifact
- [ ] Fail if any check fails
- [ ] Badge in README showing CI status

### Technical Details
- Use `actions/checkout@v4`, `actions/setup-python@v4`
- Install dependencies: `pip install -r requirements.txt -r requirements-dev.txt`
- Run ruff: `ruff check . --output-format=github`
- Run mypy: `mypy src/ --strict`
- Run pytest: `pytest --cov=src --cov-report=xml --cov-report=term --cov-fail-under=90`
- Upload coverage to GitHub (optional: integrate with Codecov)

### Testing Requirements
- Verify workflow runs successfully on a test push
- Verify it fails correctly when tests fail
- Verify it fails when coverage is <90%
- Check execution time is reasonable (<5 minutes)

### Files to Create
- `.github/workflows/ci.yml`

### References
- GitHub Actions documentation
- CI/CD best practices
- Python testing in CI

---

## Issue #15: Documentation - README, Architecture, and User Guide

### Description
Create comprehensive documentation: update README with setup instructions, create architecture document, and write user guide for non-technical users.

### Context
Good documentation is essential for maintainability and user adoption. Non-technical users need step-by-step guides.

### Acceptance Criteria
- [ ] Update `README.md` with:
  - Project description and features
  - Prerequisites (Python 3.10+, Google Cloud project)
  - Installation instructions
  - Quick start guide
  - Configuration (environment variables)
  - Running tests
  - CI/CD badge
  - Contributing guidelines
  - License
- [ ] Create `docs/architecture.md` documenting:
  - System architecture diagram (ASCII or link to image)
  - Component descriptions (API, Core, UI, Google Photos integration)
  - Data flow diagrams (compare, sync)
  - Technology stack
  - Design decisions and rationale
- [ ] Create `docs/user_guide.md` with:
  - Step-by-step setup (Google Cloud Console, OAuth credentials)
  - How to authenticate accounts
  - How to compare accounts
  - How to sync accounts (with warnings)
  - Troubleshooting common issues
  - FAQ
- [ ] All documentation uses clear, simple language
- [ ] Include screenshots or ASCII diagrams where helpful
- [ ] Ruff linting passes on Python code examples in docs

### Technical Details
- Use Markdown for all documentation
- Include code examples with syntax highlighting
- Architecture diagram can be ASCII art or mermaid diagram
- User guide should assume zero technical knowledge
- Include troubleshooting section with common errors

### Testing Requirements
- Manual review: read through all docs
- Verify all links work
- Verify code examples are correct
- Have non-technical person review user guide for clarity

### Files to Update/Create
- `README.md` (update existing)
- `docs/architecture.md` (create)
- `docs/user_guide.md` (create)

### References
- Clean Code: Code is read more than written (same for docs)
- Write The Docs: Documentation best practices

---

## Issue #16: Security Hardening and Final Polish

### Description
Security review, add input validation, sanitize outputs, secure credential storage, and final code quality improvements.

### Context
Before release, ensure the application is secure, especially around OAuth credentials and API access.

### Acceptance Criteria
- [ ] Security audit:
  - Credentials stored securely (encrypted if possible)
  - No credentials in logs or error messages
  - Input validation on all API endpoints
  - CSRF protection for web forms if applicable
  - Rate limiting on API endpoints
- [ ] Add input sanitization:
  - Validate email addresses
  - Sanitize file paths
  - Validate JSON payloads
- [ ] Review and update `.env.example` with security notes
- [ ] Add `SECURITY.md` with security policy and responsible disclosure
- [ ] Final ruff cleanup: `ruff check --fix`
- [ ] Final type checking: `mypy src/ --strict` (100% pass)
- [ ] Run security tools: `bandit -r src/` (Python security linter)
- [ ] Update dependencies to latest secure versions
- [ ] All tests pass with ≥90% coverage

### Technical Details
- Use `cryptography` library for encrypting OAuth tokens at rest
- Add rate limiting using Flask-Limiter (optional)
- Input validation: use Pydantic or custom validators
- Sanitize error messages (don't leak sensitive info)
- Run bandit for security vulnerabilities
- Check for common issues: SQL injection (N/A), XSS (N/A), credential leakage

### Testing Requirements
- Run security scanners: `bandit -r src/`
- Verify no credentials in logs (check logging calls)
- Test input validation with malicious inputs
- Run full test suite: `pytest --cov=src --cov-report=term-missing`
- Verify coverage ≥90%

### Files to Create/Update
- `SECURITY.md`
- `.env.example` (add security notes)
- Update code for security improvements

### References
- OWASP Top 10
- Python security best practices
- OAuth security considerations

---

# Implementation Order

Implement issues in sequential order (1 → 16):

1. ✅ Issue #1: Project Foundation
2. ✅ Issue #2: Project Structure
3. ✅ Issue #3: OAuth Authentication (TDD)
4. ✅ Issue #4: API Client (TDD)
5. ✅ Issue #5: Compare Service (TDD)
6. ✅ Issue #6: Transfer Manager (TDD)
7. ✅ Issue #7: Sync Service (TDD)
8. ✅ Issue #8: Flask API Foundation
9. ✅ Issue #9: Flask API Endpoints
10. ✅ Issue #10: Streamlit UI Foundation
11. ✅ Issue #11: Streamlit Sync View
12. ✅ Issue #12: Streamlit Compare View
13. ✅ Issue #13: E2E Tests
14. ✅ Issue #14: CI/CD
15. ✅ Issue #15: Documentation
16. ✅ Issue #16: Security & Polish

Each issue builds on previous work. Do not skip ahead.

---

# Notes for AI Agent (Claude Sonnet 4.5)

## General Guidelines
- **Always start with RED tests** (failing tests first)
- **Then write GREEN code** (minimal code to pass tests)
- **Then REFACTOR** (clean up, optimize, improve)
- Use ruff for linting: `ruff check . --fix`
- Use mypy for type checking: `mypy src/ --strict`
- Target 90% test coverage minimum
- Follow PEP 8, PEP 257 (docstrings), PEP 484 (type hints)
- Clean Code principles: KISS, SRP, DRY
- Use dependency injection (don't hard-code dependencies)
- All docstrings use Google or NumPy style
- No useless comments (code should be self-documenting)
- Meaningful variable names (no single-letter vars except loop counters)

## Testing Guidelines
- Use `pytest` for all tests
- Use `pytest-mock` or `unittest.mock` for mocking
- Use `pytest-cov` for coverage reports
- Mock external APIs (never make real API calls in tests)
- Test happy paths AND error cases
- Test edge cases (empty inputs, large inputs, invalid inputs)
- Tests should be fast (<1s each typically)
- Tests should be deterministic (no flaky tests)

## Code Style
- Line length: 88 characters (Black standard)
- Use type hints everywhere
- Use dataclasses or Pydantic for data models
- Prefer composition over inheritance
- Keep functions small (<20 lines ideally)
- One function does one thing
- Use descriptive names: `calculate_total_photos()` not `calc()`

## Common Patterns
- **Config**: Load from environment variables using `python-dotenv`
- **Logging**: Use Python's `logging` module, structured logs
- **Error handling**: Catch specific exceptions, provide helpful messages
- **API responses**: Consistent JSON format with `success`, `data`, `error` fields
- **Async**: Use if needed for long operations, but keep simple initially

## When Stuck
- Re-read the issue description carefully
- Check existing code in the repository
- Look at test examples from previous issues
- Follow the TDD cycle: RED → GREEN → REFACTOR
- Ask clarifying questions if requirements are unclear

## Success Criteria
Each issue is complete when:
- All tests pass (`pytest`)
- Coverage ≥90% (`pytest --cov --cov-report=term-missing`)
- Linting passes (`ruff check .`)
- Type checking passes (`mypy src/ --strict`)
- Code follows PEP standards and Clean Code principles
- Documentation is clear and complete
