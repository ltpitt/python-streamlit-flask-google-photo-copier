# GitHub Copilot Instructions - Google Photos Sync Application

## Project Overview

**Google Photos Sync** is a production-grade Python application that enables monodirectional synchronization of Google Photos from a source account to a target account. The application is built with an API-first architecture using Flask for the backend REST API and Streamlit for a user-friendly GUI.

### Core Mission
Enable non-technical users to safely and effortlessly sync their Google Photos between accounts with zero possibility of mistakes, while maintaining 100% data and metadata integrity.

---

## Architecture & Tech Stack

### Technology Stack
- **Backend API**: Flask 3.1.2 (REST API, API-first design)
- **Frontend GUI**: Streamlit 1.52.2 (user-friendly interface)
- **External API**: Google Photos API (OAuth 2.0, read/write operations)
- **Testing**: pytest, pytest-cov, pytest-mock
- **Code Quality**: ruff (linting & formatting), mypy (type checking)
- **Python Version**: 3.10+ (use modern Python features)

### Architecture Layers

```
┌─────────────────────────────────────────────────────────────┐
│                     Streamlit UI Layer                      │
│              (User Interface & Interactions)                │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Requests
┌────────────────────▼────────────────────────────────────────┐
│                     Flask API Layer                         │
│           (REST Endpoints, Request Validation)              │
└────────────────────┬────────────────────────────────────────┘
                     │ Service Calls
┌────────────────────▼────────────────────────────────────────┐
│                  Core Business Logic                        │
│         (CompareService, SyncService, TransferManager)      │
│              Framework-Agnostic Services                    │
└────────────────────┬────────────────────────────────────────┘
                     │ API Calls
┌────────────────────▼────────────────────────────────────────┐
│              Google Photos Integration                      │
│         (GooglePhotosClient, OAuth, API Wrapper)            │
└─────────────────────────────────────────────────────────────┘
```

### Project Structure

```
src/google_photos_sync/
├── api/                    # Flask API layer (thin controllers)
│   ├── app.py             # Application factory
│   ├── routes.py          # REST endpoints
│   └── middleware.py      # Error handling, logging
├── core/                   # Business logic (framework-agnostic)
│   ├── compare_service.py # Account comparison logic
│   ├── sync_service.py    # Sync orchestration
│   └── transfer_manager.py # Memory-efficient transfers
├── google_photos/          # Google Photos API integration
│   ├── auth.py            # OAuth 2.0 flow
│   ├── client.py          # API client wrapper
│   └── models.py          # Data models (Photo, Album)
├── ui/                     # Streamlit GUI
│   ├── app.py             # Main Streamlit app
│   └── components/        # Reusable UI components
├── utils/                  # Shared utilities
│   ├── logging_config.py  # Structured logging
│   └── validators.py      # Input validation
└── config.py              # Configuration management

tests/
├── unit/                   # Unit tests (isolated, mocked)
├── integration/            # Integration tests (multiple components)
├── e2e/                    # End-to-end tests (full workflows)
└── conftest.py            # Pytest fixtures and configuration
```

---

## Virtual Environment Setup - MANDATORY

**ALWAYS use a virtual environment. Never install packages globally.**

We use **uv** (modern, blazing-fast Python package manager from Astral, the same team behind Ruff) as the primary tool. It's 10-100x faster than pip for installing packages and creating virtual environments.

### Initial Setup

#### 1. Install uv (One-Time Setup)

**Windows (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Alternative (using pip):**
```bash
pip install uv
```

#### 2. Create Virtual Environment

**Using uv (RECOMMENDED - Fast!):**
```bash
# Create virtual environment
uv venv

# Or specify Python version
uv venv --python 3.10
```

**Using standard venv (Fallback):**
```bash
python -m venv .venv
```

#### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1

# If you get execution policy error:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

**Verify activation:**
```bash
# You should see (.venv) in your prompt
which python  # Unix
where python  # Windows
# Should point to .venv/Scripts/python or .venv/bin/python
```

#### 4. Install Dependencies

**Using uv (RECOMMENDED - 10-100x faster!):**
```bash
# Install production dependencies
uv pip install -r requirements.txt

# Install development dependencies
uv pip install -r requirements-dev.txt

# Install both
uv pip install -r requirements.txt -r requirements-dev.txt

# Install package in editable mode
uv pip install -e .
```

**Using standard pip (Fallback):**
```bash
pip install -r requirements.txt -r requirements-dev.txt
pip install -e .
```

### Quick Reference Commands

```bash
# Create venv
uv venv

# Activate (Windows PowerShell)
.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate

# Install dependencies (fast!)
uv pip install -r requirements.txt -r requirements-dev.txt

# Deactivate when done
deactivate
```

### Why uv?

- **Speed**: 10-100x faster than pip (written in Rust)
- **Compatible**: Drop-in replacement for pip (`uv pip install ...`)
- **Modern**: Uses modern Python packaging standards
- **Reliable**: From Astral, the team behind Ruff (our linter)
- **CI/CD Friendly**: Dramatically reduces pipeline run times

### CI/CD Usage

In GitHub Actions, uv can reduce dependency installation from 60-90 seconds to 5-10 seconds:

```yaml
- name: Set up uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh
  
- name: Create venv and install dependencies
  run: |
    uv venv
    source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows
    uv pip install -r requirements.txt -r requirements-dev.txt
```

### Important Rules

1. **Always activate venv** before running any Python commands
2. **Never commit `.venv/` directory** (already in .gitignore)
3. **Use `uv pip` instead of `pip`** for speed (but `pip` works too)
4. **Verify activation** with `which python` or `where python`
5. **Deactivate when switching projects** with `deactivate` command

### Troubleshooting

**Problem**: "python not found" or using wrong Python
- **Solution**: Activate virtual environment first

**Problem**: PowerShell execution policy error
- **Solution**: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Problem**: Packages not found after installation
- **Solution**: Ensure venv is activated (`(.venv)` in prompt)

**Problem**: uv not installed
- **Solution**: Install with `pip install uv` or use installation scripts above

---

## Core Principles & Standards

### 1. Test-Driven Development (TDD) - MANDATORY

**TDD is non-negotiable. Always follow the RED → GREEN → REFACTOR cycle.**

#### RED Phase - Write Failing Tests First
```python
# ALWAYS start here - write the test BEFORE any implementation
def test_sync_preserves_metadata():
    """Test that photo metadata is preserved during sync."""
    # Arrange
    source_photo = create_mock_photo(
        id="123",
        filename="vacation.jpg",
        created_time="2025-01-01T10:00:00Z",
        exif_data={"camera": "Canon"}
    )
    
    # Act
    result = sync_service.sync_photo(source_photo)
    
    # Assert
    assert result.filename == "vacation.jpg"
    assert result.created_time == "2025-01-01T10:00:00Z"
    assert result.exif_data["camera"] == "Canon"
```

#### GREEN Phase - Minimal Implementation
```python
# Write ONLY enough code to make the test pass
class SyncService:
    def sync_photo(self, photo: Photo) -> Photo:
        # Minimal implementation - just enough to pass
        return photo
```

#### REFACTOR Phase - Clean Up
```python
# Now improve the code: extract methods, improve names, optimize
class SyncService:
    def sync_photo(self, photo: Photo) -> Photo:
        """Sync a single photo preserving all metadata.
        
        Args:
            photo: Source photo with metadata
            
        Returns:
            Synced photo with preserved metadata
        """
        validated_photo = self._validate_photo(photo)
        transferred_photo = self._transfer_with_metadata(validated_photo)
        return transferred_photo
```

#### TDD Requirements
- **Never** write implementation code before tests
- Each function/method must have corresponding tests
- Aim for **90% minimum test coverage** (enforced in CI/CD)
- Tests must be deterministic (no flaky tests)
- Mock external dependencies (Google API, filesystem, network)

### 2. SOLID Principles - MANDATORY

#### S - Single Responsibility Principle
Each class/module has ONE reason to change.

```python
# ✅ GOOD - Single responsibility
class GooglePhotosClient:
    """Handles ONLY Google Photos API communication."""
    def list_photos(self) -> List[Photo]: ...
    def download_photo(self, photo_id: str) -> bytes: ...

class SyncService:
    """Handles ONLY sync orchestration logic."""
    def sync_accounts(self, source: str, target: str) -> SyncResult: ...

# ❌ BAD - Multiple responsibilities
class GooglePhotosSyncClient:
    """Does too much - API calls AND sync logic AND UI updates."""
    def list_photos(self): ...
    def sync_accounts(self): ...
    def update_progress_bar(self): ...  # Wrong layer!
```

#### O - Open/Closed Principle
Open for extension, closed for modification.

```python
# ✅ GOOD - Extend via inheritance or composition
class TransferStrategy(ABC):
    @abstractmethod
    def transfer(self, photo: Photo) -> Photo: ...

class StreamingTransferStrategy(TransferStrategy):
    def transfer(self, photo: Photo) -> Photo:
        # Memory-efficient streaming
        ...

class BatchTransferStrategy(TransferStrategy):
    def transfer(self, photo: Photo) -> Photo:
        # Batch processing
        ...
```

#### L - Liskov Substitution Principle
Subtypes must be substitutable for their base types.

```python
# ✅ GOOD - Subclass behaves like base class
class PhotoStorage(ABC):
    def save(self, photo: Photo) -> bool: ...

class GooglePhotosStorage(PhotoStorage):
    def save(self, photo: Photo) -> bool:
        # Implements contract correctly
        return self._upload_to_google(photo)
```

#### I - Interface Segregation Principle
Clients shouldn't depend on interfaces they don't use.

```python
# ✅ GOOD - Focused interfaces
class Readable(Protocol):
    def read(self) -> List[Photo]: ...

class Writable(Protocol):
    def write(self, photo: Photo) -> bool: ...

# Use only what you need
class CompareService:
    def __init__(self, source: Readable, target: Readable):
        # Only needs reading, not writing
        ...

# ❌ BAD - Fat interface
class PhotoRepository(Protocol):
    def read(self) -> List[Photo]: ...
    def write(self, photo: Photo) -> bool: ...
    def delete(self, photo: Photo) -> bool: ...
    def sync(self, other: 'PhotoRepository') -> bool: ...
```

#### D - Dependency Inversion Principle
Depend on abstractions, not concretions. Use dependency injection.

```python
# ✅ GOOD - Dependency injection, depends on abstractions
class SyncService:
    def __init__(
        self,
        compare_service: CompareService,
        transfer_manager: TransferManager,
        logger: Logger
    ):
        self._compare = compare_service
        self._transfer = transfer_manager
        self._logger = logger

# ❌ BAD - Hard-coded dependencies
class SyncService:
    def __init__(self):
        self._compare = CompareService()  # Concrete class!
        self._transfer = TransferManager()  # Can't mock in tests!
```

### 3. PEP Standards - MANDATORY

#### PEP 8 - Style Guide
- **Line length**: 88 characters (Black standard)
- **Naming conventions**:
  - `snake_case` for functions, variables, module names
  - `PascalCase` for classes
  - `UPPER_CASE` for constants
  - `_leading_underscore` for private/internal
- **Imports**: Standard library → Third-party → Local (separated by blank lines)
- **Whitespace**: 2 blank lines between top-level definitions

```python
# ✅ GOOD - PEP 8 compliant
import os
from typing import List

from google.oauth2.credentials import Credentials

from google_photos_sync.core.models import Photo

MAX_CONCURRENT_TRANSFERS = 5  # Constant


class TransferManager:  # PascalCase
    """Manages photo transfers efficiently."""
    
    def transfer_photos(self, photos: List[Photo]) -> List[Photo]:  # snake_case
        """Transfer multiple photos concurrently."""
        max_workers = self._get_max_workers()  # Private method
        return self._execute_transfers(photos, max_workers)
```

#### PEP 257 - Docstring Conventions
- All public modules, classes, functions must have docstrings
- Use Google or NumPy style (be consistent)
- First line: brief summary (one line)
- Followed by detailed description if needed
- Document Args, Returns, Raises

```python
def sync_accounts(
    source_account: str,
    target_account: str,
    dry_run: bool = False
) -> SyncResult:
    """Synchronize photos from source to target account.
    
    Performs monodirectional sync ensuring target becomes identical
    to source. This operation is idempotent and safe to retry.
    
    Args:
        source_account: Email of source Google Photos account
        target_account: Email of target Google Photos account
        dry_run: If True, only preview changes without executing
        
    Returns:
        SyncResult containing statistics and status of the operation
        
    Raises:
        AuthenticationError: If OAuth credentials are invalid
        SyncError: If sync operation fails
        
    Example:
        >>> result = sync_accounts("user@gmail.com", "backup@gmail.com")
        >>> print(f"Synced {result.photos_transferred} photos")
    """
    ...
```

#### PEP 484 - Type Hints
- **Use type hints everywhere** (enforced by mypy --strict)
- Use modern syntax: `list[str]` instead of `List[str]` (Python 3.10+)
- Use `typing` module for complex types

```python
from typing import Optional, Protocol
from collections.abc import Callable

# ✅ GOOD - Complete type hints
def process_photos(
    photos: list[Photo],
    filter_fn: Optional[Callable[[Photo], bool]] = None,
    max_count: int = 100
) -> list[Photo]:
    """Process photos with optional filtering."""
    ...

class PhotoClient(Protocol):
    """Protocol for photo client implementations."""
    def fetch(self, photo_id: str) -> Optional[Photo]: ...
```

### 4. Clean Code Principles - MANDATORY

#### Meaningful Names
```python
# ✅ GOOD - Clear, descriptive names
def calculate_sync_statistics(
    source_photos: list[Photo],
    target_photos: list[Photo]
) -> SyncStatistics:
    photos_to_add = _find_missing_photos(source_photos, target_photos)
    photos_to_delete = _find_extra_photos(source_photos, target_photos)
    return SyncStatistics(to_add=len(photos_to_add), to_delete=len(photos_to_delete))

# ❌ BAD - Unclear names
def calc(s: list, t: list) -> dict:
    a = _fmp(s, t)
    d = _fep(s, t)
    return {"a": len(a), "d": len(d)}
```

#### Small Functions
- Functions should do ONE thing
- Ideal length: < 20 lines
- If it needs "and" in the name, it's doing too much

```python
# ✅ GOOD - Small, focused functions
def sync_photo(self, photo: Photo) -> Photo:
    """Sync a single photo from source to target."""
    validated_photo = self._validate_photo(photo)
    downloaded_data = self._download_photo_data(validated_photo)
    uploaded_photo = self._upload_photo_data(downloaded_data)
    return uploaded_photo

# Each helper does one thing
def _validate_photo(self, photo: Photo) -> Photo: ...
def _download_photo_data(self, photo: Photo) -> bytes: ...
def _upload_photo_data(self, data: bytes) -> Photo: ...
```

#### No Useless Comments
Code should be self-documenting. Only comment WHY, not WHAT.

```python
# ✅ GOOD - Comment explains WHY
def _calculate_chunk_size(self, file_size: int) -> int:
    # Use larger chunks for bigger files to reduce API calls
    # while staying under 32MB limit to prevent memory issues
    if file_size > 100_000_000:  # 100MB
        return 32_000_000  # 32MB chunks
    return 8_000_000  # 8MB chunks for smaller files

# ❌ BAD - Comment repeats the code
def _calculate_chunk_size(self, file_size: int) -> int:
    # Check if file size is greater than 100 million
    if file_size > 100_000_000:
        # Return 32 million
        return 32_000_000
    # Return 8 million
    return 8_000_000
```

#### DRY (Don't Repeat Yourself)
```python
# ✅ GOOD - Extract common logic
def _make_api_request(
    self,
    endpoint: str,
    method: str = "GET",
    **kwargs
) -> dict:
    """Shared API request logic with retry and error handling."""
    for attempt in range(self.max_retries):
        try:
            response = self._execute_request(endpoint, method, **kwargs)
            return response.json()
        except APIError as e:
            if attempt == self.max_retries - 1:
                raise
            self._handle_retry(e, attempt)

# ❌ BAD - Repeated logic
def get_photos(self):
    for attempt in range(3):
        try:
            response = requests.get(...)
            return response.json()
        except: ...

def upload_photo(self, photo):
    for attempt in range(3):  # Same retry logic repeated!
        try:
            response = requests.post(...)
            return response.json()
        except: ...
```

### 5. KISS Principle - Keep It Simple, Stupid

**Simple solutions are better than clever ones.**

```python
# ✅ GOOD - Simple and clear
def is_photo_synced(source_photo: Photo, target_photo: Photo) -> bool:
    """Check if photos are identical by comparing key attributes."""
    return (
        source_photo.id == target_photo.id
        and source_photo.filename == target_photo.filename
        and source_photo.created_time == target_photo.created_time
    )

# ❌ BAD - Unnecessarily complex
def is_photo_synced(source_photo: Photo, target_photo: Photo) -> bool:
    """Check if photos are identical."""
    attrs = ['id', 'filename', 'created_time']
    return all(
        getattr(source_photo, attr) == getattr(target_photo, attr)
        for attr in attrs
    )  # Harder to read, debug, and maintain
```

---

## Code Quality Tools

### Ruff - Linting & Formatting
```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

**Configuration** (in `pyproject.toml`):
```toml
[tool.ruff]
line-length = 88
target-version = "py310"
select = [
    "E",   # pycodestyle errors
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "W",   # pycodestyle warnings
    "B",   # flake8-bugbear
    "C90", # mccabe complexity
]

[tool.ruff.per-file-ignores]
"tests/**/*.py" = ["S101"]  # Allow assert in tests
```

### Mypy - Type Checking
```bash
# Strict type checking
mypy src/ --strict
```

**Configuration** (in `pyproject.toml`):
```toml
[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### Pytest - Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_sync_service.py

# Run with verbose output
pytest -v

# Fail if coverage below 90%
pytest --cov=src --cov-fail-under=90
```

---

## Project-Specific Requirements

### 1. Memory Efficiency - CRITICAL

**Never load entire photo files into memory.** Use streaming.

```python
# ✅ GOOD - Streaming transfer
def transfer_photo(self, photo: Photo) -> Photo:
    """Transfer photo using streaming to minimize memory usage."""
    with self.source_client.download_stream(photo.id) as source_stream:
        uploaded_photo = self.target_client.upload_stream(
            source_stream,
            metadata=photo.metadata,
            chunk_size=8_000_000  # 8MB chunks
        )
    return uploaded_photo

# ❌ BAD - Loads entire file in memory
def transfer_photo(self, photo: Photo) -> Photo:
    photo_data = self.source_client.download(photo.id)  # Could be GBs!
    return self.target_client.upload(photo_data, photo.metadata)
```

### 2. Idempotency - CRITICAL

**Sync operations must be safely repeatable.**

```python
# ✅ GOOD - Idempotent sync
def sync_photo(self, photo: Photo) -> SyncResult:
    """Sync photo idempotently - safe to call multiple times."""
    existing = self.target_client.find_by_id(photo.id)
    
    if existing and self._is_identical(photo, existing):
        return SyncResult(status="already_synced", action="skip")
    
    if existing:
        # Update if different
        return self._update_photo(photo, existing)
    
    # Create if doesn't exist
    return self._create_photo(photo)

# ❌ BAD - Not idempotent, will fail or duplicate on retry
def sync_photo(self, photo: Photo) -> SyncResult:
    self.target_client.upload(photo)  # No check if exists!
```

### 3. API Rate Limiting - CRITICAL

**Don't be aggressive with Google API. Respect rate limits.**

```python
# ✅ GOOD - Conservative concurrency and backoff
class TransferManager:
    MAX_CONCURRENT_TRANSFERS = 3  # Conservative (not 100!)
    
    def transfer_photos(self, photos: list[Photo]) -> list[Photo]:
        with ThreadPoolExecutor(max_workers=self.MAX_CONCURRENT_TRANSFERS) as executor:
            futures = [executor.submit(self._transfer_with_retry, p) for p in photos]
            return [f.result() for f in as_completed(futures)]
    
    def _transfer_with_retry(self, photo: Photo) -> Photo:
        for attempt in range(3):
            try:
                return self._transfer_photo(photo)
            except RateLimitError as e:
                # Exponential backoff: 1s, 2s, 4s
                wait_time = 2 ** attempt
                logger.warning(f"Rate limited, waiting {wait_time}s")
                time.sleep(wait_time)
        raise TransferError(f"Failed after 3 retries: {photo.id}")
```

### 4. User Safety - CRITICAL

**Prevent user mistakes with clear warnings and confirmations.**

```python
# ✅ GOOD - Multiple safeguards in UI
def display_sync_confirmation(source: str, target: str, stats: SyncStats):
    """Display clear warning before destructive sync operation."""
    st.error("⚠️ DESTRUCTIVE OPERATION WARNING")
    st.warning(f"""
    **Target account ({target}) will be MODIFIED** to exactly match 
    source account ({source}).
    
    This includes:
    - Adding {stats.photos_to_add} photos to target
    - DELETING {stats.photos_to_delete} photos from target
    
    **This cannot be undone.**
    """)
    
    # Confirmation checkbox
    confirm_checkbox = st.checkbox(
        f"I understand that {target} will be permanently modified"
    )
    
    # Type account name to confirm
    typed_account = st.text_input(
        f"Type target account name '{target}' to confirm:"
    )
    
    # Only enable button if both confirmations
    if confirm_checkbox and typed_account == target:
        if st.button("🔴 EXECUTE SYNC (Irreversible)"):
            execute_sync()
    else:
        st.button("Execute Sync", disabled=True)
```

### 5. Metadata Preservation - CRITICAL

**All photo metadata must be preserved exactly.**

```python
# ✅ GOOD - Complete metadata preservation
@dataclass
class Photo:
    """Photo with complete metadata."""
    id: str
    filename: str
    created_time: str
    media_type: str  # image/jpeg, video/mp4
    mime_type: str
    file_size: int
    width: int
    height: int
    
    # EXIF data
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    focal_length: Optional[str] = None
    aperture: Optional[str] = None
    iso: Optional[int] = None
    
    # Location
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_name: Optional[str] = None
    
    # Google Photos specific
    description: Optional[str] = None
    is_favorite: bool = False
    
def preserve_all_metadata(self, source: Photo, target: Photo) -> Photo:
    """Ensure ALL metadata is copied from source to target."""
    # Don't just copy some fields - copy ALL metadata
    return dataclasses.replace(
        target,
        **{
            field.name: getattr(source, field.name)
            for field in dataclasses.fields(source)
            if field.name != 'id'  # Keep target's ID
        }
    )
```

---

## Testing Standards

### Test Organization

```
tests/
├── unit/                       # Fast, isolated tests
│   ├── test_sync_service.py   # Test business logic
│   ├── test_compare_service.py
│   └── test_transfer_manager.py
├── integration/                # Multiple components
│   ├── test_api_routes.py     # Test Flask endpoints
│   └── test_oauth_flow.py
└── e2e/                        # Full workflows
    └── test_sync_workflow.py  # End-to-end scenarios
```

### Test Naming Convention

```python
# Pattern: test_<function>_<scenario>_<expected_result>

def test_sync_photo_when_not_exists_creates_new():
    """Test sync creates photo when it doesn't exist on target."""
    ...

def test_sync_photo_when_exists_and_identical_skips():
    """Test sync skips photo when already synced."""
    ...

def test_sync_photo_when_rate_limited_retries_with_backoff():
    """Test sync retries with exponential backoff on rate limit."""
    ...
```

### Testing Best Practices

```python
# ✅ GOOD - Well-structured test
def test_compare_accounts_identifies_missing_photos():
    """Test compare correctly identifies photos missing on target."""
    # Arrange - Set up test data
    source_photos = [
        create_photo(id="1", filename="photo1.jpg"),
        create_photo(id="2", filename="photo2.jpg"),
    ]
    target_photos = [
        create_photo(id="1", filename="photo1.jpg"),
    ]
    mock_source_client = Mock(spec=GooglePhotosClient)
    mock_source_client.list_photos.return_value = source_photos
    mock_target_client = Mock(spec=GooglePhotosClient)
    mock_target_client.list_photos.return_value = target_photos
    
    compare_service = CompareService(
        source_client=mock_source_client,
        target_client=mock_target_client
    )
    
    # Act - Execute the test
    result = compare_service.compare_accounts()
    
    # Assert - Verify expectations
    assert len(result.missing_on_target) == 1
    assert result.missing_on_target[0].id == "2"
    assert result.missing_on_target[0].filename == "photo2.jpg"
```

### Fixtures and Mocking

```python
# tests/conftest.py - Shared fixtures
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_google_client():
    """Mock Google Photos client for testing."""
    client = Mock(spec=GooglePhotosClient)
    client.list_photos.return_value = []
    client.download_photo.return_value = b"fake_photo_data"
    return client

@pytest.fixture
def sample_photo():
    """Sample photo for testing."""
    return Photo(
        id="test-123",
        filename="test.jpg",
        created_time="2025-01-01T10:00:00Z",
        media_type="image/jpeg",
        file_size=1024000,
        width=1920,
        height=1080
    )

# Use in tests
def test_something(mock_google_client, sample_photo):
    service = SyncService(client=mock_google_client)
    result = service.sync_photo(sample_photo)
    assert result.id == "test-123"
```

---

## Error Handling

### Custom Exceptions

```python
# src/google_photos_sync/exceptions.py

class GooglePhotosSyncError(Exception):
    """Base exception for all sync errors."""
    pass

class AuthenticationError(GooglePhotosSyncError):
    """OAuth authentication failed."""
    pass

class RateLimitError(GooglePhotosSyncError):
    """Google API rate limit exceeded."""
    pass

class TransferError(GooglePhotosSyncError):
    """Photo transfer failed."""
    pass

class SyncError(GooglePhotosSyncError):
    """Sync operation failed."""
    pass
```

### Error Handling Pattern

```python
# ✅ GOOD - Specific exception handling
def sync_photo(self, photo: Photo) -> Photo:
    """Sync photo with proper error handling."""
    try:
        return self._execute_sync(photo)
    except RateLimitError as e:
        logger.warning(f"Rate limited for photo {photo.id}, will retry")
        raise  # Re-raise for retry logic
    except AuthenticationError as e:
        logger.error(f"Auth failed for photo {photo.id}: {e}")
        raise  # Fatal error, don't retry
    except TransferError as e:
        logger.error(f"Transfer failed for photo {photo.id}: {e}")
        raise SyncError(f"Failed to sync photo {photo.id}") from e
    except Exception as e:
        logger.exception(f"Unexpected error syncing photo {photo.id}")
        raise SyncError(f"Unexpected error: {e}") from e

# ❌ BAD - Bare except
def sync_photo(self, photo: Photo) -> Photo:
    try:
        return self._execute_sync(photo)
    except:  # Too broad! Catches everything including KeyboardInterrupt
        print("Error")  # Useless error message
        return None  # Wrong return type!
```

---

## Logging Standards

### Structured Logging

```python
# src/google_photos_sync/utils/logging_config.py

import logging
import sys

def setup_logging(level: str = "INFO") -> None:
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("google_photos_sync.log")
        ]
    )

# Use in code
logger = logging.getLogger(__name__)

def sync_accounts(self, source: str, target: str) -> SyncResult:
    logger.info(f"Starting sync from {source} to {target}")
    
    try:
        result = self._execute_sync(source, target)
        logger.info(
            f"Sync completed: {result.photos_transferred} photos, "
            f"{result.photos_deleted} deleted"
        )
        return result
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise
```

---

## Configuration Management

```python
# src/google_photos_sync/config.py

import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()  # Load .env file

@dataclass
class Config:
    """Application configuration."""
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "")
    
    # Transfer settings
    MAX_CONCURRENT_TRANSFERS: int = int(os.getenv("MAX_CONCURRENT_TRANSFERS", "3"))
    CHUNK_SIZE_MB: int = int(os.getenv("CHUNK_SIZE_MB", "8"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))
    
    # Flask
    FLASK_ENV: str = os.getenv("FLASK_ENV", "development")
    FLASK_SECRET_KEY: str = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    def validate(self) -> None:
        """Validate required configuration."""
        if not self.GOOGLE_CLIENT_ID:
            raise ValueError("GOOGLE_CLIENT_ID is required")
        if not self.GOOGLE_CLIENT_SECRET:
            raise ValueError("GOOGLE_CLIENT_SECRET is required")

# Usage
config = Config()
config.validate()
```

---

## Common Patterns & Anti-Patterns

### ✅ DO THIS

```python
# Use dependency injection
class SyncService:
    def __init__(self, client: GooglePhotosClient, logger: Logger):
        self._client = client
        self._logger = logger

# Use type hints
def process(data: list[Photo]) -> SyncResult: ...

# Use descriptive variable names
photos_to_transfer = compare_result.missing_on_target

# Use early returns to reduce nesting
def validate_photo(photo: Photo) -> bool:
    if not photo.id:
        return False
    if not photo.filename:
        return False
    return True

# Use context managers for resources
with open(file_path, 'rb') as f:
    data = f.read()

# Use dataclasses for data structures
@dataclass
class SyncResult:
    photos_transferred: int
    photos_deleted: int
    elapsed_time: float
```

### ❌ DON'T DO THIS

```python
# Don't use global state
global_client = GooglePhotosClient()  # Bad!

# Don't ignore type hints
def process(data):  # Missing type hints
    return None  # Missing return type

# Don't use cryptic names
pt = cr.mot  # What is this?!

# Don't use deep nesting
def validate(photo):
    if photo:
        if photo.id:
            if photo.filename:
                if len(photo.filename) > 0:
                    return True  # Too deep!
    return False

# Don't forget to close resources
f = open(file_path)
data = f.read()
# f never closed!

# Don't use plain dicts for structured data
result = {"transferred": 10, "deleted": 5}  # Use dataclass!
```

---

## Development Workflow

### 1. Before Starting Any Feature

```bash
# Create and activate virtual environment (if not already done)
uv venv
source .venv/bin/activate  # macOS/Linux
# OR
.venv\Scripts\Activate.ps1  # Windows PowerShell

# Install dependencies (fast with uv!)
uv pip install -r requirements.txt -r requirements-dev.txt

# Create feature branch
git checkout -b feature/issue-N-description

# Verify tests pass
pytest
```

### 2. TDD Cycle for Each Feature

```bash
# 1. RED - Write failing test
# Edit: tests/unit/test_my_feature.py
pytest tests/unit/test_my_feature.py  # Should FAIL

# 2. GREEN - Write minimal implementation
# Edit: src/google_photos_sync/my_feature.py
pytest tests/unit/test_my_feature.py  # Should PASS

# 3. REFACTOR - Clean up code
ruff check . --fix
ruff format .
mypy src/ --strict

# Verify still passes
pytest tests/unit/test_my_feature.py
```

### 3. Before Committing

```bash
# Run all checks
make lint      # or: ruff check .
make format    # or: ruff format .
make typecheck # or: mypy src/ --strict
make test      # or: pytest --cov=src --cov-fail-under=90

# If all pass, commit
git add .
git commit -m "feat: implement feature X following TDD"
```

### 4. PR Checklist

- [ ] All tests pass (90%+ coverage)
- [ ] Ruff linting passes (zero errors)
- [ ] Mypy type checking passes (strict mode)
- [ ] Code follows TDD (tests written first)
- [ ] Code follows SOLID principles
- [ ] Code follows PEP standards
- [ ] Clean code principles applied
- [ ] Docstrings for all public APIs
- [ ] No useless comments
- [ ] Updated documentation if needed

---

## Key Reminders

### When Writing Code
1. **Test first** - Always RED → GREEN → REFACTOR
2. **Type everything** - Use type hints on all functions
3. **Inject dependencies** - Don't hard-code or use globals
4. **Keep it simple** - KISS over clever
5. **Single responsibility** - One class/function does one thing
6. **Stream don't load** - Memory efficiency for photos
7. **Be conservative** - Don't hammer Google APIs
8. **Idempotent operations** - Safe to retry
9. **User safety first** - Clear warnings, confirmations
10. **Preserve metadata** - 100% metadata integrity

### When Reviewing Code
1. Are there tests? Do they pass?
2. Is coverage ≥90%?
3. Does it follow TDD?
4. Are SOLID principles followed?
5. Is it PEP compliant?
6. Is it clean code (small functions, clear names)?
7. Are there type hints everywhere?
8. Is it simple (KISS)?
9. Is it memory-efficient?
10. Is it safe for users?

### Red Flags
- ❌ Implementation before tests
- ❌ Type hints missing
- ❌ Hard-coded dependencies
- ❌ Global state or singletons
- ❌ Loading entire files in memory
- ❌ Aggressive API usage (>5 concurrent)
- ❌ No idempotency checks
- ❌ Missing user confirmations for destructive ops
- ❌ Metadata not fully preserved
- ❌ Coverage <90%

---

## Resources & References

### Python Standards
- [PEP 8 - Style Guide](https://peps.python.org/pep-0008/)
- [PEP 257 - Docstring Conventions](https://peps.python.org/pep-0257/)
- [PEP 484 - Type Hints](https://peps.python.org/pep-0484/)

### Principles
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [Test-Driven Development](https://en.wikipedia.org/wiki/Test-driven_development)

### Tools
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Mypy Documentation](https://mypy.readthedocs.io/)
- [Pytest Documentation](https://docs.pytest.org/)

### APIs
- [Google Photos API](https://developers.google.com/photos)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

---

**Remember: This is a production application for real users. Quality, safety, and user experience are paramount. When in doubt, choose simplicity, safety, and clarity over complexity or cleverness.**
