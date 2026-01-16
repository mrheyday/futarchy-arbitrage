# IBalancerBatchRouter
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyArbExecutorV5.sol)

------------------------
Balancer BatchRouter (swapExactIn) – typed interface for BUY step 6
------------------------


## Functions
### swapExactIn


```solidity
function swapExactIn(
    SwapPathExactAmountIn[] calldata paths,
    uint256 deadline,
    bool wethIsEth,
    bytes calldata userData
)
    external
    payable
    returns (uint256[] memory pathAmountsOut, address[] memory tokensOut, uint256[] memory amountsOut);
```

## Structs
### SwapPathStep

```solidity
struct SwapPathStep {
    address pool;
    address tokenOut;
    bool isBuffer;
}
```

### SwapPathExactAmountIn

```solidity
struct SwapPathExactAmountIn {
    address tokenIn;
    SwapPathStep[] steps;
    uint256 exactAmountIn;
    uint256 minAmountOut;
}
```

