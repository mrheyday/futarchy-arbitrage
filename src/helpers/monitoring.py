"""
Monitoring and Alerting Infrastructure for Futarchy Arbitrage Bot
Tracks metrics, health, and performance with alerting via Discord/Slack/Email
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any
import aiohttp
import json
from web3 import Web3

logger = logging.getLogger(__name__)


@dataclass
class Metric:
    """Metric data point"""
    timestamp: float
    name: str
    value: float
    tags: Dict[str, str]


@dataclass
class Alert:
    """Alert configuration"""
    name: str
    severity: str  # critical, warning, info
    threshold: float
    comparison: str  # gt, lt, eq
    cooldown: int  # seconds between alerts
    last_triggered: float = 0.0


class MonitoringClient:
    """
    Central monitoring client for tracking bot health and performance
    """
    
    def __init__(
        self,
        discord_webhook: Optional[str] = None,
        slack_webhook: Optional[str] = None,
        email_config: Optional[Dict[str, str]] = None,
        metrics_buffer_size: int = 10000,
    ):
        self.discord_webhook = discord_webhook
        self.slack_webhook = slack_webhook
        self.email_config = email_config
        
        self.metrics: List[Metric] = []
        self.metrics_buffer_size = metrics_buffer_size
        
        self.alerts: Dict[str, Alert] = {}
        self.alert_history: List[Dict[str, Any]] = []
        
        self.counters: Dict[str, int] = {}
        self.gauges: Dict[str, float] = {}
        
        logger.info("MonitoringClient initialized")
    
    # ==================== Metric Recording ====================
    
    def record_metric(self, name: str, value: float, tags: Optional[Dict[str, str]] = None) -> None:
        """Record a metric data point"""
        metric = Metric(
            timestamp=time.time(),
            name=name,
            value=value,
            tags=tags or {}
        )
        
        self.metrics.append(metric)
        
        # Trim buffer if needed
        if len(self.metrics) > self.metrics_buffer_size:
            self.metrics = self.metrics[-self.metrics_buffer_size:]
        
        # Update gauges
        self.gauges[name] = value
        
        # Check alerts
        self._check_alerts(name, value)
    
    def increment_counter(self, name: str, amount: int = 1) -> None:
        """Increment a counter"""
        self.counters[name] = self.counters.get(name, 0) + amount
        self.record_metric(f"counter.{name}", float(self.counters[name]))
    
    def record_trade(
        self,
        side: str,
        amount: Decimal,
        profit: Decimal,
        gas_used: int,
        tx_hash: str,
        success: bool
    ) -> None:
        """Record trade metrics"""
        tags = {
            "side": side,
            "success": str(success),
            "tx_hash": tx_hash
        }
        
        self.record_metric("trade.amount", float(amount), tags)
        self.record_metric("trade.profit", float(profit), tags)
        self.record_metric("trade.gas_used", float(gas_used), tags)
        
        if success:
            self.increment_counter("trades.successful")
        else:
            self.increment_counter("trades.failed")
    
    def record_balance(self, token: str, balance: Decimal) -> None:
        """Record token balance"""
        self.record_metric(f"balance.{token}", float(balance))
    
    def record_gas_price(self, gas_price_gwei: float) -> None:
        """Record current gas price"""
        self.record_metric("network.gas_price_gwei", gas_price_gwei)
    
    def record_price_spread(self, market: str, spread: Decimal) -> None:
        """Record price spread for arbitrage opportunity"""
        self.record_metric(f"spread.{market}", float(spread))
    
    # ==================== Alerting ====================
    
    def add_alert(
        self,
        name: str,
        severity: str,
        threshold: float,
        comparison: str = "gt",
        cooldown: int = 300
    ) -> None:
        """Add an alert rule"""
        self.alerts[name] = Alert(
            name=name,
            severity=severity,
            threshold=threshold,
            comparison=comparison,
            cooldown=cooldown
        )
        logger.info(f"Added alert: {name} ({severity}) - threshold {threshold}")
    
    def _check_alerts(self, metric_name: str, value: float) -> None:
        """Check if any alerts should trigger"""
        for alert_name, alert in self.alerts.items():
            if not alert_name.startswith(metric_name):
                continue
            
            # Check cooldown
            if time.time() - alert.last_triggered < alert.cooldown:
                continue
            
            # Check threshold
            should_trigger = False
            if alert.comparison == "gt" and value > alert.threshold:
                should_trigger = True
            elif alert.comparison == "lt" and value < alert.threshold:
                should_trigger = True
            elif alert.comparison == "eq" and abs(value - alert.threshold) < 0.01:
                should_trigger = True
            
            if should_trigger:
                asyncio.create_task(self._trigger_alert(alert, metric_name, value))
                alert.last_triggered = time.time()
    
    async def _trigger_alert(self, alert: Alert, metric_name: str, value: float) -> None:
        """Trigger an alert"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "alert_name": alert.name,
            "severity": alert.severity,
            "metric": metric_name,
            "value": value,
            "threshold": alert.threshold
        }
        
        self.alert_history.append(alert_data)
        
        message = (
            f"🚨 **{alert.severity.upper()} ALERT**: {alert.name}\n"
            f"Metric: {metric_name}\n"
            f"Value: {value:.4f}\n"
            f"Threshold: {alert.threshold:.4f}\n"
            f"Time: {alert_data['timestamp']}"
        )
        
        logger.warning(f"Alert triggered: {alert.name} - {metric_name}={value}")
        
        # Send to notification channels
        await self._send_discord(message, alert.severity)
        await self._send_slack(message, alert.severity)
    
    async def _send_discord(self, message: str, severity: str) -> None:
        """Send alert to Discord"""
        if not self.discord_webhook:
            return
        
        color = {"critical": 0xFF0000, "warning": 0xFFA500, "info": 0x0000FF}.get(severity, 0x808080)
        
        payload = {
            "embeds": [{
                "title": "Futarchy Arbitrage Bot Alert",
                "description": message,
                "color": color,
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.discord_webhook, json=payload) as resp:
                    if resp.status != 204:
                        logger.error(f"Discord webhook failed: {resp.status}")
        except Exception as e:
            logger.error(f"Error sending Discord alert: {e}")
    
    async def _send_slack(self, message: str, severity: str) -> None:
        """Send alert to Slack"""
        if not self.slack_webhook:
            return
        
        payload = {
            "text": message,
            "attachments": [{
                "color": {"critical": "danger", "warning": "warning", "info": "good"}.get(severity, "#808080")
            }]
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.slack_webhook, json=payload) as resp:
                    if resp.status != 200:
                        logger.error(f"Slack webhook failed: {resp.status}")
        except Exception as e:
            logger.error(f"Error sending Slack alert: {e}")
    
    # ==================== Health Checks ====================
    
    async def check_health(self, web3: Web3) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health = {
            "timestamp": datetime.now().isoformat(),
            "checks": {}
        }
        
        # RPC connection
        try:
            block = web3.eth.block_number
            health["checks"]["rpc"] = {
                "status": "healthy",
                "block_number": block
            }
        except Exception as e:
            health["checks"]["rpc"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Recent trades
        recent_trades = sum(1 for m in self.metrics[-100:] if m.name.startswith("trade."))
        health["checks"]["recent_trades"] = {
            "status": "healthy" if recent_trades > 0 else "warning",
            "count": recent_trades
        }
        
        # Error rate
        successful = self.counters.get("trades.successful", 0)
        failed = self.counters.get("trades.failed", 0)
        total = successful + failed
        error_rate = (failed / total * 100) if total > 0 else 0
        
        health["checks"]["error_rate"] = {
            "status": "healthy" if error_rate < 10 else "warning",
            "rate": f"{error_rate:.2f}%",
            "successful": successful,
            "failed": failed
        }
        
        # Metrics buffer
        health["checks"]["metrics"] = {
            "status": "healthy",
            "buffer_size": len(self.metrics),
            "buffer_usage": f"{len(self.metrics) / self.metrics_buffer_size * 100:.1f}%"
        }
        
        return health
    
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring summary"""
        return {
            "counters": self.counters,
            "gauges": self.gauges,
            "metrics_count": len(self.metrics),
            "alerts_configured": len(self.alerts),
            "alerts_triggered": len(self.alert_history),
            "recent_alerts": self.alert_history[-10:]
        }


def setup_default_alerts(monitor: MonitoringClient) -> None:
    """Configure default alert rules"""
    
    # Critical alerts
    monitor.add_alert("balance.sdai.low", "critical", 0.1, "lt", cooldown=600)
    monitor.add_alert("trade.profit.negative", "critical", -0.01, "lt", cooldown=300)
    monitor.add_alert("network.gas_price_gwei.high", "critical", 500, "gt", cooldown=300)
    
    # Warning alerts
    monitor.add_alert("trade.gas_used.high", "warning", 1000000, "gt", cooldown=600)
    monitor.add_alert("spread.too_small", "warning", 0.005, "lt", cooldown=600)
    
    # Info alerts
    monitor.add_alert("trade.profit.good", "info", 0.1, "gt", cooldown=3600)
    
    logger.info("Default alerts configured")
