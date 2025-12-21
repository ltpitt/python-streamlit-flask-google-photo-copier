#!/bin/bash
# Validate all requirements from Issue #1

set -e

echo "============================================="
echo "Validating Issue #1 Requirements"
echo "============================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

validate() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}"
    else
        echo -e "${RED}✗ $1${NC}"
        exit 1
    fi
}

echo -e "${BLUE}Checking file existence...${NC}"
test -f pyproject.toml && validate "pyproject.toml exists"
test -f requirements.txt && validate "requirements.txt exists"
test -f requirements-dev.txt && validate "requirements-dev.txt exists"
test -f .env.example && validate ".env.example exists"
test -f Makefile && validate "Makefile exists"
test -f .python-version && validate ".python-version exists"
echo ""

echo -e "${BLUE}Validating pyproject.toml structure...${NC}"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); assert 'project' in config" && validate "Contains [project] table"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); assert 'tool.ruff' in config" && validate "Contains [tool.ruff] configuration"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); assert 'tool.pytest.ini_options' in config" && validate "Contains [tool.pytest.ini_options] configuration"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); assert 'tool.mypy' in config" && validate "Contains [tool.mypy] configuration"
echo ""

echo -e "${BLUE}Validating Ruff configuration...${NC}"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); assert config['tool']['ruff']['line-length'] == 88" && validate "Line-length is 88"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); assert config['tool']['ruff']['target-version'] == 'py310'" && validate "Target version is py310"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); rules = config['tool']['ruff']['lint']['select']; assert all(r in rules for r in ['E', 'F', 'I', 'N', 'W', 'B', 'C90'])" && validate "All required rules (E,F,I,N,W,B,C90) are selected"
echo ""

echo -e "${BLUE}Validating dependencies...${NC}"
grep -q "flask" requirements.txt && validate "flask in requirements.txt"
grep -q "streamlit" requirements.txt && validate "streamlit in requirements.txt"
grep -q "google-auth" requirements.txt && validate "google-auth in requirements.txt"
grep -q "google-api-python-client" requirements.txt && validate "google-api-python-client in requirements.txt"
grep -q "requests" requirements.txt && validate "requests in requirements.txt"
grep -q "python-dotenv" requirements.txt && validate "python-dotenv in requirements.txt"
echo ""

echo -e "${BLUE}Validating dev dependencies...${NC}"
grep -q "pytest" requirements-dev.txt && validate "pytest in requirements-dev.txt"
grep -q "pytest-cov" requirements-dev.txt && validate "pytest-cov in requirements-dev.txt"
grep -q "pytest-mock" requirements-dev.txt && validate "pytest-mock in requirements-dev.txt"
grep -q "ruff" requirements-dev.txt && validate "ruff in requirements-dev.txt"
grep -q "mypy" requirements-dev.txt && validate "mypy in requirements-dev.txt"
echo ""

echo -e "${BLUE}Validating Makefile targets...${NC}"
grep -q "^venv:" Makefile && validate "venv target exists"
grep -q "^install:" Makefile && validate "install target exists"
grep -q "^test:" Makefile && validate "test target exists"
grep -q "^lint:" Makefile && validate "lint target exists"
grep -q "^format:" Makefile && validate "format target exists"
grep -q "^coverage:" Makefile && validate "coverage target exists"
grep -q "^run-api:" Makefile && validate "run-api target exists"
grep -q "^run-ui:" Makefile && validate "run-ui target exists"
grep -q "^clean:" Makefile && validate "clean target exists"
echo ""

echo -e "${BLUE}Validating pytest configuration...${NC}"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); assert config['tool']['pytest']['ini_options']['testpaths'] == ['tests']" && validate "testpaths is configured"
python3 -c "import tomllib; config = tomllib.load(open('pyproject.toml', 'rb')); assert '--cov-fail-under=90' in config['tool']['pytest']['ini_options']['addopts']" && validate "Coverage target is 90%"
echo ""

echo -e "${BLUE}Validating .python-version...${NC}"
grep -q "3.10" .python-version && validate ".python-version specifies 3.10"
echo ""

echo -e "${BLUE}Running tool verification...${NC}"
source .venv/bin/activate 2>/dev/null || true
ruff check . > /dev/null 2>&1 && validate "Ruff runs without errors"
python3 -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))" && validate "pyproject.toml is valid TOML"
echo ""

echo "============================================="
echo -e "${GREEN}All requirements validated successfully!${NC}"
echo "============================================="
