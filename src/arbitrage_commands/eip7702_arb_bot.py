#!/usr/bin/env python3
"""
EIP-7702 Arbitrage Bot.
Monitors prices and executes atomic arbitrage using EIP-7702 bundled transactions.
"""

import os
import sys
import time
import logging
import argparse
from decimal import Decimal
from web3 import Web3
from eth_account import Account

# Add project root to path
sys.path.append(os.getcwd())

try:
    from src.helpers.swapr_price import get_pool_price as swapr_price
    from src.helpers.balancer_price import get_pool_price as bal_price
    from src.arbitrage_commands.buy_cond_eip7702 import build_buy_conditional_bundle
    from src.arbitrage_commands.sell_cond_eip7702 import build_sell_conditional_bundle
    from src.executor.eip7702_sender import send_eip7702_bundle
    from src.config.network import DEFAULT_RPC_URLS
except ImportError as e:
    print(f"Import Error: {e}")
    print("Ensure you are running from the project root.")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("EIP7702Bot")

DEFAULT_EXECUTOR_ADDRESS = "0x65eb5a03635c627a0f254707712812B234753F31"

def make_web3() -> Web3:
    rpc_url = os.getenv("RPC_URL", DEFAULT_RPC_URLS[0])
    return Web3(Web3.HTTPProvider(rpc_url))

def fetch_swapr(pool: str, w3: Web3, *, base_token_index: int = 0) -> tuple[str, str, str]:
    price, base, quote = swapr_price(w3, pool, base_token_index=base_token_index)
    return base, quote, str(price)

def fetch_balancer(pool: str, w3: Web3) -> tuple[str, str, str]:
    price, base, quote = bal_price(w3, pool)
    return base, quote, str(price)

def run_once(
    w3: Web3,
    account: Account,
    amount: float,
    tolerance: float,
    executor_address: str,
    dry_run: bool
) -> None:
    # Load Env Vars
    addr_yes = os.getenv("SWAPR_POOL_YES_ADDRESS")
    addr_pred_yes = os.getenv("SWAPR_POOL_PRED_YES_ADDRESS")
    addr_no = os.getenv("SWAPR_POOL_NO_ADDRESS")
    addr_bal = os.getenv("BALANCER_POOL_ADDRESS")
    
    proposal_addr = os.getenv("FUTARCHY_PROPOSAL_ADDRESS")
    sdai_addr = os.getenv("SDAI_TOKEN_ADDRESS")
    company_addr = os.getenv("COMPANY_TOKEN_ADDRESS")
    
    sdai_yes = os.getenv("SWAPR_SDAI_YES_ADDRESS")
    sdai_no = os.getenv("SWAPR_SDAI_NO_ADDRESS")
    gno_yes = os.getenv("SWAPR_GNO_YES_ADDRESS")
    gno_no = os.getenv("SWAPR_GNO_NO_ADDRESS")

    if not all([addr_yes, addr_pred_yes, addr_no, addr_bal, proposal_addr, sdai_addr, company_addr, sdai_yes, sdai_no, gno_yes, gno_no]):
        logger.error("Missing environment variables. Check your .env file.")
        return

    # Fetch Prices
    try:
        _, _, yes_price_str = fetch_swapr(addr_yes, w3, base_token_index=1)
        _, _, pred_yes_price_str = fetch_swapr(addr_pred_yes, w3, base_token_index=0)
        _, _, no_price_str = fetch_swapr(addr_no, w3, base_token_index=1)
        _, _, bal_price_str = fetch_balancer(addr_bal, w3)
    except Exception as e:
        logger.error(f"Error fetching prices: {e}")
        return

    yes_price = float(yes_price_str)
    pred_yes_price = float(pred_yes_price_str)
    no_price = float(no_price_str)
    bal_price_val = float(bal_price_str)

    # Calculate Ideal Price
    # ideal_price = pred_price * yes_price + (1 - pred_price) * no_price
    ideal_bal_price = pred_yes_price * yes_price + (1.0 - pred_yes_price) * no_price
    
    logger.info(f"Prices - YES: {yes_price:.4f}, NO: {no_price:.4f}, PRED: {pred_yes_price:.4f}")
    logger.info(f"Balancer Price: {bal_price_val:.4f} | Ideal Price: {ideal_bal_price:.4f}")
    
    diff = bal_price_val - ideal_bal_price
    logger.info(f"Difference: {diff:.4f}")

    amount_wei = w3.to_wei(amount, "ether")
    
    # Decision Logic
    if abs(diff) < tolerance:
        logger.info("Price difference within tolerance. No trade.")
        return

    calls = []
    action = ""

    if diff > 0:
        # Balancer Price > Ideal Price => Company token is expensive on Balancer relative to conditional markets.
        action = "BUY_CONDITIONAL"
        logger.info(f"Opportunity: {action} (Diff: {diff:.4f} > 0)")
        
        calls = build_buy_conditional_bundle(
            w3=w3,
            proposal=proposal_addr,
            collateral_token=sdai_addr,
            conditional_tokens={'YES': sdai_yes, 'NO': sdai_no},
            company_token=company_addr,
            amount_in=amount_wei,
            recipient=account.address
        )
        
    else:
        # Balancer Price < Ideal Price => Company token is cheap on Balancer.
        action = "SELL_CONDITIONAL"
        logger.info(f"Opportunity: {action} (Diff: {diff:.4f} < 0)")
        
        calls = build_sell_conditional_bundle(
            w3=w3,
            proposal=proposal_addr,
            collateral_token=sdai_addr,
            conditional_tokens={'YES': sdai_yes, 'NO': sdai_no},
            conditional_company_tokens={'YES': gno_yes, 'NO': gno_no},
            company_token=company_addr,
            balancer_pool_address=addr_bal,
            amount_in=amount_wei,
            recipient=account.address
        )

    if not calls:
        logger.warning("Failed to build transaction bundle.")
        return

    logger.info(f"Built bundle with {len(calls)} operations.")

    if dry_run:
        logger.info("[DRY RUN] Skipping execution.")
        return

    try:
        tx_hash = send_eip7702_bundle(
            w3=w3,
            account=account,
            implementation_address=executor_address,
            calls=calls,
            gas_limit=3_000_000 # Estimate or config
        )
        logger.info(f"🚀 Transaction Sent: {tx_hash}")
    except Exception as e:
        logger.error(f"Execution Failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="EIP-7702 Arbitrage Bot")
    parser.add_argument("--amount", type=float, required=True, help="Amount to trade (in sDAI)")
    parser.add_argument("--interval", type=int, default=60, help="Interval between checks (seconds)")
    parser.add_argument("--tolerance", type=float, default=0.02, help="Price difference tolerance")
    parser.add_argument("--executor", type=str, default=DEFAULT_EXECUTOR_ADDRESS, help="EIP-7702 Implementation Address")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without sending transactions")
    
    args = parser.parse_args()

    # Setup Web3 and Account
    w3 = make_web3()
    if not w3.is_connected():
        logger.critical("Could not connect to RPC.")
        sys.exit(1)
        
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        logger.critical("PRIVATE_KEY env var not set.")
        sys.exit(1)
        
    account = Account.from_key(private_key)
    logger.info(f"Bot Address: {account.address}")
    logger.info(f"Executor: {args.executor}")

    logger.info(f"Starting loop. Interval: {args.interval}s, Amount: {args.amount}, Tolerance: {args.tolerance}")

    while True:
        try:
            run_once(w3, account, args.amount, args.tolerance, args.executor, args.dry_run)
        except KeyboardInterrupt:
            logger.info("Stopping bot.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
        
        time.sleep(args.interval)

if __name__ == "__main__":
    main()