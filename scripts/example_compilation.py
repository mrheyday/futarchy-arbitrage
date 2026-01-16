#!/usr/bin/env python3
"""
Quick reference: Generate all compilation artifacts for a contract.

This script demonstrates the complete workflow for compiling, analyzing,
and deploying Solidity contracts with comprehensive artifact generation.

Run this to see all available compilation outputs.
"""

import subprocess
import sys
from pathlib import Path


def print_section(title: str):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def run_example():
    """Run example compilation workflow"""

    contract_name = sys.argv[1] if len(sys.argv) > 1 else "FutarchyArbExecutorV5"

    print_section("Comprehensive Solidity Compilation Example")
    print(f"Contract: {contract_name}")

    # 1. Compile with all artifacts
    print_section("Step 1: Compile with comprehensive artifacts")
    print(f"Command: python3 scripts/compile_all.py --contract {contract_name}")
    print("\nThis generates:")
    print("  ✓ ABI (JSON interface)")
    print("  ✓ Bytecode (deployment + runtime)")
    print("  ✓ Assembly (EVM ASM)")
    print("  ✓ Opcodes (human-readable)")
    print("  ✓ Storage layout")
    print("  ✓ Method identifiers")
    print("  ✓ Abstract Syntax Tree")

    input("\nPress Enter to compile...")

    try:
        subprocess.run([
            "python3", "scripts/compile_all.py",
            "--contract", contract_name
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n⚠️  Compilation failed: {e}")
        return

    # 2. Show generated artifacts
    print_section("Step 2: Generated Artifacts")

    artifacts_dir = Path("artifacts")

    files_to_check = [
        ("ABI", artifacts_dir / "abi" / f"{contract_name}.json"),
        ("Method IDs", artifacts_dir / "abi" / f"{contract_name}.methods.txt"),
        ("Bytecode", artifacts_dir / "bytecode" / f"{contract_name}.hex"),
        ("Runtime", artifacts_dir / "bytecode" / f"{contract_name}.runtime.bin"),
        ("Assembly", artifacts_dir / "asm" / f"{contract_name}.asm"),
        ("Opcodes", artifacts_dir / "opcodes" / f"{contract_name}.opcodes"),
        ("Readable Opcodes", artifacts_dir / "opcodes" / f"{contract_name}.readable.txt"),
        ("Storage Layout", artifacts_dir / "storage" / f"{contract_name}.storage.json"),
        ("AST", artifacts_dir / "ast" / f"{contract_name}.ast.json"),
    ]

    for label, path in files_to_check:
        if path.exists():
            size = path.stat().st_size
            print(f"  ✓ {label:20s} {path} ({size:,} bytes)")
        else:
            print(f"  ✗ {label:20s} {path} (not found)")

    # 3. Bytecode analysis
    print_section("Step 3: Bytecode Analysis")

    runtime_path = artifacts_dir / "bytecode" / f"{contract_name}.runtime.bin"
    if runtime_path.exists():
        bytecode_hex = runtime_path.read_text().strip()
        bytecode_size = len(bytecode_hex) // 2

        print(f"Contract size: {bytecode_size:,} bytes")
        print(f"24KB limit: {24576:,} bytes")

        if bytecode_size > 24576:
            print("⚠️  Contract exceeds 24KB limit by {} bytes".format(bytecode_size - 24576))
            print("\nSize reduction strategies:")
            print("  1. Enable Via-IR: --via-ir (already enabled)")
            print("  2. Extract libraries")
            print("  3. Use proxy pattern")
        else:
            remaining = 24576 - bytecode_size
            percent = (bytecode_size / 24576) * 100
            print("✓ Within limit ({:.1f}% used, {:,} bytes remaining)".format(percent, remaining))

    # 4. Opcode analysis
    print_section("Step 4: Opcode Analysis (Gas Hints)")

    opcodes_path = artifacts_dir / "opcodes" / f"{contract_name}.opcodes"
    if opcodes_path.exists():
        opcodes = opcodes_path.read_text()

        sload_count = opcodes.count("SLOAD")
        sstore_count = opcodes.count("SSTORE")
        call_count = opcodes.count("CALL") + opcodes.count("STATICCALL") + opcodes.count("DELEGATECALL")

        print(f"SLOAD operations: {sload_count} (200 gas each)")
        print(f"SSTORE operations: {sstore_count} (20000 gas for new slot)")
        print(f"External calls: {call_count}")

        if sload_count > 10:
            print("\n💡 Optimization tip: Consider caching frequently read storage in memory")
        if sstore_count > 5:
            print("💡 Optimization tip: Batch storage updates to reduce SSTORE operations")

    # 5. Method identifiers
    print_section("Step 5: Function Selectors")

    methods_path = artifacts_dir / "abi" / f"{contract_name}.methods.txt"
    if methods_path.exists():
        methods = methods_path.read_text().strip()
        print("4-byte function selectors:")
        for line in methods.split('\n')[:10]:  # Show first 10
            if line.strip():
                print(f"  {line}")

        total_methods = len(methods.split('\n'))
        if total_methods > 10:
            print(f"  ... and {total_methods - 10} more")

    # 6. Next steps
    print_section("Next Steps")
    print("Deploy with pre-compiled artifacts:")
    print("  python3 scripts/deploy_executor_v5_precompiled.py")
    print("\nVerify on Gnosisscan:")
    print(f"  Use artifacts/bytecode/{contract_name}.bin")
    print("\nFormal verification (SMT):")
    print(f"  python3 scripts/compile_all.py --contract {contract_name} --smt")
    print("\nDetailed documentation:")
    print("  docs/BUILD_ARTIFACTS.md")

    print_section("Example Complete!")


if __name__ == "__main__":
    run_example()
