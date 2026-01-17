"""
Price Aggregator - Multi-source price validation

Fetches prices from multiple DEXs and detects anomalies:
- Balancer V2
- Swapr (Algebra)
- CowSwap (optional)

Provides:
- Weighted average pricing
- Anomaly detection (price deviation > threshold)
- Liquidity checks
- Price impact estimation
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from dataclasses import dataclass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.logging_config import setup_logger
from helpers.web3_setup import get_web3_instance
from helpers.balancer_helpers import get_balancer_price
from helpers.swapr_helpers import get_swapr_price

logger = setup_logger("price_aggregator")


@dataclass
class PriceSource:
    """Price from a single source"""
    source: str  # "Balancer", "Swapr", etc.
    price: Decimal
    liquidity: Decimal  # Available liquidity in base token
    timestamp: float
    is_valid: bool
    error: Optional[str] = None


@dataclass
class AggregatedPrice:
    """Aggregated price from multiple sources"""
    weighted_avg: Decimal
    median: Decimal
    min_price: Decimal
    max_price: Decimal
    spread_percent: Decimal
    sources: List[PriceSource]
    is_anomaly: bool
    recommended_price: Decimal


class PriceAggregator:
    """Aggregate prices from multiple DEXs with anomaly detection"""
    
    def __init__(
        self,
        max_spread_percent: Decimal = Decimal("5.0"),
        min_sources: int = 2,
    ):
        """
        Args:
            max_spread_percent: Max acceptable spread between sources (%)
            min_sources: Minimum number of valid sources required
        """
        self.w3 = get_web3_instance()
        self.max_spread_percent = max_spread_percent
        self.min_sources = min_sources
    
    def get_aggregated_price(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal = Decimal("1"),
    ) -> AggregatedPrice:
        """
        Get aggregated price from multiple sources.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount_in: Input amount (for price impact calculation)
        
        Returns:
            AggregatedPrice with weighted average, median, and anomaly detection
        """
        sources = []
        
        # Fetch from Balancer
        balancer_price = self._get_balancer_price(token_in, token_out, amount_in)
        if balancer_price:
            sources.append(balancer_price)
        
        # Fetch from Swapr
        swapr_price = self._get_swapr_price(token_in, token_out, amount_in)
        if swapr_price:
            sources.append(swapr_price)
        
        # TODO: Add CowSwap, Curve, etc.
        
        # Validate we have enough sources
        valid_sources = [s for s in sources if s.is_valid]
        if len(valid_sources) < self.min_sources:
            logger.warning(
                f"Insufficient price sources: {len(valid_sources)}/{self.min_sources}"
            )
        
        # Calculate aggregated metrics
        if not valid_sources:
            # Return fallback
            return AggregatedPrice(
                weighted_avg=Decimal(0),
                median=Decimal(0),
                min_price=Decimal(0),
                max_price=Decimal(0),
                spread_percent=Decimal(0),
                sources=sources,
                is_anomaly=True,
                recommended_price=Decimal(0),
            )
        
        prices = [s.price for s in valid_sources]
        liquidities = [s.liquidity for s in valid_sources]
        
        # Weighted average by liquidity
        total_liquidity = sum(liquidities)
        if total_liquidity > 0:
            weighted_avg = sum(
                p * (l / total_liquidity) for p, l in zip(prices, liquidities)
            )
        else:
            weighted_avg = sum(prices) / len(prices)
        
        # Median
        sorted_prices = sorted(prices)
        mid = len(sorted_prices) // 2
        if len(sorted_prices) % 2 == 0:
            median = (sorted_prices[mid - 1] + sorted_prices[mid]) / 2
        else:
            median = sorted_prices[mid]
        
        # Min/max
        min_price = min(prices)
        max_price = max(prices)
        
        # Spread
        if min_price > 0:
            spread_percent = ((max_price - min_price) / min_price) * 100
        else:
            spread_percent = Decimal(0)
        
        # Anomaly detection
        is_anomaly = spread_percent > self.max_spread_percent
        if is_anomaly:
            logger.warning(
                f"Price anomaly detected! Spread: {spread_percent:.2f}% "
                f"(threshold: {self.max_spread_percent}%)"
            )
        
        # Recommended price (use median if anomaly, weighted avg otherwise)
        recommended_price = median if is_anomaly else weighted_avg
        
        return AggregatedPrice(
            weighted_avg=weighted_avg,
            median=median,
            min_price=min_price,
            max_price=max_price,
            spread_percent=spread_percent,
            sources=sources,
            is_anomaly=is_anomaly,
            recommended_price=recommended_price,
        )
    
    def _get_balancer_price(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
    ) -> Optional[PriceSource]:
        """Fetch price from Balancer"""
        try:
            # TODO: Implement actual Balancer price fetch
            # For now, use placeholder
            price = Decimal("1.05")  # Mock price
            liquidity = Decimal("10000")  # Mock liquidity
            
            return PriceSource(
                source="Balancer",
                price=price,
                liquidity=liquidity,
                timestamp=self.w3.eth.get_block("latest")["timestamp"],
                is_valid=True,
            )
        except Exception as e:
            logger.error(f"Balancer price fetch failed: {e}")
            return PriceSource(
                source="Balancer",
                price=Decimal(0),
                liquidity=Decimal(0),
                timestamp=0,
                is_valid=False,
                error=str(e),
            )
    
    def _get_swapr_price(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
    ) -> Optional[PriceSource]:
        """Fetch price from Swapr"""
        try:
            # TODO: Implement actual Swapr price fetch
            # For now, use placeholder
            price = Decimal("1.03")  # Mock price
            liquidity = Decimal("5000")  # Mock liquidity
            
            return PriceSource(
                source="Swapr",
                price=price,
                liquidity=liquidity,
                timestamp=self.w3.eth.get_block("latest")["timestamp"],
                is_valid=True,
            )
        except Exception as e:
            logger.error(f"Swapr price fetch failed: {e}")
            return PriceSource(
                source="Swapr",
                price=Decimal(0),
                liquidity=Decimal(0),
                timestamp=0,
                is_valid=False,
                error=str(e),
            )
    
    def estimate_price_impact(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
    ) -> Decimal:
        """
        Estimate price impact for a trade of given size.
        
        Returns:
            Price impact as percentage (e.g., 2.5 for 2.5% impact)
        """
        # Get price for small amount (1 token)
        small_price = self.get_aggregated_price(token_in, token_out, Decimal("1"))
        
        # Get price for actual trade amount
        large_price = self.get_aggregated_price(token_in, token_out, amount_in)
        
        if small_price.recommended_price == 0:
            return Decimal(0)
        
        # Calculate impact
        impact = abs(
            (large_price.recommended_price - small_price.recommended_price)
            / small_price.recommended_price
        ) * 100
        
        return impact
    
    def check_sufficient_liquidity(
        self,
        token_in: str,
        token_out: str,
        amount_in: Decimal,
        max_impact_percent: Decimal = Decimal("2.0"),
    ) -> Tuple[bool, Decimal]:
        """
        Check if there's sufficient liquidity for trade without excessive impact.
        
        Returns:
            (is_sufficient, estimated_impact_percent)
        """
        impact = self.estimate_price_impact(token_in, token_out, amount_in)
        is_sufficient = impact <= max_impact_percent
        
        if not is_sufficient:
            logger.warning(
                f"Insufficient liquidity! Impact: {impact:.2f}% "
                f"(max: {max_impact_percent}%)"
            )
        
        return is_sufficient, impact


def main():
    """Test price aggregator"""
    aggregator = PriceAggregator(max_spread_percent=Decimal("5.0"))
    
    # Mock token addresses
    token_in = os.getenv("SDAI_TOKEN_ADDRESS", "0x0")
    token_out = os.getenv("COMPANY_TOKEN_ADDRESS", "0x0")
    
    # Get aggregated price
    result = aggregator.get_aggregated_price(token_in, token_out, Decimal("100"))
    
    print("\n" + "="*60)
    print("PRICE AGGREGATOR RESULTS")
    print("="*60)
    print(f"Weighted Average: {result.weighted_avg:.6f}")
    print(f"Median:          {result.median:.6f}")
    print(f"Min Price:       {result.min_price:.6f}")
    print(f"Max Price:       {result.max_price:.6f}")
    print(f"Spread:          {result.spread_percent:.2f}%")
    print(f"Anomaly:         {'YES ⚠️' if result.is_anomaly else 'NO ✅'}")
    print(f"Recommended:     {result.recommended_price:.6f}")
    print("\nSources:")
    for source in result.sources:
        status = "✅" if source.is_valid else "❌"
        print(f"  {status} {source.source:<12} Price: {source.price:.6f}  "
              f"Liquidity: {source.liquidity:.2f}")
    print("="*60)
    
    # Check liquidity
    sufficient, impact = aggregator.check_sufficient_liquidity(
        token_in, token_out, Decimal("100")
    )
    print(f"\nLiquidity Check: {'✅ Sufficient' if sufficient else '❌ Insufficient'}")
    print(f"Price Impact:    {impact:.2f}%")


if __name__ == "__main__":
    main()
