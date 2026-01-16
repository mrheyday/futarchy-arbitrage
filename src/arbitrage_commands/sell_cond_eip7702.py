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
    
    return calls