"""
Balancer Swapper - Execute swaps on Balancer pools.

Provides a class-based interface for Balancer swap execution,
used by unified_bot.py and other high-level components.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from web3 import Web3
from eth_account import Account

from src.helpers.balancer_swap import get_balancer_pool_id, build_sell_gno_to_sdai_swap_tx, build_buy_gno_to_sdai_swap_tx
from src.helpers.web3_setup import get_web3_instance

__all__ = ["BalancerSwapper"]


class BalancerSwapper:
    """Executes swaps on Balancer pools."""
    
    def __init__(
        self,
        w3: Web3 | None = None,
        pool_address: str | None = None,
        private_key: str | None = None,
    ):
        """Initialize the Balancer swapper.
        
        Args:
            w3: Web3 instance. If None, creates from env vars.
            pool_address: Default pool address.
            private_key: Private key for signing transactions.
        """
        self.w3 = w3 or get_web3_instance()
        self.pool_address = pool_address
        self.private_key = private_key
        self.account = Account.from_key(private_key) if private_key else None
    
    def get_pool_id(self, pool_address: str | None = None) -> str:
        """Get the pool ID for a Balancer pool.

        Args:
            pool_address: Pool address. Uses default if not provided.

        Returns:
            Pool ID as hex string
        """
        addr = pool_address or self.pool_address
        if addr is None:
            raise ValueError("No pool address provided")
        return get_balancer_pool_id(self.w3, addr)
    
    def execute_swap(
        self,
        direction: str,  # "buy" or "sell"
        amount_in: int,
        min_amount_out: int = 0,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute a swap transaction.

        Note: This is a simplified interface. For full control, use the
        build_sell_gno_to_sdai_swap_tx or build_buy_gno_to_sdai_swap_tx
        functions directly with a TenderlyClient.

        Args:
            direction: "buy" (sDAI→GNO) or "sell" (GNO→sDAI)
            amount_in: Amount of input token (wei)
            min_amount_out: Minimum output amount (wei)
            dry_run: If True, only simulate without sending.

        Returns:
            Result dictionary with 'success', 'tx_hash', etc.
        """
        if self.account is None:
            return {"success": False, "error": "No private key configured"}

        return {
            "success": False,
            "error": "Direct execution requires TenderlyClient. Use executor modules instead.",
            "hint": "See src.executor.arbitrage_executor for full swap execution."
        }

