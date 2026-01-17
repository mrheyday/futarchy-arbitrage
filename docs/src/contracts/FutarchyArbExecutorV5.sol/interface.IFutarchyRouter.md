# IFutarchyRouter

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyArbExecutorV5.sol)

Futarchy router interface used for proper splits

## Functions

### splitPosition

```solidity
function splitPosition(address proposal, address token, uint256 amount) external;
```

### mergePositions

Merge conditional collateral (YES/NO) back into base collateral `token` for a given `proposal`.
Expected to transferFrom both conditional legs from `msg.sender` (this executor) and mint `token`.

```solidity
function mergePositions(address proposal, address token, uint256 amount) external;
```
