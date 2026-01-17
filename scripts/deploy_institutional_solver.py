"""
Deployment script for Institutional Solver Intelligence System
================================================================

Deploys the CLZ-enhanced solver system with proper initialization.
January 2026 post-Fusaka deployment.
"""

import json
import os
from web3 import Web3
from eth_account import Account
import time

# Configuration
RPC_URL = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
CHAIN_ID = int(os.getenv("CHAIN_ID", "100"))  # Gnosis Chain

# Contract addresses (configure these)
ZK_VERIFIER = os.getenv("ZK_VERIFIER", "0x0000000000000000000000000000000000000000")
PAYMASTER = os.getenv("PAYMASTER", "0x0000000000000000000000000000000000000000")

# Flashloan providers on Gnosis Chain
AAVE_POOL = "0xb50201558B00496A145fE76f7424749556E326D8"  # Aave V3 Pool
BALANCER_VAULT = "0xBA12222222228d8Ba445958a75a0704d566BF2C8"  # Balancer V2 Vault
# Morpho not on Gnosis, using placeholder
MORPHO_PLACEHOLDER = "0x0000000000000000000000000000000000000000"


def load_contract_artifacts(contract_name: str) -> dict:
    """Load compiled contract artifacts."""
    # Path to Foundry output
    artifact_path = f"out/{contract_name}.sol/{contract_name}.json"
    
    if not os.path.exists(artifact_path):
        print(f"Contract artifacts not found at {artifact_path}")
        print("Please compile contracts first with: forge build --profile institutional")
        return None
    
    with open(artifact_path) as f:
        artifact = json.load(f)
    
    return {
        'abi': artifact['abi'],
        'bytecode': artifact['bytecode']['object']
    }


def deploy_institutional_solver_system(
    w3: Web3,
    deployer_account: Account,
    zk_verifier: str,
    paymaster: str,
    flashloan_providers: list[str]
) -> str:
    """
    Deploy InstitutionalSolverSystem contract.
    
    Args:
        w3: Web3 instance
        deployer_account: Deployer account
        zk_verifier: ZK verifier contract address
        paymaster: Paymaster contract address
        flashloan_providers: List of flashloan provider addresses
        
    Returns:
        Deployed contract address
    """
    print("=" * 60)
    print("Deploying Institutional Solver Intelligence System")
    print("=" * 60)
    print(f"Network: {w3.provider.endpoint_uri}")
    print(f"Chain ID: {w3.eth.chain_id}")
    print(f"Deployer: {deployer_account.address}")
    print(f"Balance: {w3.from_wei(w3.eth.get_balance(deployer_account.address), 'ether')} ETH")
    print()
    
    # Load contract artifacts
    print("Loading contract artifacts...")
    artifacts = load_contract_artifacts("InstitutionalSolverSystem")
    if not artifacts:
        return None
    
    # Create contract instance
    contract = w3.eth.contract(
        abi=artifacts['abi'],
        bytecode=artifacts['bytecode']
    )
    
    # Constructor arguments
    constructor_args = (
        Web3.to_checksum_address(zk_verifier),
        Web3.to_checksum_address(paymaster),
        [Web3.to_checksum_address(p) for p in flashloan_providers]
    )
    
    print("Constructor arguments:")
    print(f"  ZK Verifier: {constructor_args[0]}")
    print(f"  Paymaster: {constructor_args[1]}")
    print(f"  Flashloan Providers:")
    for provider in constructor_args[2]:
        print(f"    - {provider}")
    print()
    
    # Estimate gas
    print("Estimating gas...")
    try:
        gas_estimate = contract.constructor(*constructor_args).estimate_gas({
            'from': deployer_account.address
        })
        print(f"Gas estimate: {gas_estimate:,}")
    except Exception as e:
        print(f"Gas estimation failed: {e}")
        gas_estimate = 5000000  # Fallback
        print(f"Using fallback gas limit: {gas_estimate:,}")
    
    # Build transaction
    print("\nBuilding deployment transaction...")
    nonce = w3.eth.get_transaction_count(deployer_account.address)
    gas_price = w3.eth.gas_price
    
    tx = contract.constructor(*constructor_args).build_transaction({
        'from': deployer_account.address,
        'nonce': nonce,
        'gas': gas_estimate,
        'gasPrice': gas_price,
        'chainId': w3.eth.chain_id
    })
    
    print(f"Nonce: {nonce}")
    print(f"Gas Price: {w3.from_wei(gas_price, 'gwei')} gwei")
    print(f"Max Cost: {w3.from_wei(gas_estimate * gas_price, 'ether')} ETH")
    print()
    
    # Sign and send transaction
    print("Signing transaction...")
    signed_tx = deployer_account.sign_transaction(tx)
    
    print("Sending transaction...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"Transaction hash: {tx_hash.hex()}")
    
    # Wait for receipt
    print("Waiting for confirmation...")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
    
    if receipt['status'] == 1:
        print("✓ Deployment successful!")
        print(f"Contract address: {receipt['contractAddress']}")
        print(f"Gas used: {receipt['gasUsed']:,}")
        print(f"Block number: {receipt['blockNumber']}")
        
        # Save deployment info
        deployment_info = {
            'contract': 'InstitutionalSolverSystem',
            'address': receipt['contractAddress'],
            'deployer': deployer_account.address,
            'tx_hash': tx_hash.hex(),
            'block_number': receipt['blockNumber'],
            'gas_used': receipt['gasUsed'],
            'constructor_args': {
                'zk_verifier': zk_verifier,
                'paymaster': paymaster,
                'flashloan_providers': flashloan_providers
            },
            'timestamp': int(time.time()),
            'chain_id': w3.eth.chain_id
        }
        
        output_file = f"deployments/institutional_solver_{int(time.time())}.json"
        os.makedirs("deployments", exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\nDeployment info saved to: {output_file}")
        
        return receipt['contractAddress']
    else:
        print("✗ Deployment failed!")
        return None


def initialize_system(
    w3: Web3,
    contract_address: str,
    deployer_account: Account
):
    """
    Initialize the deployed system with initial configuration.
    
    Args:
        w3: Web3 instance
        contract_address: Deployed contract address
        deployer_account: Deployer account (owner)
    """
    print("\n" + "=" * 60)
    print("Initializing System")
    print("=" * 60)
    
    # Load contract
    artifacts = load_contract_artifacts("InstitutionalSolverSystem")
    contract = w3.eth.contract(
        address=Web3.to_checksum_address(contract_address),
        abi=artifacts['abi']
    )
    
    # Example: Open first auction
    print("\nOpening auction #1...")
    tx = contract.functions.openAuction(1).build_transaction({
        'from': deployer_account.address,
        'nonce': w3.eth.get_transaction_count(deployer_account.address),
        'gas': 100000,
        'gasPrice': w3.eth.gas_price,
        'chainId': w3.eth.chain_id
    })
    
    signed_tx = deployer_account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt['status'] == 1:
        print("✓ Auction #1 opened")
    else:
        print("✗ Failed to open auction")
    
    print("\n" + "=" * 60)
    print("System initialized successfully!")
    print("=" * 60)


def main():
    """Main deployment function."""
    if not PRIVATE_KEY:
        print("Error: PRIVATE_KEY environment variable not set")
        return
    
    # Initialize Web3
    print("Connecting to RPC...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        print("Error: Could not connect to RPC")
        return
    
    print(f"✓ Connected to {RPC_URL}")
    
    # Load deployer account
    deployer_account = Account.from_key(PRIVATE_KEY)
    
    # Deploy system
    flashloan_providers = [AAVE_POOL, BALANCER_VAULT]
    
    contract_address = deploy_institutional_solver_system(
        w3=w3,
        deployer_account=deployer_account,
        zk_verifier=ZK_VERIFIER,
        paymaster=PAYMASTER,
        flashloan_providers=flashloan_providers
    )
    
    if contract_address:
        # Initialize system
        initialize_system(w3, contract_address, deployer_account)
        
        print("\n" + "=" * 60)
        print("DEPLOYMENT COMPLETE")
        print("=" * 60)
        print(f"Contract Address: {contract_address}")
        print("\nNext steps:")
        print("1. Verify contract on block explorer")
        print("2. Set up monitoring and telemetry")
        print("3. Configure authorized solvers")
        print("4. Test with small amounts first")
        print("=" * 60)


if __name__ == "__main__":
    main()
