#!/usr/bin/env python3
"""
Test script to verify EIP-7702 authorization generation and recovery.
Uses the logic from scripts/eip7702_auth.py
"""

import sys
import os

# Ensure we can import from local scripts
sys.path.append(os.getcwd())

try:
    from scripts.eip7702_auth import sign_authorization
except ImportError:
    print("Error: Could not import sign_authorization from scripts.eip7702_auth")
    sys.exit(1)

from eth_account import Account
from eth_utils import keccak
import rlp

def test_auth_generation():
    # 1. Setup Test Data
    # Private key for testing (do not use in production)
    priv_key = "0x0000000000000000000000000000000000000000000000000000000000000001"
    account = Account.from_key(priv_key)
    target_contract = "0x1234567890123456789012345678901234567890"
    chain_id = 100 # Gnosis
    nonce = 5

    print(f"Testing EIP-7702 Auth Generation")
    print(f"Signer: {account.address}")
    print(f"Target: {target_contract}")

    # 2. Generate Authorization
    auth = sign_authorization(priv_key, target_contract, chain_id, nonce)
    
    # 3. Verify Payload Construction
    # EIP-7702 Payload: 0x05 || RLP([chain_id, address, nonce])
    MAGIC = b'\x05'
    addr_bytes = bytes.fromhex(target_contract[2:])
    encoded_payload = rlp.encode([chain_id, addr_bytes, nonce])
    digest = keccak(MAGIC + encoded_payload)
    
    # 4. Verify Signature Recovery
    # Reconstruct signature from r, s, yParity
    r = int(auth['r'], 16)
    s = int(auth['s'], 16)
    v = auth['yParity'] + 27 # Convert yParity (0/1) to standard v (27/28) for eth_account
    
    signature_bytes = r.to_bytes(32, 'big') + s.to_bytes(32, 'big') + v.to_bytes(1, 'big')
    recovered_address = Account.recoverHash(digest, signature=signature_bytes)
    
    assert recovered_address == account.address, f"Recovery failed! Got {recovered_address}, expected {account.address}"
    print(f"✅ Signature verified successfully! Recovered: {recovered_address}")

if __name__ == "__main__":
    test_auth_generation()