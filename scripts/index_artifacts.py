#!/usr/bin/env python3
"""
Index all Solidity artifacts: bytecode, ABI, ASM, opcodes, storage layout.
Outputs a comprehensive index JSON for off-chain storage.
"""
import json
import os
import re
from pathlib import Path
from typing import Any

# Production contracts to index
CONTRACTS = [
    "FutarchyArbExecutorV5",
    "FutarchyArbExecutorV4",
    "FutarchyArbExecutorV3",
    "FutarchyArbitrageExecutorV2",
    "PectraWrapper",
    "SafetyModule",
    "InstitutionalSolverSystem",
    "PredictionArbExecutorV1",
    "FutarchyBatchExecutor",
    "FutarchyBatchExecutorV2",
]

# Solady CLZ library contracts
CLZ_CONTRACTS = [
    "LibBit",
    "LibSort",
    "FixedPointMathLib",
    "SafeCastLib",
]

# EVM Opcode reference
OPCODE_NAMES = {
    0x00: "STOP", 0x01: "ADD", 0x02: "MUL", 0x03: "SUB", 0x04: "DIV",
    0x10: "LT", 0x11: "GT", 0x14: "EQ", 0x15: "ISZERO", 0x16: "AND",
    0x17: "OR", 0x18: "XOR", 0x19: "NOT", 0x1a: "BYTE", 0x1b: "SHL",
    0x1c: "SHR", 0x1d: "SAR", 0x20: "KECCAK256",
    0x30: "ADDRESS", 0x31: "BALANCE", 0x32: "ORIGIN", 0x33: "CALLER",
    0x34: "CALLVALUE", 0x35: "CALLDATALOAD", 0x36: "CALLDATASIZE",
    0x37: "CALLDATACOPY", 0x38: "CODESIZE", 0x39: "CODECOPY",
    0x3a: "GASPRICE", 0x3b: "EXTCODESIZE", 0x3c: "EXTCODECOPY",
    0x3d: "RETURNDATASIZE", 0x3e: "RETURNDATACOPY", 0x3f: "EXTCODEHASH",
    0x40: "BLOCKHASH", 0x41: "COINBASE", 0x42: "TIMESTAMP", 0x43: "NUMBER",
    0x50: "POP", 0x51: "MLOAD", 0x52: "MSTORE", 0x53: "MSTORE8",
    0x54: "SLOAD", 0x55: "SSTORE", 0x56: "JUMP", 0x57: "JUMPI",
    0x58: "PC", 0x59: "MSIZE", 0x5a: "GAS", 0x5b: "JUMPDEST",
    0x5f: "PUSH0", 0x60: "PUSH1", 0x7f: "PUSH32",
    0x80: "DUP1", 0x8f: "DUP16", 0x90: "SWAP1", 0x9f: "SWAP16",
    0xa0: "LOG0", 0xa4: "LOG4",
    0xf0: "CREATE", 0xf1: "CALL", 0xf2: "CALLCODE", 0xf3: "RETURN",
    0xf4: "DELEGATECALL", 0xf5: "CREATE2", 0xfa: "STATICCALL",
    0xfd: "REVERT", 0xfe: "INVALID", 0xff: "SELFDESTRUCT",
}

OUT_DIR = Path("out")
ARTIFACTS_DIR = Path("artifacts/indexed")


def extract_opcodes(bytecode: str) -> dict[str, Any]:
    """Extract opcodes from bytecode hex string with statistics."""
    if not bytecode or bytecode == "0x":
        return {"opcodes": [], "stats": {}}

    # Remove 0x prefix
    code = bytecode[2:] if bytecode.startswith("0x") else bytecode

    opcodes = []
    stats: dict[str, int] = {}
    i = 0
    while i < len(code):
        if i + 2 > len(code):
            break
        op = int(code[i:i+2], 16)
        op_name = OPCODE_NAMES.get(op, f"0x{op:02x}")
        opcodes.append(op_name)
        stats[op_name] = stats.get(op_name, 0) + 1

        # Skip PUSH data
        if 0x60 <= op <= 0x7f:
            push_bytes = op - 0x5f
            i += 2 + (push_bytes * 2)
        else:
            i += 2

    # Sort stats by frequency
    sorted_stats = dict(sorted(stats.items(), key=lambda x: -x[1])[:20])

    return {
        "opcodes_sample": opcodes[:100],
        "opcode_count": len(opcodes),
        "unique_opcodes": len(stats),
        "opcode_frequency": sorted_stats,
    }


def extract_function_selectors(abi: list[dict]) -> dict[str, str]:
    """Extract function selectors from ABI."""
    from hashlib import sha3_256
    
    selectors = {}
    for item in abi:
        if item.get("type") == "function":
            name = item["name"]
            inputs = ",".join(i["type"] for i in item.get("inputs", []))
            sig = f"{name}({inputs})"
            # Use keccak256 (we'll compute manually)
            selectors[name] = sig
    return selectors


def load_contract_artifact(name: str) -> dict[str, Any] | None:
    """Load a contract's compiled artifact."""
    artifact_path = OUT_DIR / f"{name}.sol" / f"{name}.json"
    if not artifact_path.exists():
        print(f"  ⚠️  {name}: artifact not found")
        return None
    
    with open(artifact_path) as f:
        return json.load(f)


def index_contract(name: str) -> dict[str, Any] | None:
    """Create comprehensive index for a contract."""
    artifact = load_contract_artifact(name)
    if not artifact:
        return None
    
    # Extract components
    abi = artifact.get("abi", [])
    bytecode = artifact.get("bytecode", {})
    deployed_bytecode = artifact.get("deployedBytecode", {})
    method_ids = artifact.get("methodIdentifiers", {})
    storage_layout = artifact.get("storageLayout", {})
    metadata = artifact.get("metadata", {})
    
    # Get bytecode strings
    creation_code = bytecode.get("object", "") if isinstance(bytecode, dict) else ""
    runtime_code = deployed_bytecode.get("object", "") if isinstance(deployed_bytecode, dict) else ""
    
    # Get ASM
    asm = deployed_bytecode.get("assembly", "") if isinstance(deployed_bytecode, dict) else ""
    
    # Extract opcode analysis
    opcode_analysis = extract_opcodes(runtime_code)

    index = {
        "name": name,
        "abi": abi,
        "abi_function_count": len([a for a in abi if a.get("type") == "function"]),
        "abi_event_count": len([a for a in abi if a.get("type") == "event"]),
        "abi_error_count": len([a for a in abi if a.get("type") == "error"]),
        "bytecode": {
            "creation": creation_code[:200] + "..." if len(creation_code) > 200 else creation_code,
            "creation_size": len(creation_code) // 2 if creation_code else 0,
            "runtime": runtime_code[:200] + "..." if len(runtime_code) > 200 else runtime_code,
            "runtime_size": len(runtime_code) // 2 if runtime_code else 0,
            "creation_full": creation_code,
            "runtime_full": runtime_code,
        },
        "opcodes": opcode_analysis,
        "method_identifiers": method_ids,
        "storage_layout": storage_layout,
        "asm": asm if isinstance(asm, str) else str(asm),
        "metadata": {
            "compiler": metadata.get("compiler", {}).get("version", "unknown") if isinstance(metadata, dict) else "unknown",
            "optimizer": metadata.get("settings", {}).get("optimizer", {}) if isinstance(metadata, dict) else {},
            "evm_version": metadata.get("settings", {}).get("evmVersion", "unknown") if isinstance(metadata, dict) else "unknown",
        }
    }

    return index


def main():
    """Build complete artifact index."""
    print("=== Indexing Solidity Artifacts ===\n")

    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    master_index = {
        "version": "1.0.0",
        "generated": __import__("datetime").datetime.now().isoformat(),
        "contracts": {},
        "clz_libraries": {},
        "summary": {
            "total_contracts": 0,
            "total_functions": 0,
            "total_events": 0,
            "total_errors": 0,
            "total_bytecode_size": 0,
        }
    }

    # Index main contracts
    print("== Main Contracts ==")
    for name in CONTRACTS:
        print(f"Indexing {name}...")
        index = index_contract(name)
        if index:
            master_index["contracts"][name] = index
            master_index["summary"]["total_contracts"] += 1
            master_index["summary"]["total_functions"] += index["abi_function_count"]
            master_index["summary"]["total_events"] += index["abi_event_count"]
            master_index["summary"]["total_errors"] += index["abi_error_count"]
            master_index["summary"]["total_bytecode_size"] += index["bytecode"]["runtime_size"]

            # Save individual contract index
            with open(ARTIFACTS_DIR / f"{name}.json", "w") as f:
                json.dump(index, f, indent=2)
            print(f"  ✅ {name}: {index['bytecode']['runtime_size']}B, {index['abi_function_count']} fn, {index['opcodes']['opcode_count']} ops")

    # Index CLZ/Solady libraries
    print("\n== Solady CLZ Libraries ==")
    for name in CLZ_CONTRACTS:
        print(f"Indexing {name}...")
        index = index_contract(name)
        if index:
            master_index["clz_libraries"][name] = {
                "name": name,
                "runtime_size": index["bytecode"]["runtime_size"],
                "opcodes": index["opcodes"],
            }
            print(f"  ✅ {name}: {index['bytecode']['runtime_size']}B")

    # Save master index
    with open(ARTIFACTS_DIR / "master_index.json", "w") as f:
        json.dump(master_index, f, indent=2)

    # Save lightweight summary for off-chain
    summary = {
        "version": master_index["version"],
        "generated": master_index["generated"],
        "summary": master_index["summary"],
        "contract_list": list(master_index["contracts"].keys()),
        "clz_libraries": list(master_index["clz_libraries"].keys()),
    }
    with open(ARTIFACTS_DIR / "offchain_summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print(f"\n✅ Indexed {master_index['summary']['total_contracts']} contracts")
    print(f"   Total functions: {master_index['summary']['total_functions']}")
    print(f"   Total events: {master_index['summary']['total_events']}")
    print(f"   Total errors: {master_index['summary']['total_errors']}")
    print(f"   Total bytecode: {master_index['summary']['total_bytecode_size']} bytes")
    print(f"   CLZ libraries: {len(master_index['clz_libraries'])}")
    print(f"   Output: {ARTIFACTS_DIR}/")


if __name__ == "__main__":
    main()

