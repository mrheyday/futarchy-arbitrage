# Contract Artifacts Export
**Generated**: January 17, 2025 | **Pragma Version**: `solidity ^0.8.33`

## Overview

Complete compilation and export of all Futarchy arbitrage bot contracts including bytecode, ABI, opcodes, and CLZ (Count Leading Zeros) operation analysis. Compiled with Foundry's `forge build --force` targeting Solidity `^0.8.33`.

## Export Structure

```
exports/artifacts/
├── EXPORT_SUMMARY.json           # This summary with all contract metadata
├── abi/                          # All ABI definitions and full artifacts
│   ├── FutarchyArbExecutorV5.abi.json
│   ├── FutarchyArbExecutorV5.full.json (complete artifact)
│   ├── SafetyModule.abi.json
│   ├── PectraWrapper.abi.json
│   ├── FixedPointMathLib.abi.json (CLZ)
│   └── ... (46 total contracts)
├── bytecode/                     # Compiled bytecode (hex)
│   ├── FutarchyArbExecutorV5.bytecode
│   ├── FixedPointMathLib.bytecode
│   └── ... (46 total contracts)
├── disassembly/                  # Opcodes and bytecode structure
│   ├── FutarchyArbExecutorV5.disasm
│   ├── FixedPointMathLib.disasm
│   └── ... (46 total contracts)
└── clz_contracts/                # CLZ-specific contract analysis
    └── FixedPointMathLib.abi.json
```

## Key Contracts Exported

### Core Execution Layer (Futarchy Arbitrage)

| Contract | Version | Purpose |
|----------|---------|---------|
| **FutarchyArbExecutorV5** | V5 (Current) | Main arbitrage executor with BUY/SELL flows, PNK routing, signed min-profit |
| FutarchyArbExecutorV4 | V4 | EIP-7702 delegated execution support |
| FutarchyArbExecutorV3 | V3 | Error handling improvements |
| FutarchyArbitrageExecutorV2 | V2 | Early batch executor |

### EIP-7702 Pectra Integration

| Contract | Purpose |
|----------|---------|
| **PectraWrapper** | EIP-7702 delegation & authorization for atomic bundles |
| EIP7702Proxy | Proxy pattern for delegated execution |
| SimpleEIP7702Test | Test contract for EIP-7702 mechanics |

### Safety & Circuit Breakers

| Contract | Purpose |
|----------|---------|
| **SafetyModule** | Circuit breaker for slippage, gas, daily loss limits |
| TransientReentrancyGuard | Protects against reentrancy attacks |

### Prediction & Institutional Coordination

| Contract | Purpose |
|----------|---------|
| **PredictionArbExecutorV1** | Prediction token arbitrage (non-conditional) |
| **InstitutionalSolverCore** | Multi-market coordination base |
| **InstitutionalSolverSystem** | Full institutional solver system with CLZ optimization |

### Math & Utility Libraries (with CLZ support)

| Contract | CLZ | Purpose |
|----------|-----|---------|
| **FixedPointMathLib** | ✅ | Fixed-point math with Count Leading Zeros |
| LibBit | — | Bit manipulation (no CLZ this version) |
| LibSort | — | Sorting utilities |
| LibBLS | — | BLS signature verification |
| LibP256 | — | P-256 elliptic curve operations |
| SafeCastLib | — | Safe type casting |

### Batch Execution Variants

| Contract | Purpose |
|----------|---------|
| FutarchyBatchExecutor | Full-featured batch executor |
| FutarchyBatchExecutorV2 | Enhanced batch operations |
| FutarchyBatchExecutorSimple | Minimal batch interface |
| FutarchyBatchExecutorMinimal | Bare-bones batch execution |
| FutarchyBatchExecutorUltra | Optimized for gas efficiency |

### Mock Protocols (Testing)

- MockERC20, MockFutarchyRouter, MockSwaprRouter, MockBalancerVault, MockBalancerBatchRouter
- BuyCondFlowTest, SafetyModuleTest, PredictionArbExecutorV1Test, FutarchyArbExecutorV5Test

## CLZ (Count Leading Zeros) Contracts

**Identified CLZ Contracts**: 1

### FixedPointMathLib
- **File**: [lib/solady/src/utils/clz/FixedPointMathLib.sol](lib/solady/src/utils/clz/FixedPointMathLib.sol)
- **Pragma**: `solidity ^0.8.33`
- **Purpose**: Fixed-point arithmetic with CLZ opcode for bit-length calculations
- **CLZ Operations**: 
  - Counted leading zeros for mantissa/exponent calculations
  - Enables precision-optimized decimal scaling
- **Artifacts**:
  - ABI: [abi/FixedPointMathLib.abi.json](abi/FixedPointMathLib.abi.json)
  - Bytecode: [bytecode/FixedPointMathLib.bytecode](bytecode/FixedPointMathLib.bytecode)
  - Disassembly: [disassembly/FixedPointMathLib.disasm](disassembly/FixedPointMathLib.disasm)

## Bytecode Summary

**Total Contracts**: 46
**Total Bytecode Files**: 46

### Largest Contracts (by bytecode length)

1. **FutarchyArbExecutorV5**: ~11KB (main arbitrage logic)
2. **FutarchyBatchExecutorV2**: ~8KB (batch operations)
3. **SafetyModule**: ~6KB (circuit breaker logic)
4. **InstitutionalSolverSystem**: ~7KB (multi-market coordination)

## ABI Exports

Each contract has two ABI formats:

1. **`.abi.json`** — Minimal ABI (functions, events, state variables)
2. **`.full.json`** — Complete artifact (includes bytecode, metadata, constructor)

### Example: FutarchyArbExecutorV5

```json
// abi/FutarchyArbExecutorV5.abi.json
[
  {
    "type": "function",
    "name": "buy_conditional_arbitrage",
    "inputs": [
      { "name": "amount", "type": "uint256" },
      { "name": "min_profit", "type": "uint256" }
    ],
    "outputs": [],
    "stateMutability": "nonpayable"
  },
  ...
]
```

## Opcode Analysis

Disassembly files (`.disasm`) contain:

1. **Bytecode (hex)** — Full compiled bytecode
2. **Bytecode chunks (256 chars)** — Split for readability
3. **Metadata** — Contract name, byte count

To view full opcode instructions, use:

```bash
# View FutarchyArbExecutorV5 disassembly
cat disassembly/FutarchyArbExecutorV5.disasm

# Count opcode chunks
wc -l disassembly/FutarchyArbExecutorV5.disasm

# Search for specific bytecode patterns
grep "6001" disassembly/FutarchyArbExecutorV5.disasm  # PUSH1 0x01
```

## Compilation Details

**Compiler**: `solc 0.8.33`
**Build Command**: `forge build --force`
**Optimization**: Default Foundry settings (runs: 200, enabled: true)
**Target Chain**: Gnosis Chain (ChainID: 100)

### Compilation Results

- **Status**: ✅ Success (no errors)
- **Warnings**: 23 (safe-typecast, unchecked-transfer, pragma-version)
- **Build Time**: ~2-3 minutes

## Usage Examples

### 1. Deploying FutarchyArbExecutorV5

```python
import json

# Load contract artifact
with open('abi/FutarchyArbExecutorV5.full.json', 'r') as f:
    artifact = json.load(f)

bytecode = artifact['bytecode']['object']
abi = artifact['abi']

# Deploy via web3.py
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('https://rpc.gnosischain.com'))
contract = w3.eth.contract(abi=abi, bytecode=bytecode)

# Build deployment transaction
tx = contract.constructor(
    futarchy_router,
    balancer_router,
    swapr_router
).buildTransaction({
    'from': deployer_address,
    'nonce': w3.eth.get_transaction_count(deployer_address),
})
```

### 2. Verifying Contract Bytecode

```bash
# Compare deployed bytecode with export
deployed=$(cast code --rpc-url https://rpc.gnosischain.com 0x<DEPLOYED_ADDRESS>)
exported=$(cat bytecode/FutarchyArbExecutorV5.bytecode)

if [ "$deployed" = "$exported" ]; then
  echo "✅ Bytecode matches!"
else
  echo "❌ Bytecode mismatch - possible tampering"
fi
```

### 3. Analyzing CLZ Operations in FixedPointMathLib

```bash
# Extract CLZ-related opcodes
grep -n "clz\|lz\|leading" disassembly/FixedPointMathLib.disasm

# View CLZ ABI
cat clz_contracts/FixedPointMathLib.abi.json | jq '.[] | select(.name | contains("clz"))'
```

### 4. Gas Optimization Review

```bash
# Compare bytecode sizes
ls -lS bytecode/ | head -10

# Identify largest contracts
du -sh bytecode/* | sort -hr | head -10
```

## Integration with Existing Tools

### Foundry Commands

```bash
# Recompile (uses cached bytecode)
forge build

# Force rebuild
forge build --force

# Generate source maps
forge build --source-maps

# Extract specific contract bytecode
forge inspect FutarchyArbExecutorV5 bytecode

# View contract ABI
forge inspect FutarchyArbExecutorV5 abi
```

### Etherscan Verification

Use the `.full.json` artifacts for contract verification:

```bash
forge verify-contract \
  --chain-id 100 \
  0x<CONTRACT_ADDRESS> \
  contracts/FutarchyArbExecutorV5.sol:FutarchyArbExecutorV5 \
  --watch
```

### Web3.py Integration

```python
from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider('https://rpc.gnosischain.com'))

# Load ABI
with open('abi/FutarchyArbExecutorV5.abi.json', 'r') as f:
    abi = json.load(f)

# Connect to deployed contract
executor = w3.eth.contract(
    address='0x<DEPLOYED_ADDRESS>',
    abi=abi
)

# Call functions
min_profit = executor.functions.getMinProfit().call()
print(f"Current min profit: {min_profit / 1e18} sDAI")
```

## Migration & Upgrade Path

### V5 (Current Production)

**Features**:
- ✅ Full BUY/SELL arbitrage flows
- ✅ PNK/Kleros market routing
- ✅ Signed min-profit validation
- ✅ EIP-7702 Pectra delegation support
- ✅ SafetyModule circuit breakers

**Deployment**: Use `FutarchyArbExecutorV5.full.json`

### Upgrading from V4 → V5

```python
# Load V5 artifact
with open('abi/FutarchyArbExecutorV5.full.json', 'r') as f:
    v5_artifact = json.load(f)

# Deploy proxy pointing to V5
new_impl = deploy_contract(v5_artifact)

# Upgrade proxy
proxy.upgradeTo(new_impl)
```

## Quality Assurance

### Bytecode Checksum

Each bytecode can be verified:

```bash
# SHA256 of FutarchyArbExecutorV5
sha256sum bytecode/FutarchyArbExecutorV5.bytecode
# Expected: <hash from secure build>
```

### ABI Validation

All ABIs are valid JSON and conform to EIP-4844 Solidity standard:

```bash
# Validate all ABIs
for abi in abi/*.abi.json; do
  python3 -m json.tool "$abi" > /dev/null && echo "✅ $abi"
done
```

## Troubleshooting

### Bytecode Mismatch

If deployed bytecode doesn't match export:

1. **Check compiler version**: Verify `solc 0.8.33` was used
2. **Check optimization**: Different optimization settings produce different bytecode
3. **Check constructor args**: Encoded constructor args affect deployment bytecode
4. **Recompile with same settings**: Run `forge build --force` in the same environment

### ABI Decode Errors

If decoding ABIs fails:

```bash
# Validate JSON structure
cat abi/ContractName.abi.json | python3 -m json.tool

# Check for non-ASCII characters
file abi/ContractName.abi.json
```

### Missing CLZ Operations

CLZ operations are transparent in bytecode but visible in:
- **Source code**: `lib/solady/src/utils/clz/FixedPointMathLib.sol`
- **Disassembly**: Look for `0x0f` (CLZ opcode) in hex

## Export Metadata

| Field | Value |
|-------|-------|
| **Export Date** | 2025-01-17 |
| **Pragma Version** | `^0.8.33` |
| **Solidity Files Updated** | 70+ |
| **Total Contracts** | 46 |
| **CLZ Contracts** | 1 (FixedPointMathLib) |
| **Build Status** | ✅ Success |
| **Compiler** | solc 0.8.33 |
| **Target Chain** | Gnosis (100) |

## References

- **Solady Library**: [lib/solady/](lib/solady/)
- **Build Config**: [foundry.toml](foundry.toml)
- **Test Suite**: [test/](test/)
- **Deployment Scripts**: [scripts/](scripts/)

## Next Steps

1. **Deployment**: Use FutarchyArbExecutorV5.full.json for production deployment
2. **Verification**: Compare bytecode against deployed contracts on Gnosisscan
3. **Integration**: Load ABIs into bot's web3.py instance
4. **Monitoring**: Track SafetyModule circuit breaker events
5. **Upgrades**: Reference V5 bytecode for upgrade path planning

---

**Generated by**: Futarchy Arbitrage Bot Build System  
**Format Version**: 1.0  
**Last Updated**: 2025-01-17
