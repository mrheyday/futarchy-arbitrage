#!/usr/bin/env python3
"""
Deploy FutarchyArbExecutorV5 using pre-compiled artifacts from artifacts/ directory.

This version assumes you've already run:
    ./scripts/compile.sh
    # or
    python scripts/compile_all.py --contract FutarchyArbExecutorV5

Benefits over inline compilation:
- Faster deployment (no recompilation)
- Consistent bytecode across environments
- Easier verification (bytecode exactly matches compiled artifacts)

Usage:
    source .env.0x<PROPOSAL_ADDRESS>
    python scripts/deploy_executor_v5_precompiled.py
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

from web3 import Web3
from eth_account import Account


# Artifact paths
ARTIFACTS_DIR = Path("artifacts")
ABI_PATH = ARTIFACTS_DIR / "abi" / "FutarchyArbExecutorV5.json"
BYTECODE_PATH = ARTIFACTS_DIR / "bytecode" / "FutarchyArbExecutorV5.hex"
DEPLOYMENTS_DIR = Path("deployments")
GNOSISSCAN_API_URL = "https://api.gnosisscan.io/api"


def require_env(var: str) -> str:
    """Get required environment variable or exit"""
    v = os.getenv(var)
    if not v:
        raise SystemExit(f"Missing required env var: {var}")
    return v


def load_artifacts() -> tuple[str, list]:
    """Load pre-compiled ABI and bytecode"""

    if not ABI_PATH.exists():
        raise SystemExit(
            f"ABI not found: {ABI_PATH}\n"
            "Run: ./scripts/compile.sh first"
        )

    if not BYTECODE_PATH.exists():
        raise SystemExit(
            f"Bytecode not found: {BYTECODE_PATH}\n"
            "Run: ./scripts/compile.sh first"
        )

    print(f"Loading artifacts from {ARTIFACTS_DIR}/")

    # Load ABI
    with open(ABI_PATH) as f:
        abi = json.load(f)

    # Load bytecode
    with open(BYTECODE_PATH) as f:
        bytecode = f.read().strip()

    print(f"  ✓ ABI loaded: {len(abi)} items")
    print(f"  ✓ Bytecode loaded: {len(bytecode)} chars")

    return bytecode, abi


def _eip1559_fees(w3: Web3) -> dict:
    """Return EIP-1559 fee fields or legacy gasPrice"""
    try:
        latest = w3.eth.get_block("latest")
        base_fee = latest.get("baseFeePerGas")
    except Exception:
        base_fee = None

    if base_fee is not None:
        tip = int(os.getenv("PRIORITY_FEE_WEI", "1"))
        mult = int(os.getenv("MAX_FEE_MULTIPLIER", "2"))
        max_fee = int(base_fee) * mult + tip
        return {"maxFeePerGas": int(max_fee), "maxPriorityFeePerGas": int(tip)}

    # Legacy fallback
    bump = int(os.getenv("MIN_GAS_PRICE_BUMP_WEI", "1"))
    return {"gasPrice": int(w3.eth.gas_price) + bump}


def deploy(bytecode: str, abi: list) -> tuple[str, dict, str]:
    """Deploy contract and return (address, receipt, tx_hash)"""

    rpc_url = require_env("RPC_URL")
    private_key = require_env("PRIVATE_KEY")

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        raise SystemExit("Failed to connect to RPC_URL")

    account = Account.from_key(private_key)
    chain_id = w3.eth.chain_id

    print("\nDeployment Details:")
    print(f"  RPC: {rpc_url}")
    print(f"  Chain ID: {chain_id}")
    print(f"  Deployer: {account.address}")

    bal = w3.from_wei(w3.eth.get_balance(account.address), 'ether')
    print(f"  Balance: {bal} xDAI")

    # Create contract instance
    Contract = w3.eth.contract(abi=abi, bytecode=bytecode)

    # Detect constructor arguments
    ctor_inputs = []
    for item in abi:
        if item.get("type") == "constructor":
            ctor_inputs = item.get("inputs", [])
            break

    # Build transaction
    if len(ctor_inputs) == 0:
        print("\n  Constructor: no arguments")
        tx = Contract.constructor().build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": chain_id,
        })
    else:
        # V5 uses 3 constructor arguments
        futarchy_router = require_env("FUTARCHY_ROUTER_ADDRESS")
        swapr_router = require_env("SWAPR_ROUTER_ADDRESS")
        proposal = require_env("FUTARCHY_PROPOSAL_ADDRESS")

        print("\n  Constructor arguments:")
        print(f"    futarchyRouter: {futarchy_router}")
        print(f"    swaprRouter: {swapr_router}")
        print(f"    proposal: {proposal}")

        tx = Contract.constructor(
            futarchy_router,
            swapr_router,
            proposal
        ).build_transaction({
            "from": account.address,
            "nonce": w3.eth.get_transaction_count(account.address),
            "chainId": chain_id,
        })

    # Estimate gas with buffer
    try:
        gas_est = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas_est * 1.2)
        print(f"  Gas estimate: {gas_est} (using {tx['gas']} with 20% buffer)")
    except Exception as e:
        print(f"  Gas estimation failed: {e}")
        tx["gas"] = 3_000_000
        print(f"  Using fallback gas: {tx['gas']}")

    # Sign and send
    signed = account.sign_transaction(tx)
    raw = getattr(signed, "rawTransaction", None) or getattr(signed, "raw_transaction", None)
    tx_hash = w3.eth.send_raw_transaction(raw)

    print(f"\n  Deploy tx: {tx_hash.hex()}")
    print(f"  Gnosisscan: https://gnosisscan.io/tx/{tx_hash.hex()}")

    print("\n  Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

    if receipt.status != 1:
        raise SystemExit("Deployment failed (status != 1)")

    contract_address = receipt.contractAddress
    print(f"\n  ✅ Deployed at: {contract_address}")
    print(f"  Gas used: {receipt.gasUsed}")

    return contract_address, receipt, tx_hash.hex()


def save_deployment(address: str, receipt: dict, tx_hash: str, abi: list):
    """Save deployment info to deployments/ directory"""

    DEPLOYMENTS_DIR.mkdir(exist_ok=True)

    timestamp = int(time.time())
    deployment_file = DEPLOYMENTS_DIR / f"deployment_executor_v5_{timestamp}.json"

    deployment_info = {
        "contract": "FutarchyArbExecutorV5",
        "address": address,
        "tx_hash": tx_hash,
        "block_number": receipt.blockNumber,
        "gas_used": receipt.gasUsed,
        "deployer": receipt["from"],
        "timestamp": timestamp,
        "datetime": datetime.fromtimestamp(timestamp).isoformat(),
        "chain_id": os.getenv("CHAIN_ID", "100"),
        "constructor_args": {
            "futarchyRouter": os.getenv("FUTARCHY_ROUTER_ADDRESS", ""),
            "swaprRouter": os.getenv("SWAPR_ROUTER_ADDRESS", ""),
            "proposal": os.getenv("FUTARCHY_PROPOSAL_ADDRESS", "")
        },
        "abi": abi,
        "artifacts_used": {
            "abi_path": str(ABI_PATH),
            "bytecode_path": str(BYTECODE_PATH)
        }
    }

    with open(deployment_file, 'w') as f:
        json.dump(deployment_info, f, indent=2)

    print(f"\n  Deployment info saved: {deployment_file}")

    # Also update latest symlink (optional)
    latest_link = DEPLOYMENTS_DIR / "latest_executor_v5.json"
    if latest_link.exists() or latest_link.is_symlink():
        latest_link.unlink()
    latest_link.symlink_to(deployment_file.name)
    print(f"  Latest symlink: {latest_link}")


def main():
    print("="*60)
    print("FutarchyArbExecutorV5 Deployment (Pre-compiled)")
    print("="*60)

    # Load pre-compiled artifacts
    bytecode, abi = load_artifacts()

    # Deploy
    address, receipt, tx_hash = deploy(bytecode, abi)

    # Save deployment info
    save_deployment(address, receipt, tx_hash, abi)

    print("\n" + "="*60)
    print("✅ Deployment Complete!")
    print("="*60)
    print(f"\nContract address: {address}")
    print(f"Transaction: https://gnosisscan.io/tx/{tx_hash}")
    print(f"Contract: https://gnosisscan.io/address/{address}")
    print("\nNext steps:")
    print("  1. Verify on Gnosisscan (use artifacts/bytecode/FutarchyArbExecutorV5.bin)")
    print("  2. Update .env file with FUTARCHY_ARB_EXECUTOR_V5={address}")
    print("  3. Test with: python -m src.executor.arbitrage_executor --address {address}")


if __name__ == "__main__":
    main()
