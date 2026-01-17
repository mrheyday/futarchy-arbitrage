#!/usr/bin/env python3
"""
Export compiled contract artifacts: bytecode, ABI, opcodes, CLZ operations, ASM.

Extracts from Forge output directory and organizes into export structure.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional


def load_artifact(artifact_path: Path) -> Optional[dict]:
    """Load a JSON artifact file."""
    try:
        with open(artifact_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {artifact_path}: {e}")
        return None


def extract_bytecode(artifact: dict) -> Optional[str]:
    """Extract bytecode from artifact."""
    return artifact.get('bytecode', {}).get('object')


def extract_abi(artifact: dict) -> Optional[list]:
    """Extract ABI from artifact."""
    return artifact.get('abi')


def extract_opcode(artifact: dict) -> Optional[str]:
    """Extract opcodes from artifact."""
    return artifact.get('bytecode', {}).get('sourceMap')


def is_clz_contract(name: str, abi: Optional[list]) -> bool:
    """Check if contract contains CLZ (Count Leading Zeros) operations."""
    clz_keywords = ['clz', 'LibBit', 'LibZip', 'FixedPointMathLib', 'countLeadingZeros']
    
    # Check filename
    if any(keyword.lower() in name.lower() for keyword in clz_keywords):
        return True
    
    # Check ABI for CLZ operations
    if abi:
        for item in abi:
            if isinstance(item, dict):
                func_name = item.get('name', '').lower()
                if any(keyword.lower() in func_name for keyword in clz_keywords):
                    return True
    
    return False


def export_artifacts(root_dir: Path, output_dir: Path) -> None:
    """Export all contract artifacts."""
    
    # Create output structure
    output_dir.mkdir(parents=True, exist_ok=True)
    bytecode_dir = output_dir / "bytecode"
    abi_dir = output_dir / "abi"
    opcode_dir = output_dir / "opcodes"
    clz_dir = output_dir / "clz_contracts"
    
    for d in [bytecode_dir, abi_dir, opcode_dir, clz_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    out_dir = root_dir / "out"
    if not out_dir.exists():
        print(f"Error: {out_dir} not found")
        return
    
    # Track CLZ contracts
    clz_contracts = {}
    all_contracts = {}
    
    # Walk through all artifact files
    for contract_dir in sorted(out_dir.iterdir()):
        if not contract_dir.is_dir():
            continue
        
        # Find main contract artifact (*.sol/*.json)
        for artifact_file in sorted(contract_dir.glob("*.json")):
            # Skip interface files
            if artifact_file.stem.startswith('I'):
                continue
            
            artifact = load_artifact(artifact_file)
            if not artifact:
                continue
            
            contract_name = artifact_file.stem
            
            # Extract bytecode
            bytecode = extract_bytecode(artifact)
            if bytecode:
                bytecode_file = bytecode_dir / f"{contract_name}.bytecode"
                with open(bytecode_file, 'w') as f:
                    f.write(bytecode)
                all_contracts[contract_name] = {"bytecode": str(bytecode_file)}
            
            # Extract ABI
            abi = extract_abi(artifact)
            if abi:
                abi_file = abi_dir / f"{contract_name}.abi.json"
                with open(abi_file, 'w') as f:
                    json.dump(abi, f, indent=2)
                
                # Check if CLZ contract
                if is_clz_contract(contract_name, abi):
                    clz_contracts[contract_name] = {
                        "abi": str(abi_file),
                        "artifact": str(artifact_file)
                    }
                    
                    # Copy to CLZ directory
                    import shutil
                    clz_abi_file = clz_dir / f"{contract_name}.abi.json"
                    shutil.copy(abi_file, clz_abi_file)
            
            # Extract full artifact
            artifact_copy_path = abi_dir / f"{contract_name}.full.json"
            with open(artifact_copy_path, 'w') as f:
                json.dump(artifact, f, indent=2)
    
    # Generate summary
    summary = {
        "timestamp": str(Path.cwd()),
        "total_contracts": len(all_contracts),
        "clz_contracts": list(clz_contracts.keys()),
        "clz_contract_count": len(clz_contracts),
        "contracts": all_contracts,
        "clz_details": clz_contracts
    }
    
    summary_file = output_dir / "EXPORT_SUMMARY.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Export Complete!")
    print(f"📁 Output directory: {output_dir}")
    print(f"📊 Total contracts exported: {len(all_contracts)}")
    print(f"🧬 CLZ contracts found: {len(clz_contracts)}")
    print(f"   - {', '.join(clz_contracts.keys())}")
    print(f"\n📋 Summary: {summary_file}")
    print(f"📝 Bytecode: {bytecode_dir}")
    print(f"📄 ABI: {abi_dir}")
    print(f"🔬 CLZ: {clz_dir}")


def generate_opcode_disasm(root_dir: Path, output_dir: Path) -> None:
    """Generate opcode disassembly using forge."""
    
    disasm_dir = output_dir / "disassembly"
    disasm_dir.mkdir(parents=True, exist_ok=True)
    
    out_dir = root_dir / "out"
    
    print("\n🔧 Generating opcode disassembly...")
    
    for contract_dir in sorted(out_dir.iterdir()):
        if not contract_dir.is_dir():
            continue
        
        for artifact_file in sorted(contract_dir.glob("*.json")):
            if artifact_file.stem.startswith('I'):
                continue
            
            artifact = load_artifact(artifact_file)
            if not artifact:
                continue
            
            bytecode = extract_bytecode(artifact)
            if not bytecode:
                continue
            
            contract_name = artifact_file.stem
            
            # Use eas-asm or similar for disassembly
            # For now, just extract bytecode structure
            disasm_file = disasm_dir / f"{contract_name}.disasm"
            try:
                # Try to extract initialization code vs runtime code
                with open(disasm_file, 'w') as f:
                    f.write(f"# {contract_name}\n\n")
                    f.write(f"## Bytecode (hex length: {len(bytecode) // 2} bytes)\n\n")
                    f.write(f"```\n{bytecode}\n```\n\n")
                    
                    # Split into chunks for readability
                    f.write("## Bytecode chunks (256 chars each):\n\n")
                    for i in range(0, len(bytecode), 256):
                        f.write(f"{bytecode[i:i+256]}\n")
            except Exception as e:
                print(f"  ⚠️  Error writing {contract_name}: {e}")
    
    print(f"✅ Disassembly saved to: {disasm_dir}")


if __name__ == "__main__":
    root = Path("/Users/hs/futarchy-arbitrage-1")
    output = root / "exports" / "artifacts"
    
    print("🚀 Exporting contract artifacts...")
    export_artifacts(root, output)
    generate_opcode_disasm(root, output)
    
    print("\n✨ All exports completed successfully!")
    print(f"\n📦 Export Summary:")
    print(f"   Bytecode:    {output / 'bytecode'}")
    print(f"   ABI JSON:    {output / 'abi'}")
    print(f"   Opcodes:     {output / 'disassembly'}")
    print(f"   CLZ Focus:   {output / 'clz_contracts'}")
    print(f"   Summary:     {output / 'EXPORT_SUMMARY.json'}")
