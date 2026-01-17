# Operational Readiness Guide

# Institutional Solver Intelligence System

## Pre-Deployment Checklist

### Environment Setup

- [ ] **RPC Configuration**
  - [ ] Primary RPC URL configured
  - [ ] Backup RPC URLs available
  - [ ] WebSocket endpoint (optional)
  - [ ] Rate limits verified

- [ ] **Account Setup**
  - [ ] Deployer account funded (minimum 1 xDAI for gas)
  - [ ] Private key secured in environment variable
  - [ ] Backup keys generated
  - [ ] Multi-sig owner (recommended for production)

- [ ] **Contract Dependencies**
  - [ ] ZK Verifier contract deployed (or set to 0x0 if disabled)
  - [ ] Paymaster contract deployed (or set to 0x0 if disabled)
  - [ ] Flashloan provider addresses verified:
    - [ ] Aave V3 Pool: `0xb50201558B00496A145fE76f7424749556E326D8`
    - [ ] Balancer V2 Vault: `0xBA12222222228d8Ba445958a75a0704d566BF2C8`
    - [ ] Morpho (if available on network)

### Build & Compilation

- [ ] **Foundry Installed**

  ```bash
  forge --version
  # Should show 0.8.33 or later
  ```

- [ ] **Solady Dependencies**

  ```bash
  forge install transmissions11/solady
  ```

- [ ] **Compile Contracts**

  ```bash
  forge build --profile institutional
  ```

- [ ] **Verify Compilation**
  - [ ] No compilation errors
  - [ ] Via-IR optimization enabled
  - [ ] Bytecode size < 24KB
  - [ ] Gas optimizations verified

### Testing

- [ ] **Run Unit Tests**

  ```bash
  forge test --profile institutional -vvv
  ```

- [ ] **Expected Results**
  - [ ] All auction tests pass
  - [ ] All reputation tests pass
  - [ ] All compliance tests pass
  - [ ] All access control tests pass

- [ ] **Gas Benchmarks**

  ```bash
  forge test --profile institutional --gas-report
  ```

  - [ ] Intent submission < 100k gas
  - [ ] Auction settlement < 500k gas
  - [ ] Batch execution within bounds

## Deployment Process

### Step 1: Deploy Contract

```bash
# Set environment variables
export RPC_URL="https://rpc.gnosischain.com"
export PRIVATE_KEY="your_private_key"
export ZK_VERIFIER="0x0000000000000000000000000000000000000000"
export PAYMASTER="0x0000000000000000000000000000000000000000"

# Run deployment script
python scripts/deploy_institutional_solver.py
```

**Expected Output:**

- Deployment transaction hash
- Contract address
- Gas used
- Deployment info saved to `deployments/` directory

### Step 2: Verify Contract

```bash
# Get contract address from deployment output
export CONTRACT_ADDRESS="deployed_address"

# Verify on block explorer
forge verify-contract \
  --chain-id 100 \
  --compiler-version 0.8.33 \
  --via-ir \
  --constructor-args $(cast abi-encode "constructor(address,address,address[])" $ZK_VERIFIER $PAYMASTER "[$AAVE,$BALANCER]") \
  $CONTRACT_ADDRESS \
  contracts/InstitutionalSolverSystem.sol:InstitutionalSolverSystem
```

### Step 3: Initial Configuration

```python
from src.helpers.institutional_solver_client import InstitutionalSolverClient
from web3 import Web3

# Initialize client
w3 = Web3(Web3.HTTPProvider(RPC_URL))
client = InstitutionalSolverClient(w3, CONTRACT_ADDRESS, ABI, PRIVATE_KEY)

# Set compliance flags for initial solvers
client.contract.functions.setComplianceFlags(
    solver_address,
    0x7  # KYC | Accredited | Sanctions Clear
).transact()

# Initialize first solver reputations
client.update_reputation(solver1, 200)
client.update_reputation(solver2, 200)
client.update_reputation(solver3, 200)

# Open first auction
client.contract.functions.openAuction(1).transact()
```

## Operational Procedures

### Daily Operations

#### Morning Checklist

- [ ] Check system health
  ```bash
  python -c "from src.helpers.institutional_solver_monitor import SolverMonitor; monitor.health_check()"
  ```
- [ ] Review overnight events
- [ ] Check solver reputations
- [ ] Verify flashloan provider availability

#### Ongoing Monitoring

- [ ] Monitor via telemetry script
  ```bash
  export INSTITUTIONAL_SOLVER_ADDRESS="contract_address"
  python src/helpers/institutional_solver_monitor.py
  ```
- [ ] Track gas usage trends
- [ ] Monitor auction participation
- [ ] Check MEV protection metrics

#### End of Day

- [ ] Review all settled auctions
- [ ] Calculate daily metrics
- [ ] Backup database
  ```bash
  cp institutional_solver_state.db backups/state_$(date +%Y%m%d).db
  cp monitoring.db backups/monitoring_$(date +%Y%m%d).db
  ```

### Weekly Operations

- [ ] **Security Review**
  - [ ] Review all reputation slashes
  - [ ] Check for unusual patterns
  - [ ] Verify compliance flags
  - [ ] Audit access control changes

- [ ] **Performance Analysis**
  - [ ] Compare gas usage to baseline
  - [ ] Analyze CLZ optimization impact
  - [ ] Review auction settlement times
  - [ ] Check flashloan success rates

- [ ] **System Updates**
  - [ ] Update solver whitelist if needed
  - [ ] Adjust reputation thresholds
  - [ ] Review and close inactive auctions

## Incident Response

### System Failures

#### Contract Reverts

1. **Identify Failure**

   ```bash
   # Get transaction details
   cast tx <tx_hash> --rpc-url $RPC_URL
   cast tx <tx_hash> --trace --rpc-url $RPC_URL
   ```

2. **Analyze Error**
   - Check error message
   - Review function requirements
   - Verify input parameters

3. **Resolution**
   - Fix input data
   - Update reputation if needed
   - Retry transaction

#### Flashloan Failures

1. **Check Provider Status**
   - Test Aave availability
   - Test Balancer availability
   - Check provider liquidity

2. **Failover**
   - System automatically tries next provider
   - Monitor logs for provider performance

3. **Recovery**
   - Wait for provider recovery
   - Remove failed provider if persistent issues

### Security Incidents

#### Unauthorized Access Attempt

1. **Immediate Actions**
   - Review transaction logs
   - Check owner address
   - Verify no state changes

2. **Investigation**
   - Identify attack vector
   - Check access controls
   - Review recent changes

3. **Mitigation**
   - Rotate keys if needed
   - Update access controls
   - Deploy fixes if necessary

#### MEV Attack Detection

1. **Detection**
   - Monitor entropy metrics
   - Check for pattern anomalies
   - Review auction bids

2. **Response**
   - Transaction will revert if entropy < 100
   - Investigate suspicious patterns
   - Update MEV protection if needed

3. **Prevention**
   - Adjust entropy thresholds
   - Monitor competitor activity
   - Implement additional checks

## Maintenance Procedures

### Database Maintenance

```bash
# Vacuum databases monthly
sqlite3 institutional_solver_state.db "VACUUM;"
sqlite3 monitoring.db "VACUUM;"

# Export data for analysis
sqlite3 monitoring.db ".mode csv" ".output metrics.csv" "SELECT * FROM metrics;"
```

### Contract Upgrades

**Note:** This contract is not upgradeable. For major changes:

1. Deploy new contract version
2. Migrate state if necessary
3. Update all client integrations
4. Deprecate old contract gradually

### Solver Management

```python
# Add new solver
client.contract.functions.setComplianceFlags(new_solver, 0x7).transact()
client.update_reputation(new_solver, 100)

# Remove solver (set reputation below minimum)
client.update_reputation(bad_solver, -500)
```

## Performance Metrics

### Key Performance Indicators (KPIs)

1. **Gas Efficiency**
   - Target: 5-15% reduction vs baseline
   - Measurement: `forge test --gas-report`

2. **Auction Success Rate**
   - Target: >95% successful settlements
   - Measurement: settled_auctions / total_auctions

3. **Flashloan Success Rate**
   - Target: >90% first-provider success
   - Measurement: successful_loans / total_attempts

4. **System Uptime**
   - Target: 99.9%
   - Measurement: health_check_passes / total_checks

### Monitoring Dashboards

**Recommended Metrics:**

- Intent submission rate
- Auction participation
- Solver reputation distribution
- Gas usage trends
- CLZ optimization impact

## Troubleshooting

### Common Issues

#### "AuctionClosed" Error

- **Cause:** Trying to commit bid to closed auction
- **Solution:** Check auction state before committing

#### "ReputationSlash" Error

- **Cause:** Solver reputation below minimum (100)
- **Solution:** Update solver reputation or use different solver

#### "ComplianceViolation" Error

- **Cause:** Missing required compliance flags
- **Solution:** Set compliance flags for solver

#### "FlashloanFailed" Error

- **Cause:** All providers unavailable or amount too small
- **Solution:** Check provider liquidity, verify amount > 2^10

#### Gas Estimation Failed

- **Cause:** Transaction will revert
- **Solution:** Run with `debug_traceCall` to identify issue

## Contacts & Escalation

### Support Tiers

**Tier 1: Operational Issues**

- Health check failures
- Expected error messages
- Standard configuration

**Tier 2: Technical Issues**

- Unexpected reverts
- Performance degradation
- Integration problems

**Tier 3: Security Issues**

- Suspicious activity
- Access control breaches
- Contract vulnerabilities

## Appendix

### Environment Variables Reference

```bash
# Required
RPC_URL="https://rpc.gnosischain.com"
PRIVATE_KEY="0x..."
INSTITUTIONAL_SOLVER_ADDRESS="0x..."

# Optional
ZK_VERIFIER="0x..."
PAYMASTER="0x..."
CHAIN_ID="100"
```

### Useful Commands

```bash
# Check contract owner
cast call $CONTRACT_ADDRESS "owner()" --rpc-url $RPC_URL

# Get solver reputation
cast call $CONTRACT_ADDRESS "getReputation(address)(int256)" $SOLVER --rpc-url $RPC_URL

# Check auction state (custom query needed)

# Get flashloan providers count
cast call $CONTRACT_ADDRESS "flashloanProviders(uint256)(address)" 0 --rpc-url $RPC_URL
```

### Log Retention Policy

- **Operational Logs:** 90 days
- **Audit Logs:** 365 days
- **Database Backups:** 30 days
- **Metrics:** Indefinite (with aggregation)
