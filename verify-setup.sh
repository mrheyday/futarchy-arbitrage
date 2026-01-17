#!/bin/bash

# Futarchy Arbitrage - Setup Verification Script
# Verifies that the development environment is correctly configured

set -e

echo "🔍 Futarchy Arbitrage - Environment Verification"
echo "=================================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SUCCESS=0
WARNINGS=0
FAILURES=0

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((SUCCESS++))
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILURES++))
}

# Check Python version
echo "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
    REQUIRED_VERSION="3.9"
    if [[ "$PYTHON_VERSION" == "$REQUIRED_VERSION"* ]]; then
        check_pass "Python $PYTHON_VERSION installed"
    else
        check_warn "Python $PYTHON_VERSION found (recommended: 3.9.x)"
    fi
else
    check_fail "Python 3 not found"
fi

# Check virtual environment
echo ""
echo "Checking virtual environment..."
if [ -d "futarchy_env" ]; then
    check_pass "Virtual environment 'futarchy_env' exists"
    
    # Check if venv is activated
    if [[ "$VIRTUAL_ENV" == *"futarchy_env"* ]]; then
        check_pass "Virtual environment is activated"
    else
        check_warn "Virtual environment not activated (run: source futarchy_env/bin/activate)"
    fi
    
    # Check installed packages
    if [ -f "futarchy_env/bin/pip" ]; then
        INSTALLED_PACKAGES=$(futarchy_env/bin/pip list --format=freeze | wc -l)
        if [ "$INSTALLED_PACKAGES" -gt 10 ]; then
            check_pass "Dependencies installed ($INSTALLED_PACKAGES packages)"
        else
            check_warn "Few packages installed ($INSTALLED_PACKAGES) - run: pip install -e ."
        fi
    fi
else
    check_fail "Virtual environment 'futarchy_env' not found"
fi

# Check Node.js and Foundry
echo ""
echo "Checking Solidity toolchain..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    check_pass "Node.js $NODE_VERSION installed"
else
    check_warn "Node.js not found (optional for some scripts)"
fi

if command -v forge &> /dev/null; then
    FORGE_VERSION=$(forge --version | head -n1)
    check_pass "Foundry installed: $FORGE_VERSION"
else
    check_fail "Foundry (forge) not found"
fi

if command -v solc &> /dev/null; then
    SOLC_VERSION=$(solc --version | grep Version | awk '{print $2}')
    check_pass "solc $SOLC_VERSION installed"
else
    check_warn "solc not found (using Foundry's built-in solc)"
fi

# Check Git submodules
echo ""
echo "Checking Git submodules..."
if [ -d "lib/solady/.git" ]; then
    check_pass "Solady submodule initialized"
    
    # Check if on clz branch
    cd lib/solady
    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    if [ "$CURRENT_BRANCH" = "clz" ]; then
        check_pass "Solady on 'clz' branch"
    else
        check_warn "Solady not on 'clz' branch (current: $CURRENT_BRANCH)"
    fi
    cd ../..
else
    check_fail "Solady submodule not initialized (run: git submodule update --init --recursive)"
fi

# Check configuration files
echo ""
echo "Checking configuration files..."
if [ -f "foundry.toml" ]; then
    check_pass "foundry.toml exists"
    
    # Check for Osaka EVM
    if grep -q "evm_version.*=.*\"osaka\"" foundry.toml; then
        check_pass "Osaka EVM configured (CLZ opcode support)"
    else
        check_warn "Osaka EVM not configured in foundry.toml"
    fi
else
    check_fail "foundry.toml not found"
fi

if [ -f "pyproject.toml" ]; then
    check_pass "pyproject.toml exists"
else
    check_fail "pyproject.toml not found"
fi

if [ -f ".python-version" ]; then
    PYTHON_VERSION_FILE=$(cat .python-version)
    check_pass ".python-version file exists (specifies $PYTHON_VERSION_FILE)"
else
    check_warn ".python-version file not found"
fi

# Check environment files
echo ""
echo "Checking environment files..."
ENV_FILES=$(find . -maxdepth 1 -name ".env.0x*" | wc -l)
if [ "$ENV_FILES" -gt 0 ]; then
    check_pass "Found $ENV_FILES environment file(s)"
else
    check_warn "No .env.0x* files found (market-specific configuration)"
fi

# Check compiled contracts
echo ""
echo "Checking compiled contracts..."
if [ -d "out" ] && [ "$(ls -A out 2>/dev/null)" ]; then
    CONTRACT_COUNT=$(find out -name "*.json" | wc -l)
    check_pass "Contracts compiled ($CONTRACT_COUNT artifacts)"
else
    check_warn "No compiled contracts found (run: forge build)"
fi

# Check documentation
echo ""
echo "Checking documentation..."
DOCS=("docs/API_MAP.md" "docs/SCRIPTS_INDEX.md" "docs/BUILD_SUMMARY.md" "docs/CLZ_OPCODE_ANALYSIS.md")
DOC_COUNT=0
for doc in "${DOCS[@]}"; do
    if [ -f "$doc" ]; then
        ((DOC_COUNT++))
    fi
done
check_pass "Documentation: $DOC_COUNT/4 files present"

# Summary
echo ""
echo "=================================================="
echo "Verification Summary:"
echo -e "${GREEN}✓ Passed: $SUCCESS${NC}"
if [ "$WARNINGS" -gt 0 ]; then
    echo -e "${YELLOW}⚠ Warnings: $WARNINGS${NC}"
fi
if [ "$FAILURES" -gt 0 ]; then
    echo -e "${RED}✗ Failed: $FAILURES${NC}"
fi
echo ""

if [ "$FAILURES" -eq 0 ]; then
    echo -e "${GREEN}✅ Environment is ready for development!${NC}"
    exit 0
else
    echo -e "${RED}❌ Please fix the failed checks before proceeding.${NC}"
    echo ""
    echo "Quick fix commands:"
    echo "  - Install Python 3.9: https://www.python.org/downloads/"
    echo "  - Setup environment: ./setup.sh"
    echo "  - Install Foundry: curl -L https://foundry.paradigm.xyz | bash && foundryup"
    echo "  - Init submodules: git submodule update --init --recursive"
    echo "  - Compile contracts: forge build"
    exit 1
fi
