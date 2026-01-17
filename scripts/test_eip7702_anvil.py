#!/usr/bin/env python3
"""
Test EIP-7702 Sender against local Anvil fork.
Requires Anvil running on localhost:8545.
"""

import sys
import os
import logging
from web3 import Web3
from eth_account import Account

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.executor.eip7702_sender import send_eip7702_bundle
except ImportError:
    print("Error: Could not import send_eip7702_bundle. Run from project root.")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # 1. Connect to Anvil
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    if not w3.is_connected():
        print("Error: Could not connect to Anvil at http://127.0.0.1:8545")
        sys.exit(1)
        
    print(f"Connected to Anvil. Chain ID: {w3.eth.chain_id}")

    # 2. Setup Accounts
    # Anvil default account #0 (Private Key)
    # 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
    signer_key = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
    account = Account.from_key(signer_key)
    
    print(f"Signer: {account.address}")
    print(f"Balance: {w3.from_wei(w3.eth.get_balance(account.address), 'ether')} ETH")

    # 3. Deploy PectraWrapper (Implementation)
    # We need the bytecode for PectraWrapper. In a real scenario, we read from artifacts.
    # For this test, we'll assume it's already deployed or we deploy a mock.
    # Let's deploy a simple contract that acts as the implementation.
    
    # Simple contract that has execute10 and emits an event
    # This bytecode corresponds to a minimal contract with a fallback or execute function
    # For testing purposes, we will use a placeholder address if we can't compile here.
    # Ideally, run `forge create PectraWrapper --private-key ...` and use that address.
    
    # Placeholder: Assuming PectraWrapper is deployed at this address (replace with actual)
    # If running against a fresh anvil, you might need to deploy it first.
    implementation_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3" 
    
    print(f"Using Implementation: {implementation_address}")

    # 4. Construct Bundle
    # Send 0 ETH to self as a test call
    calls = [
        {
            "to": account.address,
            "data": b"",
            "value": 0
        },
        {
            "to": "0x000000000000000000000000000000000000dEaD",
            "data": b"\xde\xad\xbe\xef",
            "value": 0
        }
    ]

    # 5. Send EIP-7702 Transaction
    try:
        tx_hash = send_eip7702_bundle(
            w3=w3,
            account=account,
            implementation_address=implementation_address,
            calls=calls
        )
        print(f"✅ Transaction Sent! Hash: {tx_hash}")
    except Exception as e:
        print(f"❌ Transaction Failed: {e}")

if __name__ == "__main__":
    main()