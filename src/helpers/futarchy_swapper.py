"""
Futarchy Swapper - Execute split/merge operations via FutarchyRouter.

Provides a class-based interface for futarchy position management,
used by unified_bot.py and other high-level components.
"""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from web3 import Web3
from eth_account import Account

from src.helpers.split_position import build_split_tx, simulate_split
from src.helpers.merge_position import build_merge_tx, simulate_merge
from src.helpers.web3_setup import get_web3_instance
from src.helpers.tenderly_api import TenderlyClient

__all__ = ["FutarchySwapper"]


class FutarchySwapper:
    """Executes split/merge operations on Futarchy positions."""
    
    def __init__(
        self,
        w3: Web3 | None = None,
        router_address: str | None = None,
        proposal_address: str | None = None,
        private_key: str | None = None,
        tenderly_client: TenderlyClient | None = None,
    ):
        """Initialize the Futarchy swapper.

        Args:
            w3: Web3 instance. If None, creates from env vars.
            router_address: FutarchyRouter contract address.
            proposal_address: Proposal contract address.
            private_key: Private key for signing transactions.
            tenderly_client: TenderlyClient for building transactions.
        """
        import os
        self.w3 = w3 or get_web3_instance()
        self.router_address = router_address or os.getenv("FUTARCHY_ROUTER_ADDRESS")
        self.proposal_address = proposal_address or os.getenv("FUTARCHY_PROPOSAL_ADDRESS")
        self.private_key = private_key
        self.account = Account.from_key(private_key) if private_key else None
        self.client = tenderly_client or TenderlyClient()
    
    def build_split(
        self,
        collateral_token: str,
        amount: int,
        proposal_address: str | None = None,
    ) -> Dict[str, Any]:
        """Build a split position transaction.

        Args:
            collateral_token: Collateral token address (e.g., sDAI)
            amount: Amount to split (wei)
            proposal_address: Proposal address. Uses default if not provided.

        Returns:
            Transaction dictionary
        """
        proposal = proposal_address or self.proposal_address
        if proposal is None:
            raise ValueError("No proposal address provided")
        if self.router_address is None:
            raise ValueError("No router address configured")

        sender = self.account.address if self.account else "0x0000000000000000000000000000000000000000"

        return build_split_tx(
            w3=self.w3,
            client=self.client,
            router_addr=self.router_address,
            proposal_addr=proposal,
            collateral_addr=collateral_token,
            amount_wei=amount,
            sender=sender,
        )
    
    def build_merge(
        self,
        collateral_token: str,
        amount: int,
        proposal_address: str | None = None,
    ) -> Dict[str, Any]:
        """Build a merge positions transaction.

        Args:
            collateral_token: Collateral token address (e.g., sDAI)
            amount: Amount to merge (wei)
            proposal_address: Proposal address. Uses default if not provided.

        Returns:
            Transaction dictionary
        """
        proposal = proposal_address or self.proposal_address
        if proposal is None:
            raise ValueError("No proposal address provided")
        if self.router_address is None:
            raise ValueError("No router address configured")

        sender = self.account.address if self.account else "0x0000000000000000000000000000000000000000"

        return build_merge_tx(
            w3=self.w3,
            client=self.client,
            router_addr=self.router_address,
            proposal_addr=proposal,
            collateral_addr=collateral_token,
            amount_wei=amount,
            sender=sender,
        )
    
    def execute_split(
        self,
        collateral_token: str,
        amount: int,
        proposal_address: str | None = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute a split position transaction."""
        if self.account is None:
            return {"success": False, "error": "No private key configured"}
        
        try:
            tx = self.build_split(collateral_token, amount, proposal_address)
            
            if dry_run:
                return {"success": True, "simulated": True, "tx": tx}
            
            signed = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            
            return {"success": True, "tx_hash": tx_hash.hex(), "simulated": False}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def execute_merge(
        self,
        collateral_token: str,
        amount: int,
        proposal_address: str | None = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Execute a merge positions transaction."""
        if self.account is None:
            return {"success": False, "error": "No private key configured"}
        
        try:
            tx = self.build_merge(collateral_token, amount, proposal_address)
            
            if dry_run:
                return {"success": True, "simulated": True, "tx": tx}
            
            signed = self.account.sign_transaction(tx)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            
            return {"success": True, "tx_hash": tx_hash.hex(), "simulated": False}
        except Exception as e:
            return {"success": False, "error": str(e)}

