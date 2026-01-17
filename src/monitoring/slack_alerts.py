"""
Slack Alerting System for Circuit Breaker Events

Monitors SafetyModule events and sends alerts to Slack via webhooks.
Supports circuit breaker trips, emergency pauses, and daily loss limits.

Environment Variables:
- SLACK_WEBHOOK_URL: Slack webhook URL for alerts
- SLACK_MENTION_USERS: Comma-separated list of Slack user IDs to mention (optional)

Usage:
    # Monitor events from latest block
    python -m src.monitoring.slack_alerts --start-block latest
    
    # Monitor from specific block
    python -m src.monitoring.slack_alerts --start-block 12345678
    
    # Test alert
    python -m src.monitoring.slack_alerts --test
"""

import os
import json
import time
import argparse
import requests
from web3 import Web3
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

from src.config.logging_config import setup_logger

logger = setup_logger("slack_alerts")

class SlackAlerter:
    """Send circuit breaker alerts to Slack"""
    
    # Alert emojis
    EMOJIS = {
        'error': '🚨',
        'warning': '⚠️',
        'info': 'ℹ️',
        'success': '✅',
        'paused': '⏸️',
        'resumed': '▶️'
    }
    
    def __init__(self, webhook_url: str, mention_users: Optional[List[str]] = None):
        """
        Initialize Slack alerter
        
        Args:
            webhook_url: Slack webhook URL
            mention_users: List of Slack user IDs to mention (e.g., ['U01234567'])
        """
        self.webhook_url = webhook_url
        self.mention_users = mention_users or []
        
        # Test connection
        if not self._test_connection():
            logger.error("Failed to connect to Slack webhook")
            raise ValueError("Invalid Slack webhook URL")
    
    def _test_connection(self) -> bool:
        """Test Slack webhook connection"""
        try:
            response = requests.post(
                self.webhook_url,
                json={'text': '🔧 SafetyModule monitoring initialized'},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Slack connection test failed: {e}")
            return False
    
    def _format_mentions(self) -> str:
        """Format user mentions"""
        if not self.mention_users:
            return ""
        return " " + " ".join([f"<@{uid}>" for uid in self.mention_users])
    
    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = 'info',
        fields: Optional[Dict[str, str]] = None,
        mention: bool = False
    ) -> bool:
        """
        Send formatted alert to Slack
        
        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (error, warning, info, success)
            fields: Additional fields to display
            mention: Whether to mention configured users
        
        Returns:
            True if alert sent successfully
        """
        emoji = self.EMOJIS.get(severity, 'ℹ️')
        
        # Build message text
        text = f"{emoji} *{title}*{self._format_mentions() if mention else ''}"
        
        # Build attachment fields
        attachment_fields = []
        if fields:
            for key, value in fields.items():
                attachment_fields.append({
                    'title': key,
                    'value': value,
                    'short': len(str(value)) < 50
                })
        
        # Add timestamp
        attachment_fields.append({
            'title': 'Time',
            'value': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'short': True
        })
        
        # Build Slack payload
        payload = {
            'text': text,
            'attachments': [{
                'color': self._get_color(severity),
                'text': message,
                'fields': attachment_fields,
                'footer': 'SafetyModule Monitor',
                'ts': int(time.time())
            }]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Slack alert sent: {title}")
                return True
            else:
                logger.error(f"Slack alert failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def _get_color(self, severity: str) -> str:
        """Get color for alert severity"""
        colors = {
            'error': '#FF0000',    # Red
            'warning': '#FFA500',  # Orange
            'info': '#0000FF',     # Blue
            'success': '#00FF00',  # Green
            'paused': '#800080',   # Purple
            'resumed': '#008000'   # Dark green
        }
        return colors.get(severity, '#808080')  # Gray default
    
    def slippage_circuit_tripped(self, event_data: Dict) -> bool:
        """Alert for slippage circuit breaker trip"""
        return self.send_alert(
            title='Slippage Circuit Breaker Triggered',
            message=f'Trade blocked due to excessive slippage',
            severity='warning',
            fields={
                'Trade Amount': f"{Web3.from_wei(event_data.get('tradeAmount', 0), 'ether')} ETH",
                'Expected Output': f"{Web3.from_wei(event_data.get('expectedOutput', 0), 'ether')} ETH",
                'Actual Output': f"{Web3.from_wei(event_data.get('actualOutput', 0), 'ether')} ETH",
                'Slippage %': f"{event_data.get('slippageBps', 0) / 100}%",
                'Max Allowed': f"{event_data.get('maxAllowedBps', 500) / 100}%",
                'Block': str(event_data.get('blockNumber', 'N/A')),
                'Tx Hash': event_data.get('transactionHash', 'N/A')
            },
            mention=True
        )
    
    def gas_circuit_tripped(self, event_data: Dict) -> bool:
        """Alert for gas price circuit breaker trip"""
        return self.send_alert(
            title='Gas Price Circuit Breaker Triggered',
            message=f'Trade blocked due to excessive gas price',
            severity='warning',
            fields={
                'Gas Price': f"{Web3.from_wei(event_data.get('gasPrice', 0), 'gwei')} gwei",
                'Max Allowed': f"{Web3.from_wei(event_data.get('maxGasPrice', 0), 'gwei')} gwei",
                'Block': str(event_data.get('blockNumber', 'N/A')),
                'Tx Hash': event_data.get('transactionHash', 'N/A')
            },
            mention=False  # Less critical
        )
    
    def daily_loss_circuit_tripped(self, event_data: Dict) -> bool:
        """Alert for daily loss limit circuit breaker trip"""
        return self.send_alert(
            title='Daily Loss Limit Exceeded',
            message=f'Trading halted: daily loss limit reached',
            severity='error',
            fields={
                'Today Loss': f"{Web3.from_wei(event_data.get('todayLoss', 0), 'ether')} ETH",
                'Max Allowed': f"{Web3.from_wei(event_data.get('maxDailyLoss', 0), 'ether')} ETH",
                'Block': str(event_data.get('blockNumber', 'N/A')),
                'Tx Hash': event_data.get('transactionHash', 'N/A')
            },
            mention=True  # Critical
        )
    
    def emergency_paused(self, event_data: Dict) -> bool:
        """Alert for emergency pause"""
        return self.send_alert(
            title='🚨 EMERGENCY PAUSE ACTIVATED',
            message=f'All trading has been paused by owner',
            severity='paused',
            fields={
                'Owner': event_data.get('owner', 'N/A'),
                'Block': str(event_data.get('blockNumber', 'N/A')),
                'Tx Hash': event_data.get('transactionHash', 'N/A')
            },
            mention=True  # Critical
        )
    
    def emergency_resumed(self, event_data: Dict) -> bool:
        """Alert for emergency unpause"""
        return self.send_alert(
            title='Trading Resumed',
            message=f'Emergency pause has been lifted',
            severity='resumed',
            fields={
                'Owner': event_data.get('owner', 'N/A'),
                'Block': str(event_data.get('blockNumber', 'N/A')),
                'Tx Hash': event_data.get('transactionHash', 'N/A')
            },
            mention=True
        )

class SafetyModuleMonitor:
    """Monitor SafetyModule contract events and send alerts"""
    
    EVENT_SIGNATURES = {
        'SlippageCircuitTripped': Web3.keccak(text='SlippageCircuitTripped(uint256,uint256,uint256,uint256)').hex(),
        'GasCircuitTripped': Web3.keccak(text='GasCircuitTripped(uint256,uint256)').hex(),
        'DailyLossCircuitTripped': Web3.keccak(text='DailyLossCircuitTripped(uint256,uint256)').hex(),
        'EmergencyPaused': Web3.keccak(text='EmergencyPaused(address)').hex(),
        'EmergencyUnpaused': Web3.keccak(text='EmergencyUnpaused(address)').hex()
    }
    
    def __init__(
        self,
        w3: Web3,
        contract_address: str,
        alerter: SlackAlerter,
        contract_abi: List[Dict]
    ):
        """
        Initialize monitor
        
        Args:
            w3: Web3 instance
            contract_address: SafetyModule contract address
            alerter: SlackAlerter instance
            contract_abi: Contract ABI
        """
        self.w3 = w3
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.alerter = alerter
        self.contract = w3.eth.contract(address=self.contract_address, abi=contract_abi)
    
    def process_event(self, event: Dict) -> None:
        """Process a single event and send alert"""
        event_name = event.get('event')
        event_data = dict(event.get('args', {}))
        
        # Add block and tx info
        event_data['blockNumber'] = event.get('blockNumber')
        event_data['transactionHash'] = event.get('transactionHash', '').hex() if event.get('transactionHash') else 'N/A'
        
        logger.info(f"Processing event: {event_name}")
        
        # Route to appropriate alert handler
        if event_name == 'SlippageCircuitTripped':
            self.alerter.slippage_circuit_tripped(event_data)
        elif event_name == 'GasCircuitTripped':
            self.alerter.gas_circuit_tripped(event_data)
        elif event_name == 'DailyLossCircuitTripped':
            self.alerter.daily_loss_circuit_tripped(event_data)
        elif event_name == 'EmergencyPaused':
            self.alerter.emergency_paused(event_data)
        elif event_name == 'EmergencyUnpaused':
            self.alerter.emergency_resumed(event_data)
        else:
            logger.warning(f"Unknown event: {event_name}")
    
    def monitor(self, from_block: int, poll_interval: int = 15) -> None:
        """
        Monitor contract events in real-time
        
        Args:
            from_block: Block number to start monitoring from
            poll_interval: Seconds between polls
        """
        logger.info(f"Starting event monitor from block {from_block}")
        logger.info(f"Monitoring contract: {self.contract_address}")
        logger.info(f"Poll interval: {poll_interval} seconds")
        
        current_block = from_block
        
        try:
            while True:
                try:
                    # Get latest block
                    latest_block = self.w3.eth.block_number
                    
                    if current_block > latest_block:
                        # Wait for new blocks
                        time.sleep(poll_interval)
                        continue
                    
                    # Fetch events
                    to_block = min(current_block + 1000, latest_block)  # Process in chunks
                    
                    logger.debug(f"Checking blocks {current_block} to {to_block}")
                    
                    # Get all SafetyModule events
                    events = self.contract.events.SlippageCircuitTripped.get_logs(
                        fromBlock=current_block,
                        toBlock=to_block
                    )
                    events += self.contract.events.GasCircuitTripped.get_logs(
                        fromBlock=current_block,
                        toBlock=to_block
                    )
                    events += self.contract.events.DailyLossCircuitTripped.get_logs(
                        fromBlock=current_block,
                        toBlock=to_block
                    )
                    events += self.contract.events.EmergencyPaused.get_logs(
                        fromBlock=current_block,
                        toBlock=to_block
                    )
                    events += self.contract.events.EmergencyUnpaused.get_logs(
                        fromBlock=current_block,
                        toBlock=to_block
                    )
                    
                    # Process events
                    for event in sorted(events, key=lambda e: e['blockNumber']):
                        self.process_event(event)
                    
                    if events:
                        logger.info(f"Processed {len(events)} events")
                    
                    # Update current block
                    current_block = to_block + 1
                    
                    # Wait before next poll
                    time.sleep(poll_interval)
                    
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    logger.error(f"Error in monitor loop: {e}")
                    time.sleep(poll_interval)
                    
        except KeyboardInterrupt:
            logger.info("Monitor stopped by user")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Monitor SafetyModule and send Slack alerts")
    parser.add_argument(
        '--start-block',
        type=str,
        default='latest',
        help='Block number to start monitoring from (or "latest")'
    )
    parser.add_argument(
        '--poll-interval',
        type=int,
        default=15,
        help='Seconds between polls (default: 15)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Send test alert and exit'
    )
    
    args = parser.parse_args()
    
    # Load environment
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if not webhook_url:
        logger.error("SLACK_WEBHOOK_URL environment variable not set")
        logger.info("Get webhook URL from: https://api.slack.com/messaging/webhooks")
        return
    
    # Parse mention users
    mention_users = []
    if os.getenv('SLACK_MENTION_USERS'):
        mention_users = [u.strip() for u in os.getenv('SLACK_MENTION_USERS').split(',')]
    
    # Initialize alerter
    try:
        alerter = SlackAlerter(webhook_url, mention_users)
    except ValueError as e:
        logger.error(f"Failed to initialize Slack alerter: {e}")
        return
    
    # Test mode
    if args.test:
        logger.info("Sending test alert...")
        alerter.send_alert(
            title='Test Alert',
            message='SafetyModule monitoring is configured correctly',
            severity='success',
            fields={'Status': 'All systems operational'},
            mention=True
        )
        logger.info("Test alert sent!")
        return
    
    # Load contract details
    rpc_url = os.getenv('RPC_URL')
    contract_address = os.getenv('SAFETY_MODULE_ADDRESS')
    
    if not rpc_url or not contract_address:
        logger.error("RPC_URL and SAFETY_MODULE_ADDRESS environment variables required")
        return
    
    # Connect to network
    logger.info(f"Connecting to RPC: {rpc_url}")
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        logger.error("Failed to connect to RPC")
        return
    
    logger.info(f"Connected! Chain ID: {w3.eth.chain_id}")
    
    # Load contract ABI
    abi_path = Path(__file__).parent.parent.parent / "out" / "SafetyModule.sol" / "SafetyModule.json"
    if not abi_path.exists():
        logger.error(f"Contract ABI not found: {abi_path}")
        logger.info("Run: forge build")
        return
    
    with open(abi_path, 'r') as f:
        contract_abi = json.load(f)['abi']
    
    # Determine start block
    if args.start_block == 'latest':
        start_block = w3.eth.block_number
        logger.info(f"Starting from latest block: {start_block}")
    else:
        start_block = int(args.start_block)
    
    # Initialize and start monitor
    monitor = SafetyModuleMonitor(w3, contract_address, alerter, contract_abi)
    monitor.monitor(from_block=start_block, poll_interval=args.poll_interval)

if __name__ == '__main__':
    main()
