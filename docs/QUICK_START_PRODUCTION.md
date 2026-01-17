# Quick Start Guide: Production Features

## 1. Install Extended Dependencies

```bash
# Activate virtual environment
source futarchy_env/bin/activate

# Install new requirements
pip install -r requirements-extended.txt
```

## 2. Run Foundry Tests

```bash
# Run all new tests
forge test --match-contract "FutarchyArbExecutorV5Test|PredictionArbExecutorV1Test|InstitutionalSolverSystemTest" -vv

# Run specific test suite
forge test --match-contract FutarchyArbExecutorV5Test -vvv

# Check coverage
forge coverage
```

## 3. Setup Monitoring

```bash
# Add to .env
DISCORD_WEBHOOK=https://discord.com/api/webhooks/YOUR_WEBHOOK
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR_WEBHOOK
```

```python
# In your bot script
from src.helpers.monitoring import MonitoringClient, setup_default_alerts

monitor = MonitoringClient(
    discord_webhook=os.getenv("DISCORD_WEBHOOK"),
    slack_webhook=os.getenv("SLACK_WEBHOOK")
)
setup_default_alerts(monitor)

# Record metrics
monitor.record_trade(
    side="buy",
    amount=Decimal("1.5"),
    profit=Decimal("0.02"),
    gas_used=250000,
    tx_hash=tx_hash,
    success=True
)

# Health check
health = await monitor.check_health(web3)
print(health)
```

## 4. Setup Hardware Wallet

```bash
# For Ledger
pip install ledgerblue
# Connect device, unlock, open Ethereum app

# For Trezor
pip install trezor[ethereum]
# Connect device and unlock
```

```python
from src.helpers.hardware_wallet import HardwareWalletManager

# Initialize
hw_wallet = HardwareWalletManager(
    wallet_type="ledger",  # or "trezor"
    derivation_path="m/44'/60'/0'/0/0"
)

# Get address (displays on device)
address = hw_wallet.get_address(verify=True)
print(f"Trading with: {address}")

# Sign and send transaction
tx = {
    "to": executor_address,
    "value": 0,
    "data": call_data,
    "nonce": web3.eth.get_transaction_count(address),
    "gasPrice": web3.eth.gas_price,
    "gas": 500000,
    "chainId": 100
}
tx_hash = hw_wallet.sign_and_send_transaction(web3, tx)
```

## 5. Polymarket Integration

```bash
# Add to .env
POLYGON_RPC_URL=https://polygon-rpc.com
```

```python
from src.helpers.polymarket_integration import PolymarketClient, PolymarketArbitrageExecutor

# Initialize (requires Polygon Web3)
polymarket = PolymarketClient(web3=polygon_web3)

# Get market prices
yes_price = polymarket.get_market_price(condition_id, 1)
no_price = polymarket.get_market_price(condition_id, 0)

# Execute cross-chain arbitrage
executor = PolymarketArbitrageExecutor(polymarket, gnosis_web3)
result = await executor.execute_cross_chain_arbitrage(
    polymarket_condition=condition_id,
    gnosis_market=market_address,
    amount=Decimal("100"),
    min_profit=Decimal("0.02")
)
```

## 6. Run Production Bot with All Features

```python
import asyncio
import os
from decimal import Decimal
from web3 import Web3

from src.helpers.monitoring import MonitoringClient, setup_default_alerts
from src.helpers.hardware_wallet import HardwareWalletManager
from src.config.network import get_web3


async def production_bot():
    # Setup monitoring
    monitor = MonitoringClient(
        discord_webhook=os.getenv("DISCORD_WEBHOOK"),
        slack_webhook=os.getenv("SLACK_WEBHOOK")
    )
    setup_default_alerts(monitor)
    
    # Setup hardware wallet
    hw_wallet = HardwareWalletManager(wallet_type="ledger")
    address = hw_wallet.get_address(verify=True)
    
    # Connect to network
    web3 = get_web3()
    
    print(f"🚀 Production bot starting")
    print(f"📍 Address: {address}")
    print(f"🔔 Alerts: Discord + Slack")
    
    while True:
        try:
            # Health check
            health = await monitor.check_health(web3)
            if health["checks"]["rpc"]["status"] != "healthy":
                print("⚠️  RPC unhealthy, skipping iteration")
                await asyncio.sleep(60)
                continue
            
            # Check balance
            balance = web3.eth.get_balance(address) / 1e18
            monitor.record_balance("eth", Decimal(str(balance)))
            
            # Record gas price
            gas_price_gwei = web3.eth.gas_price / 1e9
            monitor.record_gas_price(gas_price_gwei)
            
            # TODO: Add your arbitrage logic here
            # If profitable opportunity found:
            # 1. Build transaction
            # 2. Sign with hardware wallet
            # 3. Send and record metrics
            
            print(f"✓ Health check passed | Balance: {balance:.4f} ETH | Gas: {gas_price_gwei:.2f} gwei")
            
            await asyncio.sleep(120)
            
        except KeyboardInterrupt:
            print("\n👋 Shutting down gracefully...")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            monitor.increment_counter("errors.unhandled")
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(production_bot())
```

## 7. Deploy to Production (Linux)

```bash
# Create systemd service
sudo nano /etc/systemd/system/futarchy-arb.service
```

```ini
[Unit]
Description=Futarchy Arbitrage Bot
After=network.target

[Service]
Type=simple
User=arbitrage
WorkingDirectory=/home/arbitrage/futarchy-arbitrage-1
Environment="PATH=/home/arbitrage/futarchy-arbitrage-1/futarchy_env/bin"
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
# Enable and start
sudo systemctl enable futarchy-arb
sudo systemctl start futarchy-arb

# Check status
sudo systemctl status futarchy-arb

# View logs
sudo journalctl -u futarchy-arb -f
```

## 8. Monitoring Dashboard

### Discord Alerts
Automatically sent for:
- 🔴 Critical: Low balance, negative profit, RPC failures
- 🟡 Warning: High gas, small spreads
- 🟢 Info: Large profitable trades

### Custom Alerts

```python
# Add custom alert rules
monitor.add_alert(
    name="balance.sdai.critical",
    severity="critical",
    threshold=0.05,
    comparison="lt",
    cooldown=300
)

monitor.add_alert(
    name="trade.profit.excellent",
    severity="info",
    threshold=1.0,
    comparison="gt",
    cooldown=3600
)
```

## 9. Testing Checklist

Before production:
- [ ] Run all Foundry tests: `forge test`
- [ ] Test hardware wallet connection
- [ ] Verify Discord/Slack webhooks
- [ ] Check RPC connectivity
- [ ] Test with small amounts first
- [ ] Monitor logs for 24h
- [ ] Verify alert notifications work

## 10. Security Checklist

- [ ] Hardware wallet tested and confirmed
- [ ] Private keys removed from `.env`
- [ ] Balance alerts configured
- [ ] RPC endpoints use authentication
- [ ] Systemd service runs as non-root user
- [ ] Logs don't contain sensitive data
- [ ] Backup recovery seed phrase (offline)

## Troubleshooting

### Ledger Not Detected
```bash
# Linux: Add udev rules
wget -q -O - https://raw.githubusercontent.com/LedgerHQ/udev-rules/master/add_udev_rules.sh | sudo bash

# Reconnect device
```

### Discord Webhook Fails
```python
# Test webhook manually
import requests
response = requests.post(
    os.getenv("DISCORD_WEBHOOK"),
    json={"content": "Test message"}
)
print(response.status_code)  # Should be 204
```

### Tests Don't Compile
```bash
# Clean and rebuild
forge clean
forge build

# Check Solidity version
forge --version  # Should be 0.8.33
```

## Resources

- [PRODUCTION_DEPLOYMENT.md](./PRODUCTION_DEPLOYMENT.md) - Full deployment guide
- [FEATURES_IMPLEMENTATION.md](./FEATURES_IMPLEMENTATION.md) - Implementation details
- [COMPETITIVE_ANALYSIS.md](./COMPETITIVE_ANALYSIS.md) - Strategic positioning
