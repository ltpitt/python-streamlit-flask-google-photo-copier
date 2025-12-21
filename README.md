# Google Photos Sync

A production-grade Python application for monodirectional synchronization of Google Photos between accounts, featuring a Flask REST API backend and Streamlit UI frontend.

## Features

- **API-First Architecture**: Clean separation between Flask backend and Streamlit frontend
- **100% Type Safety**: Full mypy strict type checking
- **TDD-Driven**: Test-driven development with 90% minimum coverage
- **Modern Tooling**: Uses uv for blazing-fast dependency management
- **Production Ready**: Following PEP standards and clean code principles

## Quick Start

### Prerequisites
- Python 3.10 or higher
- uv package manager (or pip as fallback)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ltpitt/python-streamlit-flask-google-photo-copier.git
   cd python-streamlit-flask-google-photo-copier
   ```

2. **Install uv (if not already installed)**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Windows PowerShell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # Or via pip
   pip install uv
   ```

3. **Create and activate virtual environment**
   ```bash
   # Create venv
   uv venv
   
   # Activate (macOS/Linux)
   source .venv/bin/activate
   
   # Activate (Windows PowerShell)
   .venv\Scripts\Activate.ps1
   ```

4. **Install dependencies**
   ```bash
   # Fast installation with uv (recommended)
   uv pip install -r requirements.txt -r requirements-dev.txt
   
   # Install in editable mode
   uv pip install -e .
   ```

5. **Verify setup**
   ```bash
   ./verify-setup.sh
   ```

### Using Make Commands

```bash
# Create virtual environment
make venv

# Activate venv first, then:
source .venv/bin/activate

# Install dependencies
make install-dev

# Run tests
make test

# Lint and format
make lint
make format

# Type check
make typecheck
```

## Development

See [SETUP.md](SETUP.md) for detailed setup documentation.

### Project Structure
```
src/google_photos_sync/    # Main application package
tests/                      # Test suite
  unit/                     # Unit tests
  integration/              # Integration tests
  e2e/                      # End-to-end tests
```

### Code Quality Tools
- **Ruff**: Linting and formatting (88 char line length)
- **Mypy**: Strict type checking
- **Pytest**: Testing with 90% minimum coverage

## Contributing

1. Follow TDD: Write tests first (RED → GREEN → REFACTOR)
2. Maintain 90%+ test coverage
3. Use type hints everywhere
4. Follow PEP standards (PEP 8, PEP 257, PEP 484)
5. Apply SOLID principles and clean code practices

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Documentation

- [Setup Guide](SETUP.md) - Detailed setup and configuration
- [GitHub Issues](GITHUB_ISSUES.md) - Project planning and tasks
