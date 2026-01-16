# IFutarchyRouter
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/PredictionArbExecutorV1.sol)


## Functions
### splitPosition

Split base collateral `token` into conditional YES/NO for `proposal`.


```solidity
function splitPosition(address proposal, address token, uint256 amount) external;
```

### mergePositions

Merge conditional collateral (YES/NO) back into base collateral `token` for `proposal`.
Transfers both conditional legs from `msg.sender` and mints `token`.


```solidity
function mergePositions(address proposal, address token, uint256 amount) external;
```

