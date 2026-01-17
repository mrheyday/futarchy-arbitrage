# MEVProtection

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/SupportingModules.sol)

## Functions

### checkMEVEntropy

```solidity
function checkMEVEntropy(bytes32 txHash, uint256 blockNumber) internal returns (uint256 entropy);
```

### calculateBidEntropy

```solidity
function calculateBidEntropy(address bidder, uint256 bidValue) internal view returns (uint256);
```

## Events

### MEVCheckPassed

```solidity
event MEVCheckPassed(bytes32 entropyHash, uint256 entropy);
```

## Errors

### MEVDetected

```solidity
error MEVDetected();
```
