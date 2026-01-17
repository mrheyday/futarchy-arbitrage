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
<<<<<<< Updated upstream
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


def buy_conditional_simple(
    w3: Web3,
    proposal: str,
    collateral_token: str,
    conditional_sdai_yes: str,
    conditional_sdai_no: str,
    conditional_company_yes: str,
    conditional_company_no: str,
    company_token: str,
    amount_in: int,
    recipient: str,
    private_key: str,
    *,
    futarchy_router: str | None = None,
    swapr_router: str | None = None,
    balancer_vault: str | None = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Execute the buy conditional arbitrage flow.

    This is a simplified wrapper for EIP-7702 bundle execution.

    Args:
        w3: Web3 instance
        proposal: Futarchy proposal address
        collateral_token: sDAI token address
        conditional_sdai_yes: Conditional sDAI YES token address
        conditional_sdai_no: Conditional sDAI NO token address
        conditional_company_yes: Conditional Company YES token address
        conditional_company_no: Conditional Company NO token address
        company_token: Company token address
        amount_in: Amount of sDAI to use (in wei)
        recipient: Address to receive output
        private_key: Private key for signing
        futarchy_router: Optional FutarchyRouter address override
        swapr_router: Optional Swapr router address override
        balancer_vault: Optional Balancer vault address override
        dry_run: If True, only simulate without broadcasting

    Returns:
        Dict with execution result:
        - success: bool
        - tx_hash: str (if success)
        - error: str (if failed)
        - simulated: bool
    """
    import os

    # Use provided addresses or fall back to env/defaults
    global FUTARCHY_ROUTER, SWAPR_ROUTER, BALANCER_VAULT
    if futarchy_router:
        FUTARCHY_ROUTER = futarchy_router
    elif os.getenv("FUTARCHY_ROUTER_ADDRESS"):
        FUTARCHY_ROUTER = os.getenv("FUTARCHY_ROUTER_ADDRESS")

    if swapr_router:
        SWAPR_ROUTER = swapr_router
    elif os.getenv("SWAPR_ROUTER_ADDRESS"):
        SWAPR_ROUTER = os.getenv("SWAPR_ROUTER_ADDRESS")

    if balancer_vault:
        BALANCER_VAULT = balancer_vault
    elif os.getenv("BALANCER_VAULT_ADDRESS"):
        BALANCER_VAULT = os.getenv("BALANCER_VAULT_ADDRESS")

    conditional_tokens = {
        'YES': conditional_sdai_yes,
        'NO': conditional_sdai_no,
    }

    try:
        # Build the bundle
        calls = build_buy_conditional_bundle(
            w3=w3,
            proposal=proposal,
            collateral_token=collateral_token,
            conditional_tokens=conditional_tokens,
            company_token=company_token,
            amount_in=amount_in,
            recipient=recipient,
        )

        if dry_run:
            return {
                "success": True,
                "simulated": True,
                "calls": len(calls),
                "tx_hash": None,
            }

        # In production, this would use EIP-7702 bundling via PectraWrapper
        # For now, return simulation result
        return {
            "success": True,
            "simulated": True,
            "calls": len(calls),
            "tx_hash": None,
            "message": "EIP-7702 execution requires PectraWrapper delegation"
        }

    except Exception as e:
        return {
            "success": False,
            "simulated": False,
            "error": str(e),
            "tx_hash": None,
        }
=======
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
>>>>>>> Stashed changes
