# Multi-Chain Configuration Template

Use this template to configure deployments across Base and Polygon networks.

## Base Mainnet Configuration

```json
{
  "network": "Base",
  "chain_id": 8453,
  "rpc_url": "https://mainnet.base.org",
  "explorer_url": "https://basescan.org",
  "contracts": {
    "futarchy_router": "0x...",
    "balancer_router": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    "swapr_router": "0x6131B5fAe19EA4f9D964eAc0408E3616eDA97B7f",
    "multicall3": "0xcA11bde05977b3631167028862bE2a173976CA11"
  },
  "tokens": {
    "sdai": "0x...",
    "dai": "0x..."
  },
  "settings": {
    "min_profit_threshold": "0.001",
    "slippage_tolerance": 0.02,
    "gas_price_threshold": "50",
    "max_daily_loss": "100"
  }
}
```

## Polygon Mainnet Configuration

```json
{
  "network": "Polygon",
  "chain_id": 137,
  "rpc_url": "https://polygon-rpc.com",
  "explorer_url": "https://polygonscan.com",
  "contracts": {
    "futarchy_router": "0x...",
    "balancer_router": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    "swapr_router": "0x6131B5fAe19EA4f9D964eAc0408E3616eDA97B7f",
    "multicall3": "0xcA11bde05977b3631167028862bE2a173976CA11"
  },
  "tokens": {
    "sdai": "0x...",
    "dai": "0x..."
  },
  "settings": {
    "min_profit_threshold": "0.0005",
    "slippage_tolerance": 0.02,
    "gas_price_threshold": "100",
    "max_daily_loss": "100"
  }
}
```

## Base Sepolia Testnet Configuration

```json
{
  "network": "Base Sepolia",
  "chain_id": 84532,
  "rpc_url": "https://sepolia.base.org",
  "explorer_url": "https://sepolia.basescan.org",
  "contracts": {
    "futarchy_router": "0x...",
    "balancer_router": "0x...",
    "swapr_router": "0x...",
    "multicall3": "0xcA11bde05977b3631167028862bE2a173976CA11"
  },
  "tokens": {
    "sdai": "0x...",
    "dai": "0x..."
  },
  "settings": {
    "min_profit_threshold": "0.0001",
    "slippage_tolerance": 0.05,
    "gas_price_threshold": "10",
    "max_daily_loss": "10"
  }
}
```

## Polygon Mumbai Testnet Configuration

```json
{
  "network": "Polygon Mumbai",
  "chain_id": 80001,
  "rpc_url": "https://rpc-mumbai.maticvigil.com",
  "explorer_url": "https://mumbai.polygonscan.com",
  "contracts": {
    "futarchy_router": "0x...",
    "balancer_router": "0x...",
    "swapr_router": "0x...",
    "multicall3": "0xcA11bde05977b3631167028862bE2a173976CA11"
  },
  "tokens": {
    "sdai": "0x...",
    "dai": "0x..."
  },
  "settings": {
    "min_profit_threshold": "0.0001",
    "slippage_tolerance": 0.05,
    "gas_price_threshold": "10",
    "max_daily_loss": "10"
  }
}
```

## Environment Variables

Create `.env` files for each network:

### .env.base
```bash
# Base Mainnet
CHAIN_ID=8453
RPC_URL=https://mainnet.base.org
EXPLORER_URL=https://basescan.org
ETHERSCAN_API_KEY=...
PRIVATE_KEY=0x...
FUTARCHY_ROUTER_ADDRESS=0x...
BALANCER_ROUTER_ADDRESS=0xBA12222222228d8Ba445958a75a0704d566BF2C8
SWAPR_ROUTER_ADDRESS=0x6131B5fAe19EA4f9D964eAc0408E3616eDA97B7f
EXECUTOR_ADDRESS=0x...
SAFETY_MODULE_ADDRESS=0x...
```

### .env.polygon
```bash
# Polygon Mainnet
CHAIN_ID=137
RPC_URL=https://polygon-rpc.com
EXPLORER_URL=https://polygonscan.com
POLYGONSCAN_API_KEY=...
PRIVATE_KEY=0x...
FUTARCHY_ROUTER_ADDRESS=0x...
BALANCER_ROUTER_ADDRESS=0xBA12222222228d8Ba445958a75a0704d566BF2C8
SWAPR_ROUTER_ADDRESS=0x6131B5fAe19EA4f9D964eAc0408E3616eDA97B7f
EXECUTOR_ADDRESS=0x...
SAFETY_MODULE_ADDRESS=0x...
```

### .env.base_sepolia
```bash
# Base Sepolia Testnet
CHAIN_ID=84532
RPC_URL=https://sepolia.base.org
EXPLORER_URL=https://sepolia.basescan.org
ETHERSCAN_API_KEY=...
PRIVATE_KEY=0x...
FUTARCHY_ROUTER_ADDRESS=0x...
BALANCER_ROUTER_ADDRESS=0x...
SWAPR_ROUTER_ADDRESS=0x...
EXECUTOR_ADDRESS=0x...
SAFETY_MODULE_ADDRESS=0x...
```

### .env.polygon_mumbai
```bash
# Polygon Mumbai Testnet
CHAIN_ID=80001
RPC_URL=https://rpc-mumbai.maticvigil.com
EXPLORER_URL=https://mumbai.polygonscan.com
POLYGONSCAN_API_KEY=...
PRIVATE_KEY=0x...
FUTARCHY_ROUTER_ADDRESS=0x...
BALANCER_ROUTER_ADDRESS=0x...
SWAPR_ROUTER_ADDRESS=0x...
EXECUTOR_ADDRESS=0x...
SAFETY_MODULE_ADDRESS=0x...
```

## Deployment Workflow

1. **Update contract addresses** in configuration files
2. **Set environment variables** for target network
3. **Run pre-deployment checks**:
   ```bash
   python3 scripts/deploy_multi_chain.py \
     --network base \
     --check-balance
   ```
4. **Dry-run deployment** first:
   ```bash
   forge script scripts/deploy_multi_chain.sol:BaseDeployment \
     --rpc-url https://mainnet.base.org \
     --dry-run
   ```
5. **Broadcast to network**:
   ```bash
   forge script scripts/deploy_multi_chain.sol:BaseDeployment \
     --rpc-url https://mainnet.base.org \
     --broadcast \
     --private-key $PRIVATE_KEY
   ```
6. **Save deployment artifacts**:
   ```bash
   python3 scripts/deploy_multi_chain.py \
     --network base \
     --save-config
   ```

## Key Differences Between Networks

### Gas Costs
- **Base**: ~30-50 gwei (lower due to OP Stack rollup)
- **Polygon**: ~50-100 gwei (PoS sidechain)

### Transaction Speed
- **Base**: 2-5 seconds finality
- **Polygon**: 2-3 seconds finality

### Liquidity
- **Base**: Growing DeFi ecosystem
- **Polygon**: Mature DeFi with high TVL

### Recommendation
For initial deployment:
1. Start with **Base Sepolia** testnet
2. Verify contract functionality
3. Deploy to **Polygon Mumbai** testnet
4. Then deploy to **Base Mainnet** (lower gas costs)
5. Finally deploy to **Polygon Mainnet** (high liquidity)
