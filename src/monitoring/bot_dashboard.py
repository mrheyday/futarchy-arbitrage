"""
Real-time Bot Dashboard

Displays:
- Active bots and their status
- Current positions and PnL
- Recent trades (success/failure)
- Alert conditions (low balance, circuit breakers)
- Gas prices and profitability thresholds
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config.config_manager import ConfigManager
from src.config.logging_config import setup_logger
from src.helpers.web3_setup import get_web3_instance

logger = setup_logger("bot_dashboard", level=10)  # DEBUG


@dataclass
class BotStatus:
    """Bot status information"""
    bot_name: str
    wallet_address: str
    is_active: bool
    assigned_market: Optional[str]
    sdai_balance: Decimal
    company_balance: Decimal
    gas_balance: Decimal  # ETH balance for gas
    last_trade_time: Optional[datetime]
    trades_today: int
    profit_today: Decimal
    circuit_breaker_status: str


@dataclass
class TradeRecord:
    """Trade record from database"""
    timestamp: datetime
    bot_name: str
    side: str  # BUY/SELL
    amount: Decimal
    profit: Decimal
    gas_cost: Decimal
    tx_hash: str
    success: bool


class BotDashboard:
    """Real-time monitoring dashboard for arbitrage bots"""
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        self.config_manager = config_manager or ConfigManager()
        self.w3 = get_web3_instance()
        
    def get_all_bot_statuses(self) -> List[BotStatus]:
        """Fetch status for all registered bots"""
        bots = self.config_manager.get_all_bots()
        statuses = []
        
        for bot in bots:
            try:
                status = self._get_bot_status(bot)
                statuses.append(status)
            except Exception as e:
                logger.error(f"Failed to get status for {bot['name']}: {e}")
        
        return statuses
    
    def _get_bot_status(self, bot_config: Dict) -> BotStatus:
        """Get detailed status for a single bot"""
        wallet = bot_config["wallet_address"]
        
        # Get balances from chain
        sdai_balance = self._get_token_balance(
            wallet,
            os.getenv("SDAI_TOKEN_ADDRESS")
        )
        company_balance = self._get_token_balance(
            wallet,
            os.getenv("COMPANY_TOKEN_ADDRESS")
        )
        gas_balance = Decimal(self.w3.eth.get_balance(wallet)) / Decimal(10**18)
        
        # Get trade history from Supabase
        trades = self._get_recent_trades(bot_config["name"], hours=24)
        trades_today = len(trades)
        profit_today = sum(t.profit for t in trades)
        last_trade_time = trades[0].timestamp if trades else None
        
        # Check circuit breaker status (placeholder)
        circuit_status = self._check_circuit_breakers(bot_config)
        
        return BotStatus(
            bot_name=bot_config["name"],
            wallet_address=wallet,
            is_active=bot_config.get("is_active", True),
            assigned_market=bot_config.get("assigned_market"),
            sdai_balance=sdai_balance,
            company_balance=company_balance,
            gas_balance=gas_balance,
            last_trade_time=last_trade_time,
            trades_today=trades_today,
            profit_today=profit_today,
            circuit_breaker_status=circuit_status,
        )
    
    def _get_token_balance(self, wallet: str, token_address: str) -> Decimal:
        """Get ERC20 token balance"""
        if not token_address:
            return Decimal(0)
        
        # ERC20 balanceOf ABI
        balance_of_abi = [{
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }]
        
        token = self.w3.eth.contract(
            address=self.w3.to_checksum_address(token_address),
            abi=balance_of_abi
        )
        
        balance = token.functions.balanceOf(
            self.w3.to_checksum_address(wallet)
        ).call()
        
        return Decimal(balance) / Decimal(10**18)
    
    def _get_recent_trades(self, bot_name: str, hours: int = 24) -> List[TradeRecord]:
        """Fetch recent trades from Supabase"""
        # TODO: Implement Supabase query
        # For now, return empty list
        return []
    
    def _check_circuit_breakers(self, bot_config: Dict) -> str:
        """Check circuit breaker status"""
        # TODO: Query SafetyModule contract
        # For now, return OK
        return "OK"
    
    def print_dashboard(self):
        """Print formatted dashboard to console"""
        statuses = self.get_all_bot_statuses()
        
        print("\n" + "="*100)
        print(" "*35 + "FUTARCHY ARBITRAGE BOT DASHBOARD")
        print("="*100)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Active Bots: {sum(1 for s in statuses if s.is_active)}/{len(statuses)}")
        print("="*100)
        
        # Header
        header = (
            f"{'Bot Name':<20} {'Status':<10} {'sDAI':<12} {'Company':<12} "
            f"{'Gas (ETH)':<10} {'Trades':<8} {'Profit':<12} {'Circuit':<15}"
        )
        print(header)
        print("-"*100)
        
        # Bot rows
        total_profit = Decimal(0)
        total_trades = 0
        
        for status in statuses:
            status_str = "ACTIVE" if status.is_active else "INACTIVE"
            total_profit += status.profit_today
            total_trades += status.trades_today
            
            # Alert if low balance
            gas_alert = " ⚠️" if status.gas_balance < Decimal("0.01") else ""
            sdai_alert = " ⚠️" if status.sdai_balance < Decimal("10") else ""
            
            row = (
                f"{status.bot_name:<20} "
                f"{status_str:<10} "
                f"{status.sdai_balance:>10.2f}{sdai_alert:<2} "
                f"{status.company_balance:>10.2f}  "
                f"{status.gas_balance:>8.4f}{gas_alert:<2} "
                f"{status.trades_today:>6}  "
                f"{status.profit_today:>10.2f}  "
                f"{status.circuit_breaker_status:<15}"
            )
            print(row)
        
        print("-"*100)
        print(f"{'TOTAL':<20} {'':<10} {'':<12} {'':<12} {'':<10} "
              f"{total_trades:>6}  {total_profit:>10.2f}")
        print("="*100)
        
        # Alerts section
        alerts = self._get_alerts(statuses)
        if alerts:
            print("\n⚠️  ALERTS:")
            for alert in alerts:
                print(f"  - {alert}")
        
        print("\n")
    
    def _get_alerts(self, statuses: List[BotStatus]) -> List[str]:
        """Generate alert messages"""
        alerts = []
        
        for status in statuses:
            # Low gas alert
            if status.gas_balance < Decimal("0.01"):
                alerts.append(
                    f"{status.bot_name}: Low gas balance ({status.gas_balance:.4f} ETH)"
                )
            
            # Low sDAI alert
            if status.sdai_balance < Decimal("10"):
                alerts.append(
                    f"{status.bot_name}: Low sDAI balance ({status.sdai_balance:.2f})"
                )
            
            # Inactive bot
            if not status.is_active and status.assigned_market:
                alerts.append(
                    f"{status.bot_name}: Inactive but assigned to market"
                )
            
            # No recent trades
            if status.is_active and status.last_trade_time:
                hours_since_trade = (datetime.now() - status.last_trade_time).total_seconds() / 3600
                if hours_since_trade > 24:
                    alerts.append(
                        f"{status.bot_name}: No trades in {hours_since_trade:.1f} hours"
                    )
            
            # Circuit breaker tripped
            if status.circuit_breaker_status != "OK":
                alerts.append(
                    f"{status.bot_name}: Circuit breaker - {status.circuit_breaker_status}"
                )
        
        return alerts
    
    def get_market_summary(self) -> Dict:
        """Get summary of all markets"""
        # TODO: Fetch from Supabase market_events table
        return {
            "total_markets": 0,
            "active_markets": 0,
            "total_volume_24h": Decimal(0),
        }
    
    def monitor_loop(self, interval_seconds: int = 60):
        """Continuous monitoring loop"""
        import time
        
        try:
            while True:
                self.print_dashboard()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\nDashboard stopped.")


def main():
    """Run dashboard"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Futarchy Arbitrage Bot Dashboard")
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Update interval in seconds (default: 60)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Print once and exit (don't loop)",
    )
    
    args = parser.parse_args()
    
    dashboard = BotDashboard()
    
    if args.once:
        dashboard.print_dashboard()
    else:
        dashboard.monitor_loop(interval_seconds=args.interval)


if __name__ == "__main__":
    main()
