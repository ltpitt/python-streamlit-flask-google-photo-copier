# Google Photos Sync

[![CI](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/actions/workflows/ci.yml/badge.svg)](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

A production-grade Python application for safe, monodirectional synchronization of Google Photos between accounts. Built with an API-first architecture featuring a Flask REST API backend and Streamlit UI frontend.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Security](#security)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Running Tests](#running-tests)
- [Development](#development)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Overview

**Google Photos Sync** enables you to create exact backups of your Google Photos library by synchronizing from a source account to a target account. The application ensures 100% data integrity, preserving all metadata including EXIF data, GPS coordinates, and timestamps.

### Key Highlights

- 🔒 **Safe by Design**: Multiple confirmation steps before any destructive operations
- 👁️ **Preview First**: Compare accounts to see exactly what will change
- 🔄 **Idempotent**: Safe to run multiple times - won't create duplicates
- 📊 **100% Metadata Preservation**: All photo information is preserved exactly
- 💾 **Memory Efficient**: Streams photos in chunks (never loads entire files in memory)
- ⚡ **Fast & Modern**: Uses uv for 10-100x faster dependency management

## Features

### Architecture & Quality
- **API-First Architecture**: Clean separation between Flask backend and Streamlit frontend
- **100% Type Safety**: Full mypy strict type checking
- **Test-Driven Development**: 90%+ test coverage with comprehensive test suite
- **SOLID Principles**: Clean architecture with dependency injection
- **Production Ready**: Following PEP 8, PEP 257, and PEP 484 standards

### User Experience
- **Non-Technical Friendly**: Simple UI designed for users with zero technical knowledge
- **Real-Time Progress**: Live updates during sync operations
- **Detailed Reporting**: Complete statistics and action logs
- **Dry-Run Mode**: Preview changes without executing them

### Technical Excellence
- **Memory Efficient**: Streaming transfers (8MB chunks) for photos of any size
- **Conservative API Usage**: Respects Google rate limits (max 3 concurrent transfers)
- **Comprehensive Logging**: Structured logging for debugging and monitoring
- **Error Recovery**: Automatic retry with exponential backoff

## 🔒 Security

Google Photos Sync implements multiple layers of security to protect your data and credentials:

### Credential Protection
- **OAuth 2.0 Authentication**: Industry-standard secure authentication
- **Encrypted Token Storage**: Credentials encrypted at rest using Fernet (AES-128-CBC + HMAC)
- **Scoped Permissions**: 
  - Source account: Read-only access (`photoslibrary.readonly`)
  - Target account: Append-only access (`photoslibrary.appendonly`)
- **No Password Storage**: Uses OAuth tokens, never stores passwords

### Input Validation & Sanitization
- **Email Validation**: All email addresses validated using Pydantic
- **Path Sanitization**: File paths sanitized to prevent directory traversal attacks
- **JSON Validation**: All API payloads validated for required fields and structure
- **Type Safety**: Full mypy strict type checking prevents type-related vulnerabilities

### API Security
- **Rate Limiting**: API endpoints rate-limited to prevent abuse (60 requests/minute)
- **CORS Protection**: Cross-origin requests restricted to allowed origins
- **Request Timeouts**: All HTTP requests have timeouts to prevent hanging connections
- **CSRF Protection**: State parameter in OAuth flow prevents CSRF attacks

### Data Protection
- **No Credential Logging**: Sensitive data never appears in logs
- **Sanitized Errors**: Error messages don't expose internal details
- **Memory Safe**: Photos streamed, not loaded into memory (prevents memory dumps)
- **Secure Defaults**: Debug mode disabled and secure keys required in production

### Security Auditing
- **Bandit Security Scanner**: All code scanned for common Python security issues
- **Dependency Scanning**: Regular updates and vulnerability checks
- **Security Policy**: See [SECURITY.md](SECURITY.md) for:
  - Supported versions
  - Vulnerability reporting process
  - Production security checklist
  - Best practices

### Production Security Checklist
Before deploying to production, ensure:
- [ ] Set `CREDENTIAL_ENCRYPTION_KEY` to strong random value
- [ ] Set `FLASK_SECRET_KEY` to strong random value
- [ ] Set `FLASK_ENV=production` and `FLASK_DEBUG=false`
- [ ] Enable HTTPS/TLS on production server
- [ ] Restrict credentials directory permissions (`chmod 700`)
- [ ] Configure CORS for production domain only
- [ ] Enable API rate limiting
- [ ] Review and rotate credentials regularly

For complete security documentation, see:
- [SECURITY.md](SECURITY.md) - Security policy and vulnerability reporting
- [docs/user_guide.md](docs/user_guide.md) - OAuth setup and credentials
- [.env.example](.env.example) - Configuration with security notes

## Prerequisites

Before you begin, ensure you have:

### Required
- **Python 3.10+**: [Download Python](https://www.python.org/downloads/)
- **Google Cloud Project**: For OAuth credentials (free)
  - Create at [Google Cloud Console](https://console.cloud.google.com/)
  - Enable Photos Library API
  - Create OAuth 2.0 Desktop credentials
  - See [User Guide](docs/user_guide.md) for detailed setup instructions
- **Two Google Accounts**:
  - Source account (with photos to copy FROM)
  - Target account (to copy photos TO)

### Recommended
- **uv Package Manager**: 10-100x faster than pip
  - Install: `curl -LsSf https://astral.sh/uv/install.sh | sh` (macOS/Linux)
  - Install: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` (Windows)
  - Alternative: `pip install uv`

## Installation

### Quick Install (5 minutes)

1. **Clone the repository**
   ```bash
   git clone https://github.com/ltpitt/python-streamlit-flask-google-photo-copier.git
   cd python-streamlit-flask-google-photo-copier
   ```

2. **Create virtual environment**
   ```bash
   # Using uv (fast!)
   uv venv
   
   # Using standard venv (fallback)
   python -m venv .venv
   ```

3. **Activate virtual environment**
   ```bash
   # macOS/Linux
   source .venv/bin/activate
   
   # Windows PowerShell
   .venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**
   ```bash
   # Using uv (recommended - 10-100x faster!)
   uv pip install -r requirements.txt -r requirements-dev.txt
   uv pip install -e .
   
   # Using pip (fallback)
   pip install -r requirements.txt -r requirements-dev.txt
   pip install -e .
   ```

5. **Verify installation**
   ```bash
   # Run automated verification
   ./verify-setup.sh
   
   # Or manually verify
   python --version    # Should show 3.10+
   ruff --version      # Should show ruff version
   pytest --version    # Should show pytest version
   ```

### Using Makefile (Alternative)

If you prefer using Make:

```bash
# Create virtual environment
make venv

# Activate venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\Activate.ps1  # Windows

# Install dependencies
make install-dev

# Run all checks
make lint
make format
make typecheck
make test
```

## Configuration

### Environment Variables

1. **Copy the example configuration**
   ```bash
   # macOS/Linux
   cp .env.example .env
   
   # Windows
   copy .env.example .env
   ```

2. **Edit `.env` file** with your credentials:
   ```bash
   # Google OAuth Configuration (REQUIRED)
   # Get these from: https://console.cloud.google.com/apis/credentials
   GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   GOOGLE_REDIRECT_URI=http://localhost:8080/oauth2callback
   
   # Transfer Settings (OPTIONAL - defaults work well)
   MAX_CONCURRENT_TRANSFERS=3   # Conservative (prevents rate limits)
   CHUNK_SIZE_MB=8              # Memory-efficient chunk size
   MAX_RETRIES=3                # Retry attempts for failed operations
   
   # Flask Configuration
   FLASK_ENV=development
   FLASK_SECRET_KEY=change_this_in_production
   
   # Logging
   LOG_LEVEL=INFO               # DEBUG for troubleshooting
   LOG_FILE=google_photos_sync.log
   ```

3. **Keep `.env` private**
   - ⚠️ **NEVER** commit `.env` to version control
   - ⚠️ **NEVER** share your credentials
   - Already in `.gitignore` for safety

### Getting Google OAuth Credentials

See the [User Guide](docs/user_guide.md#setting-up-google-cloud-one-time-setup) for step-by-step instructions on:
1. Creating a Google Cloud project
2. Enabling Photos Library API
3. Creating OAuth 2.0 credentials
4. Adding test users

## Quick Start

### 1. Run the Application

You need to run **two servers** in separate terminals:

**Terminal 1 - Flask API (Backend)**:
```bash
# Activate virtual environment first!
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Start Flask API
python -m flask --app src/google_photos_sync/api/app.py run
```

**Terminal 2 - Streamlit UI (Frontend)**:
```bash
# Activate virtual environment first!
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Start Streamlit UI (opens browser automatically)
streamlit run src/google_photos_sync/ui/app.py
```

### 2. Authenticate Your Accounts

1. Open browser to [http://localhost:8501](http://localhost:8501)
2. Click **"Authenticate Source Account"** → Sign in with source Google account
3. Click **"Authenticate Target Account"** → Sign in with target Google account
4. Grant permissions when prompted

### 3. Compare Accounts (Safe Preview)

1. Click **"Compare Accounts"** tab
2. Click **"Compare Accounts"** button
3. Review the differences:
   - Photos missing on target (will be added)
   - Photos extra on target (will be deleted)
   - Photos with different metadata (will be updated)

### 4. Sync Accounts (Makes Changes)

⚠️ **WARNING**: This modifies your target account!

1. Click **"Sync Accounts"** tab
2. Review the warning message carefully
3. Check the confirmation box
4. Type the target account email exactly
5. Click **"🔴 EXECUTE SYNC"**
6. Wait for completion (don't close browser or terminals)

## Usage

### Basic Workflow

```bash
# 1. Start both servers (in separate terminals)
python -m flask --app src/google_photos_sync/api/app.py run
streamlit run src/google_photos_sync/ui/app.py

# 2. Open browser to http://localhost:8501

# 3. Authenticate both accounts

# 4. Compare (safe - read-only)
#    - Review what will change

# 5. Sync (destructive - modifies target)
#    - Only if comparison looks correct
#    - Target becomes identical to source
```

### Advanced Usage

**Dry-Run Mode** (API only):
```python
# Preview sync without making changes
result = sync_service.sync_accounts(
    source_account="source@gmail.com",
    target_account="target@gmail.com",
    dry_run=True  # No actual changes
)
```

**Programmatic Usage**:
```python
from google_photos_sync.core.compare_service import CompareService
from google_photos_sync.core.sync_service import SyncService
from google_photos_sync.google_photos.client import GooglePhotosClient

# Create clients
source_client = GooglePhotosClient(source_credentials)
target_client = GooglePhotosClient(target_credentials)

# Compare accounts
compare_service = CompareService(source_client, target_client)
result = compare_service.compare_accounts("source@gmail.com", "target@gmail.com")

print(f"Missing on target: {len(result.missing_on_target)}")
print(f"Extra on target: {len(result.extra_on_target)}")

# Sync accounts
transfer_manager = TransferManager(source_client, target_client)
sync_service = SyncService(compare_service, transfer_manager)
sync_result = sync_service.sync_accounts("source@gmail.com", "target@gmail.com")

print(f"Photos added: {sync_result.photos_added}")
print(f"Photos deleted: {sync_result.photos_deleted}")
```

## Running Tests

### Quick Test

```bash
# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1

# Run all tests with coverage
pytest

# Or using Make
make test
```

### Test Categories

```bash
# Unit tests only (fast, isolated)
pytest tests/unit/

# Integration tests (multiple components)
pytest tests/integration/

# End-to-end tests (full workflows)
pytest tests/e2e/

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_sync_service.py

# Run specific test function
pytest tests/unit/test_sync_service.py::test_sync_accounts_adds_missing_photos
```

### Coverage Reports

```bash
# Generate coverage report
pytest --cov=src --cov-report=term-missing --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Coverage must be ≥90% (enforced in CI/CD)
pytest --cov=src --cov-fail-under=90
```

### Test with Different Python Versions

```bash
# Test with Python 3.10
python3.10 -m pytest

# Test with Python 3.11
python3.11 -m pytest

# Test with Python 3.12
python3.12 -m pytest
```

## Development

### Project Structure

```
python-streamlit-flask-google-photo-copier/
├── src/google_photos_sync/     # Main application package
│   ├── api/                    # Flask REST API
│   │   ├── app.py             # Application factory
│   │   ├── routes.py          # API endpoints
│   │   └── middleware.py      # Error handling
│   ├── core/                   # Business logic (framework-agnostic)
│   │   ├── compare_service.py # Account comparison
│   │   ├── sync_service.py    # Sync orchestration
│   │   └── transfer_manager.py # Photo transfers
│   ├── google_photos/          # Google Photos integration
│   │   ├── auth.py            # OAuth 2.0 flow
│   │   ├── client.py          # API wrapper
│   │   └── models.py          # Data models
│   ├── ui/                     # Streamlit UI
│   │   ├── app.py             # Main UI app
│   │   └── components/        # UI components
│   ├── utils/                  # Shared utilities
│   └── config.py              # Configuration management
├── tests/                      # Test suite
│   ├── unit/                  # Unit tests (fast, isolated)
│   ├── integration/           # Integration tests
│   ├── e2e/                   # End-to-end tests
│   └── conftest.py            # Pytest fixtures
├── docs/                       # Documentation
│   ├── architecture.md        # System architecture
│   └── user_guide.md          # User guide
├── .env.example               # Environment template
├── pyproject.toml             # Project configuration
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development dependencies
└── Makefile                   # Development automation
```

### Development Workflow

#### 1. Set Up Development Environment

```bash
# Clone and navigate to project
git clone https://github.com/ltpitt/python-streamlit-flask-google-photo-copier.git
cd python-streamlit-flask-google-photo-copier

# Create virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1

# Install dependencies
uv pip install -r requirements.txt -r requirements-dev.txt
uv pip install -e .
```

#### 2. Development Commands

```bash
# Linting
ruff check .                    # Check for issues
ruff check . --fix             # Auto-fix issues

# Formatting
ruff format .                   # Format all code

# Type Checking
mypy src/ --strict             # Strict type checking

# Testing
pytest                         # Run all tests
pytest --cov=src              # With coverage
pytest -v                      # Verbose output
pytest tests/unit/            # Unit tests only

# All checks (before committing)
ruff check . && ruff format . && mypy src/ --strict && pytest
```

#### 3. Git Workflow

```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make changes following TDD:
# 1. Write failing test (RED)
# 2. Write minimal code to pass (GREEN)
# 3. Refactor code (REFACTOR)

# Run all checks
make lint && make format && make typecheck && make test

# Commit changes
git add .
git commit -m "feat: add your feature description"

# Push to GitHub
git push origin feature/your-feature-name

# Create Pull Request on GitHub
```

### Code Quality Standards

#### Test-Driven Development (TDD)

**Always follow RED → GREEN → REFACTOR**:

```python
# 1. RED - Write failing test first
def test_sync_preserves_metadata():
    """Test that photo metadata is preserved during sync."""
    source_photo = create_mock_photo(metadata={"camera": "Canon"})
    result = sync_service.sync_photo(source_photo)
    assert result.metadata["camera"] == "Canon"  # FAILS - not implemented yet

# 2. GREEN - Write minimal code to pass
def sync_photo(self, photo):
    return photo  # Simplest implementation

# 3. REFACTOR - Improve code quality
def sync_photo(self, photo: Photo) -> Photo:
    """Sync photo with metadata preservation."""
    validated = self._validate_photo(photo)
    return self._transfer_with_metadata(validated)
```

#### Code Style

- **Line Length**: 88 characters (Black/Ruff standard)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Type Hints**: Required on all functions (enforced by mypy --strict)
- **Docstrings**: Required for all public functions (Google style)

Example:
```python
def sync_accounts(
    source_account: str,
    target_account: str,
    dry_run: bool = False
) -> SyncResult:
    """Synchronize target account to match source account.
    
    Args:
        source_account: Email of source Google Photos account
        target_account: Email of target Google Photos account
        dry_run: If True, preview changes without executing
        
    Returns:
        SyncResult with statistics and action details
        
    Raises:
        AuthenticationError: If credentials invalid
        SyncError: If sync operation fails
    """
    ...
```

### Tools Reference

| Tool | Purpose | Command |
|------|---------|---------|
| **Ruff** | Linting & formatting | `ruff check .` `ruff format .` |
| **Mypy** | Type checking | `mypy src/ --strict` |
| **Pytest** | Testing | `pytest --cov=src` |
| **uv** | Package management | `uv pip install -r requirements.txt` |

### CI/CD Pipeline

All pull requests automatically run:

1. **Lint**: Ruff checks code style
2. **Type Check**: Mypy validates type hints
3. **Test**: Pytest runs full test suite on Python 3.10, 3.11, 3.12
4. **Coverage**: Must maintain ≥90% coverage

View CI results: [GitHub Actions](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/actions)

## Documentation

### Available Documentation

- **[User Guide](docs/user_guide.md)**: Complete step-by-step guide for end users
  - Google Cloud setup
  - Installation instructions
  - Authentication process
  - How to compare and sync accounts
  - Troubleshooting and FAQ
  
- **[Architecture Documentation](docs/architecture.md)**: Technical architecture details
  - System architecture diagrams
  - Component descriptions
  - Data flow diagrams
  - Technology stack
  - Design decisions and rationale
  
- **[Setup Guide](SETUP.md)**: Detailed development setup
  - Virtual environment setup
  - Dependency installation
  - Development workflow
  - Tool configuration

### API Documentation

The Flask API exposes these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/oauth2callback` | POST | OAuth callback handler |
| `/api/compare` | POST | Compare source and target accounts |
| `/api/sync` | POST | Execute sync operation |

### Code Examples

See `tests/` directory for comprehensive code examples:
- `tests/unit/` - Unit test examples
- `tests/integration/` - Integration test examples
- `tests/e2e/` - End-to-end workflow examples

## Contributing

We welcome contributions! Please follow these guidelines:

### Before Contributing

1. **Read the Documentation**
   - [Architecture Documentation](docs/architecture.md)
   - [Development Workflow](#development-workflow)
   
2. **Check Existing Issues**
   - [GitHub Issues](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/issues)
   - See if your idea/bug is already being discussed

3. **Discuss Major Changes**
   - Open an issue first for major features
   - Get feedback before spending time coding

### Contribution Guidelines

#### Code Standards

1. **Test-Driven Development (TDD)**
   - Write tests **before** implementation (RED → GREEN → REFACTOR)
   - Maintain **90%+ test coverage** (enforced in CI)
   - All tests must pass before merging

2. **Type Safety**
   - Use type hints on **all** functions
   - Pass `mypy src/ --strict` without errors

3. **Code Style**
   - Follow **PEP 8** (style guide)
   - Follow **PEP 257** (docstrings)
   - Follow **PEP 484** (type hints)
   - Use **Ruff** for linting and formatting
   - Line length: **88 characters**

4. **SOLID Principles**
   - Single Responsibility Principle
   - Open/Closed Principle
   - Liskov Substitution Principle
   - Interface Segregation Principle
   - Dependency Inversion Principle

5. **Clean Code**
   - Meaningful names
   - Small functions (<20 lines ideal)
   - No useless comments
   - DRY (Don't Repeat Yourself)
   - KISS (Keep It Simple, Stupid)

#### Pull Request Process

1. **Fork and Clone**
   ```bash
   # Fork on GitHub, then:
   git clone https://github.com/YOUR_USERNAME/python-streamlit-flask-google-photo-copier.git
   cd python-streamlit-flask-google-photo-copier
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/bug-description
   ```

3. **Make Changes**
   - Write tests first (TDD)
   - Implement minimal code to pass tests
   - Refactor for quality
   - Ensure all checks pass:
     ```bash
     ruff check . --fix
     ruff format .
     mypy src/ --strict
     pytest --cov=src --cov-fail-under=90
     ```

4. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add your feature"
   # or
   git commit -m "fix: resolve bug description"
   ```
   
   **Commit Message Format**:
   - `feat:` - New feature
   - `fix:` - Bug fix
   - `docs:` - Documentation changes
   - `test:` - Test updates
   - `refactor:` - Code refactoring
   - `style:` - Code style changes
   - `chore:` - Maintenance tasks

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```
   - Go to GitHub and create Pull Request
   - Fill out the PR template
   - Link related issues

6. **Wait for Review**
   - CI/CD pipeline runs automatically
   - Maintainers will review your code
   - Address any feedback
   - Once approved, your PR will be merged

#### What to Contribute

**Good First Issues**:
- Documentation improvements
- Test coverage improvements
- Bug fixes
- UI enhancements

**Feature Ideas**:
- Album synchronization
- Incremental sync (sync only new photos)
- CLI interface
- Progress persistence (resume interrupted syncs)
- Multi-target sync (one source → multiple targets)

**Not Accepting**:
- Breaking changes to public API (without discussion)
- Features that compromise user safety
- Code that doesn't follow standards
- Contributions without tests

### Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help newcomers learn

## Troubleshooting

### Common Issues

#### Installation Issues

**Problem**: `python: command not found`
- **Solution**: Install Python 3.10+ from [python.org](https://www.python.org/downloads/)
- Ensure "Add Python to PATH" is checked during installation

**Problem**: `uv: command not found`
- **Solution**: Install uv: `pip install uv`
- Or follow install instructions in [Prerequisites](#recommended)

**Problem**: Virtual environment won't activate
- **Windows PowerShell**: Run `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
- Then try activating again

#### Authentication Issues

**Problem**: "This app isn't verified" warning
- **Solution**: Click "Advanced" → "Go to Google Photos Sync (unsafe)"
- This is normal for personal projects

**Problem**: OAuth redirect fails
- **Solution**: Verify `GOOGLE_REDIRECT_URI` in `.env` matches Google Cloud Console
- Should be: `http://localhost:8080/oauth2callback`

#### Runtime Issues

**Problem**: Flask won't start (port 5000 in use)
- **Solution**: Change port in `.env`: `FLASK_PORT=5001`
- Or stop other application using port 5000

**Problem**: "Rate limit exceeded" during sync
- **Solution**: Wait 30 minutes, then try again
- **Prevention**: Reduce `MAX_CONCURRENT_TRANSFERS` in `.env` to `2` or `1`

**Problem**: Sync stalls/hangs
- **Solution**: Check internet connection
- Wait 10-15 minutes (may be rate limiting)
- If still stuck, stop (Ctrl+C) and restart sync (safe - idempotent)

### Getting Help

1. **Check Documentation**
   - [User Guide](docs/user_guide.md) - Detailed troubleshooting section
   - [Architecture Docs](docs/architecture.md) - Technical details

2. **Search Issues**
   - [GitHub Issues](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/issues)
   - Your problem may already be solved

3. **Ask for Help**
   - [Open new issue](https://github.com/ltpitt/python-streamlit-flask-google-photo-copier/issues/new)
   - Include:
     - Operating system
     - Python version
     - Error messages (full text)
     - Steps to reproduce
   - **DO NOT** include your credentials or `.env` file

## License

MIT License

Copyright (c) 2025 Davide Nastri

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

See [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- Built with [Flask](https://flask.palletsprojects.com/) and [Streamlit](https://streamlit.io/)
- Uses [Google Photos API](https://developers.google.com/photos)
- Powered by [uv](https://github.com/astral-sh/uv) for fast dependency management
- Linted and formatted with [Ruff](https://github.com/astral-sh/ruff)

## Project Status

**Version**: 0.1.0  
**Status**: Active Development  
**Python**: 3.10+ required  
**License**: MIT

### Roadmap

- [x] Core sync functionality
- [x] Comparison preview
- [x] User-friendly UI
- [x] Comprehensive documentation
- [ ] Album synchronization (planned)
- [ ] Incremental sync (planned)
- [ ] CLI interface (planned)
- [ ] Progress persistence (planned)

---

**Made with ❤️ for safe Google Photos backups**
