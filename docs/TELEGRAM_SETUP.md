# Telegram Alerts Setup Guide

This guide walks you through setting up Telegram alerts for the Futarchy Arbitrage Bot.

## Quick Start

1. **Create a Telegram Bot**
2. **Get Your Chat ID**
3. **Configure Environment Variables**
4. **Test the Integration**

## Step 1: Create a Telegram Bot

### Using BotFather

1. Open Telegram and search for `@BotFather`
2. Start a conversation and send `/newbot`
3. Follow the prompts:
   - **Bot name**: Choose a display name (e.g., "Futarchy Arbitrage Alerts")
   - **Bot username**: Choose a unique username ending in "bot" (e.g., "futarchy_arb_bot")
4. BotFather will respond with your **bot token**:
   ```
   Use this token to access the HTTP API:
   1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
   ```
5. **Save this token securely** - you'll need it for the environment variable

### Optional: Customize Your Bot

- Set a profile picture: `/setuserpic`
- Set description: `/setdescription`
- Set about text: `/setabouttext`

## Step 2: Get Your Chat ID

You need to know where the bot should send messages. You have two options:

### Option A: Personal Chat (Recommended for testing)

1. Search for your bot username in Telegram
2. Start a conversation by clicking "Start"
3. Send any message to your bot
4. Get your chat ID using one of these methods:

**Method 1: Using @userinfobot**
- Search for `@userinfobot` in Telegram
- Start a conversation
- Your chat ID will be displayed (it's a number like `123456789`)

**Method 2: Using the Bot API**
```bash
# Replace YOUR_BOT_TOKEN with your actual token
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates

# Look for "chat":{"id": YOUR_CHAT_ID} in the response
```

### Option B: Group Chat (For team notifications)

1. Create a new Telegram group
2. Add your bot to the group (search by username)
3. Send a message in the group
4. Get the group chat ID:
```bash
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getUpdates

# Group chat IDs are negative numbers like -123456789
```

## Step 3: Configure Environment Variables

Add these variables to your `.env` file:

```bash
# Required
TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz123456789
TELEGRAM_CHAT_ID=123456789

# Optional
TELEGRAM_SILENT=false  # Set to "true" for silent notifications
```

### Security Best Practices

- **Never commit** your bot token to version control
- Add `.env*` to `.gitignore` (already done in this project)
- Use different bots for development and production
- Revoke old tokens if compromised (via @BotFather → `/mybots` → select bot → "API Token" → "Revoke Token")

## Step 4: Test the Integration

### Test with the Standalone Script

```bash
# Activate virtual environment
source futarchy_env/bin/activate

# Set environment variables
source .env.0x<PROPOSAL_ADDRESS>  # Or your .env file

# Run test
python -m src.monitoring.telegram_alerts
```

Expected output:
```
✅ Telegram alerter initialized

📤 Sending test alerts...
✅ Test alerts sent!
```

You should receive 3 test messages in your Telegram chat:
1. Bot start notification
2. Sample trade alert
3. Trading summary

### Test with the EIP-7702 Bot

```bash
# Dry run mode with alerts
python -m src.arbitrage_commands.eip7702_bot \
    --amount 0.001 \
    --interval 30 \
    --dry-run \
    --max-iterations 1
```

You should receive:
- Bot start notification when bot launches
- Trade notification if opportunity is found (dry run won't execute)
- Bot stop notification when you press Ctrl+C

## Alert Types

The bot sends different types of alerts:

### 1. Trade Alerts

Sent after each successful or failed trade execution:

**Content:**
- Trade type (BUY/SELL)
- Amount traded
- Profit/loss in sDAI and percentage
- Ideal price vs Balancer price
- Gas used and cost
- Transaction hash (clickable link to Gnosisscan)
- Execution time

**Example:**
```
🟢 BUY Trade SUCCESSFUL ✅

Amount: 1.5000 sDAI
Profit: 💰 +0.0500 sDAI (+3.33%)

Ideal Price: 1.002000
Balancer Price: 1.035000
Spread: +3.29%

⛽ Gas Used: 250,000
Gas Price: 1.50 gwei
Gas Cost: 0.000375 ETH

Transaction: 0x1234...abcdef
🕒 Execution: 2.30s

2026-01-16 12:34:56 UTC
```

### 2. Bot Status Alerts

Sent when bot starts or stops:

**Bot Start:**
```
🤖 Bot Status: START

EIP-7702 Arbitrage Bot Started

Amount: 0.1 sDAI
Tolerance: 2%
Mode: Live Trading
Network: Gnosis Chain

2026-01-16 12:00:00 UTC
```

**Bot Stop:**
```
🛑 Bot Status: STOP

Bot stopped by user

Reason: Manual interruption (Ctrl+C)

2026-01-16 18:00:00 UTC
```

### 3. Error Alerts

Sent when critical errors occur:

```
🚨 ERROR ALERT

Error: Transaction failed: insufficient funds
Context: BUY trade for 1.5 sDAI

Traceback:
...last 10 lines of stack trace...

2026-01-16 12:34:56 UTC
```

### 4. Trading Summary (Manual)

Can be triggered manually for periodic summaries:

```python
from src.monitoring.telegram_alerts import create_alerter_from_env

telegram = create_alerter_from_env()
telegram.send_summary(
    trades_count=10,
    total_profit=0.45,
    total_volume=15.0,
    success_rate=90.0,
    period="24h"
)
```

## Customization

### Silent Notifications

For less important alerts, enable silent mode:

```bash
TELEGRAM_SILENT=true
```

Note: Trade and error alerts are always sent with sound, regardless of this setting.

### HTML Formatting

Messages use HTML formatting. You can customize the alerter:

```python
from src.monitoring.telegram_alerts import TelegramAlerter

alerter = TelegramAlerter(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
    chat_id=os.getenv("TELEGRAM_CHAT_ID"),
    silent=False,
    disable_preview=True  # Disable link previews
)

# Send custom message
alerter._send_message(
    "<b>Custom Alert</b>\n\nYour message here",
    parse_mode="HTML"
)
```

### Multiple Recipients

To send to multiple chats, create multiple alerters:

```python
alerters = [
    TelegramAlerter(bot_token=TOKEN, chat_id=ADMIN_CHAT_ID),
    TelegramAlerter(bot_token=TOKEN, chat_id=TEAM_CHAT_ID),
]

for alerter in alerters:
    alerter.send_trade_alert(...)
```

## Troubleshooting

### Bot Token Invalid

**Error:** `Invalid Telegram bot token or chat ID`

**Solutions:**
1. Verify token format: `123456789:ABCdef...` (should contain a colon)
2. Check for extra spaces or quotes in `.env` file
3. Generate a new token via @BotFather if compromised

### Chat Not Found

**Error:** `Chat not found`

**Solutions:**
1. Make sure you've started a conversation with the bot (send any message first)
2. For groups, ensure the bot is still a member
3. Verify chat ID is correct (use `/getUpdates` to check)
4. For groups, ensure chat ID is negative (e.g., `-123456789`)

### Connection Timeout

**Error:** `Failed to connect to Telegram API`

**Solutions:**
1. Check internet connection
2. Verify firewall isn't blocking `api.telegram.org`
3. Try again - Telegram API may be temporarily down

### Rate Limiting

If sending too many messages:

**Error:** `429 Too Many Requests`

**Solutions:**
1. Reduce message frequency
2. Batch updates instead of sending individual messages
3. Wait 30-60 seconds before retrying

## Best Practices

1. **Use Different Bots for Environments**
   - Create separate bots for development, staging, and production
   - Use prefixes in bot names (e.g., "DEV - Futarchy Bot")

2. **Monitor Bot Health**
   - Periodically check if bot is still active
   - Set up a daily heartbeat message

3. **Secure Your Token**
   - Never share bot tokens publicly
   - Use environment variables, not hardcoded values
   - Rotate tokens periodically

4. **Group Organization**
   - Use separate group chats for errors vs. trade notifications
   - Pin important messages in groups
   - Archive old messages to keep chat clean

5. **Message Formatting**
   - Keep messages concise but informative
   - Use emojis for quick visual scanning
   - Include clickable links for transactions

## Advanced Features

### Inline Keyboards (Future Enhancement)

Add interactive buttons to messages:

```python
# Future implementation
payload = {
    'chat_id': chat_id,
    'text': 'Trade executed',
    'reply_markup': {
        'inline_keyboard': [[
            {'text': 'View on Gnosisscan', 'url': explorer_url},
            {'text': 'Pause Bot', 'callback_data': 'pause'}
        ]]
    }
}
```

### Message Threading

Organize related alerts:

```python
# Send initial message
response = alerter._send_message("Starting trades...")
message_id = response.json()['result']['message_id']

# Reply to it
payload = {
    'chat_id': chat_id,
    'text': 'Trade 1 completed',
    'reply_to_message_id': message_id
}
```

### Rich Media

Send charts or graphs:

```python
# Send photo with caption
requests.post(
    f"https://api.telegram.org/bot{token}/sendPhoto",
    data={
        'chat_id': chat_id,
        'caption': 'Profit chart for today'
    },
    files={'photo': open('chart.png', 'rb')}
)
```

## Related Documentation

- [Slack Alerts](SLACK_ALERTS_QUICKSTART.md)
- [Structured Logging](../src/config/logging_config.py)
- [Production Monitoring](PRODUCTION_DEPLOYMENT.md)
- [Telegram Bot API Documentation](https://core.telegram.org/bots/api)
