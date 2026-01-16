"""
Telegram Alerting System for Trading Notifications

Sends real-time alerts for successful trades, errors, and bot status via Telegram Bot API.

Environment Variables:
- TELEGRAM_BOT_TOKEN: Bot token from @BotFather
- TELEGRAM_CHAT_ID: Chat ID where alerts should be sent
- TELEGRAM_SILENT: Set to "true" for silent notifications (optional)

Setup:
1. Create a bot with @BotFather on Telegram
2. Get your chat ID by messaging @userinfobot
3. Set environment variables in .env file

Usage:
    from src.monitoring.telegram_alerts import TelegramAlerter
    
    alerter = TelegramAlerter(
        bot_token=os.getenv("TELEGRAM_BOT_TOKEN"),
        chat_id=os.getenv("TELEGRAM_CHAT_ID")
    )
    
    # Send trade alert
    alerter.send_trade_alert(
        side="buy",
        amount=1.5,
        profit=0.05,
        tx_hash="0x123...",
        success=True
    )
"""

import os
import requests
from typing import Optional, Dict
from decimal import Decimal
from datetime import datetime

from src.config.logging_config import setup_logger

logger = setup_logger("telegram_alerts")


class TelegramAlerter:
    """Send trading alerts via Telegram Bot API"""
    
    # Alert emojis
    EMOJIS = {
        'trade_buy': '🟢',
        'trade_sell': '🔴',
        'profit': '💰',
        'loss': '📉',
        'error': '🚨',
        'warning': '⚠️',
        'info': 'ℹ️',
        'success': '✅',
        'failed': '❌',
        'bot_start': '🤖',
        'bot_stop': '🛑',
        'gas': '⛽',
        'clock': '🕒'
    }
    
    def __init__(
        self, 
        bot_token: str, 
        chat_id: str,
        silent: bool = False,
        disable_preview: bool = True
    ):
        """
        Initialize Telegram alerter
        
        Args:
            bot_token: Telegram bot token from @BotFather
            chat_id: Chat ID where messages will be sent
            silent: Send silent notifications
            disable_preview: Disable link previews in messages
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.silent = silent
        self.disable_preview = disable_preview
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        
        # Test connection
        if not self._test_connection():
            logger.error("Failed to connect to Telegram API")
            raise ValueError("Invalid Telegram bot token or chat ID")
    
    def _test_connection(self) -> bool:
        """Test Telegram bot connection"""
        try:
            response = requests.get(
                f"{self.api_url}/getMe",
                timeout=5
            )
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"Connected to Telegram bot: {bot_info['result']['username']}")
                return True
            return False
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False
    
    def _send_message(
        self, 
        text: str, 
        parse_mode: str = "HTML",
        silent: Optional[bool] = None
    ) -> bool:
        """
        Send text message via Telegram
        
        Args:
            text: Message text (supports HTML or Markdown)
            parse_mode: Message format ("HTML" or "Markdown")
            silent: Override default silent setting
        
        Returns:
            True if message sent successfully
        """
        payload = {
            'chat_id': self.chat_id,
            'text': text,
            'parse_mode': parse_mode,
            'disable_web_page_preview': self.disable_preview,
            'disable_notification': silent if silent is not None else self.silent
        }
        
        try:
            response = requests.post(
                f"{self.api_url}/sendMessage",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Telegram message sent successfully")
                return True
            else:
                error_data = response.json()
                logger.error(f"Telegram API error: {error_data.get('description', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_trade_alert(
        self,
        side: str,
        amount: float,
        profit: float,
        tx_hash: Optional[str] = None,
        success: bool = True,
        gas_used: Optional[int] = None,
        gas_price: Optional[float] = None,
        ideal_price: Optional[float] = None,
        balancer_price: Optional[float] = None,
        execution_time: Optional[float] = None
    ) -> bool:
        """
        Send trade execution alert
        
        Args:
            side: Trade side ("buy" or "sell")
            amount: Trade amount in sDAI
            profit: Profit/loss in sDAI
            tx_hash: Transaction hash
            success: Whether trade was successful
            gas_used: Gas used in wei
            gas_price: Gas price in gwei
            ideal_price: Ideal price from Swapr
            balancer_price: Balancer pool price
            execution_time: Execution time in seconds
        
        Returns:
            True if alert sent successfully
        """
        # Choose emoji based on side and success
        if success:
            emoji = self.EMOJIS['trade_buy'] if side.lower() == 'buy' else self.EMOJIS['trade_sell']
            status_emoji = self.EMOJIS['success']
            status_text = "SUCCESSFUL"
        else:
            emoji = self.EMOJIS['failed']
            status_emoji = self.EMOJIS['failed']
            status_text = "FAILED"
        
        # Profit emoji
        profit_emoji = self.EMOJIS['profit'] if profit >= 0 else self.EMOJIS['loss']
        
        # Build message
        lines = [
            f"{emoji} <b>{side.upper()} Trade {status_text}</b> {status_emoji}",
            "",
            f"<b>Amount:</b> {amount:.4f} sDAI",
            f"<b>Profit:</b> {profit_emoji} {profit:+.4f} sDAI ({(profit/amount*100):+.2f}%)",
        ]
        
        # Add price info if available
        if ideal_price is not None and balancer_price is not None:
            spread = ((balancer_price - ideal_price) / ideal_price * 100)
            lines.extend([
                "",
                f"<b>Ideal Price:</b> {ideal_price:.6f}",
                f"<b>Balancer Price:</b> {balancer_price:.6f}",
                f"<b>Spread:</b> {spread:+.2f}%"
            ])
        
        # Add gas info if available
        if gas_used is not None:
            gas_cost_eth = (gas_used * (gas_price or 0)) / 1e9 if gas_price else None
            lines.append("")
            lines.append(f"{self.EMOJIS['gas']} <b>Gas Used:</b> {gas_used:,}")
            if gas_price is not None:
                lines.append(f"<b>Gas Price:</b> {gas_price:.2f} gwei")
            if gas_cost_eth is not None:
                lines.append(f"<b>Gas Cost:</b> {gas_cost_eth:.6f} ETH")
        
        # Add transaction hash
        if tx_hash:
            # Gnosis Chain explorer
            explorer_url = f"https://gnosisscan.io/tx/{tx_hash}"
            lines.append("")
            lines.append(f"<b>Transaction:</b> <a href='{explorer_url}'>{tx_hash[:10]}...{tx_hash[-8:]}</a>")
        
        # Add execution time
        if execution_time is not None:
            lines.append(f"{self.EMOJIS['clock']} <b>Execution:</b> {execution_time:.2f}s")
        
        # Add timestamp
        lines.append("")
        lines.append(f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>")
        
        message = "\n".join(lines)
        return self._send_message(message, silent=False)  # Never silent for trades
    
    def send_bot_status(
        self,
        status: str,
        message: str,
        details: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send bot status update
        
        Args:
            status: Status type ("start", "stop", "error", "warning", "info")
            message: Status message
            details: Additional details to display
        
        Returns:
            True if alert sent successfully
        """
        emoji_map = {
            'start': self.EMOJIS['bot_start'],
            'stop': self.EMOJIS['bot_stop'],
            'error': self.EMOJIS['error'],
            'warning': self.EMOJIS['warning'],
            'info': self.EMOJIS['info']
        }
        
        emoji = emoji_map.get(status, self.EMOJIS['info'])
        
        lines = [
            f"{emoji} <b>Bot Status: {status.upper()}</b>",
            "",
            message
        ]
        
        if details:
            lines.append("")
            for key, value in details.items():
                lines.append(f"<b>{key}:</b> {value}")
        
        lines.append("")
        lines.append(f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>")
        
        message_text = "\n".join(lines)
        return self._send_message(message_text)
    
    def send_error_alert(
        self,
        error: str,
        context: Optional[str] = None,
        traceback: Optional[str] = None
    ) -> bool:
        """
        Send error alert
        
        Args:
            error: Error message
            context: Error context
            traceback: Stack trace (optional)
        
        Returns:
            True if alert sent successfully
        """
        lines = [
            f"{self.EMOJIS['error']} <b>ERROR ALERT</b>",
            "",
            f"<b>Error:</b> {error}"
        ]
        
        if context:
            lines.append(f"<b>Context:</b> {context}")
        
        if traceback:
            # Truncate long tracebacks
            tb_lines = traceback.split('\n')
            if len(tb_lines) > 10:
                tb_preview = '\n'.join(tb_lines[-10:])
                lines.append(f"\n<pre>{tb_preview}</pre>")
            else:
                lines.append(f"\n<pre>{traceback}</pre>")
        
        lines.append("")
        lines.append(f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>")
        
        message = "\n".join(lines)
        return self._send_message(message, silent=False)  # Never silent for errors
    
    def send_summary(
        self,
        trades_count: int,
        total_profit: float,
        total_volume: float,
        success_rate: float,
        period: str = "24h"
    ) -> bool:
        """
        Send trading summary
        
        Args:
            trades_count: Number of trades executed
            total_profit: Total profit in sDAI
            total_volume: Total volume traded
            success_rate: Success rate percentage
            period: Time period for summary
        
        Returns:
            True if alert sent successfully
        """
        profit_emoji = self.EMOJIS['profit'] if total_profit >= 0 else self.EMOJIS['loss']
        
        lines = [
            f"📊 <b>Trading Summary ({period})</b>",
            "",
            f"<b>Trades:</b> {trades_count}",
            f"<b>Success Rate:</b> {success_rate:.1f}%",
            f"<b>Total Volume:</b> {total_volume:.2f} sDAI",
            f"<b>Total Profit:</b> {profit_emoji} {total_profit:+.4f} sDAI",
            ""
        ]
        
        if trades_count > 0:
            avg_profit = total_profit / trades_count
            lines.append(f"<b>Avg Profit/Trade:</b> {avg_profit:+.4f} sDAI")
        
        lines.append("")
        lines.append(f"<i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</i>")
        
        message = "\n".join(lines)
        return self._send_message(message)


def create_alerter_from_env() -> Optional[TelegramAlerter]:
    """
    Create TelegramAlerter from environment variables
    
    Returns:
        TelegramAlerter instance or None if not configured
    """
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        logger.warning("Telegram not configured (TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID missing)")
        return None
    
    try:
        silent = os.getenv("TELEGRAM_SILENT", "false").lower() == "true"
        return TelegramAlerter(bot_token=bot_token, chat_id=chat_id, silent=silent)
    except Exception as e:
        logger.error(f"Failed to create Telegram alerter: {e}")
        return None


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Test alert system
    alerter = create_alerter_from_env()
    
    if not alerter:
        print("❌ Telegram not configured. Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID")
        sys.exit(1)
    
    print("✅ Telegram alerter initialized")
    
    # Send test alerts
    print("\n📤 Sending test alerts...")
    
    # Bot start
    alerter.send_bot_status(
        status="start",
        message="EIP-7702 arbitrage bot started",
        details={
            "Environment": "Production",
            "Network": "Gnosis Chain",
            "Version": "v1.0.0"
        }
    )
    
    # Successful trade
    alerter.send_trade_alert(
        side="buy",
        amount=1.5,
        profit=0.05,
        tx_hash="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        success=True,
        gas_used=250000,
        gas_price=1.5,
        ideal_price=1.002,
        balancer_price=1.035,
        execution_time=2.3
    )
    
    # Trading summary
    alerter.send_summary(
        trades_count=10,
        total_profit=0.45,
        total_volume=15.0,
        success_rate=90.0,
        period="24h"
    )
    
    print("✅ Test alerts sent!")
