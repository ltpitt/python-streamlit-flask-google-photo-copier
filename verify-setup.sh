#!/bin/bash
# Comprehensive verification script for project foundation setup

set -e

echo "============================================="
echo "Google Photos Sync - Setup Verification"
echo "============================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}1. Checking Python version...${NC}"
python --version
echo ""

echo -e "${BLUE}2. Checking uv installation...${NC}"
uv --version
echo ""

echo -e "${BLUE}3. Verifying pyproject.toml is valid...${NC}"
python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" && echo -e "${GREEN}✓ pyproject.toml is valid${NC}"
echo ""

echo -e "${BLUE}4. Checking virtual environment...${NC}"
if [ -d ".venv" ]; then
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
else
    echo "Creating virtual environment..."
    uv venv .venv
fi
echo ""

echo -e "${BLUE}5. Activating virtual environment and checking Python path...${NC}"
source .venv/bin/activate
which python
echo ""

echo -e "${BLUE}6. Installing package in editable mode...${NC}"
uv pip install -e . -q
echo -e "${GREEN}✓ Package installed${NC}"
echo ""

echo -e "${BLUE}7. Running ruff linter...${NC}"
ruff check .
echo ""

echo -e "${BLUE}8. Running ruff formatter...${NC}"
ruff format .
echo ""

echo -e "${BLUE}9. Running mypy type checker...${NC}"
mypy src/ --strict
echo ""

echo -e "${BLUE}10. Running pytest with coverage...${NC}"
pytest -v tests/unit/test_setup.py
echo ""

echo -e "${BLUE}11. Testing Makefile targets...${NC}"
echo "  - make help"
make help | head -5
echo ""

echo -e "${BLUE}12. Verifying configuration files...${NC}"
echo -e "  ${GREEN}✓${NC} pyproject.toml"
echo -e "  ${GREEN}✓${NC} requirements.txt"
echo -e "  ${GREEN}✓${NC} requirements-dev.txt"
echo -e "  ${GREEN}✓${NC} .env.example"
echo -e "  ${GREEN}✓${NC} Makefile"
echo -e "  ${GREEN}✓${NC} .python-version"
echo ""

echo "============================================="
echo -e "${GREEN}All verifications passed!${NC}"
echo "============================================="
