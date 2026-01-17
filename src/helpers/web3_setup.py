"""
Web3 setup helper - provides common web3 instance utilities.

Public API
----------
get_web3_instance(rpc_url=None)
    Return a Web3 instance connected to the specified RPC URL.
    Falls back to RPC_URL or GNOSIS_RPC_URL environment variables.
"""
from __future__ import annotations

import os
from typing import Optional

from web3 import Web3

__all__ = ["get_web3_instance", "get_web3"]

# Cached web3 instance
_w3_instance: Optional[Web3] = None


def get_web3_instance(rpc_url: str | None = None) -> Web3:
    """
    Get a Web3 instance connected to the specified RPC URL.
    
    Args:
        rpc_url: Optional RPC URL. If not provided, uses RPC_URL or GNOSIS_RPC_URL env vars.
    
    Returns:
        Web3 instance
        
    Raises:
        RuntimeError: If no RPC URL is available
    """
    global _w3_instance
    
    if rpc_url is None:
        rpc_url = os.getenv("RPC_URL") or os.getenv("GNOSIS_RPC_URL")
    
    if rpc_url is None:
        raise RuntimeError("No RPC URL available. Set RPC_URL or GNOSIS_RPC_URL environment variable.")
    
    # Return cached instance if URL matches
    if _w3_instance is not None and _w3_instance.provider.endpoint_uri == rpc_url:
        return _w3_instance
    
    _w3_instance = Web3(Web3.HTTPProvider(rpc_url))
    return _w3_instance


def get_web3(rpc_url: str | None = None) -> Web3:
    """Alias for get_web3_instance for backward compatibility."""
    return get_web3_instance(rpc_url)

