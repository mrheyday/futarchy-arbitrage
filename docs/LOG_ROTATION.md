# Log Rotation Configuration

This document describes the log rotation setup for the Futarchy Arbitrage Bot.

## Overview

The bot generates several types of logs that require different rotation strategies:

1. **Application logs** (`*.log`) - Daily rotation, 30 days retention
2. **Trade logs** (`trades_*.log`) - Monthly rotation, 12 months retention, uncompressed
3. **Error logs** (`*_errors.log`) - Daily rotation, 90 days retention, size-based triggers

## Rotation Strategies

### Python Built-in Rotation (Default)

The bot uses Python's `logging.handlers` for automatic log rotation:

- **TimedRotatingFileHandler** - Rotates at midnight, keeps 30 backups
- **RotatingFileHandler** - Rotates when file reaches 10MB, keeps 5 backups

Configuration: `src/config/logging_config.py`

### System-level Rotation (Production)

For production deployments, use `logrotate` (Linux) for centralized log management.

## Setup Instructions

### Linux (logrotate)

1. **Install logrotate configuration**:
   ```bash
   sudo chmod +x scripts/setup_logrotate.sh
   sudo ./scripts/setup_logrotate.sh
   ```

2. **Verify installation**:
   ```bash
   sudo logrotate -d /etc/logrotate.d/futarchy-arbitrage
   ```

3. **Manual rotation** (if needed):
   ```bash
   sudo logrotate -f /etc/logrotate.d/futarchy-arbitrage
   ```

### macOS (newsyslog)

macOS uses `newsyslog` instead of logrotate:

1. **Create newsyslog config**:
   ```bash
   sudo vi /etc/newsyslog.d/futarchy-arbitrage.conf
   ```

2. **Add configuration** (adjust paths):
   ```
   # logfilename          [owner:group]    mode count size when  flags [/pid_file] [sig_num]
   /path/to/logs/*.log    user:staff      644  30    10M   *     GJ
   /path/to/logs/trades_*.log  user:staff  644  12    *     $M1   J
   /path/to/logs/*_errors.log  user:staff  644  90    50M   *     GJ
   ```

3. **Test configuration**:
   ```bash
   sudo newsyslog -nvv
   ```

### Docker

For Docker deployments, mount the logs directory as a volume:

```yaml
services:
  futarchy-bot:
    volumes:
      - ./logs:/app/logs
      - /etc/logrotate.d/futarchy-arbitrage:/etc/logrotate.d/futarchy-arbitrage:ro
```

Run logrotate as a sidecar container or host-level cron job.

## Rotation Policies

### Application Logs

- **Frequency**: Daily at midnight
- **Retention**: 30 days
- **Compression**: Gzip (delayed by 1 day)
- **Max Size**: No limit
- **Files**: `eip7702_bot.log`, `simple_bot.log`, etc.

### Trade Logs

- **Frequency**: Monthly (1st of month)
- **Retention**: 12 months
- **Compression**: None (for audit compliance)
- **Max Size**: No limit
- **Files**: `trades_*.log`

**Rationale**: Trade logs are audit trails and should be easily readable. Keep longer for accounting/tax purposes.

### Error Logs

- **Frequency**: Daily OR when file reaches 50MB
- **Retention**: 90 days
- **Compression**: Gzip (delayed by 1 day)
- **Max Size**: 50MB per file
- **Files**: `*_errors.log`

**Rationale**: Error logs can grow quickly during incidents. Size-based rotation prevents disk exhaustion.

## Monitoring Rotation

### Check Rotation Status

```bash
# List rotated logs
ls -lh logs/*.log* | head -20

# Check last rotation time
stat -c '%y %n' logs/*.log

# View rotation history
grep futarchy-arbitrage /var/log/logrotate
```

### Disk Space Monitoring

```bash
# Check logs directory size
du -sh logs/

# Check individual log sizes
du -h logs/* | sort -h | tail -10

# Alert if logs exceed 1GB
if [ $(du -s logs/ | cut -f1) -gt 1048576 ]; then
    echo "Warning: Logs directory exceeds 1GB"
fi
```

## Troubleshooting

### Logrotate Not Running

**Symptom**: Logs not rotating despite configuration

**Solutions**:
1. Check if logrotate service is running:
   ```bash
   systemctl status cron  # or crond on RHEL
   ```

2. Check logrotate cron job:
   ```bash
   ls -l /etc/cron.daily/logrotate
   ```

3. Run manually and check for errors:
   ```bash
   sudo logrotate -v /etc/logrotate.d/futarchy-arbitrage
   ```

### Permission Errors

**Symptom**: `error: skipping "/path/to/log" because parent directory has insecure permissions`

**Solution**:
```bash
# Fix logs directory permissions
sudo chmod 755 logs/
sudo chown -R $USER:$USER logs/

# Update logrotate config to use correct user
sudo vi /etc/logrotate.d/futarchy-arbitrage
# Change "create 0644 www-data www-data" to your user
```

### Rotation Not Compressing

**Symptom**: Rotated logs not compressed

**Solutions**:
1. Check if `compress` option is enabled in config
2. Verify `delaycompress` is set (compression happens on next rotation)
3. Manually compress old logs:
   ```bash
   find logs/ -name "*.log-*" -type f ! -name "*.gz" -mtime +1 -exec gzip {} \;
   ```

### Process Not Reopening Log Files

**Symptom**: Bot still writes to rotated log files

**Solution**: Bot must handle `SIGHUP` signal to reopen log files:

```python
import signal
import logging

def handle_sighup(signum, frame):
    """Reopen log files on SIGHUP"""
    # Close all handlers
    for handler in logging.root.handlers:
        handler.close()
    # Reconfigure logging
    logging.basicConfig(force=True)

signal.signal(signal.SIGHUP, handle_sighup)
```

## Best Practices

1. **Separate trade logs**: Keep trade logs separate and uncompressed for auditing
2. **Monitor disk space**: Set up alerts for logs directory exceeding thresholds
3. **Archive old logs**: Move logs older than 90 days to cold storage (S3, archive)
4. **Test rotation**: Regularly test rotation with `logrotate -f`
5. **Backup before rotation**: Consider copying logs to backup location before rotation
6. **Use structured logging**: JSON format makes log aggregation easier (ELK, Splunk)

## Log Aggregation

For production deployments, consider centralized log aggregation:

### ELK Stack (Elasticsearch, Logstash, Kibana)

```bash
# Install Filebeat
sudo apt-get install filebeat

# Configure Filebeat to ship logs
sudo vi /etc/filebeat/filebeat.yml
```

```yaml
filebeat.inputs:
- type: log
  paths:
    - /path/to/logs/*.log
  fields:
    app: futarchy-arbitrage
    env: production
  json.keys_under_root: true

output.elasticsearch:
  hosts: ["localhost:9200"]
```

### CloudWatch (AWS)

```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure log streaming
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

## Related Documentation

- [Structured Logging Guide](../src/config/logging_config.py)
- [Monitoring & Alerts](SLACK_ALERTS_QUICKSTART.md)
- [Production Deployment](PRODUCTION_DEPLOYMENT.md)
