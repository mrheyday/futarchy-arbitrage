#!/bin/bash

# Futarchy Arbitrage Bot Environment Setup Script
# This script sets up the Python environment for the futarchy arbitrage bot

set -e # Exit on error

echo "🚀 Setting up Futarchy Arbitrage Bot environment..."

# Check Python version
REQUIRED_PYTHON="3.9"
if [ -f ".python-version" ]; then
<<<<<<< Updated upstream
<<<<<<< Updated upstream
	REQUIRED_PYTHON=$(cat .python-version | cut -d. -f1,2)
=======
    REQUIRED_PYTHON=$(cat .python-version | cut -d. -f1,2)
>>>>>>> Stashed changes
=======
    REQUIRED_PYTHON=$(cat .python-version | cut -d. -f1,2)
>>>>>>> Stashed changes
fi

echo "📦 Checking for Python ${REQUIRED_PYTHON}..."

# Try to find the best Python version
PYTHON_CMD=""
for cmd in python${REQUIRED_PYTHON} python3.9 python3; do
<<<<<<< Updated upstream
<<<<<<< Updated upstream
	if command -v "$cmd" &>/dev/null; then
		VERSION=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
		if [[ "$VERSION" == "$REQUIRED_PYTHON"* ]]; then
			PYTHON_CMD="$cmd"
			break
		fi
	fi
done

if [ -z "$PYTHON_CMD" ]; then
	echo "❌ Python ${REQUIRED_PYTHON} not found!"
	echo "Please install Python ${REQUIRED_PYTHON} first:"
	echo "  Ubuntu/Debian: sudo apt-get install python${REQUIRED_PYTHON} python${REQUIRED_PYTHON}-venv python${REQUIRED_PYTHON}-dev"
	echo "  macOS: brew install python@${REQUIRED_PYTHON}"
	exit 1
=======
=======
>>>>>>> Stashed changes
    if command -v "$cmd" &> /dev/null; then
        VERSION=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
        if [[ "$VERSION" == "$REQUIRED_PYTHON"* ]]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "❌ Python ${REQUIRED_PYTHON} not found!"
    echo "Please install Python ${REQUIRED_PYTHON} first:"
    echo "  Ubuntu/Debian: sudo apt-get install python${REQUIRED_PYTHON} python${REQUIRED_PYTHON}-venv python${REQUIRED_PYTHON}-dev"
    echo "  macOS: brew install python@${REQUIRED_PYTHON}"
    exit 1
>>>>>>> Stashed changes
fi

echo "✅ Found Python: $PYTHON_CMD ($($PYTHON_CMD --version))"

# Check for venv module
echo "📦 Checking for venv module..."
<<<<<<< Updated upstream
<<<<<<< Updated upstream
if ! $PYTHON_CMD -m venv --help &>/dev/null; then
	echo "❌ Python venv module not found!"
	echo "Please install it:"
	echo "  Ubuntu/Debian: sudo apt-get install python${REQUIRED_PYTHON}-venv"
	exit 1
=======
=======
>>>>>>> Stashed changes
if ! $PYTHON_CMD -m venv --help &> /dev/null; then
    echo "❌ Python venv module not found!"
    echo "Please install it:"
    echo "  Ubuntu/Debian: sudo apt-get install python${REQUIRED_PYTHON}-venv"
    exit 1
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
fi

# Create virtual environment
VENV_DIR="futarchy_env"
if [ -d "$VENV_DIR" ]; then
<<<<<<< Updated upstream
<<<<<<< Updated upstream
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
=======
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies from requirements.txt..."
if [ -f "requirements.txt" ]; then
<<<<<<< Updated upstream
<<<<<<< Updated upstream
	pip install -r requirements.txt
else
	echo "⚠️  requirements.txt not found, skipping dependency installation"
=======
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, skipping dependency installation"
>>>>>>> Stashed changes
=======
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, skipping dependency installation"
>>>>>>> Stashed changes
fi

# Install development dependencies if pyproject.toml exists
if [ -f "pyproject.toml" ]; then
<<<<<<< Updated upstream
<<<<<<< Updated upstream
	echo "📦 Installing package in editable mode..."
	pip install -e .

	read -p "Install development dependencies? (y/N): " -n 1 -r
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		pip install -e ".[dev]"
	fi
=======
=======
>>>>>>> Stashed changes
    echo "📦 Installing package in editable mode..."
    pip install -e .
    
    read -p "Install development dependencies? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pip install -e ".[dev]"
    fi
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
fi

# Check for Solidity compiler
echo "🔧 Checking for Solidity compiler..."
<<<<<<< Updated upstream
<<<<<<< Updated upstream
if ! command -v solc &>/dev/null; then
	echo "⚠️  Solidity compiler (solc) not found!"
	read -p "Do you want to install solc 0.8.24? (y/N): " -n 1 -r
	echo
	if [[ $REPLY =~ ^[Yy]$ ]]; then
		echo "📦 Installing solc 0.8.24..."
		curl -L https://github.com/ethereum/solidity/releases/download/v0.8.24/solc-static-linux --output /tmp/solc
		chmod +x /tmp/solc
		sudo mv /tmp/solc /usr/local/bin/solc
		echo "✅ Installed solc $(solc --version | head -1)"
	fi
else
	echo "✅ Found solc: $(solc --version | head -1)"
=======
=======
>>>>>>> Stashed changes
if ! command -v solc &> /dev/null; then
    echo "⚠️  Solidity compiler (solc) not found!"
    read -p "Do you want to install solc 0.8.24? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 Installing solc 0.8.24..."
        curl -L https://github.com/ethereum/solidity/releases/download/v0.8.24/solc-static-linux --output /tmp/solc
        chmod +x /tmp/solc
        sudo mv /tmp/solc /usr/local/bin/solc
        echo "✅ Installed solc $(solc --version | head -1)"
    fi
else
    echo "✅ Found solc: $(solc --version | head -1)"
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
fi

echo ""
echo "✅ Environment setup complete!"
echo ""
echo " Next steps:"
echo "  1. Activate the environment: source $VENV_DIR/bin/activate"
echo "  2. Copy and configure an environment file:"
echo "     cp .env.template .env.0x<YOUR_PROPOSAL_ADDRESS>"
echo "     # Edit the file with your configuration"
echo "  3. Source your environment file:"
echo "     source .env.0x<YOUR_PROPOSAL_ADDRESS>"
echo "  4. Run the bot:"
echo "     python -m src.arbitrage_commands.simple_bot --amount 0.01 --interval 120 --tolerance 0.2"
echo ""
<<<<<<< Updated upstream
<<<<<<< Updated upstream
echo "For more information, see README.md and CLAUDE.md"
=======
echo "For more information, see README.md and CLAUDE.md"
>>>>>>> Stashed changes
=======
echo "For more information, see README.md and CLAUDE.md"
>>>>>>> Stashed changes
