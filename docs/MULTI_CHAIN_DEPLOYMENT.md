# Multi-Chain Deployment Guide

Deploy Futarchy arbitrage contracts to Base and Polygon networks.

## Supported Networks

| Network | Chain ID | RPC | Explorer |
|---------|----------|-----|----------|
| **Base** | 8453 | https://mainnet.base.org | https://basescan.org |
| **Polygon** | 137 | https://polygon-rpc.com | https://polygonscan.com |
| **Base Sepolia** (testnet) | 84532 | https://sepolia.base.org | https://sepolia.basescan.org |
| **Polygon Mumbai** (testnet) | 80001 | https://rpc-mumbai.maticvigil.com | https://mumbai.polygonscan.com |

## Prerequisites

1. **Foundry installed**: `curl -L https://foundry.paradigm.xyz | bash`
2. **Private key**: Set `PRIVATE_KEY` environment variable
3. **RPC URLs**: Configured in `deploy_multi_chain.py` (or override with env vars)
4. **Etherscan API keys**: For contract verification
5. **Sufficient funds**: ETH for gas fees on target network

## Environment Setup

```bash
# Activate Python environment
source futarchy_env/bin/activate

# Set required environment variables
export PRIVATE_KEY="0x..."
export BASE_RPC_URL="https://mainnet.base.org"
export POLYGON_RPC_URL="https://polygon-rpc.com"
export ETHERSCAN_API_KEY="..."  # For Basescan
export POLYGONSCAN_API_KEY="..." # For Polygonscan
```

## Deployment Methods

### Method 1: Using Forge Script (Recommended)

#### Base Mainnet
```bash
# Dry-run (no transaction broadcast)
forge script scripts/deploy_multi_chain.sol:BaseDeployment \
  --rpc-url https://mainnet.base.org \
  --dry-run

# Broadcast deployment
forge script scripts/deploy_multi_chain.sol:BaseDeployment \
  --rpc-url https://mainnet.base.org \
  --broadcast \
  --private-key $PRIVATE_KEY \
  --verify \
  --etherscan-api-key $ETHERSCAN_API_KEY
```

#### Polygon Mainnet
```bash
# Dry-run (no transaction broadcast)
forge script scripts/deploy_multi_chain.sol:PolygonDeployment \
  --rpc-url https://polygon-rpc.com \
  --dry-run

# Broadcast deployment
forge script scripts/deploy_multi_chain.sol:PolygonDeployment \
  --rpc-url https://polygon-rpc.com \
  --broadcast \
  --private-key $PRIVATE_KEY \
  --verify \
  --etherscan-api-key $POLYGONSCAN_API_KEY
```

#### Testnet Deployment
```bash
# Base Sepolia
forge script scripts/deploy_multi_chain.sol:TestnetDeployment \
  --rpc-url https://sepolia.base.org \
  --broadcast \
  --private-key $PRIVATE_KEY

# Polygon Mumbai
forge script scripts/deploy_multi_chain.sol:TestnetDeployment \
  --rpc-url https://rpc-mumbai.maticvigil.com \
  --broadcast \
  --private-key $PRIVATE_KEY
```

### Method 2: Using Python Helper Script

```bash
# Check balance and gas estimates
python3 scripts/deploy_multi_chain.py \
  --network base \
  --check-balance

# Save network configuration
python3 scripts/deploy_multi_chain.py \
  --network polygon \
  --save-config

# Deploy to Base (dry-run)
python3 scripts/deploy_multi_chain.py \
  --network base \
  --deploy

# Deploy to Base (broadcast)
python3 scripts/deploy_multi_chain.py \
  --network base \
  --deploy \
  --broadcast

# Deploy to Polygon
python3 scripts/deploy_multi_chain.py \
  --network polygon \
  --deploy \
  --broadcast
```

## Contracts Deployed

### 1. SafetyModule
Circuit breaker for protecting against:
- Excessive slippage
- High gas prices
- Daily loss accumulation

### 2. PectraWrapper
EIP-7702 delegation contract for atomic bundled transactions.

### 3. FutarchyArbExecutorV5
Main arbitrage execution contract supporting:
- BUY flow: Split sDAI → swap conditionals on Swapr → merge → sell on Balancer
- SELL flow: Buy on Balancer → split → swap conditionals on Swapr → merge
- PNK/Kleros market support with multi-hop routing

## Gas Estimates

Typical deployment gas costs:
- SafetyModule: ~500,000 gas
- PectraWrapper: ~400,000 gas
- FutarchyArbExecutorV5: ~2,000,000 gas
- **Total: ~2,900,000 gas** (~$50-150 USD depending on gas price)

## Deployment Workflow

### 1. Pre-Deployment Checks
```bash
# Validate network connection
python3 scripts/deploy_multi_chain.py --network base --check-balance

# Ensure sufficient ETH balance
# Output will show: ✓ Connected, 💰 Balance, ⛽ Gas Estimates
```

### 2. Dry-Run Deployment
```bash
# Test without broadcasting
forge script scripts/deploy_multi_chain.sol:BaseDeployment \
  --rpc-url https://mainnet.base.org \
  --dry-run

# Review deployment steps without sending transactions
```

### 3. Broadcast Deployment
```bash
# Actually deploy to network
forge script scripts/deploy_multi_chain.sol:BaseDeployment \
  --rpc-url https://mainnet.base.org \
  --broadcast \
  --private-key $PRIVATE_KEY \
  --verify
```

### 4. Verify Deployment
Deployment artifacts will be saved to:
```
deployments/deployment_base_<timestamp>.json
deployments/deployment_polygon_<timestamp>.json
```

Each file contains:
```json
{
  "network": "Base",
  "timestamp": "2026-01-17T...",
  "chain_id": 8453,
  "executor_v5": "0x...",
  "safety_module": "0x...",
  "pectra_wrapper": "0x...",
  "tx_hash": "0x...",
  "block_number": 12345,
  "gas_used": 2900000
}
```

## Verification

After deployment, verify contracts on block explorer:

### Base (Basescan)
```bash
forge verify-contract <CONTRACT_ADDRESS> \
  contracts/FutarchyArbExecutorV5.sol:FutarchyArbExecutorV5 \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verifier etherscan \
  --verifier-url https://api.basescan.org/api
```

### Polygon (Polygonscan)
```bash
forge verify-contract <CONTRACT_ADDRESS> \
  contracts/FutarchyArbExecutorV5.sol:FutarchyArbExecutorV5 \
  --etherscan-api-key $POLYGONSCAN_API_KEY \
  --verifier etherscan \
  --verifier-url https://api.polygonscan.com/api
```

## Troubleshooting

### Connection Issues
```bash
# Test RPC connection
curl -X POST https://mainnet.base.org \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}'

# Expected output: {"jsonrpc":"2.0","result":"8453","id":1}
```

### Insufficient Balance
```bash
# Check balance
python3 << 'EOF'
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
balance = w3.eth.get_balance("0x...")
print(f"Balance: {w3.from_wei(balance, 'ether')} ETH")
EOF
```

### Gas Price Too High
```bash
# Check current gas price
python3 << 'EOF'
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
gas_price = w3.eth.gas_price
print(f"Gas price: {w3.from_wei(gas_price, 'gwei')} gwei")
EOF
```

### Deployment Verification Failed
```bash
# Manually verify after deployment
forge verify-contract \
  <DEPLOYED_ADDRESS> \
  contracts/FutarchyArbExecutorV5.sol:FutarchyArbExecutorV5 \
  --constructor-args $(cast abi-encode "constructor(address,address,address)" \
    <FUTARCHY_ROUTER> <BALANCER_ROUTER> <SWAPR_ROUTER>) \
  --etherscan-api-key $ETHERSCAN_API_KEY \
  --verifier etherscan
```

## Post-Deployment Configuration

After deployment, update your bot configuration:

```python
# .env.base or .env.polygon
FUTARCHY_EXECUTOR_ADDRESS="0x..."  # FutarchyArbExecutorV5 address
SAFETY_MODULE_ADDRESS="0x..."      # SafetyModule address
PECTRA_WRAPPER_ADDRESS="0x..."     # PectraWrapper address
CHAIN_ID="8453"                    # Base: 8453, Polygon: 137
```

## Network-Specific Notes

### Base
- Lower gas fees than Ethereum
- Operates as OP Stack rollup
- Same EVM compatibility as Ethereum
- Active DeFi ecosystem with Uniswap, Aave, etc.

### Polygon
- High throughput with PoS consensus
- Significantly lower gas costs
- Large existing DeFi ecosystem
- Compatible with Ethereum tools and libraries

### Testnets (Base Sepolia / Polygon Mumbai)
- Use for testing before mainnet deployment
- Free testnet ETH available from faucets
- Same contract code as mainnet
- Useful for integration testing with bot strategies

## Safety Considerations

1. **Always test on testnet first**
2. **Verify contracts after deployment**
3. **Use hardware wallet for mainnet**
4. **Double-check all contract addresses**
5. **Monitor SafetyModule circuit breakers**
6. **Start with small trade amounts**
7. **Enable Slack/Telegram alerts**

## Monitoring

After deployment, monitor contract activity:

```bash
# Watch SafetyModule events
python3 << 'EOF'
from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))

# Subscribe to circuit breaker events
# (see monitoring/slack_alerts.py)
EOF
```

## Support

For issues or questions:
1. Check `/docs/FAILURE_RECOVERY.md`
2. Review contract ABIs in `/exports/artifacts/abi/`
3. Consult Tenderly traces for failed transactions
4. Check Slack/Telegram alerts for circuit breaker triggers
