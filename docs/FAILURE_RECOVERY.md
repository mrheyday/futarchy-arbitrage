# Failure Doctrine & Recovery Plan

# Institutional Solver Intelligence System

## Overview

This document outlines the failure handling philosophy, recovery procedures, and disaster recovery plan for the Institutional Solver Intelligence System.

## Failure Doctrine

### Core Principles

1. **Fail Fast, Fail Safe**
   - Atomic transactions ensure all-or-nothing execution
   - Reverts prevent partial state changes
   - No funds at risk during failures

2. **Deterministic Recovery**
   - All state changes logged via events
   - CLZ calculations are deterministic and reproducible
   - Shadow simulations enable forensic analysis

3. **Defense in Depth**
   - Multiple validation layers
   - Reputation gating prevents bad actors
   - MEV protection via entropy checks
   - Compliance checks for regulatory safety

4. **Graceful Degradation**
   - Flashloan multi-provider failover
   - Intent resolution continues if one component fails
   - Owner can manually intervene via failoverRoute

## Failure Modes & Responses

### Intent Resolution Failures

#### Failure Mode: Intent Execution Reverts

**Detection:**

```solidity
error ExecutionFailed();
```

**Causes:**

- Invalid execution data
- Insufficient gas
- Solver logic error
- External dependency failure

**Automatic Response:**

1. Transaction reverts atomically
2. No state changes persisted
3. Gas refunded to user (minus execution cost)

**Recovery Procedure:**

```python
# 1. Analyze failure
tx_hash = "0x..."
receipt = w3.eth.get_transaction_receipt(tx_hash)
trace = w3.provider.make_request("debug_traceTransaction", [tx_hash, {}])

# 2. Fix execution data
corrected_data = fix_execution_data(original_data)

# 3. Retry with correct data
client.resolve_intent(intent_id, solver, corrected_data)
```

**Reputation Impact:**

- Solver reputation **NOT** penalized (automatic failure)
- Manual review may reveal solver fault
- Owner can slash reputation if needed

#### Failure Mode: Reputation Gate Failure

**Detection:**

```solidity
error ReputationSlash();
```

**Causes:**

- Solver reputation < 100 (minimum threshold)
- Previous slashing events
- Insufficient positive reputation accumulation

**Automatic Response:**

1. Transaction reverts immediately (pre-execution check)
2. No gas wasted on execution attempt

**Recovery Procedure:**

```python
# Option 1: Use different solver
client.resolve_intent(intent_id, alternate_solver, exec_data)

# Option 2: Restore solver reputation (owner only)
client.update_reputation(solver, 200)  # Boost to minimum + buffer
client.resolve_intent(intent_id, solver, exec_data)
```

**Prevention:**

- Monitor solver reputations regularly
- Maintain whitelist of high-reputation solvers
- Set alerts for reputation < 150

### Auction Failures

#### Failure Mode: No Bids Revealed

**Detection:**

```solidity
error InvalidBid();  // Thrown in settleAuction if tieCount == 0
```

**Causes:**

- No solvers committed bids
- All solvers failed to reveal
- Reveal values don't match commitments

**Automatic Response:**

1. Settlement transaction reverts
2. Auction remains in closed state
3. Bids can still be revealed if commit phase issue

**Recovery Procedure:**

```python
# 1. Check auction state
auction_stats = monitor.get_auction_stats(auction_id)

# 2. If no reveals, wait for reveal period
# Solvers may still reveal within the window

# 3. If reveals failed, investigate
for solver in expected_solvers:
    # Check if bid was committed
    # Verify reveal attempt
    # Contact solver for manual reveal

# 4. Settle when bids available
client.settle_auction(auction_id, revealed_solvers)

# 5. If still fails, close and restart auction
client.contract.functions.openAuction(auction_id + 1).transact()
```

**Post-Incident:**

- Review why solvers didn't reveal
- Check for network issues during reveal period
- Consider extending reveal periods

#### Failure Mode: CLZ Overflow in Bid Calculation

**Detection:**

- This is prevented by design; CLZ always returns 0-255

**Mitigation:**

```solidity
uint256 leadingZeros;
assembly { leadingZeros := clz(bid.revealValue) }
uint256 logApprox = 255 - leadingZeros;  // Always valid
```

**Recovery:**

- Not applicable (prevented by design)

### Flashloan Failures

#### Failure Mode: All Providers Fail

**Detection:**

```solidity
error FlashloanFailed();
```

**Causes:**

- All providers out of liquidity
- Amount too small (CLZ check fails)
- Network connectivity issues
- Provider contracts paused

**Automatic Response:**

1. Transaction reverts after trying all providers
2. Loop through: Aave → Balancer → Morpho
3. Each failure logged in transaction trace

**Recovery Procedure:**

```python
# 1. Check provider status
aave_liquidity = check_aave_liquidity(token)
balancer_liquidity = check_balancer_liquidity(token)

# 2. Verify amount meets CLZ requirement
min_amount = 2 ** 10  # 1024
if amount < min_amount:
    # Increase amount
    amount = min_amount

# 3. Wait for provider recovery
time.sleep(300)  # 5 minutes

# 4. Retry
client.execute_flashloan(token, amount, callback_data)

# 5. If persistent, add new provider
new_provider = "0x..."
client.contract.functions.addFlashloanProvider(new_provider).transact()
```

**Prevention:**

- Monitor provider liquidity daily
- Maintain diverse provider list
- Set amount minimums well above 2^10

### MEV Protection Failures

#### Failure Mode: Insufficient Entropy

**Detection:**

```solidity
error MEVDetected();
```

**Causes:**

- Predictable transaction patterns
- Block timestamp manipulation
- Hash collision (extremely rare)

**Automatic Response:**

1. Transaction reverts before execution
2. Protects against MEV extraction

**Recovery Procedure:**

```python
# 1. Wait for next block
time.sleep(5)

# 2. Retry transaction
# New block.timestamp will change entropy
client.resolve_intent(intent_id, solver, exec_data)

# 3. If persistent, investigate
# This should be extremely rare
# May indicate attack attempt
```

**Escalation:**

- If repeated failures: security incident
- Review transaction patterns
- Consider adjusting entropy threshold

### Compliance Failures

#### Failure Mode: Compliance Violation

**Detection:**

```solidity
error ComplianceViolation();
```

**Causes:**

- Missing KYC flag
- Missing Accredited flag
- Missing Sanctions Clear flag
- Flags not set for new solver

**Automatic Response:**

1. Transaction reverts
2. No unauthorized solver can execute

**Recovery Procedure:**

```python
# 1. Verify solver should be authorized
verify_solver_compliance(solver)

# 2. Set appropriate flags
flags = 0x7  # KYC | Accredited | Sanctions Clear
client.contract.functions.setComplianceFlags(solver, flags).transact()

# 3. Retry operation
client.resolve_intent(intent_id, solver, exec_data)
```

**Audit Trail:**

- Log all compliance flag changes
- Maintain off-chain verification records
- Review quarterly

## Shadow Simulation & Forensics

### Shadow Simulation Process

**Purpose:** Reproduce failed transactions in controlled environment

**Setup:**

```python
from eth_tester import EthereumTester
from web3 import Web3, EthereumTesterProvider

# 1. Create test environment
tester = EthereumTester()
w3_test = Web3(EthereumTesterProvider(tester))

# 2. Deploy contract in test env
test_contract = deploy_to_test_env(w3_test)

# 3. Replay state up to failure point
replay_events(test_contract, from_block=0, to_block=failure_block)

# 4. Execute failed transaction
result = simulate_transaction(test_contract, failed_tx_data)

# 5. Analyze with full trace
trace = get_full_trace(result)
analyze_failure(trace)
```

**Use Cases:**

- Understanding complex failure modes
- Testing fixes before deployment
- Training new operators
- Formal verification

### Forensic Analysis

**Event Log Analysis:**

```python
# Extract all events for failed transaction
events = []
for log in tx_receipt['logs']:
    event = contract.events[event_name]().processLog(log)
    events.append(event)

# Analyze event sequence
for event in events:
    print(f"{event['event']}: {event['args']}")

# Look for patterns:
# - Last successful state change
# - First failed validation
# - Reputation changes
# - External calls
```

**CLZ Value Verification:**

```python
# Verify CLZ calculations match on-chain
def verify_clz(value):
    # Python calculation
    py_clz = 255 - (value.bit_length() if value > 0 else 256)

    # Query contract (if possible)
    # Compare results
    return py_clz

# For each metric in failed transaction
for metric, value in failed_metrics.items():
    expected_clz = verify_clz(value)
    print(f"{metric}: value={value}, CLZ={expected_clz}")
```

## Disaster Recovery

### Scenario: Contract Compromise

**Warning Signs:**

- Unauthorized owner changes
- Unexpected reputation changes
- Mass compliance flag removal
- Suspicious auction settlements

**Immediate Actions:**

1. **Pause Operations** (if pause function exists)

   ```python
   # NOT IMPLEMENTED - Would need to add
   # contract.functions.pause().transact()
   ```

2. **Analyze Breach**
   - Review recent transactions
   - Identify attack vector
   - Assess damage

3. **Containment**
   - Rotate compromised keys
   - Update access controls
   - Block malicious solvers

**Recovery Steps:**

1. Deploy new contract version with fixes
2. Migrate state:

   ```python
   # Export state from old contract
   old_state = export_state(old_contract)

   # Import to new contract
   import_state(new_contract, old_state)
   ```

3. Update all client integrations
4. Communicate with users
5. Post-incident review

### Scenario: Data Loss

**Backup Strategy:**

- Daily SQLite database backups
- Event logs in blockchain (permanent)
- Deployment info in git repository

**Recovery:**

```bash
# 1. Restore from backup
cp backups/state_YYYYMMDD.db institutional_solver_state.db
cp backups/monitoring_YYYYMMDD.db monitoring.db

# 2. Replay events from last backup to current
python scripts/replay_events.py \
  --from-block $BACKUP_BLOCK \
  --to-block latest

# 3. Verify integrity
python scripts/verify_state.py
```

### Scenario: Network Partition

**Detection:**

- RPC connection failures
- Block production stops
- Conflicting chain tips

**Response:**

```python
# Switch to backup RPC
backup_rpcs = [
    "https://rpc.gnosischain.com",
    "https://rpc.gnosis.gateway.fm",
    "https://gnosis.publicnode.com"
]

for rpc in backup_rpcs:
    w3 = Web3(Web3.HTTPProvider(rpc))
    if w3.is_connected():
        print(f"Connected to {rpc}")
        break
```

**Prevention:**

- Maintain multiple RPC providers
- Monitor network status
- Use WebSocket for real-time updates

## Recovery Testing

### Monthly Recovery Drills

**Test 1: Database Restore**

```bash
# Simulate data loss
mv institutional_solver_state.db institutional_solver_state.db.bak

# Restore from backup
cp backups/state_$(date -d "7 days ago" +%Y%m%d).db institutional_solver_state.db

# Verify
python -c "from src.helpers.institutional_solver_client import InstitutionalSolverClient; ..."
```

**Test 2: Shadow Simulation**

```python
# Pick a recent successful transaction
test_tx = "0x..."

# Replay in shadow environment
shadow_result = replay_transaction(test_tx)

# Verify same outcome
assert shadow_result == actual_result
```

**Test 3: Failover**

```python
# Disable primary flashloan provider
# Verify automatic failover to secondary
# Confirm no operational impact
```

### Quarterly Disaster Recovery

**Full DR Drill:**

1. Simulate catastrophic failure
2. Deploy new contract
3. Restore all state
4. Verify system operational
5. Document time to recovery
6. Update procedures

## Monitoring & Alerting

### Critical Alerts

```python
# Set up alerts for:
alerts = {
    'transaction_failure_rate': {
        'threshold': 0.05,  # 5%
        'action': 'investigate_immediately'
    },
    'reputation_slash_spike': {
        'threshold': 5,  # 5 slashes in 1 hour
        'action': 'security_review'
    },
    'flashloan_failure_rate': {
        'threshold': 0.2,  # 20%
        'action': 'check_providers'
    },
    'health_check_failure': {
        'threshold': 1,  # Any failure
        'action': 'operator_notification'
    }
}
```

### Recovery Metrics

Track these to improve recovery processes:

- **Mean Time To Detect (MTTD):** Average time to detect failure
- **Mean Time To Respond (MTTR):** Average time to start recovery
- **Mean Time To Recover (MTTR):** Average time to full recovery
- **Recovery Success Rate:** % of recoveries completed successfully

**Targets:**

- MTTD: < 5 minutes
- MTTR (respond): < 15 minutes
- MTTR (recover): < 1 hour
- Success Rate: > 95%

## Conclusion

The Institutional Solver Intelligence System is designed with multiple layers of failure protection. By following this recovery plan and conducting regular drills, operators can ensure maximum uptime and rapid recovery from any incident.

**Remember:**

- Failures are opportunities to improve
- All failures should be logged and analyzed
- Recovery procedures should be tested regularly
- Documentation should be updated after each incident
