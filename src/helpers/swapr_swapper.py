"""
Swapr Swapper - Execute swaps on Swapr/Algebra pools.

Provides a class-based interface for Swapr swap execution,
used by unified_bot.py and other high-level components.

Note: Requires SWAPR_ROUTER_ADDRESS environment variable to be set.
"""
from __future__ import annotations

from typing import Any, Dict

from web3 import Web3
from eth_account import Account

from src.helpers.web3_setup import get_web3_instance

__all__ = ["SwaprSwapper"]


def _get_swapr_swap_module():
    """Lazy import of swapr_swap to avoid KeyError at module load time."""
    from src.helpers import swapr_swap
    return swapr_swap


class SwaprSwapper:
    """Executes swaps on Swapr/Algebra pools."""
    
    def __init__(
        self,
        w3: Web3 | None = None,
        pool_address: str | None = None,
        private_key: str | None = None,
    ):
        """Initialize the Swapr swapper.
        
        Args:
            w3: Web3 instance. If None, creates from env vars.
            pool_address: Default pool address.
            private_key: Private key for signing transactions.
        """
        self.w3 = w3 or get_web3_instance()
        self.pool_address = pool_address
        self.private_key = private_key
        self.account = Account.from_key(private_key) if private_key else None
    
    def build_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int = 0,
    ) -> Dict[str, Any]:
        """Build a swap transaction.

        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount of input token (wei)
            min_amount_out: Minimum output amount (wei)

        Returns:
            Transaction dictionary

        Raises:
            KeyError: If SWAPR_ROUTER_ADDRESS is not set
        """
        swapr_swap = _get_swapr_swap_module()
        sender = self.account.address if self.account else "0x0000000000000000000000000000000000000000"

        return swapr_swap.build_exact_in_tx(
            token_in=token_in,
            token_out=token_out,
            amount_in_wei=amount_in,
            amount_out_min_wei=min_amount_out,
            sender=sender,
        )
    
    def execute_swap(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int = 0,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute a swap transaction.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Amount of input token (wei)
            min_amount_out: Minimum output amount (wei)
            dry_run: If True, only build but don't send.
            
        Returns:
            Result dictionary with 'success', 'tx_hash', etc.
        """
        if self.account is None:
            return {"success": False, "error": "No private key configured"}
        
        try:
            tx = self.build_swap(
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                min_amount_out=min_amount_out,
            )
            
            if dry_run:
                return {"success": True, "simulated": True, "tx": tx}
            
            # Sign and send
            signed = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            
            return {
                "success": True,
                "tx_hash": tx_hash.hex(),
                "simulated": False,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

