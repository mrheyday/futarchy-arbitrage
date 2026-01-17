#!/usr/bin/env python3
"""
Multi-chain deployment helper for Futarchy arbitrage contracts.

Supports deployment to Base and Polygon networks.
Handles contract configuration, deployment, and verification.

Usage:
    python3 scripts/deploy_multi_chain.py --network base --deploy
    python3 scripts/deploy_multi_chain.py --network polygon --verify
    python3 scripts/deploy_multi_chain.py --network base --broadcast
"""

import json
import os
import sys
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime
from enum import Enum

from web3 import Web3
from eth_account import Account


class Network(Enum):
    """Supported networks for deployment."""
    BASE = "base"
    POLYGON = "polygon"
    BASE_SEPOLIA = "base_sepolia"
    POLYGON_MUMBAI = "polygon_mumbai"


@dataclass
class NetworkConfig:
    """Configuration for a network."""
    name: str
    chain_id: int
    rpc_url: str
    explorer_url: str
    futarchy_router: str
    balancer_router: str
    swapr_router: str
    multicall3: Optional[str] = None


class ChainConfigs:
    """Network configurations for supported chains."""
    
    BASE = NetworkConfig(
        name="Base",
        chain_id=8453,
        rpc_url="https://mainnet.base.org",
        explorer_url="https://basescan.org",
        futarchy_router="0x0000000000000000000000000000000000000000",  # TODO: Update
        balancer_router="0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        swapr_router="0x6131B5fAe19EA4f9D964eAc0408E3616eDA97B7f",
        multicall3="0xcA11bde05977b3631167028862bE2a173976CA11",
    )

    POLYGON = NetworkConfig(
        name="Polygon",
        chain_id=137,
        rpc_url="https://polygon-rpc.com",
        explorer_url="https://polygonscan.com",
        futarchy_router="0x0000000000000000000000000000000000000000",  # TODO: Update
        balancer_router="0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        swapr_router="0x6131B5fAe19EA4f9D964eAc0408E3616eDA97B7f",
        multicall3="0xcA11bde05977b3631167028862bE2a173976CA11",
    )

    BASE_SEPOLIA = NetworkConfig(
        name="Base Sepolia",
        chain_id=84532,
        rpc_url="https://sepolia.base.org",
        explorer_url="https://sepolia.basescan.org",
        futarchy_router="0x0000000000000000000000000000000000000000",  # Testnet
        balancer_router="0x0000000000000000000000000000000000000000",
        swapr_router="0x0000000000000000000000000000000000000000",
        multicall3="0xcA11bde05977b3631167028862bE2a173976CA11",
    )

    POLYGON_MUMBAI = NetworkConfig(
        name="Polygon Mumbai",
        chain_id=80001,
        rpc_url="https://rpc-mumbai.maticvigil.com",
        explorer_url="https://mumbai.polygonscan.com",
        futarchy_router="0x0000000000000000000000000000000000000000",  # Testnet
        balancer_router="0x0000000000000000000000000000000000000000",
        swapr_router="0x0000000000000000000000000000000000000000",
        multicall3="0xcA11bde05977b3631167028862bE2a173976CA11",
    )

    @classmethod
    def get(cls, network: Network) -> NetworkConfig:
        """Get configuration for a specific network."""
        mapping = {
            Network.BASE: cls.BASE,
            Network.POLYGON: cls.POLYGON,
            Network.BASE_SEPOLIA: cls.BASE_SEPOLIA,
            Network.POLYGON_MUMBAI: cls.POLYGON_MUMBAI,
        }
        return mapping[network]


@dataclass
class DeploymentResult:
    """Result of a deployment."""
    network: str
    timestamp: str
    chain_id: int
    executor_v5: str
    safety_module: str
    pectra_wrapper: str
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    gas_used: Optional[int] = None

    def save(self, filepath: Optional[str] = None) -> str:
        """Save deployment result to JSON file."""
        if filepath is None:
            # Generate default filepath
            network_name = self.network.lower().replace(" ", "_")
            filepath = f"deployments/deployment_{network_name}_{int(datetime.now().timestamp())}.json"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(asdict(self), f, indent=2)
        
        return filepath


class DeploymentManager:
    """Manages contract deployments across multiple networks."""

    def __init__(self, network: Network, private_key: Optional[str] = None):
        self.network = network
        self.config = ChainConfigs.get(network)
        self.w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
        
        # Setup account
        if private_key:
            self.account = Account.from_key(private_key)
        else:
            self.account = self._get_account_from_env()
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {self.config.name} RPC: {self.config.rpc_url}")
        
        print(f"✓ Connected to {self.config.name} (Chain ID: {self.config.chain_id})")
        print(f"  RPC: {self.config.rpc_url}")
        print(f"  Account: {self.account.address}")

    def _get_account_from_env(self) -> Account:
        """Get account from environment variables."""
        private_key = os.getenv("PRIVATE_KEY")
        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable not set")
        return Account.from_key(private_key)

    def validate_network(self) -> bool:
        """Validate network connection and chain ID."""
        chain_id = self.w3.eth.chain_id
        if chain_id != self.config.chain_id:
            raise ValueError(
                f"Chain ID mismatch: expected {self.config.chain_id}, got {chain_id}"
            )
        return True

    def check_balance(self, min_eth: float = 0.1) -> bool:
        """Check if account has sufficient ETH for deployment."""
        balance = self.w3.eth.get_balance(self.account.address)
        balance_eth = self.w3.from_wei(balance, 'ether')
        
        print(f"\n💰 Account Balance: {balance_eth:.6f} ETH")
        
        if balance_eth < min_eth:
            print(f"⚠️  Warning: Balance ({balance_eth:.6f} ETH) < minimum required ({min_eth} ETH)")
            return False
        
        return True

    def estimate_deployment_gas(self) -> Dict[str, int]:
        """Estimate gas costs for deployment."""
        # These are rough estimates; actual gas may vary
        estimates = {
            "safety_module": 500000,
            "pectra_wrapper": 400000,
            "executor_v5": 2000000,
        }
        
        gas_price = self.w3.eth.gas_price
        total_gas = sum(estimates.values())
        total_cost_eth = self.w3.from_wei(total_gas * gas_price, 'ether')
        
        print(f"\n⛽ Gas Estimates:")
        print(f"  SafetyModule: ~{estimates['safety_module']:,} gas")
        print(f"  PectraWrapper: ~{estimates['pectra_wrapper']:,} gas")
        print(f"  FutarchyArbExecutorV5: ~{estimates['executor_v5']:,} gas")
        print(f"  Total: ~{total_gas:,} gas (~{total_cost_eth:.6f} ETH at current gas price)")
        
        return estimates

    def deploy_via_forge(self, contract_name: str, broadcast: bool = False) -> Optional[str]:
        """
        Deploy contract using Forge script.
        
        Args:
            contract_name: Name of the contract (e.g., "BaseDeployment", "PolygonDeployment")
            broadcast: Whether to actually broadcast the transaction
        """
        script_path = "scripts/deploy_multi_chain.sol"
        
        cmd = [
            "forge", "script", f"{script_path}:{contract_name}",
            "--rpc-url", self.config.rpc_url,
        ]
        
        if broadcast:
            cmd.extend([
                "--broadcast",
                "--private-key", self.account.key.hex(),
            ])
        else:
            cmd.append("--dry-run")
        
        cmd.extend([
            "--verify",
            "--etherscan-api-key", os.getenv("ETHERSCAN_API_KEY", ""),
        ])
        
        print(f"\n📝 Deployment Command:")
        print(f"  {' '.join(cmd)}")
        
        # In production, you would execute this command
        # For now, we just show what would be executed
        return None

    def save_deployment_config(self, filepath: Optional[str] = None):
        """Save network configuration to file."""
        if filepath is None:
            network_name = self.config.name.lower().replace(" ", "_")
            filepath = f"config/{network_name}_deployment.json"
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        config_dict = {
            "network": self.config.name,
            "chain_id": self.config.chain_id,
            "rpc_url": self.config.rpc_url,
            "explorer_url": self.config.explorer_url,
            "contracts": {
                "futarchy_router": self.config.futarchy_router,
                "balancer_router": self.config.balancer_router,
                "swapr_router": self.config.swapr_router,
                "multicall3": self.config.multicall3,
            },
            "timestamp": datetime.now().isoformat(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_dict, f, indent=2)
        
        print(f"✓ Configuration saved to {filepath}")
        return filepath


def main():
    """Main deployment CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Deploy Futarchy arbitrage contracts to Base and Polygon"
    )
    
    parser.add_argument(
        "--network",
        type=str,
        choices=[net.value for net in Network],
        required=True,
        help="Target network (base, polygon, base_sepolia, polygon_mumbai)",
    )
    
    parser.add_argument(
        "--deploy",
        action="store_true",
        help="Execute deployment (requires --broadcast)",
    )
    
    parser.add_argument(
        "--broadcast",
        action="store_true",
        help="Actually broadcast transactions (else dry-run)",
    )
    
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify contracts on block explorer",
    )
    
    parser.add_argument(
        "--check-balance",
        action="store_true",
        help="Check account balance and gas estimates",
    )
    
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Save network configuration to file",
    )
    
    parser.add_argument(
        "--private-key",
        type=str,
        help="Private key (or use PRIVATE_KEY env var)",
    )
    
    args = parser.parse_args()
    
    # Get network enum
    network_enum = Network(args.network)
    
    # Create deployment manager
    try:
        manager = DeploymentManager(network_enum, args.private_key)
    except (ConnectionError, ValueError) as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Validate network
    try:
        manager.validate_network()
        print(f"✓ Chain ID verified: {manager.config.chain_id}")
    except ValueError as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Check balance if requested
    if args.check_balance:
        if not manager.check_balance():
            print("⚠️  Insufficient balance for deployment")
            sys.exit(1)
        manager.estimate_deployment_gas()
    
    # Save config if requested
    if args.save_config:
        manager.save_deployment_config()
    
    # Execute deployment
    if args.deploy:
        if not args.broadcast:
            print("⚠️  --deploy requires --broadcast flag")
            print("   Use --broadcast to actually broadcast transactions")
        
        contract_name = f"{network_enum.value.title().replace('_', '')}Deployment"
        print(f"\n🚀 Starting deployment to {manager.config.name}...")
        manager.deploy_via_forge(contract_name, broadcast=args.broadcast)
    else:
        print("\n📋 To deploy, use: --deploy --broadcast")


if __name__ == "__main__":
    main()
