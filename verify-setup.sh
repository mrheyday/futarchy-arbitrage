#!/bin/bash

# Quick environment verification script
# Checks that all required tools and dependencies are installed

set -e

echo "🔍 Futarchy Arbitrage Environment Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

ERRORS=0
WARNINGS=0

# Check Python
echo "🐍 Python:"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo "  ✅ Python ${PYTHON_VERSION}"
    
    # Check version is 3.9.x
    if [[ ! "$PYTHON_VERSION" =~ ^3\.9\. ]]; then
        echo "  ⚠️  Warning: Expected Python 3.9.x, found ${PYTHON_VERSION}"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "  ❌ Python not found"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check virtual environment
echo "📦 Virtual Environment:"
if [ -d "futarchy_env" ]; then
    echo "  ✅ futarchy_env/ exists"
    
    # Check if activated
    if [[ "$VIRTUAL_ENV" == *"futarchy_env"* ]]; then
        echo "  ✅ Environment is activated"
    else
        echo "  ⚠️  Environment not activated (run: source futarchy_env/bin/activate)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "  ❌ futarchy_env/ not found (run: ./setup.sh)"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Check Python packages
echo "📚 Python Packages:"
if [ -f "futarchy_env/bin/pip" ]; then
    PACKAGES=("web3" "eth-account" "requests" "python-dotenv" "supabase")
    for pkg in "${PACKAGES[@]}"; do
        if futarchy_env/bin/pip show "$pkg" &> /dev/null; then
            echo "  ✅ $pkg"
        else
            echo "  ❌ $pkg (not installed)"
            ERRORS=$((ERRORS + 1))
        fi
    done
else
    echo "  ⚠️  Cannot check packages (venv not found)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check Foundry
echo "🔨 Foundry:"
if command -v forge &> /dev/null; then
    FORGE_VERSION=$(forge --version | head -1 | awk '{print $2}')
    echo "  ✅ forge ${FORGE_VERSION}"
else
    echo "  ⚠️  forge not found (install: curl -L https://foundry.paradigm.xyz | bash)"
    WARNINGS=$((WARNINGS + 1))
fi

if command -v cast &> /dev/null; then
    echo "  ✅ cast"
else
    echo "  ⚠️  cast not found"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check Solidity compiler
echo "⚙️  Solidity:"
if command -v solc &> /dev/null; then
    SOLC_VERSION=$(solc --version 2>&1 | grep -oE 'Version: [0-9.]+' | cut -d' ' -f2)
    echo "  ✅ solc ${SOLC_VERSION}"
else
    echo "  ⚠️  solc not found (Foundry can compile without it)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check build artifacts
echo "📁 Build Artifacts:"
if [ -d "out" ]; then
    CONTRACT_COUNT=$(find out -name "*.json" -type f 2>/dev/null | wc -l | tr -d ' ')
    echo "  ✅ out/ directory (${CONTRACT_COUNT} artifacts)"
else
    echo "  ⚠️  out/ not found (run: forge build)"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Check environment files
echo "🔧 Configuration:"
ENV_COUNT=$(ls .env.0x* 2>/dev/null | wc -l | tr -d ' ')
if [ "$ENV_COUNT" -gt 0 ]; then
    echo "  ✅ Found ${ENV_COUNT} environment file(s)"
else
    echo "  ⚠️  No .env.0x* files found"
    echo "     Copy template: cp .env.template .env.0x<PROPOSAL_ADDRESS>"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Summary:"
echo "  Errors:   ${ERRORS}"
echo "  Warnings: ${WARNINGS}"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Environment is ready."
    echo ""
    echo "Next steps:"
    echo "  1. Activate: source futarchy_env/bin/activate"
    echo "  2. Configure: source .env.0x<PROPOSAL_ADDRESS>"
    echo "  3. Run bot: python -m src.arbitrage_commands.eip7702_bot --help"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Environment is functional but has ${WARNINGS} warning(s)"
    exit 0
else
    echo "❌ Environment has ${ERRORS} error(s) and ${WARNINGS} warning(s)"
    echo ""
    echo "To fix errors, run: ./setup.sh"
    exit 1
fi
