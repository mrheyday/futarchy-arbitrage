#!/usr/bin/env python3
"""
Deploy SafetyModule to Chiado Testnet

Chiado is Gnosis Chain's testnet.
RPC: https://rpc.chiadochain.net
Explorer: https://gnosis-chiado.blockscout.com
"""

import os
import json
import sys
from pathlib import Path
from web3 import Web3
from eth_account import Account
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.logging_config import setup_logger

logger = setup_logger("deploy_safety_module")

# Chiado RPC
CHIADO_RPC = "https://rpc.chiadochain.net"
CHAIN_ID = 10200  # Chiado chain ID

def load_contract_artifacts():
    """Load compiled contract bytecode and ABI"""
    # Run forge build first
    logger.info("Compiling contracts...")
    os.system("cd /Users/hs/futarchy-arbitrage-1 && forge build > /dev/null 2>&1")
    
    # Load artifacts
    artifact_path = Path(__file__).parent.parent / "out" / "SafetyModule.sol" / "SafetyModule.json"
    
    if not artifact_path.exists():
        logger.error(f"Contract artifact not found: {artifact_path}")
        logger.info("Run: forge build")
        sys.exit(1)
    
    with open(artifact_path, 'r') as f:
        artifact = json.load(f)
    
    return artifact['bytecode']['object'], artifact['abi']

def deploy_safety_module(private_key: str, rpc_url: str = CHIADO_RPC):
    """Deploy SafetyModule contract to Chiado testnet"""
    
    logger.info(f"Connecting to Chiado testnet: {rpc_url}")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        logger.error("Failed to connect to Chiado RPC")
        return None
    
    logger.info(f"Connected! Chain ID: {w3.eth.chain_id}")
    
    # Load account
    account = Account.from_key(private_key)
    logger.info(f"Deployer address: {account.address}")
    
    # Check balance
    balance = w3.eth.get_balance(account.address)
    balance_eth = w3.from_wei(balance, 'ether')
    logger.info(f"Balance: {balance_eth} xDAI")
    
    if balance == 0:
        logger.error("No xDAI balance! Get testnet tokens from: https://gnosisfaucet.com")
        return None
    
    # Load contract
    bytecode, abi = load_contract_artifacts()
    
    logger.info("Deploying SafetyModule contract...")
    
    # Create contract object
    SafetyModule = w3.eth.contract(abi=abi, bytecode=bytecode)
    
    # Build deployment transaction
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price
    
    # Estimate gas
    try:
        gas_estimate = SafetyModule.constructor().estimate_gas({
            'from': account.address
        })
        gas_limit = int(gas_estimate * 1.2)  # Add 20% buffer
        logger.info(f"Estimated gas: {gas_estimate}, using: {gas_limit}")
    except Exception as e:
        logger.warning(f"Gas estimation failed: {e}, using default")
        gas_limit = 3000000
    
    # Build transaction
    deploy_txn = SafetyModule.constructor().build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': gas_limit,
        'gasPrice': gas_price,
        'chainId': CHAIN_ID
    })
    
    # Sign transaction
    signed_txn = account.sign_transaction(deploy_txn)
    
    # Send transaction
    logger.info("Sending deployment transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    logger.info(f"Transaction hash: {tx_hash.hex()}")
    logger.info(f"Explorer: https://gnosis-chiado.blockscout.com/tx/{tx_hash.hex()}")
    
    # Wait for receipt
    logger.info("Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        contract_address = receipt['contractAddress']
        logger.info(f"✅ SafetyModule deployed successfully!")
        logger.info(f"Contract address: {contract_address}")
        logger.info(f"Explorer: https://gnosis-chiado.blockscout.com/address/{contract_address}")
        logger.info(f"Gas used: {receipt['gasUsed']:,}")
        
        # Save deployment info
        deployment_info = {
            "network": "chiado",
            "chain_id": CHAIN_ID,
            "contract": "SafetyModule",
            "address": contract_address,
            "deployer": account.address,
            "tx_hash": tx_hash.hex(),
            "block_number": receipt['blockNumber'],
            "gas_used": receipt['gasUsed'],
            "timestamp": datetime.now().isoformat(),
            "explorer": f"https://gnosis-chiado.blockscout.com/address/{contract_address}"
        }
        
        # Save to file
        deployments_dir = Path(__file__).parent.parent / "deployments"
        deployments_dir.mkdir(exist_ok=True)
        
        filename = f"safety_module_chiado_{int(datetime.now().timestamp())}.json"
        filepath = deployments_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        logger.info(f"Deployment info saved to: {filepath}")
        
        return deployment_info
    else:
        logger.error(f"❌ Deployment failed!")
        logger.error(f"Transaction reverted")
        return None

def verify_deployment(contract_address: str, rpc_url: str = CHIADO_RPC):
    """Verify deployed contract works correctly"""
    logger.info(f"\nVerifying deployment at {contract_address}...")
    
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    _, abi = load_contract_artifacts()
    
    contract = w3.eth.contract(address=contract_address, abi=abi)
    
    # Test read functions
    try:
        owner = contract.functions.owner().call()
        paused = contract.functions.paused().call()
        max_slippage = contract.functions.maxSlippageBps().call()
        max_gas_price = contract.functions.maxGasPrice().call()
        
        logger.info("✅ Contract verified!")
        logger.info(f"  Owner: {owner}")
        logger.info(f"  Paused: {paused}")
        logger.info(f"  Max slippage: {max_slippage} bps ({max_slippage/100}%)")
        logger.info(f"  Max gas price: {w3.from_wei(max_gas_price, 'gwei')} gwei")
        
        return True
    except Exception as e:
        logger.error(f"❌ Verification failed: {e}")
        return False

def main():
    """Main deployment function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Deploy SafetyModule to Chiado testnet")
    parser.add_argument(
        "--verify-only",
        type=str,
        help="Only verify existing deployment at given address"
    )
    
    args = parser.parse_args()
    
    if args.verify_only:
        verify_deployment(args.verify_only)
        return
    
    # Get private key from environment
    private_key = os.getenv("PRIVATE_KEY")
    if not private_key:
        logger.error("PRIVATE_KEY environment variable not set")
        sys.exit(1)
    
    # Deploy
    deployment_info = deploy_safety_module(private_key)
    
    if deployment_info:
        # Verify
        verify_deployment(deployment_info['address'])
        
        logger.info("\n" + "="*60)
        logger.info("DEPLOYMENT SUMMARY")
        logger.info("="*60)
        logger.info(f"Network: Chiado Testnet")
        logger.info(f"Contract: {deployment_info['address']}")
        logger.info(f"Explorer: {deployment_info['explorer']}")
        logger.info(f"Gas used: {deployment_info['gas_used']:,}")
        logger.info("="*60)
        logger.info("\nNext steps:")
        logger.info("1. Update .env with SAFETY_MODULE_ADDRESS={deployment_info['address']}")
        logger.info("2. Test circuit breakers with test transactions")
        logger.info("3. Integrate with executor contracts")
        logger.info("="*60)
    else:
        logger.error("Deployment failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
