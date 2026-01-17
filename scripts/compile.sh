#!/bin/bash
# Quick compile script for all contracts
# Generates ABI, bytecode, assembly, opcodes, and more

set -e

echo "🔨 Compiling all Solidity contracts..."
echo "========================================"

# Activate virtual environment if it exists
if [ -d "futarchy_env" ]; then
	source futarchy_env/bin/activate
fi

# Run comprehensive compiler
python3 scripts/compile_all.py "$@"

echo ""
echo "✅ Compilation complete!"
echo "Artifacts saved in artifacts/"
echo ""
echo "Directory structure:"
echo "  artifacts/abi/          - Contract ABIs (JSON)"
echo "  artifacts/bytecode/     - Deployment bytecode"
echo "  artifacts/asm/          - Assembly code"
echo "  artifacts/opcodes/      - Opcode listings"
echo "  artifacts/storage/      - Storage layouts"
echo "  artifacts/ast/          - Abstract Syntax Trees"
