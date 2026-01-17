"""
Logging Configuration for Futarchy Arbitrage Bot

Provides structured logging with:
- Timestamps
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File rotation (1 file per day)
- Separate error log
- Console and file handlers
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from typing import Optional
from datetime import datetime


# Log directory
LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log formats
DETAILED_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    console: bool = True,
    detailed: bool = False,
) -> logging.Logger:
    """
    Setup a logger with console and file handlers.
    
    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file name (defaults to name.log)
        console: Whether to log to console
        detailed: Whether to use detailed format (includes file/line)
    
    Returns:
        Configured logger instance
    
    Example:
        >>> logger = setup_logger("arbitrage_bot", level=logging.DEBUG)
        >>> logger.info("Starting arbitrage check")
        >>> logger.debug("Price: 1.05 sDAI")
        >>> logger.error("Trade failed", exc_info=True)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Choose format
    log_format = DETAILED_FORMAT if detailed else SIMPLE_FORMAT
    formatter = logging.Formatter(log_format, datefmt=DATE_FORMAT)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler with daily rotation
    if log_file is None:
        log_file = f"{name}.log"
    
    file_path = LOG_DIR / log_file
    file_handler = TimedRotatingFileHandler(
        file_path,
        when="midnight",
        interval=1,
        backupCount=30,  # Keep 30 days of logs
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Separate error log
    error_path = LOG_DIR / f"{name}_errors.log"
    error_handler = RotatingFileHandler(
        error_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(DETAILED_FORMAT, datefmt=DATE_FORMAT))
    logger.addHandler(error_handler)
    
    return logger


def setup_trade_logger(bot_name: str) -> logging.Logger:
    """
    Setup logger specifically for trade execution.
    Logs all trades to a dedicated file for audit trail.
    
    Args:
        bot_name: Name of the bot (e.g., "eip7702_bot")
    
    Returns:
        Logger configured for trade logging
    """
    logger_name = f"trade_{bot_name}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    
    if logger.handlers:
        return logger
    
    # Trade-specific format
    trade_format = "%(asctime)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(trade_format, datefmt=DATE_FORMAT)
    
    # Trade log file (never rotates, keep full history)
    trade_path = LOG_DIR / f"trades_{bot_name}_{datetime.now().strftime('%Y%m')}.log"
    trade_handler = logging.FileHandler(trade_path, encoding="utf-8")
    trade_handler.setLevel(logging.INFO)
    trade_handler.setFormatter(formatter)
    logger.addHandler(trade_handler)
    
    # Also log to console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger


def log_trade(
    logger: logging.Logger,
    side: str,
    amount: float,
    profit: float,
    gas_cost: float,
    tx_hash: Optional[str] = None,
    success: bool = True,
):
    """
    Log a trade in structured format.
    
    Args:
        logger: Trade logger instance
        side: "BUY" or "SELL"
        amount: Trade amount in sDAI
        profit: Profit in sDAI (negative for loss)
        gas_cost: Gas cost in ETH
        tx_hash: Transaction hash
        success: Whether trade succeeded
    """
    status = "SUCCESS" if success else "FAILED"
    msg = (
        f"{status} | {side} | Amount: {amount:.4f} sDAI | "
        f"Profit: {profit:.4f} sDAI | Gas: {gas_cost:.6f} ETH"
    )
    if tx_hash:
        msg += f" | TX: {tx_hash}"
    
    if success:
        logger.info(msg)
    else:
        logger.error(msg)


def log_price_check(
    logger: logging.Logger,
    balancer_price: float,
    ideal_price: float,
    spread: float,
    profitable: bool,
):
    """
    Log a price check in structured format.
    
    Args:
        logger: Logger instance
        balancer_price: Price on Balancer
        ideal_price: Synthetic ideal price from Swapr
        spread: Price spread (%)
        profitable: Whether arbitrage is profitable
    """
    msg = (
        f"PRICE CHECK | Balancer: {balancer_price:.6f} | "
        f"Ideal: {ideal_price:.6f} | Spread: {spread:.2f}% | "
        f"{'PROFITABLE' if profitable else 'NOT PROFITABLE'}"
    )
    logger.debug(msg)


# Pre-configured loggers for common use cases
def get_bot_logger(bot_name: str, debug: bool = False) -> logging.Logger:
    """Get logger for bot operations."""
    level = logging.DEBUG if debug else logging.INFO
    return setup_logger(f"bot_{bot_name}", level=level, detailed=debug)


def get_executor_logger() -> logging.Logger:
    """Get logger for executor operations."""
    return setup_logger("executor", level=logging.INFO, detailed=True)


def get_helper_logger(module_name: str) -> logging.Logger:
    """Get logger for helper modules."""
    return setup_logger(f"helper_{module_name}", level=logging.DEBUG, detailed=True)


# Example usage
if __name__ == "__main__":
    # Test logging
    logger = setup_logger("test_bot", level=logging.DEBUG)
    trade_logger = setup_trade_logger("test_bot")
    
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    log_trade(
        trade_logger,
        side="BUY",
        amount=100.0,
        profit=5.5,
        gas_cost=0.001,
        tx_hash="0x123abc",
        success=True,
    )
    
    log_price_check(
        logger,
        balancer_price=1.05,
        ideal_price=1.00,
        spread=5.0,
        profitable=True,
    )
    
    print(f"Logs written to: {LOG_DIR}")
