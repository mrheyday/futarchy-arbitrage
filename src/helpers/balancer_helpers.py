"""
Balancer helpers - wrapper functions for Balancer price fetching.

This module provides simplified interfaces to Balancer pool interactions,
wrapping the lower-level balancer_price module.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Optional, Tuple

from web3 import Web3

from src.helpers.balancer_price import get_pool_price
from src.helpers.web3_setup import get_web3_instance

__all__ = ["get_balancer_price"]


def get_balancer_price(
    token_in: str,
    token_out: str,
    pool_address: str | None = None,
    w3: Web3 | None = None,
    amount_in: Decimal = Decimal("1"),
) -> Tuple[Decimal, Decimal]:
    """
    Get the price and estimated output for a Balancer swap.
    
    Args:
        token_in: Input token address
        token_out: Output token address
        pool_address: Balancer pool address. If None, uses BALANCER_POOL_ADDRESS env var.
        w3: Web3 instance. If None, creates one from env vars.
        amount_in: Amount of input token (default: 1)
    
    Returns:
        Tuple of (price, estimated_liquidity)
        - price: Amount of token_out per 1 token_in
        - estimated_liquidity: Rough estimate of available liquidity
    """
    import os
    
    if w3 is None:
        w3 = get_web3_instance()
    
    if pool_address is None:
        pool_address = os.getenv("BALANCER_POOL_ADDRESS")
        if pool_address is None:
            raise ValueError("pool_address not provided and BALANCER_POOL_ADDRESS env var not set")
    
    try:
        price, base_token, quote_token = get_pool_price(w3, pool_address)
        
        # Determine if we need to invert the price based on token direction
        base_token_lower = base_token.lower()
        token_in_lower = token_in.lower()
        
        if base_token_lower == token_in_lower:
            # Price is already in the right direction
            effective_price = price
        else:
            # Need to invert
            effective_price = Decimal(1) / price if price > 0 else Decimal(0)
        
        # Estimate liquidity (simplified - would need pool balance query for accuracy)
        estimated_liquidity = Decimal("10000")  # Placeholder
        
        return effective_price, estimated_liquidity
        
    except Exception as e:
        # Return zero price and liquidity on error
        return Decimal(0), Decimal(0)

