# Futarchy Arbitrage Bot

## Project Overview

This is a futarchy arbitrage bot for Gnosis Chain that monitors price discrepancies between Balancer pools and Swapr pools to execute profitable trades. The bot trades conditional Company tokens (YES/NO tokens) against sDAI when prices diverge from the synthetic "ideal" price.

### Features
- **Sequential Trading**: Traditional multi-transaction arbitrage execution
- **EIP-7702 Atomic Trading**: Execute complete arbitrage flows in a single atomic transaction using Pectra bundled transactions
- **Price Monitoring**: Real-time monitoring of Swapr and Balancer pools
- **Automated Arbitrage**: Automatic execution when profitable opportunities are detected

## Environment Setup

### Automated Setup (Recommended)

The project includes an automated setup script that handles Python environment creation, dependency installation, and toolchain setup.

#### Quick Start

```bash
# Clone the repository
git clone https://github.com/futarchy-fi/futarchy-arbitrage.git
cd futarchy-arbitrage

# Run automated setup
./setup.sh
```

#### What the Setup Script Does

1. **Python Version Detection**
   - Validates Python 3.9.23 (or 3.9.x) is installed
   - Provides platform-specific installation instructions if not found
   - Uses `.python-version` file for version pinning

2. **Virtual Environment Creation**
   - Creates `futarchy_env/` virtual environment
   - Prompts before overwriting existing environments
   - Activates environment automatically

3. **Dependency Installation**
   - Upgrades pip, setuptools, and wheel
   - Installs from `requirements.txt`
   - Installs package in editable mode via `pyproject.toml`
   - Optionally installs dev dependencies (pytest, black, mypy)

4. **Solidity Toolchain Setup**
   - Checks for `solc` (Solidity compiler)
   - Optionally installs solc 0.8.33
   - Checks for Foundry (forge)
   - Optionally installs Foundry toolchain

#### Manual Setup

If you prefer manual setup or the automated script fails:

```bash
# Create virtual environment
python3.9 -m venv futarchy_env

# Activate environment
source futarchy_env/bin/activate

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .

# Install dev dependencies (optional)
pip install -e ".[dev]"

# Install Foundry (for Solidity compilation)
curl -L https://foundry.paradigm.xyz | bash
foundryup
```

### Python Version Management

The project requires Python 3.9.x. We recommend using `pyenv` for managing Python versions:

```bash
# Install pyenv (macOS)
brew install pyenv

# Install Python 3.9.23
pyenv install 3.9.23
pyenv local 3.9.23

# Run setup
./setup.sh
```

### Environment Variables

The project uses Python virtual environments. Two common environments are used:
- `futarchy_env/` - Main virtual environment (created by setup.sh)
- `venv/` - Alternative virtual environment

Environment files follow the pattern `.env.0x<address>` where the address corresponds to different futarchy market addresses.

## Common Commands

### Virtual Environment Activation
```bash
source futarchy_env/bin/activate
# or
source venv/bin/activate
```

### Running the Arbitrage Bot

#### EIP-7702 Atomic Bot (Recommended)
```bash
# Run the EIP-7702 bot with atomic execution
source futarchy_env/bin/activate && source .env.0x<PROPOSAL_ADDRESS> && python -m src.arbitrage_commands.eip7702_bot \
    --amount 0.1 \
    --interval 120 \
    --tolerance 0.02

# Dry run mode for testing
source futarchy_env/bin/activate && source .env.0x<PROPOSAL_ADDRESS> && python -m src.arbitrage_commands.eip7702_bot \
    --amount 0.001 \
    --interval 30 \
    --tolerance 0.01 \
    --dry-run \
    --max-iterations 5
```

#### Sequential Bots (Legacy)
```bash
# Basic bot with environment variables
source futarchy_env/bin/activate && source .env.0x<PROPOSAL_ADDRESS> && python -m src.arbitrage_commands.simple_bot \
    --amount 0.01 \
    --interval 120 \
    --tolerance 0.2

# Side discovery
source futarchy_env/bin/activate && source .env.0x<PROPOSAL_ADDRESS> && python -m src.arbitrage_commands.complex_bot \
    --amount 0.1 \
    --interval 120 \
    --tolerance 0.04
```

### Installing Dependencies
```bash
pip install -r requirements.txt
```

### Running Tests
```bash
python -m pytest tests/
```

## Setup and Configuration

### Market Data Fetcher

The `fetch_market_data.py` script fetches market event data from Supabase and can automatically update environment files with the correct pool and token addresses.

#### Usage

```bash
# Activate environment
source futarchy_env/bin/activate && source .env.0x<PROPOSAL_ADDRESS>

# Fetch market event using FUTARCHY_PROPOSAL_ADDRESS and update environment file
python -m src.setup.fetch_market_data --proposal --update-env .env.0x<PROPOSAL_ADDRESS>

# Fetch specific market event by ID
python -m src.setup.fetch_market_data <market_event_id>

# Search all market events for address patterns
python -m src.setup.fetch_market_data --search-addresses
```

#### Features

- **Automatic Address Extraction**: Extracts pool and token addresses from Supabase market event metadata
- **Environment File Updates**: Updates `.env` files with correct addresses for:
  - `SWAPR_POOL_YES_ADDRESS` / `SWAPR_POOL_NO_ADDRESS`
  - `SWAPR_POOL_PRED_YES_ADDRESS` / `SWAPR_POOL_PRED_NO_ADDRESS`
  - `SWAPR_SDAI_YES_ADDRESS` / `SWAPR_SDAI_NO_ADDRESS`
  - `SWAPR_GNO_YES_ADDRESS` / `SWAPR_GNO_NO_ADDRESS`
- **Metadata Inspection**: View full market event metadata structure

#### Requirements

- `SUPABASE_URL` environment variable
- `SUPABASE_ANON_KEY`, `SUPABASE_EDGE_TOKEN`, or `SUPABASE_SERVICE_ROLE_KEY` environment variable
- `FUTARCHY_PROPOSAL_ADDRESS` environment variable (for --proposal mode)

## Code Architecture

### Core Structure
- `src/arbitrage_commands/` - Main trading strategies and bot logic
  - `eip7702_bot.py` - EIP-7702 atomic arbitrage bot with bundled transactions
  - `buy_cond_eip7702.py` - Atomic buy conditional flow using EIP-7702
  - `sell_cond_eip7702.py` - Atomic sell conditional flow using EIP-7702
  - `simple_bot.py` - Sequential arbitrage bot that monitors prices and executes trades
  - `complex_bot.py` - Price discovery and side determination
  - `buy_cond.py`, `sell_cond.py` - Sequential conditional token trading logic
  - `*_onchain.py` - On-chain execution variants
- `src/helpers/` - Utility functions for price fetching, swapping, and blockchain interaction
  - `eip7702_builder.py` - EIP-7702 transaction builder for atomic execution
  - `bundle_helpers.py` - Helper functions for bundled transactions
- `src/config/` - Configuration management including ABIs, contracts, tokens, and network settings
- `src/cli/` - Command-line interface dispatcher
- `src/setup/` - Initial setup utilities for allowances and verification

### Key Components

**Price Monitoring**: The bot calculates a synthetic "ideal" price from Swapr pools:
```
ideal_price = pred_price * yes_price + (1 - pred_price) * no_price
```

**Trading Logic**: 
- If both YES and NO prices on Swapr < Balancer price → Buy conditional Company tokens
- If both YES and NO prices on Swapr > Balancer price → Sell conditional Company tokens

**Buy Conditional Company Token Process** (`buy_cond.py`):
1. **Split sDAI** into YES and NO conditional sDAI tokens using FutarchyRouter
2. **Swap conditional sDAI to conditional Company tokens** on Swapr pools (both YES and NO)
3. **Merge conditional Company tokens** back into regular Company token using FutarchyRouter
4. **Handle imbalances**: If YES/NO amounts differ, liquidate excess conditional sDAI
5. **Sell Company token for sDAI** on Balancer to complete the arbitrage loop

**Conditional sDAI Liquidation** (`conditional_sdai_liquidation.py`):
- Handles imbalances when YES and NO token amounts don't match
- For excess YES tokens: Direct swap YES→sDAI on Swapr
- For excess NO tokens: Buy YES tokens with sDAI, then merge back to sDAI
- Uses 1% slippage tolerance for liquidation swaps

**Configuration System**: Uses a modular config system in `src/config/` with:
- Network settings (`network.py`)
- Contract addresses and ABIs (`contracts.py`, `abis/`)
- Token configurations (`tokens.py`)
- Pool configurations (`pools.py`)

### Environment Variables Required
- `RPC_URL` - Gnosis Chain RPC endpoint
- `PRIVATE_KEY` - Trading account private key
- `SWAPR_POOL_YES_ADDRESS` - Swapr YES token pool
- `SWAPR_POOL_PRED_YES_ADDRESS` - Swapr prediction YES pool
- `SWAPR_POOL_NO_ADDRESS` - Swapr NO token pool
- `BALANCER_POOL_ADDRESS` - Balancer pool address
- `FUTARCHY_ROUTER_ADDRESS` - FutarchyRouter contract for splitting/merging tokens
- `FUTARCHY_PROPOSAL_ADDRESS` - Futarchy proposal contract address
- `SDAI_TOKEN_ADDRESS` - sDAI token contract
- `COMPANY_TOKEN_ADDRESS` - Company token contract (previously GNO)
- `SWAPR_SDAI_YES_ADDRESS` - Conditional sDAI YES token
- `SWAPR_SDAI_NO_ADDRESS` - Conditional sDAI NO token
- `SWAPR_GNO_YES_ADDRESS` - Conditional Company YES token
- `SWAPR_GNO_NO_ADDRESS` - Conditional Company NO token

## Protocol Integration

The bot integrates with:
- **Balancer V2** - For conditional token trading
- **Swapr** - For price discovery (Algebra/Uniswap V3 compatible)
- **Gnosis Chain** - Network for all operations
- **sDAI** - Primary trading token (Savings DAI)
- **Futarchy Markets** - Conditional token systems

## Development Notes

- The `constants.py` module is deprecated; use the new config modules instead
- Use the CLI dispatcher in `src/cli/cli.py` for running individual modules
- All price calculations use `Decimal` for precision
- Trading amounts are specified in sDAI
- The bot includes comprehensive logging and error handling

### Code Style Guidelines
- **Logging**: Use `print()` statements for arbitrage commands, `logging` module for helpers
- **Comments**: Use section headers with dashes for major sections
- **Handler Functions**: Transaction simulation handlers should be prefixed with `handle_`
- **Debug Output**: Keep debug prints minimal; consolidate into single-line summaries
- **Error Handling**: Add descriptive error messages with context

### Transaction Flow

#### EIP-7702 Atomic Flow (Recommended)
The EIP-7702 bot executes all operations atomically:
1. Monitor prices and detect arbitrage opportunities
2. Build bundled transaction with all operations (split, swap, merge, Balancer trade)
3. Execute entire arbitrage atomically in a single transaction
4. Automatic rollback if any operation fails

**Benefits:**
- **Atomic Execution**: All-or-nothing execution prevents partial failures
- **Gas Efficiency**: Single transaction instead of multiple
- **MEV Protection**: Atomic execution prevents frontrunning between steps
- **Simplified Logic**: No need for complex simulation and state tracking

#### Sequential Flow (Legacy)
The sequential bots use a simulation-first approach:
1. Build transaction bundles as Tenderly-compatible dictionaries
2. Simulate transactions to calculate optimal parameters
3. Execute on-chain only after successful simulation
4. Each transaction has an associated handler function for state tracking

## EIP-7702 Atomic Arbitrage

### Overview
The EIP-7702 implementation uses Pectra bundled transactions to execute complex DeFi arbitrage atomically. This ensures all operations succeed or fail together, eliminating risks from partial execution.

### Architecture
- **FutarchyBatchExecutorMinimal**: Deployed at `0x65eb5a03635c627a0f254707712812B234753F31`
- **Authorization**: EOA temporarily delegates execution to the batch executor contract
- **Bundle Size**: Supports up to 10 operations per transaction

### Supported Operations

#### Buy Conditional Flow (`buy_cond_eip7702.py`)
1. Split sDAI into YES/NO conditional sDAI
2. Swap YES sDAI → YES Company on Swapr
3. Swap NO sDAI → NO Company on Swapr
4. Merge YES/NO Company back to Company token
5. Sell Company for sDAI on Balancer

#### Sell Conditional Flow (`sell_cond_eip7702.py`)
1. Buy Company with sDAI on Balancer
2. Split Company into YES/NO conditional Company
3. Swap YES Company → YES sDAI on Swapr
4. Swap NO Company → NO sDAI on Swapr
5. Merge YES/NO sDAI back to regular sDAI

### Usage Examples

```bash
# Run atomic buy conditional
python -m src.arbitrage_commands.buy_cond_eip7702 0.1

# Run atomic sell conditional
python -m src.arbitrage_commands.sell_cond_eip7702 0.1 --skip-merge

# Run monitoring bot with atomic execution
python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --tolerance 0.02
```
