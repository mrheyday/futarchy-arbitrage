"""
Institutional Solver Intelligence - Monitoring & Telemetry
============================================================

Monitoring script for the CLZ-enhanced Institutional Solver System.
Tracks metrics, events, and system health.

January 2026 post-Fusaka deployment.
"""

import os
import json
import time
import sqlite3
from web3 import Web3
from decimal import Decimal
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SolverMonitor:
    """
    Monitor for Institutional Solver Intelligence System.
    Tracks events, metrics, and system health.
    """

    def __init__(
        self,
        web3: Web3,
        contract_address: str,
        contract_abi: list[dict],
        db_path: str = "monitoring.db"
    ):
        self.web3 = web3
        self.contract = web3.eth.contract(
            address=Web3.to_checksum_address(contract_address),
            abi=contract_abi
        )
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """Initialize monitoring database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT,
                block_number INTEGER,
                tx_hash TEXT,
                data TEXT,
                timestamp INTEGER
            )
        """)
        
        # Metrics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT,
                value REAL,
                clz_value INTEGER,
                timestamp INTEGER
            )
        """)
        
        # Health checks table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS health_checks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                check_name TEXT,
                status TEXT,
                details TEXT,
                timestamp INTEGER
            )
        """)
        
        conn.commit()
        conn.close()

    def monitor_events(self, from_block: int, to_block: int | None = None):
        """
        Monitor contract events.
        
        Args:
            from_block: Starting block number
            to_block: Ending block number (None for latest)
        """
        if to_block is None:
            to_block = self.web3.eth.block_number
        
        logger.info(f"Monitoring events from block {from_block} to {to_block}")
        
        # Intent events
        self._process_events(
            "IntentSubmitted",
            from_block,
            to_block
        )
        self._process_events(
            "IntentResolved",
            from_block,
            to_block
        )
        
        # Auction events
        self._process_events(
            "BidCommitted",
            from_block,
            to_block
        )
        self._process_events(
            "BidRevealed",
            from_block,
            to_block
        )
        self._process_events(
            "AuctionSettled",
            from_block,
            to_block
        )
        
        # Reputation events
        self._process_events(
            "ReputationUpdated",
            from_block,
            to_block
        )
        
        # Batch events
        self._process_events(
            "BatchExecuted",
            from_block,
            to_block
        )

    def _process_events(self, event_name: str, from_block: int, to_block: int):
        """Process specific event type."""
        try:
            event_filter = getattr(self.contract.events, event_name).create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            
            events = event_filter.get_all_entries()
            logger.info(f"Found {len(events)} {event_name} events")
            
            for event in events:
                self._store_event(
                    event_name,
                    event['blockNumber'],
                    event['transactionHash'].hex(),
                    event['args']
                )
                
                # Log event details
                logger.info(f"{event_name}: {event['args']}")
                
        except Exception as e:
            logger.error(f"Error processing {event_name} events: {e}")

    def _store_event(
        self,
        event_name: str,
        block_number: int,
        tx_hash: str,
        data: dict
    ):
        """Store event in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO events (event_name, block_number, tx_hash, data, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (
            event_name,
            block_number,
            tx_hash,
            json.dumps(dict(data)),
            int(time.time())
        ))
        
        conn.commit()
        conn.close()

    def calculate_metrics(self):
        """Calculate and store system metrics."""
        logger.info("Calculating system metrics...")
        
        metrics = {
            'total_intents': self._count_events('IntentSubmitted'),
            'resolved_intents': self._count_events('IntentResolved'),
            'total_auctions': self._count_events('AuctionSettled'),
            'total_bids': self._count_events('BidRevealed'),
        }
        
        # Calculate CLZ values for metrics
        for metric_name, value in metrics.items():
            clz_value = self._calculate_clz_log(value)
            self._store_metric(metric_name, value, clz_value)
            logger.info(f"{metric_name}: {value} (CLZ: {clz_value})")
        
        return metrics

    def _count_events(self, event_name: str) -> int:
        """Count events in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT COUNT(*) FROM events WHERE event_name = ?
        """, (event_name,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count

    def _store_metric(self, metric_name: str, value: float, clz_value: int):
        """Store metric in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO metrics (metric_name, value, clz_value, timestamp)
            VALUES (?, ?, ?, ?)
        """, (metric_name, value, clz_value, int(time.time())))
        
        conn.commit()
        conn.close()

    def _calculate_clz_log(self, value: int) -> int:
        """Calculate CLZ-based log2 approximation."""
        if value == 0:
            return 0
        
        bit_length = value.bit_length()
        leading_zeros = 256 - bit_length
        return 255 - leading_zeros

    def health_check(self) -> dict[str, bool]:
        """
        Perform system health checks.
        
        Returns:
            Dictionary of health check results
        """
        logger.info("Performing health checks...")
        
        checks = {}
        
        # Check RPC connection
        try:
            block = self.web3.eth.block_number
            checks['rpc_connection'] = True
            self._store_health_check('rpc_connection', 'OK', f'Block: {block}')
        except Exception as e:
            checks['rpc_connection'] = False
            self._store_health_check('rpc_connection', 'FAIL', str(e))
        
        # Check contract is deployed
        try:
            code = self.web3.eth.get_code(self.contract.address)
            checks['contract_deployed'] = len(code) > 0
            status = 'OK' if checks['contract_deployed'] else 'FAIL'
            self._store_health_check('contract_deployed', status, f'Code length: {len(code)}')
        except Exception as e:
            checks['contract_deployed'] = False
            self._store_health_check('contract_deployed', 'FAIL', str(e))
        
        # Check owner
        try:
            owner = self.contract.functions.owner().call()
            checks['owner_set'] = owner != "0x0000000000000000000000000000000000000000"
            self._store_health_check('owner_set', 'OK' if checks['owner_set'] else 'FAIL', f'Owner: {owner}')
        except Exception as e:
            checks['owner_set'] = False
            self._store_health_check('owner_set', 'FAIL', str(e))
        
        # Log results
        for check_name, passed in checks.items():
            status = "✓" if passed else "✗"
            logger.info(f"{status} {check_name}")
        
        return checks

    def _store_health_check(self, check_name: str, status: str, details: str):
        """Store health check result."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO health_checks (check_name, status, details, timestamp)
            VALUES (?, ?, ?, ?)
        """, (check_name, status, details, int(time.time())))
        
        conn.commit()
        conn.close()

    def get_auction_stats(self, auction_id: int) -> dict:
        """Get statistics for a specific auction."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count bids
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE event_name = 'BidRevealed' 
            AND json_extract(data, '$.auctionId') = ?
        """, (auction_id,))
        
        bid_count = cursor.fetchone()[0]
        
        # Get winner
        cursor.execute("""
            SELECT data FROM events 
            WHERE event_name = 'AuctionSettled' 
            AND json_extract(data, '$.auctionId') = ?
        """, (auction_id,))
        
        result = cursor.fetchone()
        winner = None
        winning_bid = None
        
        if result:
            data = json.loads(result[0])
            winner = data.get('winner')
            winning_bid = data.get('winningBid')
        
        conn.close()
        
        return {
            'auction_id': auction_id,
            'bid_count': bid_count,
            'winner': winner,
            'winning_bid': winning_bid
        }

    def get_solver_stats(self, solver_address: str) -> dict:
        """Get statistics for a specific solver."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count resolved intents
        cursor.execute("""
            SELECT COUNT(*) FROM events 
            WHERE event_name = 'IntentResolved' 
            AND json_extract(data, '$.solver') = ?
        """, (solver_address,))
        
        intents_resolved = cursor.fetchone()[0]
        
        # Get reputation updates
        cursor.execute("""
            SELECT SUM(CAST(json_extract(data, '$.delta') AS INTEGER)) FROM events 
            WHERE event_name = 'ReputationUpdated' 
            AND json_extract(data, '$.solver') = ?
        """, (solver_address,))
        
        reputation_delta = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return {
            'solver': solver_address,
            'intents_resolved': intents_resolved,
            'reputation_delta': reputation_delta
        }

    def run_continuous_monitoring(self, interval: int = 60):
        """
        Run continuous monitoring loop.
        
        Args:
            interval: Seconds between checks
        """
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        
        last_block = self.web3.eth.block_number
        
        try:
            while True:
                # Health check
                self.health_check()
                
                # Monitor new events
                current_block = self.web3.eth.block_number
                if current_block > last_block:
                    self.monitor_events(last_block + 1, current_block)
                    last_block = current_block
                
                # Calculate metrics
                self.calculate_metrics()
                
                # Sleep
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Monitoring error: {e}")


def main():
    """Main monitoring function."""
    # Load configuration
    RPC_URL = os.getenv("RPC_URL", "https://rpc.gnosischain.com")
    CONTRACT_ADDRESS = os.getenv("INSTITUTIONAL_SOLVER_ADDRESS")
    
    if not CONTRACT_ADDRESS:
        logger.error("INSTITUTIONAL_SOLVER_ADDRESS environment variable not set")
        return
    
    # Initialize Web3
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    
    if not w3.is_connected():
        logger.error("Could not connect to RPC")
        return
    
    logger.info(f"Connected to {RPC_URL}")
    
    # Load contract ABI (would need to be loaded from file)
    # For now, using placeholder
    CONTRACT_ABI = []  # Load from artifacts
    
    # Initialize monitor
    monitor = SolverMonitor(
        web3=w3,
        contract_address=CONTRACT_ADDRESS,
        contract_abi=CONTRACT_ABI
    )
    
    # Run monitoring
    monitor.run_continuous_monitoring(interval=60)


if __name__ == "__main__":
    main()
