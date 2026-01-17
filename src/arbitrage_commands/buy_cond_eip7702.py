"""
Buy Conditional Bundle Builder (EIP-7702).
Generates a list of encoded calls for the buy conditional arbitrage flow.
"""

from typing import List, Dict, Any
from web3 import Web3
from eth_utils import keccak

# Placeholder addresses - in production these come from config/env
FUTARCHY_ROUTER = "0x..." 
SWAPR_ROUTER = "0x..."
BALANCER_VAULT = "0x..."

def encode_approval(token: str, spender: str, amount: int) -> Dict[str, Any]:
    """Encode ERC20 approve call."""
    # approve(address,uint256) selector: 0x095ea7b3
    data = keccak(text="approve(address,uint256)")[:4] + \
           Web3.solidity_encode(["address", "uint256"], [spender, amount])
    return {
        "to": token,
        "data": data,
        "value": 0
    }

def encode_split(router: str, proposal: str, collateral: str, amount: int) -> Dict[str, Any]:
    """Encode FutarchyRouter splitPosition call."""
    # splitPosition(address,address,uint256)
    selector = keccak(text="splitPosition(address,address,uint256)")[:4]
    data = selector + Web3.solidity_encode(["address", "address", "uint256"], [proposal, collateral, amount])
    return {
        "to": router,
        "data": data,
        "value": 0
    }

def encode_merge(router: str, proposal: str, collateral: str, amount: int) -> Dict[str, Any]:
    """Encode FutarchyRouter mergePositions call."""
    # mergePositions(address,address,uint256)
    selector = keccak(text="mergePositions(address,address,uint256)")[:4]
    data = selector + Web3.solidity_encode(["address", "address", "uint256"], [proposal, collateral, amount])
    return {
        "to": router,
        "data": data,
        "value": 0
    }

def encode_swapr_exact_in(router: str, token_in: str, token_out: str, amount_in: int, min_out: int, recipient: str) -> Dict[str, Any]:
    """Encode Swapr/UniswapV3 exactInputSingle call."""
    # exactInputSingle((address,address,address,uint256,uint256,uint256,uint160))
    # Struct: tokenIn, tokenOut, recipient, deadline, amountIn, amountOutMinimum, sqrtPriceLimitX96
    selector = keccak(text="exactInputSingle((address,address,address,uint256,uint256,uint256,uint160))")[:4]
    
    params = [
        token_in,
        token_out,
        recipient,
        2**256 - 1, # deadline
        amount_in,
        min_out,
        0 # sqrtPriceLimitX96
    ]
    
    encoded_params = Web3.solidity_encode(
        ["address", "address", "address", "uint256", "uint256", "uint256", "uint160"],
        params
    )
    
    return {
        "to": router,
        "data": selector + encoded_params,
        "value": 0
    }

def build_buy_conditional_bundle(
    w3: Web3,
    proposal: str,
    collateral_token: str, # sDAI
    conditional_tokens: Dict[str, str], # {YES: addr, NO: addr}
    company_token: str,
    amount_in: int,
    recipient: str
) -> List[Dict[str, Any]]:
    """
    Build the sequence of calls for Buy Conditional Arb.
    Flow: Split sDAI -> Swap YES/NO sDAI to Company -> Merge Company -> Sell Company for sDAI
    """
    calls = []
    
    # 1. Approve sDAI to FutarchyRouter
    calls.append(encode_approval(collateral_token, FUTARCHY_ROUTER, amount_in))
    
    # 2. Split sDAI
    calls.append(encode_split(FUTARCHY_ROUTER, proposal, collateral_token, amount_in))
    
    # 3. Approve Conditional Tokens to Swapr (Optimized: assume infinite or exact)
    calls.append(encode_approval(conditional_tokens['YES'], SWAPR_ROUTER, amount_in))
    calls.append(encode_approval(conditional_tokens['NO'], SWAPR_ROUTER, amount_in))
    
    # 4. Swap YES sDAI -> YES Company (Placeholder amounts, in production use simulation results)
    calls.append(encode_swapr_exact_in(SWAPR_ROUTER, conditional_tokens['YES'], company_token, amount_in, 0, recipient))
    
    # ... (Add remaining steps: Swap NO, Merge, Sell on Balancer)
    
    return calls