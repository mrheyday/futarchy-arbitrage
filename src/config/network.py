"""
Network configuration for the Futarchy Trading Bot.

This module is currently in EXPERIMENTAL status.
Contains RPC URLs and API endpoints for various services.
Supports multiple chains: Gnosis, Base, and more.
"""

import os
from typing import Any


# =============================================================================
# CHAIN CONFIGURATIONS
# =============================================================================

CHAINS: dict[str, dict[str, Any]] = {
    "gnosis": {
        "chain_id": 100,
        "name": "Gnosis Chain",
        "currency": "xDAI",
        "block_time": 5,
        "rpc_urls": [
            "https://gnosis-mainnet.public.blastapi.io",
            "https://rpc.gnosischain.com",
            "https://rpc.ankr.com/gnosis",
        ],
        "explorer": {
            "name": "Gnosisscan",
            "url": "https://gnosisscan.io",
            "api_url": "https://api.gnosisscan.io/api",
        },
        "cowswap_api": "https://api.cow.fi/xdai",
    },
    "base": {
        "chain_id": 8453,
        "name": "Base",
        "currency": "ETH",
        "block_time": 2,
        "rpc_urls": [
            "https://mainnet.base.org",
            "https://base.publicnode.com",
            "https://rpc.ankr.com/base",
        ],
        "explorer": {
            "name": "Basescan",
            "url": "https://basescan.org",
            "api_url": "https://api.basescan.org/api",
        },
        "cowswap_api": "https://api.cow.fi/base",
    },
    "base_sepolia": {
        "chain_id": 84532,
        "name": "Base Sepolia",
        "currency": "ETH",
        "block_time": 2,
        "rpc_urls": [
            "https://sepolia.base.org",
            "https://base-sepolia.publicnode.com",
        ],
        "explorer": {
            "name": "Basescan Sepolia",
            "url": "https://sepolia.basescan.org",
            "api_url": "https://api-sepolia.basescan.org/api",
        },
        "cowswap_api": None,  # No CoWSwap on testnet
    },
    "chiado": {
        "chain_id": 10200,
        "name": "Chiado Testnet",
        "currency": "xDAI",
        "block_time": 5,
        "rpc_urls": [
            "https://rpc.chiadochain.net",
            "https://rpc.chiado.gnosis.gateway.fm",
        ],
        "explorer": {
            "name": "Chiado Explorer",
            "url": "https://gnosis-chiado.blockscout.com",
            "api_url": "https://gnosis-chiado.blockscout.com/api",
        },
        "cowswap_api": None,  # No CoWSwap on testnet
    },
}

# Chain ID to name mapping
CHAIN_ID_TO_NAME: dict[int, str] = {
    config["chain_id"]: name for name, config in CHAINS.items()
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_chain_config(chain: str | int | None = None) -> dict[str, Any]:
    """Get configuration for a specific chain.

    Args:
        chain: Chain name (e.g., 'gnosis', 'base') or chain ID.
               If None, uses CHAIN environment variable or defaults to 'gnosis'.

    Returns:
        Chain configuration dictionary.

    Raises:
        ValueError: If chain is not supported.
    """
    if chain is None:
        chain = os.getenv("CHAIN", "gnosis").lower()

    if isinstance(chain, int):
        chain = CHAIN_ID_TO_NAME.get(chain)
        if chain is None:
            raise ValueError(f"Unsupported chain ID: {chain}")

    chain = chain.lower()
    if chain not in CHAINS:
        raise ValueError(f"Unsupported chain: {chain}. Supported: {list(CHAINS.keys())}")

    return CHAINS[chain]


def get_rpc_url(chain: str | int | None = None) -> str:
    """Get the primary RPC URL for a chain.

    Uses RPC_URL environment variable if set, otherwise returns first default.
    """
    env_rpc = os.getenv("RPC_URL")
    if env_rpc:
        return env_rpc

    config = get_chain_config(chain)
    return config["rpc_urls"][0]


def get_chain_id(chain: str | None = None) -> int:
    """Get the chain ID for a chain name."""
    config = get_chain_config(chain)
    return config["chain_id"]


def get_explorer_url(chain: str | int | None = None) -> str:
    """Get the block explorer URL for a chain."""
    config = get_chain_config(chain)
    return config["explorer"]["url"]


def get_explorer_api_url(chain: str | int | None = None) -> str:
    """Get the block explorer API URL for a chain."""
    config = get_chain_config(chain)
    return config["explorer"]["api_url"]


# =============================================================================
# LEGACY COMPATIBILITY (default to Gnosis)
# =============================================================================

# Default RPC URLs (fallbacks if not set in environment)
DEFAULT_RPC_URLS: list[str] = CHAINS["gnosis"]["rpc_urls"]

# API Endpoints
COWSWAP_API_URL: str = CHAINS["gnosis"]["cowswap_api"]

# Chain configuration (default: Gnosis)
CHAIN_ID: int = CHAINS["gnosis"]["chain_id"]
CHAIN_NAME: str = CHAINS["gnosis"]["name"]
BLOCK_TIME: int = CHAINS["gnosis"]["block_time"]
GAS_LIMIT_BUFFER: float = 1.1  # 10% buffer for gas limit estimates

# Network timeouts and retries
RPC_TIMEOUT: int = 30  # seconds
MAX_RETRIES: int = 3
RETRY_DELAY: int = 1  # seconds between retries


# =============================================================================
# WEB3 INSTANCE (Lazy initialization)
# =============================================================================

def get_web3():
    """Get a Web3 instance connected to the configured RPC URL.

    Returns:
        Web3: Web3 instance
    """
    from web3 import Web3
    rpc_url = get_rpc_url()
    return Web3(Web3.HTTPProvider(rpc_url))


# Lazy-initialized web3 instance for backward compatibility
# Import as: from src.config.network import w3
class _LazyWeb3:
    """Lazy Web3 instance that initializes on first access."""
    _instance = None

    def __getattr__(self, name):
        if _LazyWeb3._instance is None:
            _LazyWeb3._instance = get_web3()
        return getattr(_LazyWeb3._instance, name)

w3 = _LazyWeb3()