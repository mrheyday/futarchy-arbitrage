# PredictionArbExecutorV1

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/PredictionArbExecutorV1.sol)

**Title:**
PredictionArbExecutorV1

---

## PredictionArbExecutorV1

Minimal executor for prediction-market arbitrage on conditional collateral.
Flows (owner-only):

- sell_conditional_arbitrage: split {currency} into YES/NO and sell both legs exact-in for {currency}.
- buy_conditional_arbitrage: buy YES/NO conditional {currency} exact-out (amount each) and merge back to {currency}.
  Notes:
- Price decisions are off-chain. This contract just executes the steps atomically.
- Profit guard `min_out_final` is a signed value in {currency} units (can be negative for testing).

## State Variables

### owner

```solidity
address public owner
```

### DEFAULT_V3_FEE

```solidity
uint24 internal constant DEFAULT_V3_FEE = 500
```

## Functions

### onlyOwner

```solidity
modifier onlyOwner() ;
```

### constructor

```solidity
constructor() ;
```

### transferOwnership

```solidity
function transferOwnership(address newOwner) external onlyOwner;
```

### \_ensureMaxAllowance

```solidity
function _ensureMaxAllowance(IERC20 token, address spender) internal;
```

### \_swaprExactIn

```solidity
function _swaprExactIn(address swapr_router, address tokenIn, address tokenOut, uint256 amountIn, uint256 minOut)
    internal
    returns (uint256 amountOut);
```

### \_swaprExactOut

```solidity
function _swaprExactOut(address swapr_router, address tokenIn, address tokenOut, uint256 amountOut, uint256 maxIn)
    internal
    returns (uint256 amountIn);
```

### \_poolFeeOrDefault

```solidity
function _poolFeeOrDefault(address pool) internal view returns (uint24);
```

### sell_conditional_arbitrage

```solidity
function sell_conditional_arbitrage(
    address futarchy_router,
    address proposal,
    address currency,
    address yes_currency,
    address no_currency,
    address swapr_router,
    uint256 amount_currency_in,
    int256 min_out_final
) external onlyOwner;
```

### buy_conditional_arbitrage

```solidity
function buy_conditional_arbitrage(
    address futarchy_router,
    address proposal,
    address currency,
    address yes_currency,
    address no_currency,
    address,
    /* yes_pool */ // for fee discovery (optional; 0 => default)
    address,
    /* no_pool */ // for fee discovery (optional; 0 => default)
    address swapr_router,
    uint256 amount_conditional_out,
    int256 min_out_final
) external onlyOwner;
```

### receive

```solidity
receive() external payable;
```

### withdrawToken

```solidity
function withdrawToken(IERC20 token, address to, uint256 amount) external onlyOwner;
```

### sweepToken

```solidity
function sweepToken(IERC20 token, address to) external onlyOwner;
```

### withdrawETH

```solidity
function withdrawETH(address payable to, uint256 amount) external onlyOwner;
```

## Events

### OwnershipTransferred

```solidity
event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
```

### InitialCollateralSnapshot

```solidity
event InitialCollateralSnapshot(address indexed collateral, uint256 balance);
```

### MaxAllowanceEnsured

```solidity
event MaxAllowanceEnsured(address indexed token, address indexed spender, uint256 allowance);
```

### SwaprExactInExecuted

```solidity
event SwaprExactInExecuted(
    address indexed router, address indexed tokenIn, address indexed tokenOut, uint256 amountIn, uint256 amountOut
);
```

### SwaprExactOutExecuted

```solidity
event SwaprExactOutExecuted(
    address indexed router, address indexed tokenIn, address indexed tokenOut, uint256 amountOut, uint256 amountIn
);
```

### ConditionalCollateralSplit

```solidity
event ConditionalCollateralSplit(
    address indexed router, address indexed proposal, address indexed collateral, uint256 amount
);
```

### ConditionalCollateralMerged

```solidity
event ConditionalCollateralMerged(
    address indexed router, address indexed proposal, address indexed collateral, uint256 amount
);
```

### ProfitVerified

```solidity
event ProfitVerified(uint256 initialBalance, uint256 finalBalance, int256 minProfit);
```
