"""
Example: Run arbitrage bot with monitoring and hardware wallet
"""

import asyncio
import os
from decimal import Decimal
from web3 import Web3

from src.helpers.monitoring import MonitoringClient, setup_default_alerts
from src.helpers.hardware_wallet import HardwareWalletManager
from src.config.network import get_web3


async def main():
    # Initialize monitoring
    monitor = MonitoringClient(
        discord_webhook=os.getenv("DISCORD_WEBHOOK"),
        slack_webhook=os.getenv("SLACK_WEBHOOK")
    )
    setup_default_alerts(monitor)
    
    # Initialize hardware wallet
    hw_wallet = HardwareWalletManager(
        wallet_type="ledger",  # or "trezor"
        derivation_path="m/44'/60'/0'/0/0"
    )
    
    # Get address (will prompt on device)
    address = hw_wallet.get_address(verify=True)
    print(f"Trading with address: {address}")
    
    # Connect to Gnosis Chain
    web3 = get_web3()
    
    # Record initial balance
    sdai_balance = web3.eth.get_balance(address) / 1e18
    monitor.record_balance("eth", Decimal(str(sdai_balance)))
    
    # Example: Health check loop
    while True:
        try:
            # Check health
            health = await monitor.check_health(web3)
            print(f"Health: {health['checks']['rpc']['status']}")
            
            # Record gas price
            gas_price_gwei = web3.eth.gas_price / 1e9
            monitor.record_gas_price(gas_price_gwei)
            
            # Example: Record trade metrics
            monitor.record_trade(
                side="buy",
                amount=Decimal("1.5"),
                profit=Decimal("0.02"),
                gas_used=250000,
                tx_hash="0x123...",
                success=True
            )
            
            # Get summary
            summary = monitor.get_summary()
            print(f"Trades: {summary['counters'].get('trades.successful', 0)} successful")
            
            await asyncio.sleep(60)
            
        except KeyboardInterrupt:
            print("Shutting down...")
            break
        except Exception as e:
            print(f"Error: {e}")
            await asyncio.sleep(30)


if __name__ == "__main__":
    asyncio.run(main())
