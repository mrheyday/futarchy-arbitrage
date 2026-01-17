# Slack Alerting System - Quick Start

## Overview
Real-time monitoring and alerting for SafetyModule circuit breaker events via Slack webhooks.

## Setup (5 minutes)

### 1. Get Slack Webhook URL
1. Visit https://api.slack.com/messaging/webhooks
2. Click "Create New App" → "From scratch"
3. Name it "SafetyModule Monitor"
4. Choose your workspace
5. Navigate to "Incoming Webhooks" → Enable
6. Click "Add New Webhook to Workspace"
7. Choose channel (e.g., #arbitrage-alerts)
8. Copy webhook URL

### 2. Configure Environment
```bash
# Required
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXX"

# Optional: Mention specific users on critical alerts
export SLACK_MENTION_USERS="U01234567,U98765432"  # Slack user IDs

# Contract address (set after deployment)
export SAFETY_MODULE_ADDRESS="0x..."
export RPC_URL="https://rpc.chiadochain.net"  # or mainnet
```

**Find Slack User IDs:**
- Click user profile in Slack
- Click "..." → "Copy member ID"

### 3. Test Connection
```bash
source futarchy_env/bin/activate
python -m src.monitoring.slack_alerts --test
```

**Expected:** Message appears in Slack channel:
```
✅ Test Alert
SafetyModule monitoring is configured correctly
Status: All systems operational
```

### 4. Start Monitoring
```bash
# Monitor from latest block (recommended)
python -m src.monitoring.slack_alerts --start-block latest

# Run in background
nohup python -m src.monitoring.slack_alerts --start-block latest > slack_monitor.log 2>&1 &
```

## Alert Types

| Event | Severity | Mentions Users | Description |
|-------|----------|----------------|-------------|
| **SlippageCircuitTripped** | ⚠️ Warning | Yes | Trade blocked: slippage > 5% |
| **GasCircuitTripped** | ⚠️ Warning | No | Trade blocked: gas > 100 gwei |
| **DailyLossCircuitTripped** | 🚨 Error | Yes | Loss limit exceeded (10 ETH) |
| **EmergencyPaused** | 🚨 Critical | Yes | All trading paused |
| **EmergencyUnpaused** | ✅ Info | Yes | Trading resumed |

## Example Alerts

### Slippage Circuit Breaker
```
⚠️ Slippage Circuit Breaker Triggered @john @alice

Trade blocked due to excessive slippage

Trade Amount: 1.5 ETH
Expected Output: 1.45 ETH
Actual Output: 1.35 ETH  
Slippage %: 6.89%
Max Allowed: 5.0%
Block: 5432150
Tx Hash: 0xabcd1234...
Time: 2026-01-16 12:15:30 UTC
```

### Daily Loss Limit
```
🚨 Daily Loss Limit Exceeded @john @alice

Trading halted: daily loss limit reached

Today Loss: 12.5 ETH
Max Allowed: 10.0 ETH
Block: 5432300
Tx Hash: 0x5678abcd...
Time: 2026-01-16 14:00:00 UTC
```

## Command Reference

```bash
# Start monitoring from latest block
python -m src.monitoring.slack_alerts --start-block latest

# Start from specific block (e.g., after deployment)
python -m src.monitoring.slack_alerts --start-block 12345678

# Custom poll interval (default: 15 seconds)
python -m src.monitoring.slack_alerts --poll-interval 30

# Test webhook connection
python -m src.monitoring.slack_alerts --test

# Run in background (systemd recommended for production)
nohup python -m src.monitoring.slack_alerts --start-block latest > /var/log/slack_monitor.log 2>&1 &
```

## Production Deployment

### Option 1: systemd Service (Recommended)

Create `/etc/systemd/system/safety-monitor.service`:
```ini
[Unit]
Description=SafetyModule Slack Monitor
After=network.target

[Service]
Type=simple
User=arbitrage
WorkingDirectory=/home/arbitrage/futarchy-arbitrage-1
Environment="PATH=/home/arbitrage/futarchy-env/bin"
Environment="SLACK_WEBHOOK_URL=https://hooks.slack.com/services/..."
Environment="SAFETY_MODULE_ADDRESS=0x..."
Environment="RPC_URL=https://rpc.gnosischain.com"
ExecStart=/home/arbitrage/futarchy-env/bin/python -m src.monitoring.slack_alerts --start-block latest
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable safety-monitor
sudo systemctl start safety-monitor

# Check status
sudo systemctl status safety-monitor

# View logs
sudo journalctl -u safety-monitor -f
```

### Option 2: Docker Container

Create `Dockerfile.monitor`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY out/ ./out/

CMD ["python", "-m", "src.monitoring.slack_alerts", "--start-block", "latest"]
```

Run:
```bash
docker build -f Dockerfile.monitor -t safety-monitor .
docker run -d \
    -e SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL \
    -e SAFETY_MODULE_ADDRESS=$SAFETY_MODULE_ADDRESS \
    -e RPC_URL=$RPC_URL \
    --name safety-monitor \
    --restart unless-stopped \
    safety-monitor
```

## Monitoring Multiple Contracts

Create `monitor_all.sh`:
```bash
#!/bin/bash

# Monitor SafetyModule on Gnosis mainnet
SAFETY_MODULE_ADDRESS=0x1111... \
RPC_URL=https://rpc.gnosischain.com \
python -m src.monitoring.slack_alerts --start-block latest &

# Monitor SafetyModule on Chiado testnet  
SAFETY_MODULE_ADDRESS=0x2222... \
RPC_URL=https://rpc.chiadochain.net \
python -m src.monitoring.slack_alerts --start-block latest &

wait
```

## Troubleshooting

### No Alerts Received
1. **Check webhook URL:**
   ```bash
   curl -X POST -H 'Content-type: application/json' \
        --data '{"text":"Test"}' \
        $SLACK_WEBHOOK_URL
   ```

2. **Verify contract address:**
   ```bash
   cast call $SAFETY_MODULE_ADDRESS "owner()" --rpc-url $RPC_URL
   ```

3. **Check logs:**
   ```bash
   tail -f logs/slack_alerts.log
   ```

### Events Not Detected
- Ensure monitoring started from correct block
- Check RPC connection is stable
- Verify SafetyModule has events (check on block explorer)

### Rate Limiting
Slack webhooks have rate limits:
- 1 message per second per webhook
- Adjust poll interval if hitting limits: `--poll-interval 30`

## Advanced Configuration

### Custom Alert Filtering
Modify `src/monitoring/slack_alerts.py`:

```python
# Only alert on critical events
def process_event(self, event: Dict) -> None:
    event_name = event.get('event')
    
    # Skip gas circuit trips (too noisy)
    if event_name == 'GasCircuitTripped':
        logger.info(f"Skipping gas circuit alert (filtered)")
        return
    
    # Continue with other events...
```

### Multiple Webhook URLs
Route different events to different channels:

```python
class MultiChannelAlerter(SlackAlerter):
    def __init__(self, webhooks: Dict[str, str]):
        self.webhooks = webhooks
    
    def slippage_circuit_tripped(self, event_data):
        # Send to #trading-alerts
        self._send(self.webhooks['trading'], ...)
    
    def emergency_paused(self, event_data):
        # Send to #critical-alerts
        self._send(self.webhooks['critical'], ...)
```

### Integration with PagerDuty
For critical events, trigger PagerDuty:

```python
import requests

def emergency_paused(self, event_data: Dict) -> bool:
    # Send Slack alert
    super().emergency_paused(event_data)
    
    # Trigger PagerDuty
    requests.post(
        'https://events.pagerduty.com/v2/enqueue',
        json={
            'routing_key': os.getenv('PAGERDUTY_KEY'),
            'event_action': 'trigger',
            'payload': {
                'summary': 'SafetyModule Emergency Pause',
                'severity': 'critical',
                'source': 'SafetyModule Monitor'
            }
        }
    )
```

## Cost & Performance

- **RPC Calls:** ~4 calls per poll interval (15s default)
- **Network Cost:** Minimal (read-only calls)
- **Memory:** ~50 MB Python process
- **Slack API:** Free tier supports this use case

## Security Notes

- Webhook URL is sensitive (anyone with URL can post to channel)
- Store in environment variable, not in code
- Rotate webhook if compromised (regenerate in Slack app settings)
- Use HTTPS for all webhook calls (enforced by Slack)

## Next Steps

1. Set up redundant monitoring (multiple servers/regions)
2. Add alerting escalation (email → Slack → PagerDuty)
3. Create runbook for responding to circuit breaker trips
4. Build historical alert dashboard (store in database)
5. Integrate with bot dashboard for unified monitoring

## Support

Issues or questions?
- Check logs: `logs/slack_alerts.log`
- Test webhook: `python -m src.monitoring.slack_alerts --test`
- Verify contract: `cast call $SAFETY_MODULE_ADDRESS "paused()"`
