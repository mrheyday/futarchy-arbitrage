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

### PNK Markets (Specialized)

PNK/Kleros markets require multi-hop routing since there's no direct sDAI↔PNK pool:

**Route**: `sDAI → WETH (Balancer Vault) → PNK (Swapr v2)`

**Implementation**:
- `src/executor/futarchy_pnk_executor.py` - Python executor for PNK flows
- `src/executor/arbitrage_pnk_executor.py` - PNK-specific SELL flow wrapper
- V5 contract function: `sell_conditional_arbitrage_pnk` - Atomic PNK SELL execution

**Usage**:
```bash
# PNK light bot
python -m src.arbitrage_commands.pnk_light_bot --amount 0.1 --interval 120

# Via arbitrage_bot_v2 with PNK type
python -m src.arbitrage_commands.arbitrage_bot_v2 --config config/pnk_market.json
# config: {"bot_type": "pnk", ...}

# Direct executor
python -m src.executor.arbitrage_pnk_executor --flow sell --amount 0.01 --execute
```

**Key differences from standard flow**:
- Uses Balancer Vault's `batchSwap` for sDAI→WETH
- Swapr v2 router for WETH→PNK
- BUY flow: Split sDAI → buy conditionals → merge → sell PNK → WETH → sDAI
- SELL flow: sDAI → WETH → buy PNK → split → sell conditionals → merge sDAI

### Key Directories

- `src/arbitrage_commands/` - Bot strategies (`eip7702_bot.py` is recommended, `simple_bot.py` for sequential)
- `src/executor/` - On-chain execution wrappers for V5 contract (`arbitrage_executor.py`, `prediction_arb_executor.py`)
- `src/helpers/` - Building blocks (swaps, splits, merges, EIP-7702 bundles)
- `src/config/` - Network, contracts, ABIs, tokens (use these, not deprecated `constants.py`)
- `contracts/` - Solidity executors (`FutarchyArbExecutorV5.sol` is current)

### Executor Modules (`src/executor/`)

| Module                       | Purpose                                         |
| ---------------------------- | ----------------------------------------------- |
| `arbitrage_executor.py`      | Standard BUY/SELL flows via V5 contract         |
| `arbitrage_pnk_executor.py`  | PNK-specific SELL flow with WETH routing        |
| `prediction_arb_executor.py` | Prediction markets (yes+no price sum arbitrage) |
| `tx_7702_executor.py`        | EIP-7702 bundle builder for V4 contract         |

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

### Market Data Setup

Before running bots, populate environment files with correct addresses from Supabase:

```bash
# Fetch market data and update .env file automatically
source futarchy_env/bin/activate
source .env.0x<PROPOSAL_ADDRESS>
python -m src.setup.fetch_market_data --proposal --update-env .env.0x<PROPOSAL_ADDRESS>
```

This fetches from Supabase `market_events` table and maps metadata to environment variables:
- `metadata.conditional_pools.yes.address` → `SWAPR_POOL_YES_ADDRESS`
- `metadata.conditional_pools.no.address` → `SWAPR_POOL_NO_ADDRESS`
- `metadata.prediction_pools.yes.address` → `SWAPR_POOL_PRED_YES_ADDRESS`
- `metadata.currencyTokens.yes.wrappedCollateralTokenAddress` → `SWAPR_SDAI_YES_ADDRESS`
- `metadata.companyTokens.yes.wrappedCollateralTokenAddress` → `SWAPR_GNO_YES_ADDRESS`

Requires: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_ANON_KEY`), `FUTARCHY_PROPOSAL_ADDRESS`

### Bot Selection Guide

| Bot | Use Case | Execution Mode | Recommended For |
|-----|----------|----------------|----------------|
| `eip7702_bot.py` | Standard arbitrage | EIP-7702 atomic | **Production** - MEV protection, single tx |
| `simple_bot.py` | Standard arbitrage | Sequential multi-tx | Legacy/fallback when EIP-7702 unavailable |
| `complex_bot.py` | Price discovery | Sequential | Side determination, testing |
| `light_bot.py` | Lightweight | Sequential | Testing, minimal dependencies |
| `pnk_light_bot.py` | PNK/Kleros markets | Sequential | PNK-specific with WETH routing |
| `unified_bot.py` | Database-driven | Configurable | Multiple markets, Supabase config |
| `arbitrage_bot_v2.py` | JSON config-based | Configurable | Custom market types via config files |

**Decision Tree**:
- **New production deployment?** → `eip7702_bot.py`
- **PNK/Kleros market?** → `pnk_light_bot.py` or `arbitrage_bot_v2.py` with `"bot_type": "pnk"`
- **Multiple markets managed centrally?** → `unified_bot.py` with Supabase
- **Testing/debugging?** → `light_bot.py` or `simple_bot.py`
- **Need custom config per market?** → `arbitrage_bot_v2.py` with JSON configs

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
# Compile all contracts with comprehensive artifacts (ABI, bytecode, ASM, opcodes, SMT)
./scripts/compile.sh
# or for specific contract
python3 scripts/compile_all.py --contract FutarchyArbExecutorV5

# Compile with Foundry (alternative)
forge build

# Compile institutional solver (Solidity 0.8.33 + Via-IR)
forge build --profile institutional

# Deploy using pre-compiled artifacts (recommended)
python3 scripts/deploy_executor_v5_precompiled.py

# Deploy with inline compilation (legacy)
python3 scripts/deploy_executor_v5.py
```

**Compilation Artifacts** (`scripts/compile_all.py`):

Generated in `artifacts/` directory:
- `abi/*.json` - Contract ABIs (JSON interface definitions)
- `abi/*.methods.txt` - Function selectors (4-byte identifiers)
- `bytecode/*.bin` - Deployment bytecode (raw hex)
- `bytecode/*.hex` - Deployment bytecode (0x prefixed)
- `bytecode/*.runtime.bin` - Runtime bytecode (on-chain code)
- `asm/*.asm` - EVM assembly output
- `opcodes/*.opcodes` - Raw opcode sequence
- `opcodes/*.readable.txt` - Human-readable opcodes with addresses
- `storage/*.storage.json` - Storage layout (variable → slot mapping)
- `ast/*.ast.json` - Abstract Syntax Tree
- `smt/*.smt2` - SMT-LIB2 for formal verification (with `--smt` flag)

**Usage Examples**:
```bash
# Check contract sizes (24KB limit)
for f in artifacts/bytecode/*.runtime.bin; do
    bytes=$(($(wc -c < "$f") / 2))
    echo "$(basename $f .runtime.bin): $bytes bytes"
done

# Count expensive opcodes (gas optimization)
grep -o "SLOAD" artifacts/opcodes/FutarchyArbExecutorV5.opcodes | wc -l

# Formal verification with SMT checker
python3 scripts/compile_all.py --contract SafetyModule --smt

# Deploy with pre-compiled artifacts
python3 scripts/deploy_executor_v5_precompiled.py
```

See [docs/BUILD_ARTIFACTS.md](../docs/BUILD_ARTIFACTS.md) for comprehensive artifact documentation.

## Institutional Solver System ⚠️ EXPERIMENTAL

**Status**: Research prototype, NOT production-ready. Use for exploration and testing only.

CLZ-optimized solver system for advanced DeFi operations combining auction economics, ZK proofs, and MEV protection. See `docs/INSTITUTIONAL_SOLVER_*.md` for detailed documentation.

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

| Protocol       | Interface                                | Notes                                                        |
| -------------- | ---------------------------------------- | ------------------------------------------------------------ |
| Balancer V2    | `balancer_swap.py`                       | Uses BatchRouter for conditional token swaps                 |
| Swapr/Algebra  | `swapr_swap.py`                          | Uniswap V3-compatible `exactInputSingle`/`exactOutputSingle` |
| FutarchyRouter | `split_position.py`, `merge_position.py` | `splitPosition`/`mergePositions` for conditional tokens      |
| Permit2        | Via executor contracts                   | Token approvals for batch operations                         |

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

## Testing & Quality Assurance

### Python Tests (pytest)

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python -m pytest tests/test_eip7702.py -v

# Test with coverage
python -m pytest tests/ --cov=src
```

Tests focus on transaction building, EIP-7702 bundles, and integration flows. Mock Web3 calls where appropriate.

### Solidity Tests (Foundry)

```bash
# Run all contract tests
forge test -vv

# Run specific contract tests
forge test --match-contract FutarchyArbExecutorV5Test -vvv

# Run with gas reports
forge test --gas-report

# Coverage
forge coverage
```

Test files in `tests/*.t.sol` use Foundry's testing framework. Critical to test V5 executor flows and institutional solver auction mechanics.

### Contract Versioning

Executor contracts have evolved through several iterations:

- **V2** (`FutarchyArbitrageExecutorV2.sol`) - Early batch executor
- **V3** (`FutarchyArbExecutorV3.sol`) - Improved error handling
- **V4** (`FutarchyArbExecutorV4.sol`) - EIP-7702 support added
- **V5** (`FutarchyArbExecutorV5.sol`) - **Current production version** with PNK routing, signed min-profit, gas semantics improvements

Always use V5 for new work unless specifically debugging legacy deployments.

## Production Monitoring & Safety

### Safety Module (`contracts/SafetyModule.sol`)

Production-grade circuit breakers protect against:

- Excessive slippage (transaction reverts if slippage > threshold)
- High gas prices (blocks trades when gas exceeds limit)
- Daily loss limits (cumulative loss tracking)

Monitor events via `src/monitoring/slack_alerts.py`.

### Structured Logging

Use `setup_logger()` from `src/config/logging_config.py`:

```python
from src.config.logging_config import setup_logger, log_trade

logger = setup_logger("my_module", level=10)  # DEBUG=10, INFO=20
logger.info("Price check started")
log_trade(side="buy", amount=Decimal("1.0"), profit=Decimal("0.05"))
```

Logs rotate daily, stored in `logs/`. Error logs separate from info logs.

### Slack/Discord/Telegram Alerts

Configure webhooks and bot tokens in environment:

```bash
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR_WEBHOOK
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_SILENT=false  # Optional: silent notifications
```

Monitor SafetyModule circuit breaker events:

```bash
python -m src.monitoring.slack_alerts --contract 0x... --check-config
```

Test Telegram alerts:

```bash
python -m src.monitoring.telegram_alerts
```

## Common Troubleshooting

Quick solutions for common issues organized by category. Check logs in `logs/` directory for detailed error traces.

### Environment Issues

| Symptom | Solution |
|---------|----------|
| **"Missing required pool address environment variables"** | Run `python -m src.setup.fetch_market_data --proposal --update-env .env.0x<ADDRESS>`<br>Verify `FUTARCHY_PROPOSAL_ADDRESS` matches Supabase market event ID<br>Check: `SWAPR_POOL_YES_ADDRESS`, `SWAPR_POOL_NO_ADDRESS`, `SWAPR_POOL_PRED_YES_ADDRESS`, `BALANCER_POOL_ADDRESS` |
| **Tenderly simulation failures** | Verify env vars: `TENDERLY_ACCESS_KEY`, `TENDERLY_ACCOUNT_SLUG`, `TENDERLY_PROJECT_SLUG`<br>Check simulations in Tenderly dashboard for detailed traces<br>Look for `TenderlyClient` errors in `logs/` directory |
| **"Insufficient balance" errors** | Check sDAI balance: `MIN_SDAI_BALANCE = 0.01` required<br>Check ETH balance: `MIN_ETH_BALANCE = 0.001` for gas<br>Fund account: `python -m src.arbitrage_commands.pull_sdai` |

### Transaction Failures

| Symptom | Solution |
|---------|----------|
| **"Transaction underpriced"** | Adjust gas settings via env: `PRIORITY_FEE_WEI`, `MAX_FEE_MULTIPLIER`<br>Check `_eip1559_fees()` in deployment scripts for fee calculation logic |
| **Slippage errors** | Increase `--tolerance` parameter (default 0.02 = 2%)<br>For liquidation: 1% slippage tolerance hardcoded in `conditional_sdai_liquidation.py`<br>SafetyModule may be blocking trades - check circuit breaker events |
| **EIP-7702 authorization failures** | Verify Pectra network support (Gnosis Chain fork)<br>Check `PectraWrapper` contract is deployed<br>Ensure correct chain ID in authorization signature |

### Price/Arbitrage Issues

| Symptom | Solution |
|---------|----------|
| **No profitable opportunities** | Lower `--tolerance` to be more aggressive (e.g., 0.01 instead of 0.04)<br>Verify ideal_price formula: `pred_price × yes_price + (1 - pred_price) × no_price`<br>Check pool liquidity hasn't dried up |
| **Bot trades but loses money** | Increase `--tolerance` to be more conservative<br>Check gas costs aren't eating profits<br>Verify signed min-profit in V5 executor is set correctly<br>Review Tenderly traces for unexpected slippage |

## Deployment Patterns

### Deploying Executor Contracts

```bash
# Source market-specific environment
source .env.0x<PROPOSAL_ADDRESS>

# Deploy V5 executor
python scripts/deploy_executor_v5.py

# Verify on Gnosisscan (auto-runs in deploy script)
# Contract addresses saved to deployments/deployment_executor_v5_<timestamp>.json
```

Deployment scripts:

- Use `solc` via subprocess (Solidity 0.8.33, Via-IR, Osaka EVM)
- Auto-verify on Gnosisscan with standard-json-input
- Save deployment info with timestamp to `deployments/`
- Address resolution: `--address` flag → env var → latest `deployments/*.json`

### Institutional Solver Deployment

```bash
# Compile with institutional profile
forge build --profile institutional

# Deploy
python scripts/deploy_institutional_solver.py
```

See `docs/INSTITUTIONAL_SOLVER_*.md` for auction mechanics, ZK integration, flashloan abstraction.
