# IAlgebraSwapRouter

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/PredictionArbExecutorV1.sol)

Algebra/Swapr exact-in (single hop)

## Functions

### exactInputSingle

```solidity
function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
```

### exactOutputSingle

```solidity
function exactOutputSingle(ExactOutputSingleParams calldata params) external payable returns (uint256 amountIn);
```

## Structs

### ExactInputSingleParams

```solidity
struct ExactInputSingleParams {
    address tokenIn;
    address tokenOut;
    address recipient;
    uint256 deadline;
    uint256 amountIn;
    uint256 amountOutMinimum;
    uint160 limitSqrtPrice; // 0 for no limit
}
```

### ExactOutputSingleParams

Algebra exact-out (no fee param, uses limitSqrtPrice)

```solidity
struct ExactOutputSingleParams {
    address tokenIn;
    address tokenOut;
    address recipient;
    uint256 deadline;
    uint256 amountOut;
    uint256 amountInMaximum;
    uint160 limitSqrtPrice; // 0 for no limit
}
```
