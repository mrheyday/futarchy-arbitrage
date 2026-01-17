"""
Balancer Fetcher - Fetch price data from Balancer pools.

Provides a class-based interface for Balancer price fetching,
used by unified_bot.py and other high-level components.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Dict, Optional, Tuple

from web3 import Web3

from src.helpers.balancer_price import get_pool_price
from src.helpers.web3_setup import get_web3_instance

__all__ = ["BalancerFetcher"]


class BalancerFetcher:
    """Fetches price data from Balancer pools."""
    
    def __init__(self, w3: Web3 | None = None, pool_address: str | None = None):
        """Initialize the Balancer fetcher.
        
        Args:
            w3: Web3 instance. If None, creates from env vars.
            pool_address: Default pool address. Can be overridden per-call.
        """
        self.w3 = w3 or get_web3_instance()
        self.pool_address = pool_address
    
    def get_price(
        self,
        pool_address: str | None = None,
        base_token_index: int = 0,
    ) -> Tuple[Decimal, str, str]:
        """Get the spot price from a Balancer pool.
        
        Args:
            pool_address: Pool address. Uses default if not provided.
            base_token_index: Index of base token (0 or 1).
            
        Returns:
            Tuple of (price, base_token_address, quote_token_address)
        """
        addr = pool_address or self.pool_address
        if addr is None:
            raise ValueError("No pool address provided")
        
        return get_pool_price(self.w3, addr, base_token_index=base_token_index)
    
    def get_prices_for_tokens(
        self,
        token_in: str,
        token_out: str,
        pool_address: str | None = None,
    ) -> Dict[str, Decimal]:
        """Get price data for a specific token pair.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            pool_address: Pool address. Uses default if not provided.
            
        Returns:
            Dict with 'price', 'inverse_price' keys
        """
        addr = pool_address or self.pool_address
        if addr is None:
            raise ValueError("No pool address provided")
        
        try:
            price, base, quote = get_pool_price(self.w3, addr)
            
            # Determine direction
            if base.lower() == token_in.lower():
                return {
                    "price": price,
                    "inverse_price": Decimal(1) / price if price > 0 else Decimal(0),
                }
            else:
                return {
                    "price": Decimal(1) / price if price > 0 else Decimal(0),
                    "inverse_price": price,
                }
        except Exception:
            return {"price": Decimal(0), "inverse_price": Decimal(0)}

