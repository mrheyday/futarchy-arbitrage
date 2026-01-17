"""
Sell Conditional Bundle Builder (EIP-7702).
Generates a list of encoded calls for the sell conditional arbitrage flow.
"""

from typing import List, Dict, Any
from web3 import Web3
from eth_utils import keccak
from src.arbitrage_commands.buy_cond_eip7702 import encode_approval, encode_split, encode_merge, encode_swapr_exact_in
from src.helpers.balancer_swap import get_balancer_pool_id

# Reusing constants/helpers from buy_cond for consistency
FUTARCHY_ROUTER = "0x..." 
SWAPR_ROUTER = "0x..."
BALANCER_VAULT = "0x..."

def encode_balancer_swap(
    vault: str,
    pool_id: str,
    token_in: str,
    token_out: str,
    amount: int,
    recipient: str
) -> Dict[str, Any]:
    """Encode Balancer V2 swap call."""
    # swap((bytes32,uint8,address,address,uint256,bytes),(address,bool,address,bool),uint256,uint256)
    # Selector: 0x52bb5f91
    
    selector = keccak(text="swap((bytes32,uint8,address,address,uint256,bytes),(address,bool,address,bool),uint256,uint256)")[:4]
    
    single_swap = (
        bytes.fromhex(pool_id[2:]) if pool_id.startswith("0x") else bytes.fromhex(pool_id),
        0, # GIVEN_IN
        token_in,
        token_out,
        amount,
        b""
    )
    
    fund_management = (
        recipient, # sender
        False,     # fromInternalBalance
        recipient, # recipient
        False      # toInternalBalance
    )
    
    limit = 0
    deadline = 2**256 - 1
    
    encoded_params = Web3.solidity_encode(
        ["(bytes32,uint8,address,address,uint256,bytes)", "(address,bool,address,bool)", "uint256", "uint256"],
        [single_swap, fund_management, limit, deadline]
    )
    
    return {
        "to": vault,
        "data": selector + encoded_params,
        "value": 0
    }

def build_sell_conditional_bundle(
    w3: Web3,
    proposal: str,
    collateral_token: str, # sDAI
    conditional_tokens: Dict[str, str], # {YES: addr, NO: addr} (sDAI)
    conditional_company_tokens: Dict[str, str], # {YES: addr, NO: addr} (Company)
    company_token: str,
    balancer_pool_address: str,
    amount_in: int,
    recipient: str
) -> List[Dict[str, Any]]:
    """
    Build the sequence of calls for Sell Conditional Arb.
    Flow: Buy Company with sDAI -> Split Company -> Swap YES/NO Company to sDAI -> Merge sDAI
    """
    calls = []
    MAX_UINT = 2**256 - 1
    
    # Fetch dynamic pool ID
    balancer_pool_id = get_balancer_pool_id(w3, balancer_pool_address)
    
    # 1. Approve sDAI to Balancer
    calls.append(encode_approval(collateral_token, BALANCER_VAULT, amount_in))
    
    # 2. Swap sDAI -> Company on Balancer
    calls.append(encode_balancer_swap(
        BALANCER_VAULT,
        balancer_pool_id,
        collateral_token,
        company_token,
        amount_in,
        recipient
    ))
    
    # 3. Approve Company to FutarchyRouter
    calls.append(encode_approval(company_token, FUTARCHY_ROUTER, MAX_UINT))
    
    # 4. Split Company Token
    # Note: Using amount_in as placeholder for split amount. 
    # In a real execution environment with patching, this would be dynamic.
    calls.append(encode_split(FUTARCHY_ROUTER, proposal, company_token, amount_in))
    
    # 5. Approve Conditional Company Tokens to Swapr
    calls.append(encode_approval(conditional_company_tokens['YES'], SWAPR_ROUTER, MAX_UINT))
    calls.append(encode_approval(conditional_company_tokens['NO'], SWAPR_ROUTER, MAX_UINT))
    
    # 6. Swap YES Company -> YES sDAI
    calls.append(encode_swapr_exact_in(
        SWAPR_ROUTER,
        conditional_company_tokens['YES'],
        conditional_tokens['YES'],
        amount_in, # Placeholder
        0,
        recipient
    ))
    
    # 7. Swap NO Company -> NO sDAI
    calls.append(encode_swapr_exact_in(
        SWAPR_ROUTER,
        conditional_company_tokens['NO'],
        conditional_tokens['NO'],
        amount_in, # Placeholder
        0,
        recipient
    ))
    
    # 8. Approve Conditional sDAI to FutarchyRouter
    calls.append(encode_approval(conditional_tokens['YES'], FUTARCHY_ROUTER, MAX_UINT))
    calls.append(encode_approval(conditional_tokens['NO'], FUTARCHY_ROUTER, MAX_UINT))
    
    # 9. Merge sDAI
    calls.append(encode_merge(FUTARCHY_ROUTER, proposal, collateral_token, amount_in))
<<<<<<< Updated upstream
<<<<<<< Updated upstream

    return calls


def sell_conditional_simple(
    w3: Web3,
    proposal: str,
    collateral_token: str,
    conditional_sdai_yes: str,
    conditional_sdai_no: str,
    conditional_company_yes: str,
    conditional_company_no: str,
    company_token: str,
    balancer_pool_address: str,
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
    Execute the sell conditional arbitrage flow.

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
        balancer_pool_address: Balancer pool address for Company/sDAI
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

    conditional_sdai_tokens = {
        'YES': conditional_sdai_yes,
        'NO': conditional_sdai_no,
    }

    conditional_company_tokens = {
        'YES': conditional_company_yes,
        'NO': conditional_company_no,
    }

    try:
        # Build the bundle
        calls = build_sell_conditional_bundle(
            w3=w3,
            proposal=proposal,
            collateral_token=collateral_token,
            conditional_tokens=conditional_sdai_tokens,
            conditional_company_tokens=conditional_company_tokens,
            company_token=company_token,
            balancer_pool_address=balancer_pool_address,
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
    
    return calls
>>>>>>> Stashed changes
=======
    
    return calls
>>>>>>> Stashed changes
