"""
EIP-7702 Transaction Sender.
Handles construction, signing, and broadcasting of Type 4 transactions.
"""

import logging
from typing import List, Dict, Any
from web3 import Web3
from eth_account import Account
from eth_utils import keccak
import rlp

logger = logging.getLogger(__name__)

def sign_authorization(account: Account, contract_address: str, chain_id: int, nonce: int) -> Dict[str, Any]:
    """
    Sign an EIP-7702 authorization tuple.
    Payload: 0x05 || RLP([chain_id, address, nonce])
    """
    MAGIC = b'\x05'
    
    if contract_address.startswith("0x"):
        addr_bytes = bytes.fromhex(contract_address[2:])
    else:
        addr_bytes = bytes.fromhex(contract_address)
        
    # RLP Encode [chain_id, address, nonce]
    encoded_payload = rlp.encode([chain_id, addr_bytes, nonce])
    
    # Construct digest
    digest = keccak(MAGIC + encoded_payload)
    
    # Sign
    signed = account.signHash(digest)
    
    # EIP-7702 uses yParity (0 or 1)
    y_parity = signed.v - 27 if signed.v >= 27 else signed.v
    
    return {
        'chainId': chain_id,
        'address': contract_address,
        'nonce': nonce,
        'yParity': y_parity,
        'r': hex(signed.r),
        's': hex(signed.s)
    }

def send_eip7702_bundle(
    w3: Web3,
    account: Account,
    implementation_address: str,
    calls: List[Dict[str, Any]],
    gas_limit: int = 2_000_000,
    priority_fee_gwei: float = 2.0
) -> str:
    """
    Send a bundle of calls as a single EIP-7702 Type 4 transaction.
    
    Args:
        w3: Web3 instance
        account: Local Account object (signer)
        implementation_address: Address of the contract to delegate to (e.g. PectraWrapper)
        calls: List of dicts with {'to': str, 'data': bytes, 'value': int}
        gas_limit: Gas limit for the transaction
        priority_fee_gwei: Max priority fee per gas
        
    Returns:
        Transaction hash as hex string
    """
    chain_id = w3.eth.chain_id
    nonce = w3.eth.get_transaction_count(account.address)
    
    # 1. Encode the batch call for the implementation contract
    # Assuming PectraWrapper.execute10(address[10], bytes[10], uint256) signature
    # or a generic execute(address[], bytes[], uint256[]) depending on the wrapper.
    # Here we construct the calldata for PectraWrapper.execute10 based on the provided context.
    
    targets = [c['to'] for c in calls]
    datas = [c['data'] for c in calls]
    # Pad to 10 for execute10 if using that specific function, or use dynamic array if supported.
    # For this implementation, we'll assume we are calling a generic `executeBatch` if available,
    # or adapting to `execute10`. Let's assume `execute10` for PectraWrapper compatibility.
    
    count = len(calls)
    if count > 10:
        raise ValueError("PectraWrapper execute10 supports max 10 calls")
        
    padded_targets = targets + [ "0x0000000000000000000000000000000000000000" ] * (10 - count)
    padded_datas = datas + [ b"" ] * (10 - count)
    
    # PectraWrapper.execute10 signature
    contract = w3.eth.contract(abi=[{
        "name": "execute10",
        "type": "function",
        "inputs": [
            {"name": "targets", "type": "address[10]"},
            {"name": "calldatas", "type": "bytes[10]"},
            {"name": "count", "type": "uint256"}
        ]
    }], address=implementation_address)
    
    tx_data = contract.encodeABI(fn_name="execute10", args=[padded_targets, padded_datas, count])

    # 2. Sign Authorization
    auth = sign_authorization(account, implementation_address, chain_id, nonce)
    
    # 3. Build Type 4 Transaction
    # Note: web3.py support for Type 4 might be experimental. 
    # We construct the dict parameters expected by a client supporting EIP-7702.
    
    base_fee = w3.eth.get_block('latest')['baseFeePerGas']
    max_fee = base_fee + w3.to_wei(priority_fee_gwei, 'gwei')
    
    tx_params = {
        'type': 4,
        'chainId': chain_id,
        'nonce': nonce,
        'to': account.address, # Self-call
        'value': 0,
        'data': tx_data,
        'gas': gas_limit,
        'maxFeePerGas': max_fee,
        'maxPriorityFeePerGas': w3.to_wei(priority_fee_gwei, 'gwei'),
        'authorizationList': [auth]
    }
    
    # 4. Sign and Send
    signed_tx = account.sign_transaction(tx_params)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    
    logger.info(f"Sent EIP-7702 Bundle: {tx_hash.hex()}")
    return tx_hash.hex()