#!/bin/bash

# Futarchy Arbitrage Bot Environment Setup Script
# This script sets up the Python environment for the futarchy arbitrage bot
# Supports: pip, pyenv, and uv package managers

set -e  # Exit on error

echo "🚀 Setting up Futarchy Arbitrage Bot environment..."
echo ""

# Detect operating system
OS="$(uname -s)"
case "${OS}" in
    Linux*)     PLATFORM="Linux";;
    Darwin*)    PLATFORM="macOS";;
    *)          PLATFORM="UNKNOWN";;
esac

echo "🖥️  Platform: ${PLATFORM}"

# Check Python version
REQUIRED_PYTHON_FULL="3.14.0"
REQUIRED_PYTHON_MINOR="3.14"

if [ -f ".python-version" ]; then
    REQUIRED_PYTHON_FULL=$(cat .python-version)
    REQUIRED_PYTHON_MINOR=$(echo "$REQUIRED_PYTHON_FULL" | cut -d. -f1,2)
fi

echo "📦 Required Python version: ${REQUIRED_PYTHON_FULL} (${REQUIRED_PYTHON_MINOR}.x acceptable)"

# Check for uv (fast Python package manager)
USE_UV=false
if command -v uv &> /dev/null; then
    echo "✅ Found uv: $(uv --version)"
    read -p "Use uv for faster installation? (Y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        USE_UV=true
    fi
fi

# Try to find the best Python version
PYTHON_CMD=""
PYTHON_VERSION=""
for cmd in python${REQUIRED_PYTHON_MINOR} python3.14 python3; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd --version 2>&1 | awk '{print $2}')
        VERSION_MINOR=$(echo "$VERSION" | cut -d. -f1,2)
        
        if [[ "$VERSION_MINOR" == "$REQUIRED_PYTHON_MINOR" ]]; then
            PYTHON_CMD=$cmd
            PYTHON_VERSION=$VERSION
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python ${REQUIRED_PYTHON_MINOR}.x not found!"
    echo ""
    echo "Please install Python ${REQUIRED_PYTHON_MINOR} first:"
    echo ""
    echo "  Option 1: Using uv (recommended - fastest):"
    echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "    uv python install ${REQUIRED_PYTHON_FULL}"
    echo "    # Then re-run this script"
    echo ""
    echo "  Option 2: Using pyenv:"
    echo "    # Install pyenv first:"
    if [[ "$PLATFORM" == "macOS" ]]; then
        echo "    brew install pyenv"
    else
        echo "    curl https://pyenv.run | bash"
    fi
    echo "    # Add to shell (bash):"
    echo "    echo 'export PYENV_ROOT=\"\$HOME/.pyenv\"' >> ~/.bashrc"
    echo "    echo 'command -v pyenv >/dev/null || export PATH=\"\$PYENV_ROOT/bin:\$PATH\"' >> ~/.bashrc"
    echo "    echo 'eval \"\$(pyenv init -)\"' >> ~/.bashrc"
    echo "    source ~/.bashrc"
    echo "    # Install Python:"
    echo "    pyenv install ${REQUIRED_PYTHON_FULL}"
    echo "    pyenv local ${REQUIRED_PYTHON_FULL}"
    echo ""
    echo "  Option 3: System package manager:"
    if [[ "$PLATFORM" == "macOS" ]]; then
        echo "    brew install python@${REQUIRED_PYTHON_MINOR}"
    else
        echo "    sudo apt-get update"
        echo "    sudo apt-get install python${REQUIRED_PYTHON_MINOR} python${REQUIRED_PYTHON_MINOR}-venv python${REQUIRED_PYTHON_MINOR}-dev"
    fi
    echo ""
    exit 1
fi

echo "✅ Found Python: $PYTHON_CMD (version ${PYTHON_VERSION})"
echo ""

# Create and setup virtual environment
VENV_DIR="futarchy_env"

if $USE_UV; then
    # Use uv for venv creation and package installation
    echo "🔧 Using uv for environment setup..."
    
    if [ -d "$VENV_DIR" ]; then
        echo "⚠️  Virtual environment '$VENV_DIR' already exists."
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Removing existing environment..."
            rm -rf "$VENV_DIR"
        fi
    fi
    
    if [ ! -d "$VENV_DIR" ]; then
        echo "🔧 Creating virtual environment with uv..."
        uv venv "$VENV_DIR" --python "$PYTHON_CMD"
    fi
    
    echo "🔌 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    echo "📦 Installing dependencies with uv (fast!)..."
    if [ -f "requirements.txt" ]; then
        uv pip install -r requirements.txt
    fi
    
    if [ -f "pyproject.toml" ]; then
        uv pip install -e .
        
        echo ""
        read -p "📦 Install development dependencies? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            uv pip install -e ".[dev]"
        fi
    fi
else
    # Use standard pip workflow
    echo "📦 Validating Python venv module..."
    if ! $PYTHON_CMD -m venv --help &> /dev/null; then
        echo "❌ Python venv module not found!"
        echo ""
        echo "Please install it:"
        echo "  Ubuntu/Debian: sudo apt-get install python${REQUIRED_PYTHON_MINOR}-venv"
        echo "  macOS: venv should be included with Python"
        echo ""
        exit 1
    fi

    echo "✅ Python venv module available"
    echo ""

    if [ -d "$VENV_DIR" ]; then
        echo "⚠️  Virtual environment '$VENV_DIR' already exists."
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "🗑️  Removing existing environment..."
            rm -rf "$VENV_DIR"
        else
            echo "📦 Using existing environment..."
        fi
    fi

    if [ ! -d "$VENV_DIR" ]; then
        echo "🔧 Creating virtual environment in '$VENV_DIR'..."
        $PYTHON_CMD -m venv "$VENV_DIR"
    fi

    echo "🔌 Activating virtual environment..."
    source "$VENV_DIR/bin/activate"

    echo "📦 Upgrading pip..."
    pip install --upgrade pip setuptools wheel
    echo ""

    echo "📦 Installing dependencies..."
    if [ -f "requirements.txt" ]; then
        echo "  → Installing from requirements.txt..."
        pip install -r requirements.txt
    else
        echo "⚠️  requirements.txt not found"
    fi

    if [ -f "pyproject.toml" ]; then
        echo "  → Installing package in editable mode..."
        pip install -e .
        
        echo ""
        read -p "📦 Install development dependencies (pytest, black, mypy)? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "  → Installing dev dependencies..."
            pip install -e ".[dev]"
        fi
    else
        echo "⚠️  pyproject.toml not found"
    fi
fi

echo ""
echo "✅ Python dependencies installed"
echo ""

# Check for Solidity compiler
echo "🔧 Checking for Solidity compiler..."
SOLC_REQUIRED_VERSION="0.8.33"

if command -v solc &> /dev/null; then
    SOLC_VERSION=$(solc --version 2>&1 | grep -oE 'Version: [0-9.]+' | cut -d' ' -f2)
    echo "✅ Found solc: ${SOLC_VERSION}"
    
    if [[ "$SOLC_VERSION" != "$SOLC_REQUIRED_VERSION" ]]; then
        echo "⚠️  Note: Project uses solc ${SOLC_REQUIRED_VERSION}, but found ${SOLC_VERSION}"
        echo "   Foundry will use the correct version automatically."
    fi
else
    echo "⚠️  Solidity compiler (solc) not found!"
    echo ""
    read -p "Do you want to install solc ${SOLC_REQUIRED_VERSION}? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$PLATFORM" == "macOS" ]]; then
            echo "📦 Installing solc via Homebrew..."
            if command -v brew &> /dev/null; then
                brew tap ethereum/ethereum
                brew install solidity@8
                echo "✅ Installed solc"
            else
                echo "❌ Homebrew not found. Please install Homebrew first or use Foundry (forge)."
            fi
        elif [[ "$PLATFORM" == "Linux" ]]; then
            echo "📦 Installing solc ${SOLC_REQUIRED_VERSION}..."
            SOLC_URL="https://github.com/ethereum/solidity/releases/download/v${SOLC_REQUIRED_VERSION}/solc-static-linux"
            curl -L "$SOLC_URL" --output /tmp/solc
            chmod +x /tmp/solc
            sudo mv /tmp/solc /usr/local/bin/solc
            echo "✅ Installed solc $(/usr/local/bin/solc --version | grep -oE 'Version: [0-9.]+' | cut -d' ' -f2)"
        fi
    else
        echo "ℹ️  Skipped solc installation. You can use Foundry (forge) instead:"
        echo "   curl -L https://foundry.paradigm.xyz | bash"
        echo "   foundryup"
    fi
fi

echo ""

# Check for Foundry
echo "🔧 Checking for Foundry (forge)..."
if command -v forge &> /dev/null; then
    FORGE_VERSION=$(forge --version | head -1)
    echo "✅ Found Foundry: ${FORGE_VERSION}"
else
    echo "⚠️  Foundry (forge) not found!"
    echo ""
    read -p "Do you want to install Foundry? (Recommended) (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Installing Foundry..."
        curl -L https://foundry.paradigm.xyz | bash
        source ~/.bashrc 2>/dev/null || source ~/.zshrc 2>/dev/null || true
        foundryup
        echo "✅ Installed Foundry"
    else
        echo "ℹ️  Skipped Foundry installation."
        echo "   Note: This project uses Foundry for Solidity compilation."
        echo "   Install later with: curl -L https://foundry.paradigm.xyz | bash && foundryup"
    fi
fi

echo ""

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Environment setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Setup Summary:"
echo "  Python:  ${PYTHON_VERSION} (${PYTHON_CMD})"
echo "  Venv:    ${VENV_DIR}/"
if $USE_UV; then
    echo "  Package: uv (fast mode)"
else
    echo "  Package: pip"
fi
if command -v forge &> /dev/null; then
    echo "  Forge:   $(forge --version | head -1 | awk '{print $2}')"
fi
if command -v solc &> /dev/null; then
    echo "  Solc:    $(solc --version 2>&1 | grep -oE 'Version: [0-9.]+' | cut -d' ' -f2)"
fi
echo ""
echo "📝 Next steps:"
echo ""
echo "  1️⃣  Activate the environment:"
echo "     source ${VENV_DIR}/bin/activate"
echo ""
echo "  2️⃣  Configure your environment file:"
echo "     cp .env.template .env.0x<YOUR_PROPOSAL_ADDRESS>"
echo "     # Edit with your RPC URLs, private keys, etc."
echo ""
echo "  3️⃣  Fetch market data (optional):"
echo "     source .env.0x<YOUR_PROPOSAL_ADDRESS>"
echo "     python -m src.setup.fetch_market_data --proposal --update-env"
echo ""
echo "  4️⃣  Run a bot:"
echo "     # Sequential bot (classic)"
echo "     python -m src.arbitrage_commands.simple_bot --amount 0.01 --interval 120 --tolerance 0.2"
echo ""
echo "     # EIP-7702 bot (recommended - MEV protection)"
echo "     python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --interval 120 --tolerance 0.02"
echo ""
echo "     # Unified bot (database-driven)"
echo "     python -m src.arbitrage_commands.unified_bot --bot-name my-bot --dry-run"
echo ""
echo "  5️⃣  Compile Solidity contracts (if needed):"
echo "     forge build"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📚 Documentation:"
echo "  • README.md - Project overview"
echo "  • CLAUDE.md - Development workflow and patterns"
echo "  • docs/API_MAP.md - Contract API reference"
echo "  • docs/SCRIPTS_INDEX.md - All Python scripts catalog"
echo "  • docs/CLZ_OPCODE_ANALYSIS.md - CLZ implementation details"
echo ""
echo "🆘 Need help? Check the documentation or run scripts with --help"
echo ""