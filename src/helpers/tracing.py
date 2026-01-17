"""
Distributed Tracing for Futarchy Arbitrage Bot

OpenTelemetry-based tracing for tracking operations across:
- Trade execution flows (buy/sell)
- Contract interactions
- External API calls (Tenderly, Swapr, Balancer)
- EIP-7702 bundle creation
- Prediction market arbitrage

Installation:
    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger

Optional exporters:
    pip install opentelemetry-exporter-otlp  # For OTLP/gRPC
    pip install opentelemetry-instrumentation-requests  # Auto-instrument HTTP
    pip install opentelemetry-instrumentation-web3  # Auto-instrument web3.py
"""

import os
import logging
from contextlib import contextmanager
from functools import wraps
from typing import Optional, Dict, Any, Callable
from decimal import Decimal
from datetime import datetime

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
    )
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME
    from opentelemetry.trace import Status, StatusCode
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False

logger = logging.getLogger(__name__)


class TracingClient:
    """
    Distributed tracing client for bot operations
    
    Supports multiple exporters:
    - Jaeger (default on localhost:14250)
    - Console (stdout, for debugging)
    - OTLP (for production observability platforms)
    
    Attributes:
        tracer: OpenTelemetry tracer instance
        enabled: Whether tracing is active
    """
    
    def __init__(
        self,
        service_name: str = "futarchy-arbitrage-bot",
        exporter_type: str = "console",  # console, jaeger, otlp
        jaeger_host: str = "localhost",
        jaeger_port: int = 14250,
        otlp_endpoint: Optional[str] = None,
        enabled: bool = True,
    ):
        self.service_name = service_name
        self.enabled = enabled and OTEL_AVAILABLE
        
        if not OTEL_AVAILABLE:
            logger.warning(
                "OpenTelemetry not installed. Tracing disabled. "
                "Install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger"
            )
            self.tracer = None
            return
        
        # Setup resource
        resource = Resource(attributes={
            SERVICE_NAME: service_name,
            "deployment.environment": os.getenv("ENVIRONMENT", "development"),
            "host.name": os.getenv("HOSTNAME", "local"),
        })
        
        # Setup tracer provider
        provider = TracerProvider(resource=resource)
        
        # Configure exporter
        if exporter_type == "jaeger":
            exporter = JaegerExporter(
                agent_host_name=jaeger_host,
                agent_port=jaeger_port,
            )
            logger.info(f"Jaeger exporter configured: {jaeger_host}:{jaeger_port}")
        elif exporter_type == "otlp":
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint or "http://localhost:4317")
                logger.info(f"OTLP exporter configured: {otlp_endpoint}")
            except ImportError:
                logger.warning("OTLP exporter not installed, falling back to console")
                exporter = ConsoleSpanExporter()
        else:
            exporter = ConsoleSpanExporter()
            logger.info("Console exporter configured (stdout)")
        
        # Add span processor
        provider.add_span_processor(BatchSpanProcessor(exporter))
        
        # Set global tracer provider
        trace.set_tracer_provider(provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        logger.info(f"Tracing enabled for service: {service_name}")
    
    @contextmanager
    def start_span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Start a new span with context manager
        
        Args:
            name: Span name (e.g., "buy_conditional_tokens")
            attributes: Optional attributes to attach to span
        
        Yields:
            Span instance
        
        Example:
            with tracing.start_span("balancer_swap", {"amount": "100.0"}):
                result = do_swap()
        """
        if not self.enabled or not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(name) as span:
            if attributes:
                # Convert all values to strings for attributes
                safe_attrs = {k: str(v) for k, v in attributes.items()}
                span.set_attributes(safe_attrs)
            
            try:
                yield span
            except Exception as e:
                span.set_status(Status(StatusCode.ERROR, str(e)))
                span.record_exception(e)
                raise
    
    def trace_function(self, span_name: Optional[str] = None):
        """
        Decorator to automatically trace a function
        
        Args:
            span_name: Optional custom span name (defaults to function name)
        
        Example:
            @tracing.trace_function()
            def execute_trade(amount: Decimal):
                ...
        """
        def decorator(func: Callable) -> Callable:
            name = span_name or f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                with self.start_span(name):
                    return func(*args, **kwargs)
            
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                with self.start_span(name):
                    return await func(*args, **kwargs)
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add an event to the current span
        
        Args:
            name: Event name
            attributes: Event attributes
        """
        if not self.enabled:
            return
        
        span = trace.get_current_span()
        if span.is_recording():
            safe_attrs = {k: str(v) for k, v in (attributes or {}).items()}
            span.add_event(name, attributes=safe_attrs)
    
    def set_attributes(self, attributes: Dict[str, Any]):
        """Set attributes on current span"""
        if not self.enabled:
            return
        
        span = trace.get_current_span()
        if span.is_recording():
            safe_attrs = {k: str(v) for k, v in attributes.items()}
            span.set_attributes(safe_attrs)
    
    def record_exception(self, exception: Exception):
        """Record an exception on current span"""
        if not self.enabled:
            return
        
        span = trace.get_current_span()
        if span.is_recording():
            span.record_exception(exception)
            span.set_status(Status(StatusCode.ERROR, str(exception)))


# Global tracing client (lazy initialization)
_global_tracer: Optional[TracingClient] = None


def get_tracer(
    service_name: str = "futarchy-arbitrage-bot",
    exporter_type: Optional[str] = None,
) -> TracingClient:
    """
    Get global tracing client (singleton)
    
    Args:
        service_name: Service name for traces
        exporter_type: Exporter type (console, jaeger, otlp)
    
    Returns:
        TracingClient instance
    """
    global _global_tracer
    
    if _global_tracer is None:
        # Read config from environment
        exporter = exporter_type or os.getenv("OTEL_EXPORTER", "console")
        jaeger_host = os.getenv("JAEGER_HOST", "localhost")
        jaeger_port = int(os.getenv("JAEGER_PORT", "14250"))
        otlp_endpoint = os.getenv("OTLP_ENDPOINT")
        enabled = os.getenv("TRACING_ENABLED", "true").lower() == "true"
        
        _global_tracer = TracingClient(
            service_name=service_name,
            exporter_type=exporter,
            jaeger_host=jaeger_host,
            jaeger_port=jaeger_port,
            otlp_endpoint=otlp_endpoint,
            enabled=enabled,
        )
    
    return _global_tracer


# ==================== Trade-Specific Tracing ====================

@contextmanager
def trace_trade_execution(
    side: str,
    amount: Decimal,
    cheaper_token: str,
    flow_type: str = "eip7702",  # eip7702, sequential
):
    """
    Trace a complete trade execution
    
    Args:
        side: "BUY" or "SELL"
        amount: Trade amount in sDAI
        cheaper_token: "yes" or "no"
        flow_type: Execution type
    
    Example:
        with trace_trade_execution("BUY", Decimal("100"), "yes"):
            tx_hash = execute_buy()
    """
    tracer = get_tracer()
    
    with tracer.start_span(
        f"trade.{side.lower()}",
        attributes={
            "trade.side": side,
            "trade.amount": str(amount),
            "trade.cheaper_token": cheaper_token,
            "trade.flow_type": flow_type,
            "trade.timestamp": datetime.now().isoformat(),
        }
    ) as span:
        try:
            yield span
        except Exception as e:
            if span:
                span.set_status(Status(StatusCode.ERROR, f"Trade failed: {str(e)}"))
            raise


@contextmanager
def trace_contract_call(
    contract_name: str,
    method_name: str,
    params: Optional[Dict[str, Any]] = None,
):
    """
    Trace a smart contract call
    
    Args:
        contract_name: Contract name (e.g., "FutarchyArbExecutorV5")
        method_name: Method name (e.g., "buyConditionalArbitrage")
        params: Call parameters
    
    Example:
        with trace_contract_call("Balancer", "swap", {"amount": "100"}):
            tx = contract.functions.swap(...).transact()
    """
    tracer = get_tracer()
    
    attrs = {
        "contract.name": contract_name,
        "contract.method": method_name,
    }
    
    if params:
        for k, v in params.items():
            attrs[f"contract.params.{k}"] = str(v)
    
    with tracer.start_span(f"contract.{contract_name}.{method_name}", attributes=attrs) as span:
        yield span


@contextmanager
def trace_external_api(
    service: str,
    operation: str,
    endpoint: Optional[str] = None,
):
    """
    Trace external API call
    
    Args:
        service: Service name (e.g., "tenderly", "swapr", "balancer")
        operation: Operation name (e.g., "simulate", "get_price")
        endpoint: API endpoint URL
    
    Example:
        with trace_external_api("tenderly", "simulate", "/api/v1/simulate"):
            response = requests.post(url, json=payload)
    """
    tracer = get_tracer()
    
    attrs = {
        "external.service": service,
        "external.operation": operation,
    }
    
    if endpoint:
        attrs["external.endpoint"] = endpoint
    
    with tracer.start_span(f"external.{service}.{operation}", attributes=attrs) as span:
        yield span


@contextmanager
def trace_price_check(
    market: str,
    balancer_price: Optional[Decimal] = None,
    ideal_price: Optional[Decimal] = None,
):
    """
    Trace price check operation
    
    Args:
        market: Market identifier
        balancer_price: Price on Balancer
        ideal_price: Ideal price from Swapr
    
    Example:
        with trace_price_check("WXDAI", Decimal("1.05"), Decimal("1.00")):
            spread = calculate_spread()
    """
    tracer = get_tracer()
    
    attrs = {"price.market": market}
    
    if balancer_price:
        attrs["price.balancer"] = str(balancer_price)
    if ideal_price:
        attrs["price.ideal"] = str(ideal_price)
    
    with tracer.start_span(f"price_check.{market}", attributes=attrs) as span:
        yield span


# ==================== Helper Functions ====================

def trace_event(name: str, **attributes):
    """
    Add a trace event to the current span
    
    Args:
        name: Event name
        **attributes: Event attributes
    
    Example:
        trace_event("simulation_success", tx_hash=tx_hash, gas_used=gas)
    """
    tracer = get_tracer()
    tracer.add_event(name, attributes=attributes)


def trace_error(exception: Exception):
    """
    Record an error in the current span
    
    Args:
        exception: Exception to record
    """
    tracer = get_tracer()
    tracer.record_exception(exception)


# ==================== Auto-Instrumentation ====================

def auto_instrument_web3():
    """
    Auto-instrument web3.py for tracing
    
    Call this once at application startup to automatically trace
    all web3 RPC calls.
    """
    try:
        from opentelemetry.instrumentation.web3 import Web3Instrumentor
        Web3Instrumentor().instrument()
        logger.info("Web3 auto-instrumentation enabled")
    except ImportError:
        logger.warning("Web3 instrumentation not available. Install: opentelemetry-instrumentation-web3")


def auto_instrument_requests():
    """
    Auto-instrument requests library for tracing
    
    Call this once at application startup to automatically trace
    all HTTP requests.
    """
    try:
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        RequestsInstrumentor().instrument()
        logger.info("Requests auto-instrumentation enabled")
    except ImportError:
        logger.warning("Requests instrumentation not available. Install: opentelemetry-instrumentation-requests")


# ==================== Example Usage ====================

if __name__ == "__main__":
    import time
    
    # Initialize tracer with console exporter for demo
    tracer = get_tracer(service_name="futarchy-bot-demo", exporter_type="console")
    
    # Example 1: Manual span creation
    with tracer.start_span("example_operation", {"user": "alice"}):
        time.sleep(0.1)
        trace_event("processing_started", step=1)
        time.sleep(0.1)
        trace_event("processing_completed", step=2)
    
    # Example 2: Trade execution trace
    with trace_trade_execution("BUY", Decimal("100"), "yes"):
        time.sleep(0.2)
        trace_event("simulation_success", gas_estimate=500000)
        time.sleep(0.2)
        trace_event("transaction_sent", tx_hash="0xabc123")
    
    # Example 3: Contract call trace
    with trace_contract_call("FutarchyArbExecutorV5", "buyConditionalArbitrage", {"amount": "100"}):
        time.sleep(0.1)
        trace_event("permit2_approved")
        time.sleep(0.1)
    
    # Example 4: External API trace
    with trace_external_api("tenderly", "simulate", "/api/v1/simulate"):
        time.sleep(0.15)
        trace_event("simulation_complete", success=True)
    
    # Example 5: Decorated function
    @tracer.trace_function("custom_trade_logic")
    def execute_custom_trade(amount: Decimal):
        time.sleep(0.1)
        return {"success": True, "amount": amount}
    
    result = execute_custom_trade(Decimal("50"))
    
    print("\n✅ Tracing demo complete. Check console output above for trace spans.")
