# MonitoringTelemetry
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/SupportingModules.sol)


## Functions
### recordMetric


```solidity
function recordMetric(string memory name, uint256 value) internal;
```

### createTrace


```solidity
function createTrace(bytes memory context) internal returns (bytes32);
```

### logGasMetric


```solidity
function logGasMetric(uint256 gasUsed, string memory operation) internal;
```

## Events
### MetricRecorded

```solidity
event MetricRecorded(string metricName, uint256 value, uint256 logValue);
```

### TracePoint

```solidity
event TracePoint(bytes32 traceId, uint256 timestamp);
```

