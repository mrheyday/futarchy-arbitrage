# ISwapRouterV3ExactOutput
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyArbExecutorV5.sol)


## Functions
### exactOutputSingle


```solidity
function exactOutputSingle(ExactOutputSingleParams calldata params) external payable returns (uint256 amountIn);
```

## Structs
### ExactOutputSingleParams

```solidity
struct ExactOutputSingleParams {
    address tokenIn;
    address tokenOut;
    uint24 fee;
    address recipient;
    uint256 deadline;
    uint256 amountOut;
    uint256 amountInMaximum;
    uint160 sqrtPriceLimitX96;
}
```

