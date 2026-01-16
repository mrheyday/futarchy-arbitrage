# Futarchy Arbitrage - Complete API Map

**Generated:** 2026-01-16  
**Compiler:** Solc 0.8.33 with Via-IR, Osaka EVM  
**Optimizer:** 200 runs  
**Total Contracts:** 15 Solidity files  
**Total Scripts:** 49 Python files

---

## Contract API Reference

### FutarchyArbExecutorV5.sol

**Purpose:** Main arbitrage executor with sDAI↔WETH↔PNK routing support (Balancer Vault + Swapr)

**Function Signatures:**

| Function | Selector | Description |
|----------|----------|-------------|
| `buyPnkWithSdai(uint256,uint256,uint256)` | `ce12e70d` | Buy PNK with sDAI via Balancer→Swapr route |
| `sellPnkForSdai(uint256,uint256,uint256)` | `ea9f3f09` | Sell PNK for sDAI via Swapr→Balancer route |
| `buy_conditional_arbitrage_balancer(...)` | `de309fc3` | BUY flow: split sDAI → swap conditionals → merge |
| `sell_conditional_arbitrage_balancer(...)` | `d4b21c33` | SELL flow: buy → split → swap conditionals → merge |
| `buy_conditional_arbitrage_pnk(...)` | `de57a0ae` | BUY flow for PNK markets |
| `sell_conditional_arbitrage_pnk(...)` | `e7610d68` | SELL flow for PNK markets |
| `owner()` | `8da5cb5b` | Returns contract owner |
| `transferOwnership(address)` | `f2fde38b` | Transfer ownership |
| `sweepToken(address,address)` | `258836fe` | Recover stuck tokens |
| `withdrawETH(address,uint256)` | `4782f779` | Withdraw ETH |
| `withdrawToken(address,address,uint256)` | `01e33667` | Withdraw specific token amount |

**Deployment:** `deployments/deployment_executor_v5_1755543275.json`

**Key Features:**
- Multi-hop routing: sDAI → WETH (Balancer Vault) → PNK (Swapr v2)
- Signed min profit validation
- Gas-optimized with unchecked loops
- Custom errors (0.8.33 best practice)

---

### FutarchyArbExecutorV4.sol

**Purpose:** EIP-7702 delegation executor with bundled execution

**Function Signatures:**

| Function | Selector | Description |
|----------|----------|-------------|
| `buy_conditional_arbitrage(...)` | `e4d30e3d` | Atomic BUY flow (complex struct) |
| `runBuy(...)` | `5f66c633` | Execute BUY arbitrage |
| `runSell(...)` | `9862d8f7` | Execute SELL arbitrage |
| `execute10(address[10],bytes[10],uint256)` | `f75be35c` | Batch execute up to 10 calls |
| `executeOne(address,bytes)` | `3e16b19c` | Single delegatecall execution |

**Deployment:** `deployment_executor_v4_1754933845.json`

**Key Features:**
- EIP-7702 delegation support
- Batch execution (up to 10 calls)
- Complex struct-based parameters

---

### PredictionArbExecutorV1.sol

**Purpose:** Prediction market arbitrage (yes+no price sum exploitation)

**Function Signatures:**

| Function | Selector | Description |
|----------|----------|-------------|
| `buy_conditional_arbitrage(...)` | `2b4ed6fa` | BUY when yes+no price < 1 |
| `sell_conditional_arbitrage(...)` | `50e2e7a8` | SELL when yes+no price > 1 |
| `owner()` | `8da5cb5b` | Returns contract owner |
| `transferOwnership(address)` | `f2fde38b` | Transfer ownership |
| `sweepToken(address,address)` | `258836fe` | Recover stuck tokens |

**Deployment:** `deployments/deployment_prediction_arb_v1_1755903555.json`

**Key Features:**
- On-chain price sum detection
- Automatic side determination
- Signed min profit parameter

---

### InstitutionalSolverSystem.sol

**Purpose:** Advanced institutional solver with CLZ optimizations, auction economics, reputation, flashloans

**Function Signatures:**

| Function | Selector | Description |
|----------|----------|-------------|
| `submitIntent(uint256,bytes)` | - | Submit intent for resolution |
| `resolveIntent(uint256,address,bytes)` | - | Resolve intent with ZK/MEV checks |
| `batchResolve(uint256[],address[])` | `424f84a7` | Batch resolve multiple intents |
| `openAuction(uint256)` | - | Open auction for bids |
| `closeAuction(uint256)` | `236ed8f3` | Close auction |
| `commitBid(uint256,bytes32)` | - | Commit bid hash |
| `revealBid(uint256,uint256,bytes32)` | - | Reveal bid value |
| `settleAuction(uint256,address[])` | - | Settle auction with LibSort ranking |
| `updateReputation(address,int256)` | - | Update solver reputation |
| `getReputation(address)` | - | Get solver reputation |
| `getTopSolversByReputation(address[],uint256)` | - | Rank solvers by reputation (LibSort) |
| `executeFlashloan(address,uint256,bytes)` | - | Multi-provider flashloan abstraction |
| `addFlashloanProvider(address)` | `745a1b2a` | Add flashloan provider |
| `setComplianceFlags(address,uint256)` | - | Set compliance flags (KYC/AML) |
| `checkCompliance(address,uint256)` | `ed3310bd` | Check compliance status |
| `depositToTreasury(address,uint256)` | - | Deposit to treasury |
| `withdrawFromTreasury(address,uint256,address)` | - | Withdraw from treasury |
| `authorizeTreasuryAccess(address)` | `350a26bf` | Authorize treasury access |
| `sealExecution(uint256)` | - | Generate execution seal |
| `failoverRoute(uint256,address)` | - | Manual failover routing |

**Key Features:**
- **CLZ Optimizations:** Uses Solady's `LibBit.clz_()` for log-scaling, entropy checks
- **LibSort:** Efficient bid ranking and solver reputation sorting
- **Auction Economics:** Commit-reveal with CLZ-weighted bids
- **Reputation System:** Int256 reputation with CLZ scaling
- **Flashloan Abstraction:** Multi-provider failover (Aave, Balancer, Morpho)
- **ZK Verification:** Optional proof verification
- **MEV Protection:** Entropy-based detection
- **Compliance:** Bitmask flags for KYC/accredited/sanctions
- **Treasury Management:** Multi-token treasury with authorization

---

### InstitutionalSolverCore.sol

**Purpose:** Modular libraries for institutional solver (AuctionEconomics, ReputationSystem, FlashloanAbstraction, etc.)

**Libraries:**

#### AuctionEconomics
- `commitBid(AuctionState,address,bytes32)` - Commit bid
- `revealBid(AuctionState,address,uint256,bytes32)` - Reveal bid
- `settleAuction(AuctionState,address[])` - Settle with LibSort ranking

#### ReputationSystem
- `updateReputation(mapping,address,int256)` - Update with CLZ scaling
- `getReputation(mapping,address)` - Get reputation
- `applySlash(mapping,address,uint256)` - Slash reputation

#### FlashloanAbstraction
- `executeFlashloan(address[],address,uint256,bytes)` - Multi-provider execution
- `validateProvider(address)` - Validate flashloan provider

#### HybridExecutionCore
- `executeHybridIntent(bytes,address)` - Execute hybrid intent
- `batchExecute(bytes[],address[])` - Batch execution

#### EIP7702Proxy
- `delegateToSolver(address,bytes)` - Delegate via EIP-7702
- `revokeProxy()` - Revoke delegation

**Key Features:**
- Pure library functions for modular integration
- CLZ optimizations throughout
- LibSort for efficient ranking

---

### FutarchyBatchExecutor.sol (and variants)

**Variants:**
- `FutarchyBatchExecutor.sol` - Original batch executor
- `FutarchyBatchExecutorV2.sol` - V2 with improvements
- `FutarchyBatchExecutorSimple.sol` - Simplified version
- `FutarchyBatchExecutorMinimal.sol` - Minimal version
- `FutarchyBatchExecutorUltra.sol` - Ultra-optimized version

**Common Functions:**
- `executeBatch(...)` - Execute batch operations
- `sweepTokens(...)` - Recover stuck tokens
- Gas-optimized with unchecked loops

---

### PectraWrapper.sol

**Purpose:** EIP-7702 wrapper for Pectra upgrade compatibility

**Features:**
- EIP-7702 delegation handling
- Atomic transaction bundling

---

### SimpleEIP7702Test.sol

**Purpose:** Testing contract for EIP-7702 functionality

---

## Bytecode & Compilation Artifacts

### Build Artifacts Location
```
out/
├── FutarchyArbExecutorV5.sol/FutarchyArbExecutorV5.json
├── InstitutionalSolverSystem.sol/InstitutionalSolverSystem.json
├── PredictionArbExecutorV1.sol/PredictionArbExecutorV1.json
└── ... (all contract artifacts)
```

### Artifact Contents
Each JSON contains:
- **abi**: Full ABI specification
- **bytecode**: Deployment bytecode
- **deployedBytecode**: Runtime bytecode
- **methodIdentifiers**: Function selectors
- **storageLayout**: Storage slot mappings
- **ast**: Abstract Syntax Tree (with `--ast` flag)
- **asm**: EVM assembly (with `--extra-output asm`)

### Bytecode Sample (FutarchyArbExecutorV5)
```
0x60808060405234604d575f80546001600160a01b031916339081178255907f8be0079c531659141344cd1fd0a4f28...
```

**Size:** Check individual artifacts for deployment bytecode size

### Gas Optimization Report
Generated via: `forge test --gas-report`
- All loops use `unchecked { ++i; }`
- Custom errors instead of require strings
- Via-IR optimizer enabled
- 200 optimizer runs

---

## SMT Model Checker Analysis

### Configuration
```toml
[profile.default.model_checker]
contracts = { "contracts/FutarchyArbExecutorV5.sol" = ["FutarchyArbExecutorV5"] }
engine = "chc"
targets = ["assert", "underflow", "overflow", "divByZero"]
timeout = 100000
```

### SMT Solver
- **Solver:** z3 v4.12+
- **Location:** `/opt/homebrew/bin/z3`

### Checks Applied
- ✅ Integer overflow/underflow detection
- ✅ Division by zero checks
- ✅ Assertion violations
- ✅ Type safety (int256 ↔ uint256 casts)

### Known Warnings & Mitigations
**Int256 Overflow Guards:**
- Contracts: V5, V4, V3, PredictionArbExecutorV1
- Mitigation: Added `BalanceTooLarge` error with explicit guards:
  ```solidity
  if (finalBal > uint256(type(int256).max) || initial > uint256(type(int256).max)) {
      revert BalanceTooLarge();
  }
  ```

---

## AST (Abstract Syntax Tree)

### Generation
```bash
forge build --ast --force
```

### AST Location
ASTs embedded in build artifacts: `out/**/*.json` under `ast` key

### AST Features
- Full parse tree for all contracts
- Node types: ContractDefinition, FunctionDefinition, VariableDeclaration, etc.
- Source mappings for debugging
- Used for static analysis, linting, and optimization verification

---

## Storage Layout

### Generation
```bash
forge build --extra-output storageLayout --force
```

### Storage Layout Structure
Example for `InstitutionalSolverSystem`:
```json
{
  "storage": [
    {"label": "owner", "type": "address", "offset": 0, "slot": "0"},
    {"label": "reentrancyGuard", "type": "uint256", "offset": 0, "slot": "1"},
    {"label": "zkVerifier", "type": "address", "offset": 0, "slot": "2"},
    ...
  ]
}
```

### Key State Variables by Contract

#### FutarchyArbExecutorV5
- Slot 0: `owner` (address)
- No storage-heavy state (executor pattern)

#### InstitutionalSolverSystem
- Slot 0: `owner` (address, immutable)
- Slot 1: `reentrancyGuard` (uint256)
- Slot 2: `zkVerifier` (address)
- Slot 3: `paymaster` (address)
- Slot 4: `flashloanProviders` (address[])
- Mappings: `intents`, `resolvers`, `auctions`, `reputation`, `complianceFlags`, etc.

---

## Linting Configuration

### Foundry Lint Settings (`foundry.toml`)
```toml
[lint]
severity = ["high", "med", "low", "gas"]
exclude_lints = [
    "mixed-case-function",      # Allow snake_case for external API
    "mixed-case-variable",      # Allow snake_case for external API
    "screaming-snake-case-immutable",  # Allow lowercase immutables
    "asm-keccak256",            # keccak256 is fine for non-hot paths
    "unused-import",            # Allow imports for future use
]
ignore = ["lib/**"]
```

### Format Settings
```toml
[fmt]
line_length = 120
tab_width = 4
int_types = "long"  # Use uint256 not uint
multiline_func_header = "attributes_first"
sort_imports = true
```

---

## Solady CLZ Integration

### Library: `vectorized/solady@clz` (commit ff6256a)

### Remappings
```toml
remappings = [
    "solady/=lib/solady/",
    "solady-clz/=lib/solady/src/utils/clz/",
    "solady-utils/=lib/solady/src/utils/",
]
```

### Import Patterns
```solidity
// CLZ-optimized (Osaka EVM native CLZ opcode)
import {LibBit} from "solady-clz/LibBit.sol";
import {FixedPointMathLib} from "solady-clz/FixedPointMathLib.sol";

// Standard utils
import {LibSort} from "solady-utils/LibSort.sol";
import {SafeCastLib} from "solady-utils/SafeCastLib.sol";
```

### CLZ Usage
- **LibBit.clz_(value):** Count leading zeros (native CLZ opcode on Osaka EVM)
- **Bid scaling:** `effective_bid = value * (255 - LibBit.clz_(value)) / 256`
- **Entropy checks:** `uint256 entropy = 255 - LibBit.clz_(hash);`
- **Reputation deltas:** CLZ-weighted scaling

### LibSort Usage
- **insertionSort(uint256[]):** Sort arrays in ascending order
- **Bid ranking:** Sort effective bids, find max (last element)
- **Solver ranking:** Sort reputation values, return top N

---

## Next Steps

1. **SMT Full Report:** Run `forge verify-check --check-contracts` for comprehensive analysis
2. **Gas Profiling:** Run `forge test --gas-report` for detailed gas costs
3. **Coverage:** Run `forge coverage` for code coverage metrics
4. **Formal Verification:** Consider Certora/Halmos for invariant testing

---

**Maintainer Notes:**
- All contracts follow Solidity 0.8.33 best practices
- Custom errors replace all `require` statements
- Unchecked increments in all loops
- LibSort/LibBit integration complete
- SMT overflow guards applied
