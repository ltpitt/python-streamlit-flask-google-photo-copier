# GitHub Issues Creation Guide

This guide explains how to create GitHub issues #2-#16 from the GITHUB_ISSUES.md file.

## Issue #1 Status
✅ Issue #1 has already been created and implemented (closed).

## Issues to Create
We need to create issues #2 through #16 (15 issues total).

## Method 1: Automated Creation Using GitHub CLI (Recommended)

### Prerequisites
1. Install GitHub CLI: https://cli.github.com/
2. Authenticate: `gh auth login`

### Steps
```bash
# From the repository root directory
python3 create_github_issues.py
```

This will automatically create all 15 issues with proper formatting.

## Method 2: Manual Creation via GitHub Web UI

If you prefer manual creation or the script doesn't work, follow these steps for each issue:

### General Steps
1. Go to: https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/issues/new
2. Copy the title from below (including the "Issue #N:" prefix)
3. Copy the entire body content
4. Click "Submit new issue"

### Issues to Create

---

## Issue #2

**Title:** `Issue #2: Project Structure - Create Source and Test Directory Hierarchy`

**Body:**
```markdown
## Description
Create the complete directory structure for the application following Python packaging best practices with clear separation between API, core logic, Google Photos integration, and UI layers.

## Context
We're building an API-first application with Flask backend and Streamlit frontend. The structure must support TDD with clear test organization.

## Acceptance Criteria
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

## Technical Details
- Use `src/` layout (PEP recommends this for distributable packages)
- Package name: `google_photos_sync` (underscores, not hyphens per PEP 8)
- Each `__init__.py` should contain a one-line docstring describing the module's purpose
- Test directory structure mirrors source structure for clarity

## Testing Requirements
- Verify package is importable: `python -c "import google_photos_sync"`
- Verify pytest discovers test directories: `pytest --collect-only`

## Files to Create
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

## References
- PEP 8 (package naming)
- Python Packaging Guide (src layout)
```

---

## Issue #3

**Title:** `Issue #3: TDD - Google Photos OAuth Authentication Module`

**Body:**
```markdown
## Description
Implement OAuth 2.0 authentication for Google Photos API following TDD. Write failing tests first, then implement the authentication flow with credential storage and refresh token handling.

## Context
We need to authenticate with Google Photos API for both source (read-only) and target (append-only) accounts. Must handle OAuth flow, token storage, and automatic refresh.

## Acceptance Criteria
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

## Technical Details
- Use `google.oauth2.credentials` and `google_auth_oauthlib.flow`
- Required scopes: 
  - Source account: `https://www.googleapis.com/auth/photoslibrary.readonly`
  - Target account: `https://www.googleapis.com/auth/photoslibrary.appendonly`
- Store credentials securely (encrypt tokens if possible)
- Handle credential refresh automatically using refresh tokens
- Support multiple accounts (source and target) simultaneously

## Testing Requirements
- Mock Google OAuth endpoints (don't make real API calls in tests)
- Test token expiry and refresh logic
- Test error handling (invalid auth code, network errors, expired refresh token)
- Use pytest fixtures for common test data (mock credentials, config)
- Run with coverage: `pytest tests/unit/test_google_photos_auth.py --cov=src/google_photos_sync/google_photos/auth --cov-report=term-missing`

## Files to Create
- `tests/unit/test_google_photos_auth.py` (RED phase - write first)
- `src/google_photos_sync/google_photos/auth.py` (GREEN phase - implement after tests)

## References
- Google Photos API Authentication: https://developers.google.com/photos/library/guides/authentication-authorization
- Clean Code: Single Responsibility Principle (auth module does only authentication)
- KISS: Keep the OAuth flow simple and understandable
```

---

*Continue for Issues #4-#16...*

## Quick Reference: All Issue Titles

For quick navigation, here are all the titles:

2. Issue #2: Project Structure - Create Source and Test Directory Hierarchy
3. Issue #3: TDD - Google Photos OAuth Authentication Module
4. Issue #4: TDD - Google Photos API Client Wrapper
5. Issue #5: TDD - Compare Service for Account Comparison
6. Issue #6: TDD - Memory-Efficient Transfer Manager
7. Issue #7: TDD - Idempotent Sync Service with Monodirectional Sync
8. Issue #8: Flask API - Application Factory and Configuration
9. Issue #9: Flask API - REST Endpoints for Sync and Compare
10. Issue #10: Streamlit UI - Foundation and Layout
11. Issue #11: Streamlit UI - Sync View with Safety Warnings
12. Issue #12: Streamlit UI - Compare View
13. Issue #13: Integration Tests - End-to-End Workflow
14. Issue #14: CI/CD - GitHub Actions Workflow
15. Issue #15: Documentation - README, Architecture, and User Guide
16. Issue #16: Security Hardening and Final Polish

## Notes

- Ensure the issue number is in the title (e.g., "Issue #2: ...")
- This maintains the sequential implementation order
- Each issue builds upon previous ones
- Issue #1 is already complete

## Full Issue Content

For the complete content of each issue (body text), refer to the GITHUB_ISSUES.md file starting at line 64 for Issue #2.
