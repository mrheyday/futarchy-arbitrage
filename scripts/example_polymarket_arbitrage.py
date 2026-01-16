"""
Example: Polymarket arbitrage with Gnosis futarchy markets
"""

import asyncio
from decimal import Decimal
from src.helpers.polymarket_integration import PolymarketClient, PolymarketArbitrageExecutor
from src.config.network import get_web3


async def main():
    # Initialize Polymarket client (on Polygon)
    # Note: Requires Polygon RPC in environment
    polymarket = PolymarketClient()
    
    # Initialize Gnosis Web3
    gnosis_web3 = get_web3()
    
    # Initialize arbitrage executor
    executor = PolymarketArbitrageExecutor(polymarket, gnosis_web3)
    
    # Example: US Election 2024 market
    polymarket_condition = "0x..." # Replace with actual condition ID
    gnosis_market = "0x..." # Replace with Gnosis market address
    
    # Get current prices
    poly_yes_price = polymarket.get_market_price(polymarket_condition, 1)
    poly_no_price = polymarket.get_market_price(polymarket_condition, 0)
    
    print(f"Polymarket YES: {poly_yes_price}")
    print(f"Polymarket NO: {poly_no_price}")
    print(f"Sum: {poly_yes_price + poly_no_price}")
    
    # Execute cross-chain arbitrage
    result = await executor.execute_cross_chain_arbitrage(
        polymarket_condition=polymarket_condition,
        gnosis_market=gnosis_market,
        amount=Decimal("100"),  # 100 USDC
        min_profit=Decimal("0.02")  # 2% minimum profit
    )
    
    if result["executed"]:
        print(f"✅ Arbitrage executed!")
        print(f"Side: {result['side']}")
        print(f"Profit: {result['profit']:.4f}")
    else:
        print(f"❌ No arbitrage: {result['reason']}")


if __name__ == "__main__":
    asyncio.run(main())
