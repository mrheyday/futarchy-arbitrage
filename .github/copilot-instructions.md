# Copilot Instructions for Futarchy Arbitrage Bot

## Project Overview

Gnosis Chain arbitrage bot exploiting price discrepancies between **Balancer** and **Swapr (Algebra)** pools for conditional tokens (YES/NO) in futarchy markets. Uses sDAI as the primary trading token.

## Architecture

### Core Trading Flow
```
ideal_price = pred_price × yes_price + (1 - pred_price) × no_price
```
- **Buy flow** (`buy_cond.py`): Split sDAI → swap to conditional Company tokens → merge → sell on Balancer
- **Sell flow** (`sell_cond.py`): Buy Company on Balancer → split → swap conditional tokens → merge sDAI

### Conditional sDAI Liquidation
When YES/NO swap amounts differ after trading, excess conditional sDAI must be liquidated (`conditional_sdai_liquidation.py`):
- **Excess YES**: Direct swap YES→sDAI on Swapr
- **Excess NO**: Buy YES with sDAI → merge both back to sDAI (two-step)
- Uses 1% slippage tolerance for liquidation swaps

### PNK Token Path
For PNK markets, multi-hop routing through WETH: `sDAI → WETH (Balancer Vault) → PNK (Swapr v2)`. See `src/executor/futarchy_pnk_executor.py` and `sell_conditional_arbitrage_pnk` in V5 contract.

### Key Directories
- `src/arbitrage_commands/` - Bot strategies (`eip7702_bot.py` is recommended, `simple_bot.py` for sequential)
- `src/executor/` - On-chain execution wrappers for V5 contract (`arbitrage_executor.py`, `prediction_arb_executor.py`)
- `src/helpers/` - Building blocks (swaps, splits, merges, EIP-7702 bundles)
- `src/config/` - Network, contracts, ABIs, tokens (use these, not deprecated `constants.py`)
- `contracts/` - Solidity executors (`FutarchyArbExecutorV5.sol` is current)

### Executor Modules (`src/executor/`)
| Module | Purpose |
|--------|---------|
| `arbitrage_executor.py` | Standard BUY/SELL flows via V5 contract |
| `arbitrage_pnk_executor.py` | PNK-specific SELL flow with WETH routing |
| `prediction_arb_executor.py` | Prediction markets (yes+no price sum arbitrage) |
| `tx_7702_executor.py` | EIP-7702 bundle builder for V4 contract |

### Two Execution Modes
1. **EIP-7702 Atomic** (`*_eip7702.py`): Single bundled transaction via Pectra - preferred for MEV protection
2. **Sequential** (`buy_cond.py`, `sell_cond.py`): Multi-tx execution with simulation-first pattern

## Development Workflow

### Environment Setup
```bash
source futarchy_env/bin/activate
source .env.0x<PROPOSAL_ADDRESS>  # Market-specific addresses
```

Environment files (`.env.0x...`) contain pool/token addresses for each futarchy proposal. Use `src/setup/fetch_market_data.py --proposal --update-env` to auto-populate from Supabase.

### Running Bots
```bash
# EIP-7702 atomic (recommended)
python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --interval 120 --tolerance 0.02

# Sequential fallback
python -m src.arbitrage_commands.simple_bot --amount 0.01 --interval 120 --tolerance 0.2

# JSON config-based bot (supports multiple bot types)
python -m src.arbitrage_commands.arbitrage_bot_v2 --config config/proposal.json

# Prediction arbitrage (yes+no price sum)
python -m src.executor.prediction_arb_executor --amount 0.05 --min-profit -0.001
```

### Bot Types (`arbitrage_bot_v2`)
- `balancer` (default): Standard Balancer/Swapr conditional token arbitrage
- `pnk`/`kleros`: PNK markets with WETH routing
- `prediction`: Delegates to `prediction_arb_executor` (no price args, on-chain decision)

### Executor CLI (`src/executor/`)
```bash
# SELL flow: Balancer buy → split → sell conditionals
python -m src.executor.arbitrage_executor --flow sell --amount 0.01 --cheaper yes --execute

# BUY flow: split sDAI → buy conditionals → merge → sell
python -m src.executor.arbitrage_executor --flow buy --amount 0.01 --cheaper yes --execute
```

Address resolution: `--address` flag → `FUTARCHY_ARB_EXECUTOR_V5` env → latest `deployments/*.json`

### Solidity Contracts
```bash
# Compile arbitrage executors
forge build

# Compile institutional solver (Solidity 0.8.33 + Via-IR)
forge build --profile institutional

# Deploy (example)
python scripts/deploy_executor_v5.py
```

## Institutional Solver System (Experimental)

CLZ-optimized solver system for advanced DeFi operations. See `docs/INSTITUTIONAL_SOLVER_*.md`.

### Key Components
- `contracts/InstitutionalSolverCore.sol` - Auction economics, reputation, flashloan abstraction
- `contracts/InstitutionalSolverSystem.sol` - Integrated system with intents
- `contracts/SupportingModules.sol` - ZK, MEV protection, compliance, cross-chain
- `src/helpers/institutional_solver_client.py` - Python AI administrator with SQLite state
- `src/helpers/institutional_solver_monitor.py` - Event tracking and health monitoring

### CLZ Optimizations via Solady
Count Leading Zeros (CLZ) using **Solady's `clz` branch** (`lib/solady/src/utils/clz/LibBit.sol`):
- Import: `import {LibBit} from "solady-clz/LibBit.sol";`
- Usage: `uint256 leadingZeros = LibBit.clz_(value);`
- Bid scaling: `effective_bid = value * (255 - LibBit.clz_(value)) / 256`
- Reputation deltas, MEV entropy checks, compliance bitmasks

**Foundry remappings** in `foundry.toml`:
```toml
remappings = [
    "solady/=lib/solady/",
    "solady-clz/=lib/solady/src/utils/clz/",
    "solady-utils/=lib/solady/src/utils/",
]
```

**Import patterns**:
- CLZ-optimized: `import {LibBit} from "solady-clz/LibBit.sol";`
- CLZ-optimized: `import {FixedPointMathLib} from "solady-clz/FixedPointMathLib.sol";`
- Standard utils: `import {LibSort} from "solady-utils/LibSort.sol";`
- Standard utils: `import {SafeCastLib} from "solady-utils/SafeCastLib.sol";`

### Multi-Provider Flashloans
`FlashloanAbstraction` supports Aave, Balancer, Morpho with automatic failover.

### Deployment & Testing
```bash
# Compile (Solidity 0.8.33 + Via-IR + Osaka EVM)
forge build

# Deploy
python scripts/deploy_institutional_solver.py

# Run Foundry tests
forge test --match-contract InstitutionalSolverSystemTest
```

### Failure Recovery
See `docs/FAILURE_RECOVERY.md` for:
- Atomic transaction guarantees (all-or-nothing)
- Flashloan multi-provider failover
- Owner manual intervention via `failoverRoute`

## Debugging with Tenderly

All transactions simulate via Tenderly before on-chain execution. Required env vars:
- `TENDERLY_ACCESS_KEY`, `TENDERLY_ACCOUNT_SLUG`, `TENDERLY_PROJECT_SLUG`

Simulations auto-save to dashboard (`save: True`, `save_if_fails: True`). Check `TenderlyClient` in `src/helpers/tenderly_api.py`. Debug failed txs by inspecting traces in Tenderly UI.

## Code Conventions

### Transaction Building Pattern
All trades follow simulation-first: build Tenderly-compatible dict → simulate → execute on-chain. Handler functions prefixed with `handle_` track state.

### Logging
- `print()` in `arbitrage_commands/` for operational output
- `logging` module in `helpers/` for debug traces

### Precision
Always use `Decimal` for price calculations. Amounts are in sDAI (18 decimals).

### Task Tracking
Tasks tracked in `.claude/tasks/` with emoji status: `◐` in-progress, `✅` complete. See [CLAUDE.md](../CLAUDE.md#task-tracking-in-claudetasks) for naming conventions.

## Critical Integration Points

| Protocol | Interface | Notes |
|----------|-----------|-------|
| Balancer V2 | `balancer_swap.py` | Uses BatchRouter for conditional token swaps |
| Swapr/Algebra | `swapr_swap.py` | Uniswap V3-compatible `exactInputSingle`/`exactOutputSingle` |
| FutarchyRouter | `split_position.py`, `merge_position.py` | `splitPosition`/`mergePositions` for conditional tokens |
| Permit2 | Via executor contracts | Token approvals for batch operations |

## Configuration Management

### ConfigManager (`src/config/config_manager.py`)
Supabase-backed bot configuration with HD wallet key derivation:
- `register_bot()` - Create bot with auto-derived wallet address
- `get_bot_config()` - Fetch config including market assignments
- `assign_bot_to_market()` - Link bot to market/pool

### KeyManager (`src/config/key_manager.py`)
Derives child keys from `MASTER_PRIVATE_KEY` using derivation paths (`m/44'/60'/0'/0/N`).

### Unified Bot (`src/arbitrage_commands/unified_bot.py`)
Database-driven bot that loads config from Supabase:
```bash
python -m src.arbitrage_commands.unified_bot --bot-name my-arb-bot --dry-run
```

## Required Environment Variables
Key variables (see [CLAUDE.md](../CLAUDE.md) for full list):
- `RPC_URL`, `PRIVATE_KEY` - Gnosis Chain connection
- `TENDERLY_ACCESS_KEY`, `TENDERLY_ACCOUNT_SLUG`, `TENDERLY_PROJECT_SLUG` - Simulation
- `SWAPR_POOL_YES_ADDRESS`, `SWAPR_POOL_NO_ADDRESS`, `SWAPR_POOL_PRED_YES_ADDRESS` - Swapr pools
- `BALANCER_POOL_ADDRESS` - Balancer pool
- `FUTARCHY_ROUTER_ADDRESS`, `FUTARCHY_PROPOSAL_ADDRESS` - Futarchy contracts
- `SWAPR_SDAI_YES_ADDRESS`, `SWAPR_GNO_YES_ADDRESS`, etc. - Conditional token addresses
