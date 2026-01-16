# TreasuryFramework
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/SupportingModules.sol)


## Functions
### deposit


```solidity
function deposit(TreasuryState storage state, address token, uint256 amount) internal;
```

### withdraw


```solidity
function withdraw(TreasuryState storage state, address token, uint256 amount, address recipient, address caller)
    internal;
```

### getScaledBalance


```solidity
function getScaledBalance(TreasuryState storage state, address token) internal view returns (uint256);
```

## Events
### FundsDeposited

```solidity
event FundsDeposited(address token, uint256 amount);
```

### FundsWithdrawn

```solidity
event FundsWithdrawn(address token, uint256 amount, address recipient);
```

## Errors
### InsufficientBalance

```solidity
error InsufficientBalance();
```

### UnauthorizedWithdrawal

```solidity
error UnauthorizedWithdrawal();
```

## Structs
### TreasuryState

```solidity
struct TreasuryState {
    mapping(address => uint256) balances;
    mapping(address => bool) authorized;
}
```

