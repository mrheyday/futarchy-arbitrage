# Copilot Instructions for Futarchy Arbitrage Bot

## Project Overview

Gnosis Chain arbitrage bot that exploits price discrepancies between **Balancer** and **Swapr (Algebra)** pools for conditional tokens (YES/NO) in futarchy markets, using sDAI as the primary trading asset.

**Current date context**: January 2026. The project has evolved through multiple executor versions (V2→V5), with V5 as the current production contract. Recent developments (Jan 2026) include Python 3.14 migration, institutional solver system, and prediction arbitrage bot capabilities.

## Core Architecture

### The Arbitrage Mechanics

<<<<<<< Updated upstream
=======
### Core Trading Flow

>>>>>>> Stashed changes
```
ideal_price = prediction_price × yes_price + (1 - prediction_price) × no_price
```
<<<<<<< Updated upstream

The bot monitors Balancer and Swapr pools, detecting when **both** YES and NO prices diverge from this ideal. Two flows:

- **BUY flow** (profitable when Swapr < Balancer): Split sDAI → buy conditionals on Swapr → merge → sell Company on Balancer
- **SELL flow** (profitable when Swapr > Balancer): Buy Company on Balancer → split → sell conditionals on Swapr → merge sDAI

**Excess Conditional Liquidation** (`conditional_sdai_liquidation.py`): When YES/NO swap amounts differ, excess conditional sDAI is liquidated with 1% tolerance:
- Excess YES: Direct swap YES→sDAI on Swapr  
- Excess NO: Buy YES with sDAI, then merge both back to sDAI (two-step)

### Two Execution Architectures

| Mode | Entry Point | File Pattern | Best For |
|------|-------------|------|----------|
| **EIP-7702 Atomic** | `eip7702_bot.py` | `*_eip7702*.py` | **Production** — Single bundled tx, MEV-resistant |
| **Sequential** | `simple_bot.py`, `complex_bot.py` | `buy_cond.py`, `sell_cond.py` | Testing, fallback, side discovery |
| **Prediction Arbitrage** | `arbitrage_bot_v2.py` | `PredictionArbExecutorV1.sol` | Prediction token trades (new) |
| **Institutional Solver** | `unified_bot.py` | `InstitutionalSolverSystem.sol` | Multi-market coordination (new) |
=======

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

| Module                       | Purpose                                         |
| ---------------------------- | ----------------------------------------------- |
| `arbitrage_executor.py`      | Standard BUY/SELL flows via V5 contract         |
| `arbitrage_pnk_executor.py`  | PNK-specific SELL flow with WETH routing        |
| `prediction_arb_executor.py` | Prediction markets (yes+no price sum arbitrage) |
| `tx_7702_executor.py`        | EIP-7702 bundle builder for V4 contract         |

### Two Execution Modes

1. **EIP-7702 Atomic** (`*_eip7702.py`): Single bundled transaction via Pectra - preferred for MEV protection
2. **Sequential** (`buy_cond.py`, `sell_cond.py`): Multi-tx execution with simulation-first pattern
>>>>>>> Stashed changes

EIP-7702 uses `PectraWrapper.sol` for delegation; sequential uses Tenderly simulation then multi-tx execution. Prediction arbitrage adds V1 executor for non-conditional markets. Institutional Solver enables centralized multi-market orchestration.

<<<<<<< Updated upstream
### PNK/Kleros Markets (Special Case)

No direct sDAI↔PNK pool exists. Route: `sDAI → WETH (Balancer Vault batchSwap) → PNK (Swapr v2)`.

- **Entry**: `pnk_light_bot.py` (legacy), `arbitrage_bot_v2.py --config config/pnk_market.json` (current)
- **Executor**: `arbitrage_pnk_executor.py` handles multi-hop routing
- **Contracts**: `FutarchyArbExecutorV5.sol` has `sell_conditional_arbitrage_pnk` function

### Project Structure

```
src/arbitrage_commands/     # Bot strategies (eip7702_bot.py recommended)
src/executor/               # On-chain execution wrappers (arbitrage_executor.py main)
src/helpers/                # Building blocks (swaps, splits, merges, EIP-7702 bundles)
src/config/                 # Network, contracts, ABIs, tokens
src/setup/                  # Market data fetching from Supabase
contracts/                  # Solidity V2→V5 executors, PectraWrapper, SafetyModule
```

## Environment & Workflow

**Activation pattern**:
=======
### Environment Setup

>>>>>>> Stashed changes
```bash
source futarchy_env/bin/activate
source .env.0x<PROPOSAL_ADDRESS>  # Market-specific pool/token addresses
```

<<<<<<< Updated upstream
**Market data auto-setup** (before any bot run):
=======
Environment files (`.env.0x...`) contain pool/token addresses for each futarchy proposal. Use `src/setup/fetch_market_data.py --proposal --update-env` to auto-populate from Supabase.

### Running Bots

>>>>>>> Stashed changes
```bash
python -m src.setup.fetch_market_data --proposal --update-env .env.0x<PROPOSAL_ADDRESS>
```
Fetches Supabase `market_events` metadata and populates `SWAPR_POOL_YES_ADDRESS`, `SWAPR_POOL_NO_ADDRESS`, `SWAPR_SDAI_YES_ADDRESS`, etc.

**Required env vars**: `RPC_URL`, `PRIVATE_KEY`, `FUTARCHY_PROPOSAL_ADDRESS`, pool addresses, `TENDERLY_*` for simulation

**Preview vs Execute Mode** (Jan 2026+):
```bash
# Preview mode (safe, shows gas estimate)
python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --interval 120

# Execute mode (actually broadcasts)
python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --interval 120 --execute

# Dry-run (simulates only, max iterations)
python -m src.arbitrage_commands.eip7702_bot --amount 0.001 --dry-run --max-iterations 5
```
**Note**: Executors default to preview-only; add `--execute` to broadcast transactions. Use `--execute --force-send` to skip gas estimation.

## Bot Selection & Running

**Decision tree**:
- **Production deployment?** → `eip7702_bot.py`  
- **PNK/Kleros market?** → `arbitrage_bot_v2.py --config config/pnk_market.json` with `"bot_type": "pnk"`  
- **Testing/side discovery?** → `complex_bot.py` (discovers which direction is profitable)  
- **Legacy/fallback?** → `simple_bot.py` or `light_bot.py`  
- **Database-driven multi-market?** → `unified_bot.py` (Supabase config)  
- **Custom market config per JSON?** → `arbitrage_bot_v2.py --config config/market.json`

**Common commands**:
```bash
# Production (atomic, EIP-7702)
python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --interval 120 --tolerance 0.02

# Dry-run mode for testing
python -m src.arbitrage_commands.eip7702_bot --amount 0.001 --interval 30 --tolerance 0.01 --dry-run --max-iterations 5

# Side discovery
python -m src.arbitrage_commands.complex_bot --amount 0.1 --interval 120 --tolerance 0.04

<<<<<<< Updated upstream
# Direct executor (SELL flow example)
=======
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
>>>>>>> Stashed changes
python -m src.executor.arbitrage_executor --flow sell --amount 0.01 --cheaper yes --execute
```

## Developer Patterns & Conventions

### Modern Python Setup (Python 3.14+, Jan 2026)

The project has migrated to Python 3.14 with `uv` package manager for faster builds. Use:

<<<<<<< Updated upstream
=======
### Solidity Contracts

>>>>>>> Stashed changes
```bash
# Install dependencies with uv (fast, parallel)
uv pip install -r requirements.txt

# Or traditional pip
pip install -r requirements.txt
```

Use modern Python 3.10+ type hints (no `from __future__ import annotations` needed in most cases). See `pyproject.toml` for packaging configuration.

All trades follow **simulation-first**: build Tenderly-compatible dict → simulate → execute on-chain.

<<<<<<< Updated upstream
```python
# Example pattern from arbitrage_executor.py
tx_dict = {
    'from': sender_addr,
    'to': contract_addr,
    'data': encoded_call,
    'gas': estimated_gas,
    'gasPrice': web3.eth.gas_price,
    'nonce': web3.eth.get_transaction_count(sender_addr),
    'chainId': 100,  # Gnosis Chain
    'value': 0,
}
# Simulate via tenderly_api.py before broadcast
```

### Handler Functions & State Tracking

Transaction simulation handlers use `handle_` prefix. Example: `handle_buy_sim()`, `handle_sell_response()`.

### Logging Patterns
=======
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
>>>>>>> Stashed changes

- **`arbitrage_commands/`**: Use `print()` for operational output (bot starting, trades executed, profits)
- **`helpers/`**: Use `logging` module for debug traces (gas calculations, pool states)
- **Setup**: Use `setup_logger()` from `src/config/logging_config.py` with level (10=DEBUG, 20=INFO)

### Precision & Decimal Usage

<<<<<<< Updated upstream
Always use `Decimal` for price calculations. Amounts are in sDAI (18 decimals).

```python
from decimal import Decimal
yes_price = Decimal(str(web3_value)) / Decimal(10**18)
```

### Configuration Resolution

Use `src/config/` modules (network.py, contracts.py, tokens.py, pools.py), NOT deprecated `constants.py`:

```python
from src.config.network import DEFAULT_RPC_URLS, CHAIN_ID
from src.config.contracts import get_contract_address
from src.config.tokens import get_token_decimals
```

### Smart Contract Integration Points

| Component | File | Purpose |
|-----------|------|---------|
| Token swaps | `balancer_swap.py`, `swapr_swap.py` | Interface Balancer V2 BatchRouter and Swapr exactInputSingle |
| Position mgmt | `split_position.py`, `merge_position.py` | FutarchyRouter `splitPosition`/`mergePositions` |
| Conditional liquidation | `conditional_sdai_liquidation.py` | Handle YES/NO imbalances |
| EIP-7702 bundling | `eip7702_builder.py`, `bundle_helpers.py` | Pectra authorization & delegation |

## Solidity Contracts (Executor Versions)

**Current & Legacy**:
- **V5** (`FutarchyArbExecutorV5.sol`) — **CURRENT PRODUCTION**. BUY/SELL flows, PNK routing, signed min-profit.
- V4 (`FutarchyArbExecutorV4.sol`) — EIP-7702 support added
- V3 (`FutarchyArbExecutorV3.sol`) — Error handling improvements  
- V2 (`FutarchyArbitrageExecutorV2.sol`) — Early batch executor

**New contracts** (Jan 2026):
- `PectraWrapper.sol` — EIP-7702 delegation & authorization
- `SafetyModule.sol` — Circuit breakers (slippage, gas, daily loss limits)
- `InstitutionalSolverSystem.sol` — Multi-market coordination with CLZ optimizations
- `PredictionArbExecutorV1.sol` — Prediction token arbitrage (non-conditional markets)

**Compilation**:
```bash
./scripts/compile.sh                                    # All contracts
python3 scripts/compile_all.py --contract FutarchyArbExecutorV5  # Specific
python3 scripts/compile_all.py --contract SafetyModule --smt      # With formal verification
```

Artifacts generated to `artifacts/` (ABI, bytecode, opcodes, ASM, storage layout). Pre-compiled artifacts enable fast deployment without re-solc.

**Deployment**:
```bash
python3 scripts/deploy_executor_v5.py  # Uses pre-compiled artifacts + Gnosisscan verification
```

## Tenderly Simulation

All bots/executors simulate via Tenderly before broadcast. Required env vars:
- `TENDERLY_ACCESS_KEY`, `TENDERLY_ACCOUNT_SLUG`, `TENDERLY_PROJECT_SLUG`

Simulations auto-save to dashboard (configurable `save=True`, `save_if_fails=True`). Check `TenderlyClient` in `src/helpers/tenderly_api.py` for tracing logic. Inspect failed tx traces in Tenderly UI for debugging.

## Production Safety

**SafetyModule.sol** protects against:
- Excessive slippage (transaction reverts if > threshold)
- High gas prices (blocks trades when above limit)
- Daily loss accumulation (cumulative tracking)

Monitor circuit breaker events via `src/monitoring/slack_alerts.py` and `telegram_alerts.py`.

## EIP-7702 Bundling Deep Dive

EIP-7702 enables atomic batched transactions where an EOA temporarily acts as a contract. All Futarchy arbitrage operations (split, swap, merge) execute in a single transaction.

### Builder Pattern (`eip7702_builder.py`)

```python
from src.helpers.eip7702_builder import EIP7702TransactionBuilder

builder = EIP7702TransactionBuilder(w3, implementation_address)

# Add approval for conditional sDAI on Swapr
builder.add_approval(sdai_address, swapr_router, 2**256-1)

# Add split: sDAI → YES_sdai + NO_sdai
builder.add_futarchy_split(router, proposal, sdai_address, amount_wei)

# Add swap: YES_sdai → YES_company on Swapr
builder.add_exact_input_single(swapr_yes_pool, yes_sdai, yes_company, amount_wei)

# Add swap: NO_sdai → NO_company on Swapr
builder.add_exact_input_single(swapr_no_pool, no_sdai, no_company, amount_wei)

# Add merge: YES_company + NO_company → Company
builder.add_futarchy_merge(router, proposal, yes_addr, no_addr, min_amount)

# Execute as atomic bundle
tx = builder.build_transaction()
```

### Signing & Authorization

Each EIP-7702 transaction requires:
1. **Authorization signature** (delegation proof): signed by user private key
2. **Transaction signature** (execution): standard EIP-712 signature

```python
auth = {
    "chainId": 100,  # Gnosis Chain
    "address": implementation_address,  # PectraWrapper or executor
    "nonce": 0  # Authorization nonce (separate from tx nonce)
}

signed_auth = account.sign_authorization(auth)  # eth_account library
# Returns dict with: yParity, r, s

# Authorization included in tx type 4 field
tx['authorizationList'] = [signed_auth]
```

### Critical Constraints

- **No 0xEF opcodes** in delegated code (PectraWrapper.sol avoids them)
- **Single tx execution**: all operations succeed or all revert (atomicity)
- **Nonce tracking**: authorization nonce ≠ transaction nonce
- **Gas estimation**: must include authorization gas (~5000 extra wei)

## Conditional Liquidation Edge Cases

Liquidation handles imbalances when YES and NO swap amounts diverge. Implementation in `conditional_sdai_liquidation.py`:

### Positive Imbalance (Excess YES)

When YES amount > NO amount:
```
liquidate_conditional_sdai_amount = +X  (positive)
→ Direct swap: X YES → sDAI on Swapr
→ Single transaction
```

**Edge case**: If X is very small (dust) and gas > profit, skip liquidation.

### Negative Imbalance (Excess NO)

When NO amount > YES amount:
```
liquidate_conditional_sdai_amount = -X  (negative)
→ Two-step liquidation:
  1. Buy YES with sDAI (exact output of X YES)
  2. Merge X YES + X NO → sDAI
```

**Why two steps?** No direct NO→sDAI pool exists on Swapr. Must convert NO→YES first.

### 1% Tolerance Mechanism

```python
# Liquidation tx allows 1% slippage
min_amount = amount_to_swap * Decimal("0.99")

# Built into exact_in swap on Swapr:
# swap(amountIn, minAmountOut=...)
```

**Exception**: Tenderly simulation may fail if tolerance is too tight. Use `conditional_sdai_liquidation.py` directly for adjustment.

### When Liquidation Fails

If liquidation swap would lose money (slippage > profit):

1. **Log warning** in Tenderly simulation
2. **Skip liquidation** — let operator handle manually
3. **Track in Slack alert** — SafetyModule may block trade anyway

## Troubleshooting Common Errors

### Environment & Setup Issues

| Error | Root Cause | Solution |
|-------|-----------|----------|
| `KeyError: 'SWAPR_POOL_YES_ADDRESS'` | Missing pool addresses in `.env` file | Run `python -m src.setup.fetch_market_data --proposal --update-env .env.0x<ADDRESS>` to auto-populate from Supabase |
| `FUTARCHY_PROPOSAL_ADDRESS is None` | Env var not sourced | Ensure you run `source .env.0x<ADDRESS>` after activating venv |
| `Missing TENDERLY_* vars` | Simulation not configured | Set `TENDERLY_ACCESS_KEY`, `TENDERLY_ACCOUNT_SLUG`, `TENDERLY_PROJECT_SLUG` in `.env` |
| `Connection refused` (RPC) | Wrong `RPC_URL` or network down | Verify `echo $RPC_URL` points to Gnosis Chain endpoint (typically `https://rpc.gnosischain.com`) |

### Insufficient Balance Errors

| Error | Threshold | Solution |
|-------|-----------|----------|
| `sDAI balance too low` | < 0.01 sDAI | Fund from liquid sDAI via `python -m src.arbitrage_commands.pull_sdai --amount 1.0` |
| `ETH balance too low` | < 0.001 ETH | Bridge ETH via Arbitrary Bridge or use faucet (Chiado: https://faucet.chiadochain.net) |
| `Gas estimation failed` | Tx would fail on-chain | Increase gas limits in env or reduce trade size with `--amount` |

**Check balances**:
```bash
python3 << 'EOF'
import os
from web3 import Web3
from eth_account import Account

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
account = Account.from_key(os.getenv("PRIVATE_KEY"))
eth_bal = w3.eth.get_balance(account.address)
print(f"ETH: {eth_bal / 1e18:.6f}")
# For sDAI, use contract call with ERC20 ABI
EOF
```

### Transaction Failures During Execution

| Error | Cause | Solution |
|-------|-------|----------|
| `Slippage exceeded tolerance` | Pool price moved between sim & broadcast | Increase `--tolerance` (default 0.02 = 2%) or wait for volatility to decrease |
| `SafetyModule circuit breaker triggered` | Gas price, slippage, or daily loss limit hit | Check `src/monitoring/slack_alerts.py` for circuit breaker events; wait before retrying |
| `EIP-7702 authorization failed` | Signature mismatch or wrong chain ID | Verify `chainId: 100` in authorization dict; check auth signing in `eip7702_builder.py` |
| `Insufficient liquidity` | Pool dried up or spread too wide | Check Swapr/Balancer pool depths via UI; try different time window |

### Price & Profitability Issues

| Symptom | Debug Step | Fix |
|---------|-----------|-----|
| No profitable opportunities found | Lower `--tolerance` | Use `complex_bot.py` with `--tolerance 0.01` to discover profitable sides |
| Bot trades but loses money | Verify ideal price formula | Check Tenderly trace: does YES/NO pricing align with actual ideal? |
| Sudden profitability drop | Pool rebalance or fee impact | Monitor gas prices (`echo $PRIORITY_FEE_WEI`); adjust min-profit threshold |

**Manual price check**:
```bash
python3 << 'EOF'
from src.helpers.swapr_price import get_pool_price
from src.helpers.balancer_price import get_pool_price as bal_price
from decimal import Decimal

yes_swapr = get_pool_price("yes_pool")
no_swapr = get_pool_price("no_pool")
pred_price = Decimal("0.5")  # Example
ideal = pred_price * yes_swapr + (1 - pred_price) * no_swapr
print(f"Ideal: {ideal}, YES Swapr: {yes_swapr}, NO Swapr: {no_swapr}")
EOF
```

## Task Tracking Patterns (`.claude/tasks/`)

Tasks track long-running development efforts with strict emoji-based status:

### Directory Structure

```
.claude/tasks/
├── task-name ◐/                        # In-progress task folder
│   ├── README.md                       # Task overview
│   ├── subtask-1-name ✅.md            # Completed subtask
│   ├── subtask-2-name ◐.md             # In-progress subtask
│   └── subtask-3-name.md               # Not-started subtask
├── completed-task ✅/                  # Completed task folder
│   ├── README.md                       # Archive of approach
│   └── ...
└── README.md                           # Task registry
```

### Naming Conventions

- **Emoji in folder name**: `name ◐` (in progress), `name ✅` (complete), no emoji (not started)
- **Subtask files**: Include number and descriptor: `subtask-1-description.md`
- **Status shown by file**: `subtask-name ✅.md` (done), `subtask-name ◐.md` (active), `subtask-name.md` (pending)

### Example Task: Adding PNK Support

```
.claude/tasks/
└── add-pnk-to-v5-bot ✅/
    ├── README.md
    ├── subtask-1-constants-and-route ✅.md    # Defined PNK routing path
    ├── subtask-2-buy-flow-sdai-weth-pnk ✅.md # Implemented BUY executor
    └── subtask-3-sell-flow-pnk-weth-sdai ✅.md # Implemented SELL executor
```

### Task Handoff

When handing off to AI agents:

1. **Create task folder**: `.claude/tasks/feature-name ◐/`
2. **Write README.md**: Problem statement, requirements, success criteria
3. **List subtasks**: Break into 3-5 logical steps
4. **Link to code examples**: Reference files that show patterns to follow
5. **Update as progress**: Mark completed subtasks, move to new ones

## Testing Patterns

### Python Tests (pytest)

Test files in `tests/test_*.py` focus on transaction building and simulation:

```python
# tests/test_eip7702.py - Example EIP-7702 test structure
import pytest
from eth_account import Account
from src.helpers.eip7702_builder import EIP7702TransactionBuilder

def test_authorization_signing():
    """Test that we can sign EIP-7702 authorizations."""
    private_key = "0x" + "1" * 64  # Test key only
    account = Account.from_key(private_key)
    
    auth = {
        "chainId": 100,  # Gnosis Chain
        "address": "0x0000000000000000000000000000000000000001",
        "nonce": 0
    }
    
    signed_auth = account.sign_authorization(auth)
    
    # Verify signature fields
    assert "yParity" in signed_auth
    assert "r" in signed_auth
    assert "s" in signed_auth

def test_transaction_builder():
    """Test the EIP-7702 transaction builder."""
    w3 = Web3(...)  # Mock provider
    builder = EIP7702TransactionBuilder(w3, impl_addr)
    
    builder.add_approval(token, spender, 2**256-1)
    builder.add_exact_input_single(pool, in_token, out_token, amount)
    
    tx = builder.build_transaction()
    
    assert len(tx['authorizationList']) == 1
    assert 'data' in tx
```

**Running tests**:
```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_eip7702.py::test_authorization_signing -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=html
```

### Solidity Tests (Foundry)

Contract tests in `tests/*.t.sol` use Foundry's test framework:

```solidity
// tests/PectraWrapper.t.sol - Example Foundry test
import "forge-std/Test.sol";
import "../contracts/PectraWrapper.sol";

contract PectraWrapperTest is Test {
    PectraWrapper public wrapper;
    address public user;

    function setUp() public {
        wrapper = new PectraWrapper();
        user = makeAddr("user");
    }

    function test_EIP7702_Delegation_Simulation() public {
        // 1. Etch wrapper code onto user (simulates EIP-7702 delegation)
        bytes memory code = address(wrapper).code;
        vm.etch(user, code);

        // 2. Prepare batch calls
        address[10] memory targets;
        targets[0] = address(0xCAFE);
        bytes[10] memory datas;
        datas[0] = hex"aabbccdd";

        // 3. User executes (via delegated code)
        vm.prank(user);
        PectraWrapper(payable(user)).execute10(targets, datas, 1);
    }

    function test_RevertIf_NotOwner() public {
        // Only owner or delegated address can execute
        address attacker = makeAddr("attacker");
        vm.prank(attacker);
        
        vm.expectRevert(PectraWrapper.OnlyOwner.selector);
        wrapper.execute10([address(0)], [bytes("")], 0);
    }
}
```

**Running Solidity tests**:
```bash
# All tests
forge test -vv

# Specific contract
forge test --match-contract PectraWrapperTest -vvv

# With gas report
forge test --gas-report

# With coverage
forge coverage

# Run with verbose traces
forge test --mt test_EIP7702_Delegation_Simulation -vvvv
```

### Test Patterns to Follow

1. **Unit tests**: Single function in isolation (e.g., `test_authorization_signing`)
2. **Integration tests**: Multiple components together (e.g., `test_eip7702_arbitrage.py`)
3. **Mock external calls**: Use Tenderly simulation instead of real blockchain calls in Python tests
4. **Event verification**: Use `vm.expectEmit()` in Solidity to verify logs
5. **State changes**: Check contract state before/after (Foundry's `console2` for debugging)

## Task Tracking (`.claude/tasks/`)

Use strict emoji naming:
- **Folder**: `folder-name ◐` (in progress), `folder-name ✅` (completed)
- **Subtask files**: `subtask-N-description ◐.md` (in progress), `subtask-N-description ✅.md` (done)

Example:
```
.claude/tasks/
├── add-pnk-to-v5-bot ◐/
│   ├── subtask-1-constants-and-route ✅.md
│   ├── subtask-2-buy-flow-sdai-weth-pnk ◐.md
│   └── subtask-3-sell-flow-pnk-weth-sdai ✅.md
└── futarchy-executor-v5-alignment ✅/
```

## Critical Integration Points (Quick Reference)

| Layer | Interface | Notes |
|-------|-----------|-------|
| **Balancer V2** | `balancer_swap.py` → `balancer_price.py` | Uses BatchRouter for conditionals |
| **Swapr/Algebra** | `swapr_swap.py` → `swapr_price.py` | Uniswap V3-compatible exactInputSingle |
| **FutarchyRouter** | `split_position.py`, `merge_position.py` | Conditional token operations |
| **Permit2** | Via executor contracts | Token approvals for batch operations |
| **EIP-7702 Pectra** | `PectraWrapper.sol`, `eip7702_builder.py` | Atomic bundled txs |
=======
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
>>>>>>> Stashed changes
