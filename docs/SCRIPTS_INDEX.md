# Scripts Index - Futarchy Arbitrage Bot

**Total Scripts:** 49 Python files  
**Location:** `/scripts/`  
**Updated:** 2026-01-16

---

## Deployment Scripts

### Contract Deployment

| Script | Purpose | Contract | Notes |
|--------|---------|----------|-------|
| `deploy_executor_v4.py` | Deploy V4 executor | FutarchyArbExecutorV4 | EIP-7702 support |
| `deploy_executor_v5.py` | Deploy V5 executor | FutarchyArbExecutorV5 | **Current version**, PNK routing |
| `deploy_prediction_arb_v1.py` | Deploy prediction arbitrage | PredictionArbExecutorV1 | Yes+no price sum |
| `deploy_institutional_solver.py` | Deploy institutional solver | InstitutionalSolverSystem | Full solver system |
| `deploy_ticklens.py` | Deploy TickLens utility | TickLens | Tick data reading |
| `deploy_and_verify_v2.py` | Deploy + verify V2 | FutarchyArbitrageExecutorV2 | Legacy |

### Verification Scripts

| Script | Purpose | Notes |
|--------|---------|-------|
| `verify_contract.py` | Verify deployed contract | Generic verification |
| `verify_contract_v2.py` | Verify V2 contract | V2-specific |
| `verify_executor_v4.py` | Verify V4 executor | Etherscan/Gnosisscan |
| `verify_only_v2.py` | Verify-only (no deploy) | V2 verification |

---

## Bot Execution Scripts

### Main Bots

| Script | Bot Type | Execution | Notes |
|--------|----------|-----------|-------|
| `src/arbitrage_commands/simple_bot.py` | Sequential executor | Multi-tx | Classic approach |
| `src/arbitrage_commands/eip7702_bot.py` | Atomic executor | Single bundled tx | **Recommended** (MEV protection) |
| `src/arbitrage_commands/complex_bot.py` | Side discovery | Multi-tx | Price discovery first |
| `src/arbitrage_commands/arbitrage_bot_v2.py` | JSON config-driven | Configurable | Supports multiple bot types |
| `src/arbitrage_commands/unified_bot.py` | Database-driven | Supabase config | HD wallet derivation |

### Bot Types (arbitrage_bot_v2)
- `balancer` (default): Conditional token arbitrage
- `pnk`/`kleros`: PNK markets with WETH routing
- `prediction`: Delegates to prediction_arb_executor

### Executor CLI

| Script | Purpose | Notes |
|--------|---------|-------|
| `src/executor/arbitrage_executor.py` | V5 BUY/SELL execution | `--flow buy/sell --amount X --cheaper yes/no` |
| `src/executor/prediction_arb_executor.py` | Prediction arbitrage | `--amount X --min-profit Y` |
| `src/executor/futarchy_pnk_executor.py` | PNK-specific executor | WETH routing |
| `src/executor/tx_7702_executor.py` | EIP-7702 bundle builder | V4 contract |

---

## Trading Flow Scripts

### BUY Flow (Split → Swap → Merge)

| Script | Type | Description |
|--------|------|-------------|
| `src/arbitrage_commands/buy_cond.py` | Sequential | Split sDAI → swap to Company conditionals → merge |
| `scripts/buy_cond_sequential_eip7702.py` | EIP-7702 | Sequential with delegation |
| `scripts/buy_cond_complete_eip7702.py` | EIP-7702 | Complete atomic BUY |
| `scripts/force_buy_cond_eip7702.py` | EIP-7702 | Forced execution |
| `scripts/test_buy_cond_flow.py` | Test | BUY flow testing |

### SELL Flow (Buy → Split → Swap)

| Script | Type | Description |
|--------|------|-------------|
| `src/arbitrage_commands/sell_cond.py` | Sequential | Buy Company → split → swap conditionals |

### Conditional sDAI Liquidation

| Script | Purpose |
|--------|---------|
| `src/arbitrage_commands/conditional_sdai_liquidation.py` | Handle excess YES/NO after swaps |

**Liquidation Logic:**
- Excess YES: Direct swap YES→sDAI on Swapr
- Excess NO: Buy YES with sDAI → merge back to sDAI (two-step)
- Uses 1% slippage tolerance

---

## PNK Trading Scripts

### sDAI ↔ PNK Routes (Balancer Vault + Swapr)

| Script | Route | Description |
|--------|-------|-------------|
| `scripts/sdai_to_pnk_trade.py` | Basic | Simple sDAI→PNK trade |
| `scripts/sdai_to_pnk_via_balancer_and_swapr.py` | Multi-hop | Balancer→Swapr routing |
| `scripts/sdai_to_pnk_balancer_vault_then_swapr.py` | **Vault** | **Uses Balancer Vault batchSwap** |
| `scripts/sdai_to_pnk_balancer_then_swapr_inline.py` | Inline | Inline swap implementation |
| `scripts/call_buy_pnk_with_sdai.py` | V5 BUY | Calls V5 `buyPnkWithSdai()` |
| `scripts/call_sell_pnk_for_sdai.py` | V5 SELL | Calls V5 `sellPnkForSdai()` |

**Key Route:** sDAI → WETH (Balancer Vault) → PNK (Swapr v2)

---

## EIP-7702 Testing Scripts

### Basic Tests

| Script | Focus | Notes |
|--------|-------|-------|
| `scripts/test_eip7702_basic.py` | Basic delegation | Simple test |
| `scripts/test_eip7702_minimal.py` | Minimal setup | Minimal delegation |
| `scripts/test_eip7702_gnosis.py` | Gnosis Chain | Network-specific |
| `scripts/test_eip7702_onchain.py` | On-chain execution | Live chain test |

### Advanced EIP-7702 Tests

| Script | Focus | Notes |
|--------|-------|-------|
| `scripts/test_pectra_minimal.py` | Pectra upgrade | Minimal Pectra test |
| `scripts/test_pectra_onchain.py` | Pectra on-chain | Live Pectra test |
| `scripts/test_pectra_force_onchain.py` | Forced Pectra | Force execution |
| `scripts/debug_pectra_minimal.py` | Pectra debugging | Debug Pectra issues |
| `scripts/successful_eip7702_demo.py` | Working demo | **Reference implementation** |

### Swapr + EIP-7702

| Script | Focus | Notes |
|--------|-------|-------|
| `scripts/test_swapr_eip7702.py` | Swapr integration | Swapr with delegation |
| `scripts/swapr_eip7702_working.py` | **Working version** | **Production-ready** |
| `scripts/test_split_eip7702.py` | Split operation | Split with delegation |

---

## Setup & Configuration Scripts

### Initial Setup

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/setup_approvals_eip7702.py` | Set up EIP-7702 approvals | Permit2 configuration |
| `scripts/setup_eip7702_approvals.py` | Alternative setup | Different approach |
| `src/setup/fetch_market_data.py` | Fetch from Supabase | Updates `.env.0x<ADDRESS>` files |

**Fetch Market Data Usage:**
```bash
python -m src.setup.fetch_market_data --proposal --update-env .env.0x<PROPOSAL_ADDRESS>
```

**Address Mapping:** Extracts pool/token addresses from Supabase market event metadata

---

## Analysis & Debugging Scripts

### Bytecode Analysis

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/analyze_bytecode.py` | Analyze contract bytecode | Size, opcodes |
| `scripts/compile_without_yul.py` | Compile without Yul | Debugging |

### Interface Analysis

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/analyze_swapr_interface.py` | Analyze Swapr ABI | Interface inspection |

### Transaction Debugging

| Script | Focus | Notes |
|--------|-------|-------|
| `scripts/debug_transaction.py` | Generic tx debug | Tenderly integration |
| `scripts/debug_eip7702_transaction.py` | EIP-7702 tx debug | Delegation debugging |
| `scripts/debug_swapr_swap.py` | Swapr swap debug | Swap issues |

### Liquidity & Tick Analysis

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/fetch_algebra_liquidity.py` | Fetch Algebra liquidity | Swapr liquidity data |
| `scripts/tick_reader.py` | Read tick data | Tick bitmap reading |
| `scripts/test_ticklens_and_ticktable.py` | Test TickLens | Tick data utilities |

---

## Testing Scripts

### Contract Testing

| Script | Focus | Notes |
|--------|-------|-------|
| `scripts/test_deployed_v2.py` | Test V2 deployment | Post-deployment tests |
| `scripts/test_deployment_fix.py` | Test deployment fixes | Fix verification |
| `scripts/test_individual_steps.py` | Test individual steps | Step-by-step testing |

### Balancer Testing

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/run_balancer_buy.py` | Test Balancer buy | Buy flow testing |

---

## Utility Scripts

### Environment & Config

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/convert_env_to_json.py` | Convert .env to JSON | Config conversion |

### Event Monitoring

| Script | Purpose | Notes |
|--------|---------|-------|
| `scripts/subscribe.py` | Subscribe to events | Event monitoring |

---

## Script Execution Patterns

### Sequential Bot
```bash
source futarchy_env/bin/activate
source .env.0x<PROPOSAL_ADDRESS>
python -m src.arbitrage_commands.simple_bot --amount 0.01 --interval 120 --tolerance 0.2
```

### EIP-7702 Bot (Recommended)
```bash
python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --interval 120 --tolerance 0.02
```

### JSON Config Bot
```bash
python -m src.arbitrage_commands.arbitrage_bot_v2 --config config/proposal.json
```

### Unified Bot (Database-Driven)
```bash
python -m src.arbitrage_commands.unified_bot --bot-name my-arb-bot --dry-run
```

### Executor CLI
```bash
# SELL flow
python -m src.executor.arbitrage_executor --flow sell --amount 0.01 --cheaper yes --execute

# BUY flow
python -m src.executor.arbitrage_executor --flow buy --amount 0.01 --cheaper yes --execute

# Prediction arbitrage
python -m src.executor.prediction_arb_executor --amount 0.05 --min-profit -0.001
```

---

## Script Categories Summary

| Category | Count | Key Scripts |
|----------|-------|-------------|
| **Deployment** | 6 | `deploy_executor_v5.py`, `deploy_institutional_solver.py` |
| **Verification** | 4 | `verify_contract.py`, `verify_executor_v4.py` |
| **Bot Execution** | 5 | `eip7702_bot.py`, `simple_bot.py`, `unified_bot.py` |
| **Trading Flows** | 6 | `buy_cond.py`, `sell_cond.py`, `conditional_sdai_liquidation.py` |
| **PNK Trading** | 6 | `call_buy_pnk_with_sdai.py`, `sdai_to_pnk_balancer_vault_then_swapr.py` |
| **EIP-7702 Tests** | 11 | `successful_eip7702_demo.py`, `swapr_eip7702_working.py` |
| **Setup** | 3 | `setup_approvals_eip7702.py`, `fetch_market_data.py` |
| **Analysis** | 8 | `analyze_bytecode.py`, `debug_transaction.py`, `tick_reader.py` |
| **Testing** | 3 | `test_deployed_v2.py`, `test_individual_steps.py` |
| **Utilities** | 2 | `convert_env_to_json.py`, `subscribe.py` |

**Total:** 49 scripts

---

## Related Documentation

- **API Map:** [docs/API_MAP.md](./API_MAP.md) - Complete contract API reference
- **CLAUDE.md:** [CLAUDE.md](../CLAUDE.md) - Development workflow and patterns
- **Copilot Instructions:** [.github/copilot-instructions.md](../.github/copilot-instructions.md) - AI agent instructions

---

## Script Maintenance Notes

1. **Production Scripts:** Use `eip7702_bot.py`, `unified_bot.py`, or `arbitrage_bot_v2.py`
2. **Testing Scripts:** Many test scripts are for historical debugging - check timestamps
3. **Deprecated:** `simple_bot.py` (sequential) is deprecated but functional
4. **PNK Integration:** All PNK scripts require V5 executor with WETH routing
5. **EIP-7702:** Requires Pectra-compatible node (experimental on Gnosis)

---

**Next Steps:**
- Archive deprecated test scripts to `scripts/archive/`
- Create script usage guide with example commands
- Add health check scripts for production bots
