# Production Deployment Guide

## Overview

This guide covers deploying the futarchy arbitrage bot to production with monitoring, alerting, hardware wallet security, and Polymarket integration.

**New:** Chiado testnet deployment with SafetyModule and Slack alerts (see [Chiado Testnet Deployment](#chiado-testnet-deployment))

## Prerequisites

- Foundry (for Solidity contracts)
- Python 3.9+
- Ledger Nano S/X or Trezor hardware wallet
- RPC endpoints: Gnosis Chain, Polygon (for Polymarket)
- Notification webhooks: Discord/Slack

## Installation

### 1. Install Dependencies

```bash
# Core dependencies
pip install -r requirements.txt

# Extended features (monitoring, hardware wallets, Polymarket)
pip install -r requirements-extended.txt
```

### 2. Hardware Wallet Setup

#### Ledger
```bash
# Install Ledger libraries
pip install ledgerblue

# Connect device and unlock
# Open Ethereum app on Ledger
```

#### Trezor
```bash
# Install Trezor libraries
pip install trezor[ethereum]

# Connect device and unlock
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Configure RPC endpoints
RPC_URL=https://gnosis-rpc.publicnode.com
POLYGON_RPC_URL=https://polygon-rpc.com

# Configure monitoring webhooks
DISCORD_WEBHOOK=https://discord.com/api/webhooks/...
SLACK_WEBHOOK=https://hooks.slack.com/services/...

# Hardware wallet config
HARDWARE_WALLET_TYPE=ledger  # or trezor
DERIVATION_PATH=m/44'/60'/0'/0/0
```

## Deploy Contracts

### 1. Compile Solidity Contracts

```bash
# Compile all contracts
forge build

# Verify compilation
forge build --sizes
```

### 2. Run Tests

```bash
# Run all tests
forge test -vvv

# Run specific test suites
forge test --match-contract FutarchyArbExecutorV5Test
forge test --match-contract PredictionArbExecutorV1Test
forge test --match-contract InstitutionalSolverSystemTest

# Check coverage
forge coverage
```

### 3. Deploy V5 Executor

```bash
# Deploy to Gnosis Chain
python scripts/deploy_executor_v5.py

# Verify on Blockscout
forge verify-contract \
  --chain-id 100 \
  --compiler-version 0.8.33 \
  <CONTRACT_ADDRESS> \
  contracts/FutarchyArbExecutorV5.sol:FutarchyArbExecutorV5
```

## Configure Monitoring

### 1. Setup Alerts

```python
from src.helpers.monitoring import MonitoringClient, setup_default_alerts

monitor = MonitoringClient(
    discord_webhook=os.getenv("DISCORD_WEBHOOK"),
    slack_webhook=os.getenv("SLACK_WEBHOOK")
)

# Configure default alerts
setup_default_alerts(monitor)

# Add custom alerts
monitor.add_alert("balance.sdai.critical", "critical", 0.05, "lt", cooldown=300)
monitor.add_alert("trade.profit.excellent", "info", 0.5, "gt", cooldown=3600)
```

### 2. Health Monitoring

```python
# Run health checks every 60 seconds
import asyncio

async def monitor_loop():
    while True:
        health = await monitor.check_health(web3)
        
        if health["checks"]["rpc"]["status"] != "healthy":
            # Send alert
            await monitor._trigger_alert(...)
        
        await asyncio.sleep(60)
```

## Hardware Wallet Integration

### 1. Initialize Hardware Wallet

```python
from src.helpers.hardware_wallet import HardwareWalletManager

hw_wallet = HardwareWalletManager(
    wallet_type="ledger",
    derivation_path="m/44'/60'/0'/0/0"
)

# Get address (displays on device for verification)
address = hw_wallet.get_address(verify=True)
print(f"Trading address: {address}")
```

### 2. Sign Transactions

```python
# Build transaction
tx = {
    "to": executor_address,
    "value": 0,
    "data": executor.encodeABI(...),
    "nonce": web3.eth.get_transaction_count(address),
    "gasPrice": web3.eth.gas_price,
    "gas": 500000,
    "chainId": 100
}

# Sign with hardware wallet (requires device confirmation)
tx_hash = hw_wallet.sign_and_send_transaction(web3, tx)
print(f"Transaction: {tx_hash}")
```

## Polymarket Integration

### 1. Configure Polymarket Client

```python
from src.helpers.polymarket_integration import PolymarketClient

polymarket = PolymarketClient(
    # Polygon Web3 instance required
    web3=polygon_web3
)
```

### 2. Monitor Cross-Chain Arbitrage

```python
from src.helpers.polymarket_integration import PolymarketArbitrageExecutor

executor = PolymarketArbitrageExecutor(polymarket, gnosis_web3)

# Check arbitrage opportunity
result = await executor.execute_cross_chain_arbitrage(
    polymarket_condition="0x...",
    gnosis_market="0x...",
    amount=Decimal("100"),
    min_profit=Decimal("0.02")
)
```

## Run Production Bot

### 1. EIP-7702 Atomic Bot (Recommended)

```bash
# With hardware wallet
python -m src.arbitrage_commands.eip7702_bot \
  --amount 1.0 \
  --interval 120 \
  --tolerance 0.02 \
  --hardware-wallet ledger
```

### 2. With Monitoring

```bash
# Enable monitoring and alerting
python scripts/example_monitoring_hw_wallet.py
```

### 3. Systemd Service (Linux)

```ini
# /etc/systemd/system/futarchy-arb.service
[Unit]
Description=Futarchy Arbitrage Bot
After=network.target

[Service]
Type=simple
User=arbitrage
WorkingDirectory=/home/arbitrage/futarchy-arbitrage-1
ExecStart=/home/arbitrage/futarchy-arbitrage-1/futarchy_env/bin/python \
  -m src.arbitrage_commands.eip7702_bot \
  --amount 1.0 \
  --interval 120 \
  --tolerance 0.02
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl enable futarchy-arb
sudo systemctl start futarchy-arb

# Check logs
sudo journalctl -u futarchy-arb -f
```

## Monitoring Dashboards

### 1. Discord Alerts

Alerts are automatically sent to configured Discord webhook:
- 🔴 **Critical**: Balance too low, negative profit, gas price spike
- 🟡 **Warning**: High gas usage, small spreads
- 🟢 **Info**: Large profitable trades

### 2. Slack Integration

```python
# Configure Slack webhook in .env
SLACK_WEBHOOK=https://hooks.slack.com/services/...

# Alerts sent to configured channel
```

### 3. Metrics Export

```python
# Export metrics to Prometheus
from prometheus_client import start_http_server, Counter, Gauge

trade_counter = Counter('futarchy_trades_total', 'Total trades')
profit_gauge = Gauge('futarchy_profit', 'Current profit')

# Start metrics server
start_http_server(8000)
```

## Security Best Practices

### 1. Hardware Wallet
- ✅ Always verify addresses on device screen
- ✅ Confirm transaction details on device
- ✅ Use separate derivation paths for testing

### 2. RPC Security
- ✅ Use authenticated RPC endpoints
- ✅ Implement rate limiting
- ✅ Monitor for RPC failures

### 3. Private Keys
- ❌ Never commit private keys to git
- ❌ Never use hot wallets for large amounts
- ✅ Use hardware wallets for production

### 4. Monitoring
- ✅ Set up critical balance alerts
- ✅ Monitor error rates
- ✅ Track gas price spikes
- ✅ Set profit thresholds

## Troubleshooting

### Ledger Connection Issues

```bash
# Check device connection
lsusb | grep Ledger

# Add udev rules (Linux)
wget -q -O - https://raw.githubusercontent.com/LedgerHQ/udev-rules/master/add_udev_rules.sh | sudo bash
```

### Test Coverage Warnings

```bash
# Run tests with coverage
forge coverage --report lcov

# Generate HTML report
genhtml -o coverage/ lcov.info
open coverage/index.html
```

### Discord Webhook Not Working

```python
# Test webhook manually
import requests

response = requests.post(
    "YOUR_DISCORD_WEBHOOK",
    json={"content": "Test message"}
)
print(response.status_code)  # Should be 204
```

## Next Steps

1. **Increase Test Coverage**: Target 80%+ coverage on critical contracts
2. **Add Circuit Breakers**: Implement automatic shutdown on critical errors
3. **Expand Markets**: Support more Polymarket markets and chains
4. **Optimize Gas**: Profile and optimize contract gas usage
5. **Add Metrics**: Export to Grafana/Datadog for visualization
