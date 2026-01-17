# Distributed Tracing for Futarchy Arbitrage Bot

OpenTelemetry-based distributed tracing for monitoring arbitrage operations across the entire execution flow.

## Features

- **Trade Execution Tracing**: Track BUY/SELL flows end-to-end
- **Contract Call Tracing**: Monitor smart contract interactions
- **External API Tracing**: Track Tenderly, Swapr, Balancer API calls
- **Price Check Tracing**: Monitor price fetching and arbitrage opportunity detection
- **Auto-Instrumentation**: Automatically trace HTTP requests
- **Multiple Exporters**: Console, Jaeger, OTLP (production)

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements-tracing.txt
```

### 2. Start Jaeger (Optional - for UI)

```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14250:14250 \
  jaegertracing/all-in-one:latest
```

Access UI: http://localhost:16686

### 3. Enable Tracing

**Console Mode (Debugging)**
```bash
export TRACING_ENABLED=true
export OTEL_EXPORTER=console

python -m src.arbitrage_commands.eip7702_bot --amount 0.1 --dry-run
```

**Jaeger Mode (Production)**
```bash
export TRACING_ENABLED=true
export OTEL_EXPORTER=jaeger
export JAEGER_HOST=localhost
export JAEGER_PORT=14250

python -m src.arbitrage_commands.eip7702_bot --amount 0.1
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `TRACING_ENABLED` | Enable/disable tracing | `true` |
| `OTEL_EXPORTER` | Exporter type (console, jaeger, otlp) | `console` |
| `JAEGER_HOST` | Jaeger agent host | `localhost` |
| `JAEGER_PORT` | Jaeger agent port | `14250` |
| `OTLP_ENDPOINT` | OTLP collector endpoint | `http://localhost:4317` |
| `ENVIRONMENT` | Environment name (dev/staging/prod) | `development` |
| `HOSTNAME` | Host identifier | `local` |

## Usage Examples

### Basic Tracing

```python
from src.helpers.tracing import get_tracer, trace_trade_execution

tracer = get_tracer(service_name="my-bot")

with trace_trade_execution("BUY", amount, "yes"):
    result = execute_trade()
```

### Contract Call Tracing

```python
from src.helpers.tracing import trace_contract_call

with trace_contract_call("FutarchyArbExecutorV5", "buyConditionalArbitrage", {"amount": "100"}):
    tx_hash = contract.functions.buyConditionalArbitrage(...).transact()
```

### External API Tracing

```python
from src.helpers.tracing import trace_external_api

with trace_external_api("tenderly", "simulate", "/api/v1/simulate"):
    response = requests.post(url, json=payload)
```

### Price Check Tracing

```python
from src.helpers.tracing import trace_price_check

with trace_price_check("WXDAI", balancer_price, ideal_price):
    spread = calculate_spread()
```

### Adding Events

```python
from src.helpers.tracing import trace_event

trace_event("simulation_success", gas_used=500000, tx_hash="0xabc")
```

### Function Decorator

```python
@tracer.trace_function("calculate_profit")
def calculate_profit(amount, prices):
    return amount * (prices['balancer'] - prices['ideal'])
```

## Trace Hierarchy Example

```
trade.buy (500ms)
├── fetch_all_prices (150ms)
│   ├── fetch_swapr_prices (80ms)
│   └── fetch_balancer_price (70ms)
├── build_bundle (100ms)
│   ├── contract.Permit2.approve (30ms)
│   └── contract.FutarchyRouter.split (70ms)
├── external.tenderly.simulate (200ms)
└── contract.FutarchyArbExecutorV5.buyConditionalArbitrage (150ms)
```

## Bot Integration

### EIP-7702 Bot

Already integrated! See `src/arbitrage_commands/eip7702_bot.py`:

```python
from src.helpers.tracing import (
    get_tracer,
    trace_trade_execution,
    trace_price_check,
)

# Initialized at startup
tracer = get_tracer(service_name="eip7702-arb-bot")

# Price fetching traced
with trace_price_check("futarchy_market"):
    prices = fetch_all_prices(w3)

# Trade execution traced
with trace_trade_execution("BUY", amount, "yes", flow_type="eip7702"):
    result = execute_buy()
```

### Other Bots

To add tracing to other bots:

1. Import tracing utilities:
   ```python
   from src.helpers.tracing import get_tracer, trace_trade_execution
   ```

2. Initialize tracer at startup:
   ```python
   tracer = get_tracer(service_name="my-bot-name")
   ```

3. Wrap key operations:
   ```python
   with trace_trade_execution(side, amount, cheaper_token):
       execute_trade()
   ```

## Jaeger UI

### Viewing Traces

1. Open http://localhost:16686
2. Select service: `eip7702-arb-bot` (or your service name)
3. Search traces by:
   - Operation: `trade.buy`, `trade.sell`
   - Tags: `trade.amount`, `trade.cheaper_token`
   - Time range
   - Duration

### Analyzing Performance

- **Span Duration**: Identify slow operations
- **Span Hierarchy**: Understand call flow
- **Span Attributes**: Filter by trade parameters
- **Span Events**: Track milestones (simulation_success, transaction_sent)
- **Errors**: Automatically highlighted in red

## Production Deployment

### OTLP Exporter (Recommended)

For production, use OTLP to send traces to observability platforms:

```bash
# .env.production
TRACING_ENABLED=true
OTEL_EXPORTER=otlp
OTLP_ENDPOINT=https://otel-collector.example.com:4317
ENVIRONMENT=production
HOSTNAME=bot-01.gnosis
```

### Supported Platforms

- **Grafana Cloud**: OTLP endpoint from Grafana Cloud settings
- **Datadog APM**: Datadog agent with OTLP receiver
- **New Relic**: New Relic OTLP endpoint
- **Honeycomb**: Honeycomb OTLP endpoint
- **Self-Hosted**: OpenTelemetry Collector

### Sampling (High Volume)

For high-volume operations, configure sampling:

```python
from opentelemetry.sdk.trace.sampling import TraceIdRatioBased

# Sample 10% of traces
provider = TracerProvider(sampler=TraceIdRatioBased(0.1))
```

## Performance Impact

- **Overhead**: ~1-5ms per span (negligible for 100ms+ operations)
- **Memory**: ~100 bytes per span
- **Export**: Asynchronous batch export, no blocking
- **Network**: Minimal (batched, compressed)

## Troubleshooting

### No traces in Jaeger

1. Check Jaeger is running: `docker ps | grep jaeger`
2. Check exporter config: `echo $OTEL_EXPORTER`
3. Enable console exporter: `export OTEL_EXPORTER=console`
4. Check logs for OpenTelemetry warnings

### High overhead

1. Reduce span depth (trace only top-level operations)
2. Enable sampling (10-50% for high-volume)
3. Disable tracing for low-value operations

### Missing spans

1. Ensure `tracer.start_span()` is in `with` block
2. Check for exceptions that exit early
3. Verify exporter connection

## Files

| File | Description |
|------|-------------|
| `src/helpers/tracing.py` | Core tracing client |
| `requirements-tracing.txt` | Dependencies |
| `docs/TRACING_GUIDE.md` | Detailed integration guide |
| `src/arbitrage_commands/eip7702_bot.py` | Example integration |

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements-tracing.txt`
2. ✅ Test console mode: `export OTEL_EXPORTER=console`
3. ✅ Run EIP-7702 bot with tracing
4. ✅ Start Jaeger and view traces
5. ✅ Add tracing to other bots
6. ✅ Deploy with OTLP exporter to production platform

## References

- [OpenTelemetry Python Docs](https://opentelemetry.io/docs/instrumentation/python/)
- [Jaeger Documentation](https://www.jaegertracing.io/docs/)
- [OTLP Specification](https://opentelemetry.io/docs/reference/specification/protocol/otlp/)
