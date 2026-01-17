"""
Tracing Integration Guide for Futarchy Arbitrage Bot

This guide shows how to integrate distributed tracing into bot operations.

## Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements-tracing.txt
   ```

2. Start Jaeger (optional, for visualization):
   ```bash
   docker run -d --name jaeger \
     -p 5775:5775/udp \
     -p 6831:6831/udp \
     -p 6832:6832/udp \
     -p 5778:5778 \
     -p 16686:16686 \
     -p 14250:14250 \
     -p 14268:14268 \
     -p 9411:9411 \
     jaegertracing/all-in-one:latest
   ```
   
   Access UI at: http://localhost:16686

3. Enable tracing in your bot:
   ```python
   from src.helpers.tracing import get_tracer, trace_trade_execution
   
   # Initialize at startup
   tracer = get_tracer(service_name="my-arb-bot", exporter_type="jaeger")
   
   # Trace operations
   with trace_trade_execution("BUY", amount, "yes"):
       result = execute_trade()
   ```

## Environment Variables

Configure tracing via environment:

```bash
# Enable/disable tracing
export TRACING_ENABLED=true

# Exporter type: console, jaeger, otlp
export OTEL_EXPORTER=jaeger

# Jaeger configuration
export JAEGER_HOST=localhost
export JAEGER_PORT=14250

# OTLP configuration (production)
export OTLP_ENDPOINT=http://otel-collector:4317

# Environment tags
export ENVIRONMENT=production
export HOSTNAME=bot-node-1
```

## Integration Examples

### 1. EIP-7702 Bot Tracing

```python
from src.helpers.tracing import (
    get_tracer,
    trace_trade_execution,
    trace_contract_call,
    trace_external_api,
    trace_event,
)

# Initialize once at bot startup
tracer = get_tracer(service_name="eip7702-bot")

def execute_eip7702_buy(amount: Decimal, cheaper_token: str):
    # Trace entire trade flow
    with trace_trade_execution("BUY", amount, cheaper_token, flow_type="eip7702"):
        
        # Trace price check
        with tracer.start_span("price_check"):
            balancer_price = get_balancer_price()
            ideal_price = get_ideal_price()
            trace_event("prices_fetched", 
                       balancer=str(balancer_price),
                       ideal=str(ideal_price))
        
        # Trace Tenderly simulation
        with trace_external_api("tenderly", "simulate"):
            simulation = simulate_bundle(bundle)
            trace_event("simulation_result", 
                       success=simulation["success"],
                       gas=simulation["gas_used"])
        
        # Trace EIP-7702 bundle creation
        with tracer.start_span("build_bundle"):
            bundle = build_eip7702_bundle(...)
            trace_event("bundle_created", tx_count=len(bundle))
        
        # Trace contract execution
        with trace_contract_call("FutarchyArbExecutorV5", "buyConditionalArbitrage"):
            tx_hash = send_bundle(bundle)
            trace_event("transaction_sent", tx_hash=tx_hash)
        
        return tx_hash
```

### 2. Sequential Bot Tracing

```python
from src.helpers.tracing import trace_trade_execution, trace_contract_call

def execute_sequential_sell(amount: Decimal):
    with trace_trade_execution("SELL", amount, "yes", flow_type="sequential"):
        
        # Step 1: Buy on Balancer
        with trace_contract_call("Balancer", "swap"):
            company_amount = balancer_buy(amount)
            trace_event("balancer_swap_complete", amount=str(company_amount))
        
        # Step 2: Split position
        with trace_contract_call("FutarchyRouter", "splitPosition"):
            split_tx = split_position(company_amount)
            trace_event("position_split", tx_hash=split_tx)
        
        # Step 3: Sell conditionals on Swapr
        with trace_contract_call("Swapr", "exactInputSingle"):
            yes_out = swap_yes_token(yes_amount)
            no_out = swap_no_token(no_amount)
            trace_event("conditionals_sold", 
                       yes_out=str(yes_out),
                       no_out=str(no_out))
        
        # Step 4: Merge sDAI
        with trace_contract_call("FutarchyRouter", "mergePositions"):
            merge_tx = merge_sdai(yes_out, no_out)
            trace_event("sdai_merged", tx_hash=merge_tx)
        
        return merge_tx
```

### 3. Prediction Market Tracing

```python
from src.helpers.tracing import trace_trade_execution, trace_price_check

def check_prediction_arbitrage():
    with trace_price_check("prediction_market"):
        yes_price = get_yes_price()
        no_price = get_no_price()
        sum_price = yes_price + no_price
        
        trace_event("price_sum_check",
                   yes=str(yes_price),
                   no=str(no_price),
                   sum=str(sum_price),
                   threshold="1.0")
        
        if sum_price > Decimal("1.02"):
            with trace_trade_execution("PREDICTION_ARB", Decimal("0"), "both"):
                result = execute_prediction_arb()
                trace_event("arbitrage_executed", profit=str(result["profit"]))
```

### 4. Auto-Instrumentation

Enable automatic tracing for HTTP and Web3:

```python
from src.helpers.tracing import auto_instrument_requests, get_tracer

# At application startup
tracer = get_tracer(service_name="my-bot")
auto_instrument_requests()  # Auto-trace all HTTP requests

# Now all requests are automatically traced
response = requests.post("https://api.tenderly.co/...")  # Automatically traced!
```

### 5. Custom Span Attributes

```python
from src.helpers.tracing import get_tracer

tracer = get_tracer()

with tracer.start_span("custom_operation") as span:
    # Add custom attributes
    tracer.set_attributes({
        "user.wallet": wallet_address,
        "market.id": market_id,
        "strategy.type": "conditional_arb",
        "profit.target": "0.05",
    })
    
    # Execute operation
    result = do_something()
    
    # Add result attributes
    tracer.set_attributes({
        "result.success": result["success"],
        "result.profit": str(result["profit"]),
    })
```

### 6. Error Tracing

```python
from src.helpers.tracing import trace_error

try:
    with tracer.start_span("risky_operation"):
        result = execute_trade()
except Exception as e:
    trace_error(e)  # Records exception in span
    logger.error(f"Trade failed: {e}")
    raise
```

### 7. Function Decorator

```python
from src.helpers.tracing import get_tracer

tracer = get_tracer()

@tracer.trace_function("calculate_ideal_price")
def calculate_ideal_price(yes_price: Decimal, no_price: Decimal, pred_price: Decimal) -> Decimal:
    # Function is automatically traced
    ideal = pred_price * yes_price + (1 - pred_price) * no_price
    return ideal

# Usage
ideal_price = calculate_ideal_price(yes, no, pred)  # Automatically creates span
```

## Trace Visualization

### Jaeger UI

1. Open http://localhost:16686
2. Select service: "futarchy-arbitrage-bot"
3. View traces by operation:
   - `trade.buy` - Buy flow traces
   - `trade.sell` - Sell flow traces
   - `external.tenderly.simulate` - Tenderly API calls
   - `contract.*.* ` - Smart contract calls

### Example Trace Hierarchy

```
trade.buy (500ms)
├── price_check (50ms)
│   ├── external.swapr.get_price (20ms)
│   └── external.balancer.get_price (30ms)
├── build_bundle (100ms)
│   ├── contract.Permit2.approve (30ms)
│   └── contract.FutarchyRouter.split (70ms)
├── external.tenderly.simulate (200ms)
└── contract.FutarchyArbExecutorV5.buyConditionalArbitrage (150ms)
```

## Production Configuration

For production, use OTLP exporter to send to observability platform:

```python
# .env.production
TRACING_ENABLED=true
OTEL_EXPORTER=otlp
OTLP_ENDPOINT=https://otel.example.com:4317
ENVIRONMENT=production
HOSTNAME=bot-01.gnosis.example.com
```

Supported platforms:
- Grafana Cloud
- Datadog APM
- New Relic
- Honeycomb
- Lightstep
- Self-hosted OpenTelemetry Collector

## Performance Impact

- Overhead: ~1-5ms per span
- Memory: ~100 bytes per span
- Batch export: Spans exported asynchronously, minimal blocking
- Sampling: Configure sampling rate for high-volume operations

## Best Practices

1. **Trace business operations, not every line**
   - ✅ Trace: trade execution, price checks, contract calls
   - ❌ Don't trace: variable assignments, simple calculations

2. **Use meaningful span names**
   - ✅ Good: `trade.buy.conditional_arbitrage`
   - ❌ Bad: `function_123`

3. **Add context via attributes**
   ```python
   tracer.set_attributes({
       "trade.amount": str(amount),
       "trade.cheaper_token": cheaper_token,
       "market.id": market_id,
   })
   ```

4. **Record events for key milestones**
   ```python
   trace_event("simulation_success", gas=gas_used)
   trace_event("transaction_sent", tx_hash=tx_hash)
   trace_event("position_merged", sdai_amount=str(amount))
   ```

5. **Always record exceptions**
   ```python
   try:
       execute_trade()
   except Exception as e:
       trace_error(e)
       raise
   ```

## Troubleshooting

### Traces not appearing in Jaeger

1. Check Jaeger is running: `docker ps | grep jaeger`
2. Check exporter config: `echo $OTEL_EXPORTER`
3. Enable console exporter for debugging: `export OTEL_EXPORTER=console`

### Performance issues

1. Reduce sampling rate:
   ```python
   from opentelemetry.sdk.trace.sampling import TraceIdRatioBased
   
   # Sample 10% of traces
   provider = TracerProvider(sampler=TraceIdRatioBased(0.1))
   ```

2. Increase batch size:
   ```python
   processor = BatchSpanProcessor(
       exporter,
       max_queue_size=10000,
       max_export_batch_size=512,
   )
   ```

### Missing dependencies

```bash
# Install all tracing dependencies
pip install -r requirements-tracing.txt

# Or install individually
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-exporter-jaeger
```

## Migration Guide

### From print() to tracing

Before:
```python
print(f"Starting trade: {side} {amount}")
result = execute_trade()
print(f"Trade complete: {result['tx_hash']}")
```

After:
```python
with trace_trade_execution(side, amount, cheaper_token):
    trace_event("trade_started", side=side, amount=str(amount))
    result = execute_trade()
    trace_event("trade_complete", tx_hash=result['tx_hash'])
```

### From logging to tracing

Keep both! Logging for text output, tracing for distributed context:

```python
logger.info(f"Executing {side} trade for {amount} sDAI")

with trace_trade_execution(side, amount, cheaper_token):
    # Trace provides distributed context and timing
    result = execute_trade()
    
logger.info(f"Trade completed: {result['tx_hash']}")
```

## Next Steps

1. ✅ Install tracing dependencies
2. ✅ Start Jaeger locally (optional)
3. ✅ Add tracing to one bot file (e.g., `eip7702_bot.py`)
4. ✅ Test with console exporter
5. ✅ View traces in Jaeger UI
6. ✅ Add tracing to remaining bots
7. ✅ Configure production OTLP exporter
