#!/usr/bin/env python3
"""
Comprehensive Solidity Compiler Script

Compiles all Solidity contracts and generates:
- ABI (JSON interface)
- Bytecode (deployment code)
- Runtime bytecode
- Assembly (ASM/opcodes)
- Storage layout
- Method identifiers
- AST (Abstract Syntax Tree)
- SMT (for formal verification)
- Opcodes (human-readable)

Usage:
    python scripts/compile_all.py [--contract CONTRACT_NAME] [--optimize] [--via-ir]
    
Examples:
    # Compile all contracts
    python scripts/compile_all.py
    
    # Compile specific contract with optimization
    python scripts/compile_all.py --contract FutarchyArbExecutorV5 --optimize --via-ir
    
    # Compile with SMT checker
    python scripts/compile_all.py --contract SafetyModule --smt
"""

import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional


class SolidityCompiler:
    """Compile Solidity contracts with comprehensive output generation"""
    
    def __init__(
        self,
        solc_version: str = "0.8.33",
        contracts_dir: str = "contracts",
        output_dir: str = "build",
        artifacts_dir: str = "artifacts"
    ):
        self.solc_version = solc_version
        self.contracts_dir = Path(contracts_dir)
        self.output_dir = Path(output_dir)
        self.artifacts_dir = Path(artifacts_dir)
        
        # Create output directories
        self.output_dir.mkdir(exist_ok=True)
        self.artifacts_dir.mkdir(exist_ok=True)
        
        # Subdirectories for different outputs
        (self.artifacts_dir / "abi").mkdir(exist_ok=True)
        (self.artifacts_dir / "bytecode").mkdir(exist_ok=True)
        (self.artifacts_dir / "asm").mkdir(exist_ok=True)
        (self.artifacts_dir / "opcodes").mkdir(exist_ok=True)
        (self.artifacts_dir / "storage").mkdir(exist_ok=True)
        (self.artifacts_dir / "ast").mkdir(exist_ok=True)
        (self.artifacts_dir / "smt").mkdir(exist_ok=True)
    
    def check_solc(self) -> bool:
        """Check if solc is installed and get version"""
        try:
            result = subprocess.run(
                ["solc", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✓ Solc version: {result.stdout.split()[1]}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("✗ solc not found. Install with: brew install solidity (macOS) or solc-select")
            return False
    
    def get_contract_files(self, contract_name: Optional[str] = None) -> List[Path]:
        """Get list of contract files to compile"""
        if contract_name:
            contract_file = self.contracts_dir / f"{contract_name}.sol"
            if not contract_file.exists():
                raise FileNotFoundError(f"Contract not found: {contract_file}")
            return [contract_file]
        else:
            # Get all .sol files
            return list(self.contracts_dir.glob("*.sol"))
    
    def compile_contract(
        self,
        contract_path: Path,
        optimize: bool = True,
        optimize_runs: int = 200,
        via_ir: bool = True,
        evm_version: str = "osaka",
        generate_smt: bool = False
    ) -> Dict:
        """
        Compile a single contract with all outputs
        
        Args:
            contract_path: Path to .sol file
            optimize: Enable optimizer
            optimize_runs: Number of optimizer runs
            via_ir: Use IR-based code generator
            evm_version: EVM version target
            generate_smt: Generate SMT-LIB2 output for verification
        
        Returns:
            Dictionary with compilation results
        """
        contract_name = contract_path.stem
        print(f"\n{'='*60}")
        print(f"Compiling: {contract_name}")
        print(f"{'='*60}")
        
        # Build solc command
        solc_cmd = [
            "solc",
            "--base-path", ".",
            "--include-path", "lib/solady",
            "--include-path", "lib/solady/src/utils/clz",
            "--include-path", "lib/solady/src/utils",
        ]
        
        # Optimization settings
        if optimize:
            solc_cmd.extend([
                "--optimize",
                "--optimize-runs", str(optimize_runs)
            ])
        
        if via_ir:
            solc_cmd.append("--via-ir")
        
        solc_cmd.extend([
            "--evm-version", evm_version,
        ])
        
        # Output selections
        output_selections = [
            "--abi",
            "--bin",
            "--bin-runtime",
            "--asm",
            "--opcodes",
            "--storage-layout",
            "--hashes",
            "--ast-compact-json",
        ]
        
        if generate_smt:
            output_selections.extend([
                "--model-checker-engine", "all",
                "--model-checker-targets", "all"
            ])
        
        solc_cmd.extend(output_selections)
        solc_cmd.append(str(contract_path))
        
        print(f"Command: {' '.join(solc_cmd)}")
        
        try:
            result = subprocess.run(
                solc_cmd,
                capture_output=True,
                text=True,
                check=True,
                cwd=Path.cwd()
            )
            
            # Parse output
            output = result.stdout
            
            # Extract sections
            sections = self._parse_solc_output(output, contract_name)
            
            # Save all artifacts
            self._save_artifacts(contract_name, sections)
            
            # Generate human-readable opcodes
            if "opcodes" in sections:
                self._generate_readable_opcodes(contract_name, sections["opcodes"])

            print("✓ Compilation successful")
            return sections

        except subprocess.CalledProcessError as e:
            print("✗ Compilation failed:")
            print(e.stderr)
            return {}
    
    def _parse_solc_output(self, output: str, contract_name: str) -> Dict[str, str]:
        """Parse solc output into sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in output.split('\n'):
            # Detect section headers
            if line.startswith('======'):
                if current_section and current_content:
                    sections[current_section] = '\n'.join(current_content).strip()
                    current_content = []
                
                # Parse section name
                if 'Binary:' in line:
                    current_section = 'bytecode'
                elif 'Runtime Bytecode:' in line:
                    current_section = 'runtime_bytecode'
                elif 'Contract JSON ABI' in line:
                    current_section = 'abi'
                elif 'Assembly:' in line:
                    current_section = 'asm'
                elif 'Opcodes:' in line:
                    current_section = 'opcodes'
                elif 'Storage Layout:' in line:
                    current_section = 'storage_layout'
                elif 'Function signatures:' in line:
                    current_section = 'method_identifiers'
                elif 'AST:' in line:
                    current_section = 'ast'
                else:
                    current_section = None
            elif current_section:
                current_content.append(line)
        
        # Save last section
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def _save_artifacts(self, contract_name: str, sections: Dict[str, str]):
        """Save all compilation artifacts to files"""
        
        # ABI (JSON)
        if "abi" in sections:
            abi_path = self.artifacts_dir / "abi" / f"{contract_name}.json"
            try:
                abi_json = json.loads(sections["abi"])
                abi_path.write_text(json.dumps(abi_json, indent=2))
                print(f"  ✓ ABI saved: {abi_path}")
            except json.JSONDecodeError:
                abi_path.write_text(sections["abi"])
                print("  ✓ ABI saved (raw): {}".format(abi_path))
        
        # Bytecode
        if "bytecode" in sections:
            bytecode_path = self.artifacts_dir / "bytecode" / f"{contract_name}.bin"
            bytecode_path.write_text(sections["bytecode"])
            
            # Also save with 0x prefix
            bytecode_hex_path = self.artifacts_dir / "bytecode" / f"{contract_name}.hex"
            bytecode_hex_path.write_text("0x" + sections["bytecode"])
            print("  ✓ Bytecode saved: {}".format(bytecode_path))
        
        # Runtime bytecode
        if "runtime_bytecode" in sections:
            runtime_path = self.artifacts_dir / "bytecode" / f"{contract_name}.runtime.bin"
            runtime_path.write_text(sections["runtime_bytecode"])
            print("  ✓ Runtime bytecode saved: {}".format(runtime_path))
        
        # Assembly
        if "asm" in sections:
            asm_path = self.artifacts_dir / "asm" / f"{contract_name}.asm"
            asm_path.write_text(sections["asm"])
            print("  ✓ Assembly saved: {}".format(asm_path))

        # Opcodes
        if "opcodes" in sections:
            opcodes_path = self.artifacts_dir / "opcodes" / f"{contract_name}.opcodes"
            opcodes_path.write_text(sections["opcodes"])
            print("  ✓ Opcodes saved: {}".format(opcodes_path))
            try:
                storage_json = json.loads(sections["storage_layout"])
                storage_path.write_text(json.dumps(storage_json, indent=2))
                print(f"  ✓ Storage layout saved: {storage_path}")
            except json.JSONDecodeError:
                storage_path.write_text(sections["storage_layout"])
        
        # Method identifiers
        if "method_identifiers" in sections:
            methods_path = self.artifacts_dir / "abi" / f"{contract_name}.methods.txt"
            methods_path.write_text(sections["method_identifiers"])
            print(f"  ✓ Method identifiers saved: {methods_path}")
        
        # AST
        if "ast" in sections:
            ast_path = self.artifacts_dir / "ast" / f"{contract_name}.ast.json"
            try:
                ast_json = json.loads(sections["ast"])
                ast_path.write_text(json.dumps(ast_json, indent=2))
                print(f"  ✓ AST saved: {ast_path}")
            except json.JSONDecodeError:
                ast_path.write_text(sections["ast"])
    
    def _generate_readable_opcodes(self, contract_name: str, opcodes: str):
        """Generate human-readable opcode breakdown"""
        
        # Split opcodes into individual instructions
        opcode_list = opcodes.split()
        
        # Create readable format with addresses
        readable = []
        address = 0
        
        for opcode in opcode_list:
            # Check if it's a PUSH instruction
            if opcode.startswith("PUSH"):
                push_size = int(opcode.replace("PUSH", ""))
                readable.append(f"{address:04x}: {opcode}")
                address += 1
                
                # Next values are the pushed bytes
                for i in range(push_size):
                    if len(opcode_list) > len(readable):
                        next_byte = opcode_list[len(readable)]
                        readable.append(f"      {next_byte}")
                        address += 1
            else:
                readable.append(f"{address:04x}: {opcode}")
                address += 1
        
        # Save readable opcodes
        readable_path = self.artifacts_dir / "opcodes" / f"{contract_name}.readable.txt"
        readable_path.write_text('\n'.join(readable))
        print(f"  ✓ Readable opcodes saved: {readable_path}")
    
    def compile_all(
        self,
        contract_name: Optional[str] = None,
        optimize: bool = True,
        via_ir: bool = True,
        generate_smt: bool = False
    ):
        """Compile all contracts or a specific one"""
        
        if not self.check_solc():
            return
        
        contract_files = self.get_contract_files(contract_name)
        
        print(f"\nFound {len(contract_files)} contract(s) to compile")
        
        results = {}
        for contract_file in contract_files:
            result = self.compile_contract(
                contract_file,
                optimize=optimize,
                via_ir=via_ir,
                generate_smt=generate_smt
            )
            results[contract_file.stem] = result
        
        # Generate summary
        self._generate_summary(results)
    
    def _generate_summary(self, results: Dict):
        """Generate compilation summary"""
        
        summary_path = self.artifacts_dir / "compilation_summary.json"
        
        summary = {
            "timestamp": subprocess.run(
                ["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                capture_output=True,
                text=True
            ).stdout.strip(),
            "solc_version": self.solc_version,
            "contracts": {}
        }
        
        for contract_name, sections in results.items():
            if sections:
                # Get bytecode size
                bytecode_size = len(sections.get("bytecode", "")) // 2
                
                summary["contracts"][contract_name] = {
                    "compiled": True,
                    "bytecode_size": bytecode_size,
                    "has_abi": "abi" in sections,
                    "has_asm": "asm" in sections,
                    "has_opcodes": "opcodes" in sections,
                    "has_storage_layout": "storage_layout" in sections
                }
            else:
                summary["contracts"][contract_name] = {
                    "compiled": False
                }
        
        summary_path.write_text(json.dumps(summary, indent=2))
        print(f"\n{'='*60}")
        print(f"Summary saved: {summary_path}")
        print(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive Solidity Compiler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compile all contracts
  python scripts/compile_all.py
  
  # Compile specific contract
  python scripts/compile_all.py --contract FutarchyArbExecutorV5
  
  # Compile with SMT checking
  python scripts/compile_all.py --contract SafetyModule --smt
  
  # Compile without optimization
  python scripts/compile_all.py --no-optimize
        """
    )
    
    parser.add_argument(
        '--contract',
        help='Specific contract to compile (without .sol extension)'
    )
    parser.add_argument(
        '--no-optimize',
        action='store_true',
        help='Disable optimizer'
    )
    parser.add_argument(
        '--no-via-ir',
        action='store_true',
        help='Disable IR-based code generator'
    )
    parser.add_argument(
        '--smt',
        action='store_true',
        help='Enable SMT checker for formal verification'
    )
    parser.add_argument(
        '--solc-version',
        default='0.8.33',
        help='Solc version (default: 0.8.33)'
    )
    
    args = parser.parse_args()
    
    compiler = SolidityCompiler(solc_version=args.solc_version)
    
    compiler.compile_all(
        contract_name=args.contract,
        optimize=not args.no_optimize,
        via_ir=not args.no_via_ir,
        generate_smt=args.smt
    )


if __name__ == "__main__":
    main()
