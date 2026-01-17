# Next Steps - Deployment Checklist

## Status: ✅ All 4 Tasks Complete - Ready for Testnet Deployment

---

## Immediate Actions (5-10 minutes)

### 1. Get Chiado Testnet Tokens
- [ ] Visit https://gnosisfaucet.com
- [ ] Request 0.1 xDAI for deployer address
- [ ] Verify balance: `cast balance $DEPLOYER_ADDRESS --rpc-url https://rpc.chiadochain.net`

### 2. Deploy SafetyModule to Chiado
```bash
source futarchy_env/bin/activate
python scripts/deploy_safety_module_chiado.py
```

**Expected Output:**
```
✅ SafetyModule deployed successfully!
Contract address: 0x...
Explorer: https://gnosis-chiado.blockscout.com/address/0x...
```

- [ ] Copy contract address
- [ ] Add to .env: `SAFETY_MODULE_ADDRESS=0x...`
- [ ] Save deployment JSON from `deployments/safety_module_chiado_*.json`

### 3. Configure Slack Webhook
- [ ] Create Slack app: https://api.slack.com/messaging/webhooks
- [ ] Get webhook URL
- [ ] Export: `export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."`
- [ ] Test: `python -m src.monitoring.slack_alerts --test`

### 4. Start Monitoring
```bash
export SAFETY_MODULE_ADDRESS="0x..."  # From deployment
python -m src.monitoring.slack_alerts --start-block latest
```

- [ ] Verify monitoring started
- [ ] Check Slack channel for test message
- [ ] Monitor for 1 hour to verify stability

---

## This Week (Integration & Testing)

### Phase 1: Integrate SafetyModule with Executors
- [ ] Update FutarchyArbExecutorV5 to call SafetyModule.checkTradeAllowed()
- [ ] Add SafetyModule address to executor constructor
- [ ] Deploy updated executor to Chiado
- [ ] Test with small trades (0.001-0.01 ETH)

**Files to modify:**
- `contracts/FutarchyArbExecutorV5.sol` - Add SafetyModule integration
- `scripts/deploy_executor_v5.py` - Pass SafetyModule address

### Phase 2: Test Circuit Breakers on Testnet
- [ ] Test slippage circuit breaker (force >5% slippage)
- [ ] Test gas circuit breaker (during high gas periods)
- [ ] Test emergency pause/unpause
- [ ] Verify Slack alerts for each event type
- [ ] Document circuit breaker behavior

### Phase 3: Complete Logging Migration
- [ ] Run migration script on remaining files:
  ```bash
  python scripts/migrate_to_logging.py \
      --files src/arbitrage_commands/*.py \
      --files src/helpers/*.py \
      --files src/executor/*.py
  ```
- [ ] Verify all bots use structured logging
- [ ] Test log rotation (generate logs > 10MB)
- [ ] Set up log monitoring/alerting

---

## Next Week (Production Preparation)

### Monitoring Infrastructure
- [ ] Set up systemd service for Slack monitoring
- [ ] Configure log aggregation (optional: ELK stack)
- [ ] Add Prometheus metrics export
- [ ] Create Grafana dashboard
- [ ] Set up PagerDuty integration (for critical alerts)

### Bot Dashboard
- [ ] Run bot dashboard: `python -m src.monitoring.bot_dashboard --interval 60`
- [ ] Monitor multiple bots simultaneously
- [ ] Test alert generation (low balance, inactive bot)
- [ ] Document dashboard usage

### Price Aggregator
- [ ] Implement real price fetching (replace mocks)
- [ ] Test with live Balancer/Swapr data
- [ ] Verify anomaly detection (spread > 5%)
- [ ] Add liquidity sufficiency checks

---

## Two Weeks (Security & Audit)

### Security Audit
- [ ] Review SafetyModule contract code
- [ ] Test all edge cases (overflow, underflow, reentrancy)
- [ ] Consider external audit (optional for testnet)
- [ ] Document all findings and fixes

### Integration Tests
- [ ] Add SellCondFlow integration tests
- [ ] Test failure scenarios (insufficient funds, high slippage)
- [ ] Test with real RPC (not mocks)
- [ ] Achieve >90% coverage

### Multi-Bot Coordination
- [ ] Design shared safety limits across bots
- [ ] Implement bot registry contract
- [ ] Test coordination logic
- [ ] Document multi-bot setup

---

## One Month (Mainnet Preparation)

### SafetyModule Mainnet Deployment
- [ ] Complete security audit
- [ ] Deploy SafetyModule to Gnosis mainnet
- [ ] Set conservative limits (2% slippage, 50 gwei gas, 5 ETH loss)
- [ ] Verify deployment
- [ ] Configure monitoring

### Gradual Capital Deployment
**Week 1:** 0.1-1 ETH
- [ ] Start with minimal capital
- [ ] Monitor for 24 hours
- [ ] Review all trades and circuit breaker events
- [ ] Adjust parameters if needed

**Week 2:** 1-5 ETH
- [ ] Increase capital gradually
- [ ] Monitor profitability
- [ ] Track circuit breaker trip frequency
- [ ] Optimize bot parameters

**Week 3-4:** 5-10+ ETH
- [ ] Scale to target capital
- [ ] Enable multiple bots
- [ ] Monitor 24/7
- [ ] Document performance metrics

---

## Production Checklist (Before Mainnet)

### Code Quality
- [x] 100% test pass rate (104/104 tests)
- [x] Integration tests operational
- [x] Structured logging implemented
- [ ] Coverage >90%
- [ ] No critical Slither findings

### Infrastructure
- [x] SafetyModule contract complete
- [x] Chiado deployment script ready
- [x] Slack alerting implemented
- [ ] systemd service configured
- [ ] Multi-region monitoring

### Safety Measures
- [x] Circuit breakers implemented
- [x] Emergency pause mechanism
- [ ] Mainnet safety limits configured (conservative)
- [ ] Manual override procedures documented
- [ ] Recovery procedures tested

### Monitoring & Alerts
- [x] Slack webhook integration
- [x] Real-time event monitoring
- [ ] PagerDuty integration (optional)
- [ ] Grafana dashboards
- [ ] 24/7 on-call rotation

### Documentation
- [x] Deployment guides written
- [x] Alert configuration documented
- [x] Task completion summary
- [ ] Runbooks for common issues
- [ ] Emergency procedures

---

## Success Metrics

### Testnet (Chiado)
- [ ] 24-hour uptime without crashes
- [ ] >90% of trades profitable
- [ ] <5% circuit breaker trip rate
- [ ] All alerts received within 30 seconds

### Mainnet (After 1 Month)
- [ ] 99.9% uptime
- [ ] >80% of trades profitable
- [ ] <1% circuit breaker trip rate
- [ ] Zero emergency pauses
- [ ] ROI >5% monthly (after gas costs)

---

## Resources

### Documentation
- [README.md](../README.md) - Project overview and setup
- [PHASE1_SUMMARY.md](PHASE1_SUMMARY.md) - Implementation summary
- [TASK_COMPLETION_SUMMARY.md](TASK_COMPLETION_SUMMARY.md) - Detailed task completion
- [SLACK_ALERTS_QUICKSTART.md](SLACK_ALERTS_QUICKSTART.md) - Alerting setup
- [PRODUCTION_DEPLOYMENT.md](PRODUCTION_DEPLOYMENT.md) - Full deployment guide

### Scripts
- `scripts/deploy_safety_module_chiado.py` - Deploy SafetyModule
- `scripts/migrate_to_logging.py` - Migrate to structured logging
- `src/monitoring/slack_alerts.py` - Real-time Slack monitoring
- `src/monitoring/bot_dashboard.py` - Bot status dashboard

### Contracts
- `contracts/SafetyModule.sol` - Circuit breakers and safety checks
- `contracts/FutarchyArbExecutorV5.sol` - Main arbitrage executor
- `contracts/PredictionArbExecutorV1.sol` - Prediction market arbitrage

### Tests
- `test/SafetyModule.t.sol` - 13 tests for circuit breakers
- `test/integration/BuyCondFlow.t.sol` - 4 integration tests
- `test/FutarchyArbExecutorV5.t.sol` - 26 executor tests

---

## Support

**Questions?**
- Review documentation in `docs/`
- Check logs in `logs/`
- Test with: `--dry-run` and `--test` flags
- Start small: 0.001-0.01 ETH first

**Issues?**
- Check Slack alerts are configured
- Verify RPC connection
- Review circuit breaker parameters
- Check contract deployment status

---

**Status:** Ready to deploy! 🚀

Execute immediate actions above, then proceed with integration and testing phases.
