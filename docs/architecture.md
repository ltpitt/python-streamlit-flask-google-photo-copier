# Architecture Documentation

## System Overview

Google Photos Sync is a production-grade Python application that enables safe, monodirectional synchronization of Google Photos between accounts. The application follows an API-first architecture with clear separation between the Flask REST API backend and Streamlit UI frontend.

### Design Philosophy

- **API-First**: Core business logic is framework-agnostic and accessible via REST API
- **Type Safety**: 100% type-checked with mypy in strict mode
- **Test-Driven**: Minimum 90% code coverage with comprehensive test suite
- **SOLID Principles**: Clean architecture with dependency injection
- **User Safety**: Multiple safeguards to prevent user mistakes

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          User Interface Layer                       │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              Streamlit UI (Port 8501)                    │      │
│  │  - Authentication Flow                                    │      │
│  │  - Compare View (read-only preview)                      │      │
│  │  - Sync View (with safety confirmations)                 │      │
│  │  - Status Display & Progress Tracking                    │      │
│  └────────────────────┬─────────────────────────────────────┘      │
│                       │ HTTP Requests                               │
└───────────────────────┼─────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                          API Layer                                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │              Flask REST API (Port 5000)                  │      │
│  │  - /api/auth/oauth2callback - OAuth callback             │      │
│  │  - /api/compare - Account comparison                     │      │
│  │  - /api/sync - Sync execution                            │      │
│  │  - Error handling & validation                           │      │
│  │  - CORS configuration                                    │      │
│  └────────────────────┬─────────────────────────────────────┘      │
│                       │ Service Calls                               │
└───────────────────────┼─────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                    Core Business Logic Layer                         │
│                   (Framework-Agnostic Services)                     │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ CompareService                                              │   │
│  │ - Compare source and target accounts                       │   │
│  │ - Identify missing photos                                  │   │
│  │ - Detect metadata differences                              │   │
│  │ - Find extra photos on target                              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ SyncService                                                 │   │
│  │ - Orchestrate monodirectional sync                         │   │
│  │ - Idempotent operations (safe to retry)                    │   │
│  │ - Add missing photos to target                             │   │
│  │ - Update metadata differences                              │   │
│  │ - Delete extra photos from target                          │   │
│  │ - Progress reporting                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ TransferManager                                             │   │
│  │ - Memory-efficient photo transfers                         │   │
│  │ - Streaming downloads/uploads (8MB chunks)                 │   │
│  │ - Conservative concurrency (max 3)                         │   │
│  │ - Exponential backoff on rate limits                       │   │
│  │ - Retry logic with configurable attempts                   │   │
│  └────────────────────┬────────────────────────────────────────┘   │
│                       │ API Calls                                   │
└───────────────────────┼─────────────────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────────────────┐
│                  Google Photos Integration Layer                    │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ GooglePhotosAuth                                            │   │
│  │ - OAuth 2.0 authorization flow                             │   │
│  │ - Credential management                                    │   │
│  │ - Token refresh                                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ GooglePhotosClient                                          │   │
│  │ - List photos (paginated)                                  │   │
│  │ - Download photo data (streaming)                          │   │
│  │ - Upload photo data (streaming)                            │   │
│  │ - Get photo metadata                                       │   │
│  │ - Rate limit handling                                      │   │
│  └────────────────────┬────────────────────────────────────────┘   │
│                       │ HTTPS Requests                              │
└───────────────────────┼─────────────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Google Photos API    │
            │  (photos.google.com)  │
            └───────────────────────┘
```

## Component Descriptions

### 1. UI Layer - Streamlit Components

**Location**: `src/google_photos_sync/ui/`

#### Main Application (`app.py`)
- Entry point for Streamlit UI
- Navigation between authentication, compare, and sync views
- Session state management
- API client initialization

#### Components
- **AuthComponent**: OAuth 2.0 authentication flow for source and target accounts
- **CompareView**: Read-only comparison preview showing differences
- **SyncView**: Sync execution with multiple safety confirmations
- **ConfirmationDialog**: Safety dialog requiring explicit user confirmation
- **StatusComponent**: Real-time progress and status display

**Responsibilities**:
- User interaction and input validation
- Calling Flask API endpoints
- Displaying results and progress
- User safety warnings and confirmations

### 2. API Layer - Flask REST API

**Location**: `src/google_photos_sync/api/`

#### Application Factory (`app.py`)
- Flask application initialization
- CORS configuration for Streamlit integration
- Configuration loading (development/production/testing)
- Error handler registration

#### Routes (`routes.py`)
- `POST /api/auth/oauth2callback` - OAuth callback handler
- `POST /api/compare` - Compare two accounts (read-only)
- `POST /api/sync` - Execute sync operation
- Request validation and error handling

#### Middleware (`middleware.py`)
- Global error handling
- Request/response logging
- CORS headers
- Rate limiting enforcement

**Responsibilities**:
- HTTP request/response handling
- Input validation and sanitization
- Delegating to core business logic
- Error responses in JSON format

### 3. Core Business Logic Layer

**Location**: `src/google_photos_sync/core/`

#### CompareService (`compare_service.py`)
Compares two Google Photos accounts to identify differences.

**Key Methods**:
- `compare_accounts()` - Main comparison logic
- `_find_metadata_differences()` - Detect metadata mismatches

**Output**: `CompareResult` containing:
- Photos missing on target
- Photos with different metadata
- Extra photos on target
- Statistics

**Design**: 
- Read-only operation (no modifications)
- Efficient O(n) comparison using hash maps
- Compares configurable metadata fields

#### SyncService (`sync_service.py`)
Orchestrates monodirectional sync from source to target.

**Key Methods**:
- `sync_accounts()` - Main sync orchestration
- `_sync_missing_photos()` - Add photos to target
- `_sync_metadata_updates()` - Update metadata
- `_sync_deletions()` - Remove extra photos

**Output**: `SyncResult` containing:
- Number of photos added/deleted/updated
- Failed actions with error messages
- Detailed action log

**Design**:
- Idempotent (safe to run multiple times)
- Progress callback support
- Dry-run mode for previewing changes
- Transactional error handling

#### TransferManager (`transfer_manager.py`)
Efficiently transfers photos between accounts.

**Key Methods**:
- `transfer_photo()` - Transfer single photo with metadata
- `transfer_photos()` - Concurrent batch transfer

**Design**:
- Memory-efficient streaming (8MB chunks)
- Conservative concurrency (max 3 concurrent)
- Exponential backoff on rate limits
- Comprehensive retry logic (max 3 attempts)

**Safety Features**:
- Never loads entire photo in memory
- Respects Google API rate limits
- Graceful degradation on failures

### 4. Google Photos Integration Layer

**Location**: `src/google_photos_sync/google_photos/`

#### GooglePhotosAuth (`auth.py`)
Handles OAuth 2.0 authentication flow.

**Responsibilities**:
- Generate authorization URL
- Exchange auth code for credentials
- Refresh expired tokens
- Secure credential storage

#### GooglePhotosClient (`client.py`)
Wrapper for Google Photos API.

**Key Methods**:
- `list_photos()` - Paginated photo listing
- `download_photo()` - Streaming download
- `upload_photo()` - Streaming upload with metadata
- `get_photo_metadata()` - Retrieve metadata only

**Design**:
- Rate limit detection and backoff
- Automatic pagination handling
- Streaming I/O for memory efficiency
- Comprehensive error handling

#### Models (`models.py`)
Typed data structures for Google Photos entities.

**Classes**:
- `Photo` - Complete photo metadata (EXIF, GPS, Google Photos)
- `Album` - Album information
- All fields type-hinted for mypy validation

## Data Flow Diagrams

### Compare Flow (Read-Only)

```
┌─────────────┐
│   User      │
│  (Streamlit)│
└──────┬──────┘
       │ 1. Request comparison
       ▼
┌──────────────────┐
│  Flask API       │
│  /api/compare    │
└──────┬───────────┘
       │ 2. Invoke service
       ▼
┌──────────────────────────┐
│  CompareService          │
│  - compare_accounts()    │
└──┬────────────────────┬──┘
   │ 3a. List source    │ 3b. List target
   │     photos         │      photos
   ▼                    ▼
┌──────────────┐  ┌──────────────┐
│ Source       │  │ Target       │
│ GooglePhotos │  │ GooglePhotos │
│ Client       │  │ Client       │
└──┬───────────┘  └────────┬─────┘
   │ 4a. Photos      4b. Photos
   │     metadata        metadata
   ▼                     ▼
┌─────────────────────────────────┐
│  CompareService                 │
│  - Build hash maps              │
│  - Find missing on target       │
│  - Find extra on target         │
│  - Detect metadata differences  │
└──────────────┬──────────────────┘
               │ 5. CompareResult
               ▼
        ┌──────────────┐
        │  Flask API   │
        │  JSON response
        └──────┬───────┘
               │ 6. Display results
               ▼
        ┌──────────────┐
        │  Streamlit   │
        │  Compare View│
        └──────────────┘
```

### Sync Flow (Destructive Operation)

```
┌─────────────┐
│   User      │
│  (Streamlit)│
└──────┬──────┘
       │ 1. Request sync (with confirmations)
       ▼
┌──────────────────┐
│  Flask API       │
│  /api/sync       │
└──────┬───────────┘
       │ 2. Invoke service
       ▼
┌───────────────────────────────┐
│  SyncService                  │
│  - sync_accounts()            │
└──┬────────────────────────┬───┘
   │ 3. Compare first       │
   ▼                        │
┌──────────────────┐        │
│ CompareService   │        │
│ Get differences  │        │
└──────┬───────────┘        │
       │ 4. Differences     │
       └────────────────────┘
                  ▼
       ┌─────────────────────────┐
       │  SyncService             │
       │  For each difference:    │
       │  - Add missing photos    │
       │  - Update metadata       │
       │  - Delete extra photos   │
       └──┬───────────────────┬──┘
          │ 5a. Transfer      │ 5b. Delete
          │     photos        │     photos
          ▼                   ▼
    ┌─────────────────┐  ┌─────────────────┐
    │ TransferManager │  │ Target          │
    │ - Stream down   │  │ GooglePhotos    │
    │ - Stream up     │  │ Client          │
    └─────────────────┘  └─────────────────┘
          │
          │ 6. Progress updates (callback)
          ▼
    ┌──────────────┐
    │  Streamlit   │
    │  Progress Bar│
    └──────────────┘
          │
          │ 7. SyncResult
          ▼
    ┌──────────────┐
    │  Flask API   │
    │  JSON response
    └──────┬───────┘
           │ 8. Display results
           ▼
    ┌──────────────┐
    │  Streamlit   │
    │  Sync View   │
    └──────────────┘
```

## Technology Stack

### Core Framework
- **Python 3.10+**: Modern Python features, type hints, dataclasses
- **Flask 3.1+**: Lightweight REST API framework
- **Streamlit 1.52+**: Rapid UI development for data applications

### Google Integration
- **google-auth 2.x**: OAuth 2.0 authentication
- **google-auth-oauthlib 1.x**: OAuth flow helpers
- **google-api-python-client 2.x**: Google Photos API client

### Development Tools
- **Ruff 0.8+**: Ultra-fast linting and formatting (replaces flake8, black, isort)
- **Mypy 1.13+**: Static type checking in strict mode
- **Pytest 8.x**: Testing framework with coverage
- **uv 0.9+**: Blazing-fast package manager (10-100x faster than pip)

### Configuration & Utilities
- **python-dotenv 1.x**: Environment variable management
- **requests 2.x**: HTTP client library

## Design Decisions and Rationale

### 1. API-First Architecture

**Decision**: Separate Flask API backend from Streamlit UI frontend.

**Rationale**:
- **Flexibility**: Core logic accessible via REST API for future integrations
- **Testing**: Easier to test business logic independent of UI
- **Separation of Concerns**: Clear boundaries between layers
- **Scalability**: API can be scaled independently from UI

**Trade-off**: Added complexity of running two servers, but benefits outweigh cost for production applications.

### 2. Framework-Agnostic Core Logic

**Decision**: Core business logic (CompareService, SyncService, TransferManager) has no Flask or Streamlit dependencies.

**Rationale**:
- **Reusability**: Core can be used with any framework (CLI, web, desktop)
- **Testability**: Pure Python functions are easier to test
- **Maintainability**: Business logic changes don't affect UI/API
- **Portability**: Easy to migrate to different frameworks if needed

**Implementation**: Dependency injection ensures core receives only what it needs (clients, not frameworks).

### 3. Memory-Efficient Streaming

**Decision**: Stream photo data in 8MB chunks instead of loading entire files.

**Rationale**:
- **Scalability**: Can handle photos/videos of any size
- **Memory**: Constant memory usage regardless of photo size
- **Reliability**: Reduces risk of out-of-memory errors
- **Performance**: Allows concurrent transfers without memory pressure

**Trade-off**: Slightly more complex code, but essential for production use.

### 4. Conservative API Usage

**Decision**: Maximum 3 concurrent transfers, exponential backoff on rate limits.

**Rationale**:
- **Google API Compliance**: Respects rate limits and quotas
- **Reliability**: Reduces likelihood of being rate-limited
- **User Account Safety**: Prevents account suspension
- **Sustainable Performance**: Better to be slow and reliable than fast and fail

**Alternative Considered**: Higher concurrency (10+) was tested but caused rate limit errors.

### 5. Idempotent Sync Operations

**Decision**: Sync can be run multiple times with same result.

**Rationale**:
- **Retry Safety**: Users can safely retry failed syncs
- **Incremental Sync**: Run periodically to keep accounts in sync
- **Error Recovery**: Failures don't leave accounts in inconsistent state
- **User Confidence**: Users trust operation won't duplicate or corrupt data

**Implementation**: Check if photo exists before adding, compare metadata before updating.

### 6. Dry-Run Mode

**Decision**: Support preview-only mode that doesn't execute changes.

**Rationale**:
- **User Safety**: See what will change before committing
- **Confidence**: Users understand impact before execution
- **Testing**: Validate sync logic without modifying accounts
- **Documentation**: Example outputs for documentation

### 7. Multiple Safety Confirmations

**Decision**: Require explicit confirmations before destructive operations.

**Rationale**:
- **Prevent Mistakes**: Users must intentionally confirm
- **Clear Warnings**: Highlight destructive nature of operations
- **No Accidents**: Impossible to accidentally delete photos
- **Trust**: Users trust application won't surprise them

**Implementation**: Checkbox + type target account name + final button click.

### 8. Type Safety with Mypy Strict

**Decision**: 100% type coverage with mypy in strict mode.

**Rationale**:
- **Early Error Detection**: Catch bugs at development time
- **Documentation**: Types serve as inline documentation
- **Refactoring Safety**: Changes are validated by type checker
- **IDE Support**: Better autocomplete and refactoring tools

**Trade-off**: More verbose code, but dramatically reduces runtime errors.

### 9. Test-Driven Development

**Decision**: Minimum 90% test coverage, write tests first.

**Rationale**:
- **Confidence**: Know code works before deployment
- **Regression Prevention**: Tests catch breaking changes
- **Documentation**: Tests show how to use code
- **Design Quality**: TDD forces better design

**Implementation**: Unit tests (isolated), integration tests (multiple components), E2E tests (full workflows).

### 10. Structured Logging

**Decision**: Structured logging with configurable levels.

**Rationale**:
- **Debugging**: Detailed logs help diagnose issues
- **Production Monitoring**: Track application behavior
- **Audit Trail**: Record sync operations for accountability
- **Performance Analysis**: Identify bottlenecks

## Configuration Management

### Environment-Based Configuration

**Classes**: `DevelopmentConfig`, `ProductionConfig`, `TestingConfig`

**Design**:
- **12-Factor App**: Configuration via environment variables
- **Security**: Secrets not in code, never committed
- **Flexibility**: Same code runs in different environments
- **Validation**: Required values enforced at startup

### Configuration Sources (Priority Order)
1. Environment variables
2. `.env` file (development only)
3. Default values (sensible defaults)

## Security Considerations

### 1. OAuth 2.0 Authentication
- No password storage
- Token refresh flow
- Scopes limited to photos.readonly and photos.append

### 2. Credential Storage
- Never log credentials
- Store in-memory only (not persisted)
- Clear on session end

### 3. Input Validation
- All API inputs validated
- Type checking at runtime
- Sanitize user inputs

### 4. Rate Limiting
- Prevents abuse
- Protects user accounts
- Configurable limits

## Performance Characteristics

### Memory Usage
- **Constant**: O(1) per photo transfer (streaming)
- **Peak**: ~30-50MB for typical operation
- **Scalability**: Can sync millions of photos

### Time Complexity
- **Comparison**: O(n) where n = total photos
- **Sync**: O(m) where m = differences (photos to add/delete/update)
- **Transfer**: Limited by network speed and API rate limits

### Concurrency
- **API Requests**: Max 3 concurrent transfers
- **Blocking**: Flask runs single-threaded (WSGI server recommended for production)
- **Async**: ThreadPoolExecutor for concurrent transfers

## Extension Points

### 1. Adding New Features
- Implement in core layer first (framework-agnostic)
- Add API endpoint in Flask
- Create UI component in Streamlit

### 2. Supporting Additional APIs
- Implement new client (e.g., `DropboxPhotosClient`)
- Ensure it implements expected interface
- Inject into services via dependency injection

### 3. Custom Transfer Strategies
- Extend `TransferStrategy` base class
- Inject custom strategy into `TransferManager`
- Examples: batch uploads, multi-region, compression

### 4. Alternative UIs
- Core logic is UI-agnostic
- Can create CLI, desktop app, mobile app
- All use same Flask API

## Deployment Considerations

### Development
- Flask development server (single-threaded)
- Streamlit development server (hot reload)
- SQLite for testing (if database added)

### Production
- **WSGI Server**: gunicorn or uWSGI (multi-process)
- **Reverse Proxy**: nginx for static files and load balancing
- **Process Manager**: systemd or supervisor
- **Environment**: Docker container recommended
- **Secrets**: Environment variables or secrets manager

### Scalability
- **Horizontal**: Run multiple Flask API instances behind load balancer
- **Vertical**: Increase worker processes per instance
- **Database**: Add caching layer if needed
- **Monitoring**: Prometheus + Grafana for metrics

## Dependencies and Updates

### Dependency Management
- **uv**: Fast, reliable package resolution
- **Version Pinning**: Exact versions in requirements.txt
- **Security Updates**: Automated dependency scanning
- **Compatibility**: Test against Python 3.10, 3.11, 3.12

### Update Strategy
1. Monitor for security vulnerabilities
2. Test updates in CI/CD pipeline
3. Update in development environment
4. Run full test suite
5. Deploy to production if all tests pass

## Testing Strategy

### Unit Tests
- Test individual functions/methods in isolation
- Mock all external dependencies
- Fast execution (<1s for entire suite)
- 90%+ coverage

### Integration Tests
- Test multiple components together
- Mock only external APIs (Google Photos)
- Verify component interactions
- Test error handling

### End-to-End Tests
- Test complete workflows (compare, sync)
- Use test doubles for Google API
- Verify full data flow
- Ensure UI, API, and core work together

### CI/CD Pipeline
- **Lint**: Ruff checks on every commit
- **Type Check**: Mypy strict on every commit
- **Test**: Pytest with coverage on every commit
- **Matrix**: Test on Python 3.10, 3.11, 3.12
- **Artifacts**: Coverage reports, test results

## Resources and References

### Documentation
- [Google Photos API](https://developers.google.com/photos)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

### Best Practices
- [PEP 8 Style Guide](https://peps.python.org/pep-0008/)
- [Clean Code by Robert C. Martin](https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

### Tools
- [Ruff - Fast Python Linter](https://docs.astral.sh/ruff/)
- [Mypy - Static Type Checker](https://mypy.readthedocs.io/)
- [uv - Fast Python Package Manager](https://github.com/astral-sh/uv)

---

**Last Updated**: 2025-01-07

**Version**: 0.1.0
