# Futarchy Arbitrage Bot - Complete Setup & Usage Guide

> **For AI Agents & Developers**: This document provides step-by-step instructions for setting up, configuring, and operating the Futarchy Arbitrage Bot. Follow sections in order for first-time setup.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [Market Configuration](#market-configuration)
4. [Bot Selection Guide](#bot-selection-guide)
5. [Running the Bot](#running-the-bot)
6. [Testing](#testing)
7. [Smart Contract Deployment](#smart-contract-deployment)
8. [Production Monitoring](#production-monitoring)
9. [Troubleshooting](#troubleshooting)
10. [Infrastructure Overview](#infrastructure-overview)

---

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | ≥3.10 (3.14 recommended) | Bot runtime |
| Foundry | Latest | Solidity compilation & testing |
| Git | Any | Version control |
| Node.js | ≥18 (optional) | TickLens deployment |

### Required Accounts & Keys

- **Gnosis Chain RPC**: Public (`https://rpc.gnosis.gateway.fm`) or private (Alchemy, Infura)
- **Private Key**: EOA with ETH (for gas) and sDAI (for trading)
- **Supabase**: Project URL + API key (for market data)
- **Tenderly** (optional): For transaction simulation
- **Gnosisscan API Key** (optional): For contract verification

### Minimum Balances

| Token | Minimum | Purpose |
|-------|---------|---------|
| xDAI (ETH) | 0.01 | Gas fees |
| sDAI | 0.1 | Trading capital |

---

## Environment Setup

### Step 1: Clone & Create Virtual Environment

```bash
# Clone repository
git clone https://github.com/mrheyday/futarchy-arbitrage.git
cd futarchy-arbitrage

# Create Python virtual environment
python3 -m venv futarchy_env

# Activate (do this every session)
source futarchy_env/bin/activate
```

### Step 2: Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Verify installation
python -c "from web3 import Web3; print('web3 OK')"
python -c "from eth_account import Account; print('eth_account OK')"

# Install Foundry (if not already installed)
curl -L https://foundry.paradigm.xyz | bash
foundryup

# Install Solidity dependencies
forge install
```

### Step 3: Create Environment File

```bash
# Copy template
cp .env.example .env.0x<YOUR_PROPOSAL_ADDRESS>

# Edit with your values
nano .env.0x<YOUR_PROPOSAL_ADDRESS>
```

**Required variables** (minimum for bot operation):

```bash
# Network
RPC_URL=https://rpc.gnosis.gateway.fm
PRIVATE_KEY=0x...your_private_key...

# Market (will be auto-populated by fetch_market_data)
FUTARCHY_PROPOSAL_ADDRESS=0x...
FUTARCHY_ROUTER_ADDRESS=0x...

# Supabase (for market data fetching)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_key_here
```

### Step 4: Verify Setup

```bash
# Source environment
source futarchy_env/bin/activate
source .env.0x<YOUR_PROPOSAL_ADDRESS>

# Verify wallet connection
python3 << 'EOF'
import os
from web3 import Web3
from eth_account import Account

w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
print(f"Connected: {w3.is_connected()}")
print(f"Chain ID: {w3.eth.chain_id}")

if os.getenv("PRIVATE_KEY"):
    account = Account.from_key(os.getenv("PRIVATE_KEY"))
    balance = w3.eth.get_balance(account.address)
    print(f"Address: {account.address}")
    print(f"ETH Balance: {balance / 1e18:.6f}")
EOF
```

**Expected output**:

```text
Connected: True
Chain ID: 100
Address: 0x...
ETH Balance: 0.05...
```

---

## Market Configuration

### Automatic Setup (Recommended)

Fetch pool/token addresses from Supabase market events:

```bash
# Ensure environment is sourced
source futarchy_env/bin/activate
source .env.0x<PROPOSAL_ADDRESS>

# Fetch and update environment file
python -m src.setup.fetch_market_data --proposal --update-env .env.0x<PROPOSAL_ADDRESS>
```

**Expected output**:

```text
Fetching market event for proposal: 0x...
Found market event with ID: ...
Updating environment file...
✓ SWAPR_POOL_YES_ADDRESS=0x...
✓ SWAPR_POOL_NO_ADDRESS=0x...
✓ SWAPR_SDAI_YES_ADDRESS=0x...
Environment file updated successfully!
```

### Manual Setup

If Supabase is unavailable, manually set these in your `.env` file:

```bash
# Pool addresses (from Swapr UI or block explorer)
SWAPR_POOL_YES_ADDRESS=0x...
SWAPR_POOL_NO_ADDRESS=0x...
SWAPR_POOL_PRED_YES_ADDRESS=0x...
SWAPR_POOL_PRED_NO_ADDRESS=0x...
BALANCER_POOL_ADDRESS=0x...

# Token addresses
SDAI_TOKEN_ADDRESS=0xaf204776c7245bF4147c2612BF6e5972Ee483701
COMPANY_TOKEN_ADDRESS=0x...
SWAPR_SDAI_YES_ADDRESS=0x...
SWAPR_SDAI_NO_ADDRESS=0x...
SWAPR_GNO_YES_ADDRESS=0x...
SWAPR_GNO_NO_ADDRESS=0x...
```

### Verify Market Configuration

```bash
python3 << 'EOF'
import os
required = [
    "RPC_URL", "PRIVATE_KEY", "FUTARCHY_PROPOSAL_ADDRESS",
    "SWAPR_POOL_YES_ADDRESS", "SWAPR_POOL_NO_ADDRESS",
    "BALANCER_POOL_ADDRESS"
]
missing = [v for v in required if not os.getenv(v)]
if missing:
    print(f"❌ Missing: {', '.join(missing)}")
else:
    print("✓ All required environment variables set")
EOF
```

---

## Bot Selection Guide

### Decision Tree

```text
┌─────────────────────────────────────────────────────────────┐
│                    What do you need?                        │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
   Production?           Testing?              PNK Market?
        │                     │                     │
        ▼                     ▼                     ▼
  eip7702_bot.py        complex_bot.py       pnk_light_bot.py
  (atomic, MEV-safe)    (side discovery)     (multi-hop route)
```

### Bot Comparison

| Bot | File | Use Case | Execution |
|-----|------|----------|-----------|
| **EIP-7702 Bot** | `eip7702_bot.py` | Production trading | Atomic (single tx) |
| **Complex Bot** | `complex_bot.py` | Discover profitable side | Sequential |
| **Simple Bot** | `simple_bot.py` | Basic testing | Sequential |
| **Light Bot** | `light_bot.py` | Minimal dependencies | Sequential |
| **PNK Bot** | `pnk_light_bot.py` | Kleros/PNK markets | Multi-hop |
| **Unified Bot** | `unified_bot.py` | Multi-market (Supabase) | Database-driven |
| **Arbitrage Bot V2** | `arbitrage_bot_v2.py` | JSON config markets | Configurable |

### Command-Line Arguments

All bots support these common arguments:

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--amount` | float | 0.1 | Trade amount in sDAI |
| `--interval` | int | 120 | Seconds between price checks |
| `--tolerance` | float | 0.02 | Price deviation threshold (2%) |
| `--dry-run` | flag | false | Simulate only, don't execute |
| `--max-iterations` | int | ∞ | Stop after N iterations |
| `--execute` | flag | false | Actually broadcast transactions |

---

## Running the Bot

### Production Mode (EIP-7702)

```bash
# Activate and source environment
source futarchy_env/bin/activate
source .env.0x<PROPOSAL_ADDRESS>

# Preview mode (safe, no execution)
python -m src.arbitrage_commands.eip7702_bot \
    --amount 0.1 \
    --interval 120 \
    --tolerance 0.02

# Execute mode (broadcasts transactions)
python -m src.arbitrage_commands.eip7702_bot \
    --amount 0.1 \
    --interval 120 \
    --tolerance 0.02 \
    --execute
```

**Expected output** (preview mode):

```text
[2026-01-17 10:30:00] Starting EIP-7702 arbitrage bot...
[2026-01-17 10:30:01] Checking prices...
[2026-01-17 10:30:01] YES Price: 0.4521 | NO Price: 0.5234
[2026-01-17 10:30:01] Ideal Price: 0.4877 | Balancer: 0.4950
[2026-01-17 10:30:01] Deviation: 1.5% (below tolerance 2%)
[2026-01-17 10:30:01] No arbitrage opportunity. Waiting 120s...
```

### Testing Mode (Dry Run)

```bash
python -m src.arbitrage_commands.eip7702_bot \
    --amount 0.001 \
    --interval 30 \
    --tolerance 0.01 \
    --dry-run \
    --max-iterations 5
```

### Side Discovery

Find which direction (BUY or SELL) is profitable:

```bash
python -m src.arbitrage_commands.complex_bot \
    --amount 0.1 \
    --interval 120 \
    --tolerance 0.04
```

### Direct Execution (Skip Bot Loop)

Execute a single trade directly:

```bash
# BUY conditional flow
python -m src.arbitrage_commands.buy_cond_eip7702 0.1

# SELL conditional flow
python -m src.arbitrage_commands.sell_cond_eip7702 0.1

# Via executor module
python -m src.executor.arbitrage_executor \
    --flow sell \
    --amount 0.01 \
    --cheaper yes \
    --execute
```

### Background Execution (Systemd)

For production servers:

```bash
# Copy service file
sudo cp src/arbitrage_commands/futarchy-arb.service /etc/systemd/system/

# Edit configuration
sudo nano /etc/systemd/system/futarchy-arb.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable futarchy-arb
sudo systemctl start futarchy-arb

# Check status
sudo systemctl status futarchy-arb
journalctl -u futarchy-arb -f
```

---

## Testing

### Python Tests (pytest)

```bash
# Activate environment
source futarchy_env/bin/activate

# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_eip7702.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

**Expected output**:

```text
tests/test_eip7702.py::test_authorization_signing PASSED
tests/test_eip7702.py::test_transaction_builder PASSED
tests/test_split_position.py::test_split_encoding PASSED
...
========================= 12 passed in 3.45s =========================
```

### Solidity Tests (Foundry)

```bash
# Run all tests
forge test -vv

# Run specific contract tests
forge test --match-contract FutarchyArbExecutorV5Test -vvv
forge test --match-contract SafetyModuleTest -vvv

# Run with gas report
forge test --gas-report

# Run with coverage
forge coverage

# Generate gas snapshot
forge snapshot
```

**Expected output** (104 tests passing):

```text
[PASS] test_buy_conditional_arbitrage_balancer() (gas: 245832)
[PASS] test_sell_conditional_arbitrage_balancer() (gas: 238421)
...
Test result: ok. 104 passed; 0 failed; finished in 2.34s
```

### CI/CD Pipeline

The project includes GitHub Actions CI (`.github/workflows/ci.yml`):

- **Solidity Tests**: Foundry build + test + coverage
- **Python Tests**: pytest on Python 3.10/3.11/3.12
- **Linting**: forge fmt, black, isort
- **Security**: Slither static analysis

View results at: `https://github.com/mrheyday/futarchy-arbitrage/actions`

---

## Smart Contract Deployment

### Compile Contracts

```bash
# Compile all contracts
forge build --sizes

# Compile specific contract
python3 scripts/compile_all.py --contract FutarchyArbExecutorV5

# With formal verification (SMT)
python3 scripts/compile_all.py --contract SafetyModule --smt
```

### Deploy to Gnosis Chain

```bash
# Set deployment environment
export GNOSISSCAN_API_KEY=your_api_key

# Deploy Executor V5
python3 scripts/deploy_executor_v5.py

# Deploy SafetyModule (Chiado testnet)
python3 scripts/deploy_safety_module_chiado.py
```

**Expected output**:

```text
Deploying FutarchyArbExecutorV5...
Transaction hash: 0x...
Waiting for confirmation...
✓ Contract deployed at: 0x0A20e7398B884f69b886a626fa096976bc93Ee3d
Verifying on Gnosisscan...
✓ Verification successful!
```

### Verify Existing Contract

```bash
# Verify on Gnosisscan
forge verify-contract \
    0x0A20e7398B884f69b886a626fa096976bc93Ee3d \
    contracts/FutarchyArbExecutorV5.sol:FutarchyArbExecutorV5 \
    --chain gnosis \
    --etherscan-api-key $GNOSISSCAN_API_KEY
```

### Deployed Contracts Reference

| Contract | Address | Network |
|----------|---------|---------|
| FutarchyArbExecutorV5 | `0x0A20e7398B884f69b886a626fa096976bc93Ee3d` | Gnosis |
| PredictionArbExecutorV1 | `0x4244ab9b8BA6A1F969E867c5Bf06ea7720c7Eb10` | Gnosis |

---

## Production Monitoring

### Slack Alerts

Set up real-time notifications for circuit breaker events:

```bash
# Configure webhook
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
export SLACK_MENTION_USERS="U01234567"  # Optional user mentions

# Test connection
python -m src.monitoring.slack_alerts --test

# Start monitoring
export SAFETY_MODULE_ADDRESS="0x..."
python -m src.monitoring.slack_alerts --start-block latest
```

**Alert types**:

- 🚨 `SlippageCircuitTripped` - Trade blocked (>5% slippage)
- ⚠️ `GasCircuitTripped` - Trade blocked (>100 gwei)
- 🚨 `DailyLossCircuitTripped` - Daily loss limit exceeded
- ⏸️ `EmergencyPaused` - All trading paused

### Telegram Alerts

```bash
export TELEGRAM_BOT_TOKEN="your_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

python -m src.monitoring.telegram_alerts --start
```

### Logging

Logs are configured in `config/logging.yaml`:

```bash
# View real-time logs
tail -f logs/bot.log

# View errors only
tail -f logs/errors.log

# View trade audit trail
tail -f logs/trades.log
```

### Log Rotation

```bash
# Setup logrotate
sudo cp config/logrotate.conf /etc/logrotate.d/futarchy-arb
sudo logrotate -f /etc/logrotate.d/futarchy-arb
```

---

## Troubleshooting

### Environment Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError: web3` | Dependencies not installed | `pip install -r requirements.txt` |
| `KeyError: 'SWAPR_POOL_YES_ADDRESS'` | Missing env vars | Run `fetch_market_data --update-env` |
| `FUTARCHY_PROPOSAL_ADDRESS is None` | Env not sourced | `source .env.0x<ADDRESS>` |
| `Connection refused` (RPC) | Wrong RPC URL | Verify `echo $RPC_URL` |

### Balance Issues

| Error | Minimum Required | Solution |
|-------|------------------|----------|
| `sDAI balance too low` | 0.01 sDAI | Fund wallet or `pull_sdai --amount 1.0` |
| `ETH balance too low` | 0.001 xDAI | Bridge ETH or use Chiado faucet |
| `Gas estimation failed` | N/A | Reduce `--amount` or increase gas limit |

### Transaction Failures

| Error | Cause | Solution |
|-------|-------|----------|
| `Slippage exceeded tolerance` | Price moved | Increase `--tolerance` (e.g., 0.05) |
| `SafetyModule circuit breaker` | Limits hit | Wait, check Slack alerts |
| `EIP-7702 authorization failed` | Wrong chain ID | Verify `chainId: 100` |
| `Insufficient liquidity` | Pool empty | Try smaller amount or wait |

### Price/Profitability Issues

| Symptom | Debug Step | Fix |
|---------|------------|-----|
| No opportunities found | Check tolerance | Lower `--tolerance` to 0.01 |
| Bot trades but loses | Check Tenderly trace | Verify ideal price formula |
| Sudden profitability drop | Check gas prices | Adjust min-profit threshold |

### Debug Commands

```bash
# Check wallet balance
python3 << 'EOF'
import os
from web3 import Web3
w3 = Web3(Web3.HTTPProvider(os.getenv("RPC_URL")))
addr = "0x..."  # Your address
print(f"ETH: {w3.eth.get_balance(addr) / 1e18:.6f}")
EOF

# Check pool prices
python3 << 'EOF'
from src.helpers.swapr_price import get_pool_price
from src.helpers.balancer_price import get_pool_price as bal_price
print(f"Swapr YES: {get_pool_price('yes_pool')}")
print(f"Balancer: {bal_price()}")
EOF

# Test Tenderly connection
python3 << 'EOF'
import os
from src.helpers.tenderly_api import TenderlyClient
client = TenderlyClient()
print(f"Tenderly connected: {client.is_configured()}")
EOF
```

---

## Infrastructure Overview

### System Architecture

```text
┌─────────────────────────────────────────────────────────────────┐
│                        Arbitrage Bot                            │
├─────────────────────────────────────────────────────────────────┤
│  src/arbitrage_commands/                                        │
│  ├── eip7702_bot.py      ← Main production entry point          │
│  ├── simple_bot.py       ← Sequential fallback                  │
│  └── complex_bot.py      ← Side discovery                       │
├─────────────────────────────────────────────────────────────────┤
│  src/helpers/                                                   │
│  ├── balancer_swap.py    ← Balancer V2 integration              │
│  ├── swapr_swap.py       ← Swapr/Algebra integration            │
│  ├── split_position.py   ← FutarchyRouter split                 │
│  ├── merge_position.py   ← FutarchyRouter merge                 │
│  └── eip7702_builder.py  ← Atomic transaction builder           │
├─────────────────────────────────────────────────────────────────┤
│  src/config/                                                    │
│  ├── network.py          ← RPC, chain settings                  │
│  ├── contracts.py        ← Contract addresses                   │
│  ├── tokens.py           ← Token configs                        │
│  └── abis/               ← Contract ABIs                        │
├─────────────────────────────────────────────────────────────────┤
│  src/monitoring/                                                │
│  ├── slack_alerts.py     ← Slack notifications                  │
│  └── telegram_alerts.py  ← Telegram notifications               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Smart Contracts                            │
├─────────────────────────────────────────────────────────────────┤
│  FutarchyArbExecutorV5   ← Main executor (buy/sell flows)       │
│  PredictionArbExecutorV1 ← Prediction market arbitrage          │
│  SafetyModule            ← Circuit breakers                     │
│  PectraWrapper           ← EIP-7702 delegation                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Protocols                         │
├─────────────────────────────────────────────────────────────────┤
│  Balancer V2             ← Company/sDAI trading                 │
│  Swapr (Algebra)         ← Conditional token pools              │
│  FutarchyRouter          ← Token splitting/merging              │
│  Gnosis Chain            ← Network (Chain ID: 100)              │
└─────────────────────────────────────────────────────────────────┘
```

### Safety Module

The `SafetyModule.sol` contract provides circuit breakers:

| Circuit Breaker | Threshold | Effect |
|-----------------|-----------|--------|
| Slippage | >5% | Reverts transaction |
| Gas Price | >100 gwei | Blocks trade |
| Daily Loss | >10 ETH | Pauses trading |
| Emergency | Manual | Owner can pause all |

### Logging Configuration

Configured in `config/logging.yaml`:

| Logger | Level | Output | Purpose |
|--------|-------|--------|---------|
| `eip7702_bot` | DEBUG | console, file | Bot operations |
| `trade` | INFO | trades.log | Audit trail |
| `safety` | WARNING | monitoring.log | Circuit breakers |
| `web3` | WARNING | file | Reduce noise |

### File Structure Reference

```text
futarchy-arbitrage/
├── .env.example           ← Environment template
├── .github/workflows/     ← CI/CD pipeline
├── CLAUDE.md              ← AI agent instructions
├── SETUP.md               ← This file
├── README.md              ← Project overview
├── requirements.txt       ← Python dependencies
├── foundry.toml           ← Solidity config
├── contracts/             ← Solidity source
├── deployments/           ← Deployment records
├── src/
│   ├── arbitrage_commands/← Bot entry points
│   ├── executor/          ← Execution wrappers
│   ├── helpers/           ← Utility functions
│   ├── config/            ← Configuration
│   ├── monitoring/        ← Alerts & dashboards
│   └── setup/             ← Setup utilities
├── test/                  ← Foundry tests
├── tests/                 ← Python tests
├── scripts/               ← Deployment & utility scripts
├── config/                ← Logging & rotation config
└── logs/                  ← Runtime logs
```

---

## Quick Reference Card

### Daily Operations

```bash
# Start bot
source futarchy_env/bin/activate
source .env.0x<PROPOSAL>
python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --execute

# Check logs
tail -f logs/bot.log

# Stop bot
Ctrl+C
```

### Update Market Data

```bash
python -m src.setup.fetch_market_data --proposal --update-env .env.0x<PROPOSAL>
```

### Run Tests

```bash
python -m pytest tests/ -v    # Python
forge test -vv                # Solidity
```

### Deploy Contract

```bash
python3 scripts/deploy_executor_v5.py
```

---

## Related Documentation

- **CLAUDE.md**: AI agent coding guidelines
- **README.md**: Project overview
- **docs/PRODUCTION_DEPLOYMENT.md**: Detailed production guide
- **docs/SLACK_ALERTS_QUICKSTART.md**: Alert setup
- **.augment/rules/imported/copilot-instructions.md**: Copilot context

