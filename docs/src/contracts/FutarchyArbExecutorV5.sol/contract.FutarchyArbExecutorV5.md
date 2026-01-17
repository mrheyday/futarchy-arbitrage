# FutarchyArbExecutorV5

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyArbExecutorV5.sol)

**Title:**
FutarchyArbExecutorV5 (Step 1 & 2 only)

Snapshot collateral; ensure approvals (Permit2 + Vault); execute pre-encoded Balancer BatchRouter.swapExactIn.

Expects `buy_company_ops` to be calldata for BatchRouter.swapExactIn(paths, deadline, wethIsEth, userData).
Contract must already custody the input collateral `cur` (e.g., sDAI).

## State Variables

### TOKEN_SDAI

---

## PNK Trading Constants (Gnosis)

Fixed addresses used by the PNK buy/sell helper flows.

```solidity
address internal constant TOKEN_SDAI = 0xaf204776c7245bF4147c2612BF6e5972Ee483701
```

### TOKEN_WETH

```solidity
address internal constant TOKEN_WETH = 0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1
```

### TOKEN_PNK

```solidity
address internal constant TOKEN_PNK = 0x37b60f4E9A31A64cCc0024dce7D0fD07eAA0F7B3
```

### BALANCER_VAULT

```solidity
address internal constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8
```

### SWAPR_V2_ROUTER

```solidity
address internal constant SWAPR_V2_ROUTER = 0xE43e60736b1cb4a75ad25240E2f9a62Bff65c0C0
```

### PNK_POOL_1

Balancer batchSwap GIVEN_IN route: sDAI -> WETH (multi-branch), as observed on-chain.

```solidity
bytes32 internal constant PNK_POOL_1 = 0xa91c413d8516164868f6cca19573fe38f88f5982000200000000000000000157
```

### PNK_POOL_2

```solidity
bytes32 internal constant PNK_POOL_2 = 0x7e5870ac540adfd01a213c829f2231c309623eb10002000000000000000000e9
```

### PNK_POOL_3

```solidity
bytes32 internal constant PNK_POOL_3 = 0x40d2cbc586dd8df50001cdba3f65cd4bbc32d596000200000000000000000154
```

### PNK_POOL_4

```solidity
bytes32 internal constant PNK_POOL_4 = 0x480d4f66cc41a1b6784a53a10890e5ece31d75c000020000000000000000014e
```

### PNK_POOL_5

```solidity
bytes32 internal constant PNK_POOL_5 = 0xa99fd9950b5d5dceeaf4939e221dca8ca9b938ab000100000000000000000025
```

### PNK_ASSET_2

Assets order used for the batchSwap indices.
Index mapping for convenience.

```solidity
address internal constant PNK_ASSET_2 = 0xC0d871bD13eBdf5c4ff059D8243Fb38210608bD6
```

### PNK_ASSET_4

```solidity
address internal constant PNK_ASSET_4 = 0xE0eD85F76D9C552478929fab44693E03F0899F23
```

### PNK_ASSET_5_GNO

```solidity
address internal constant PNK_ASSET_5_GNO = 0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb
```

### PNK_IDX_SDAI

```solidity
uint256 internal constant PNK_IDX_SDAI = 0
```

### PNK_IDX_WETH

```solidity
uint256 internal constant PNK_IDX_WETH = 2
```

### BALANCER_VAULT_DEADLINE

Deadlines

```solidity
uint256 internal constant BALANCER_VAULT_DEADLINE = 9007199254740991
```

### SWAPR_V2_DEADLINE

```solidity
uint256 internal constant SWAPR_V2_DEADLINE = 3510754692
```

### owner

```solidity
address public owner
```

### PERMIT2

Uniswap Permit2 (canonical)

```solidity
address internal constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3
```

### MAX_UINT160

```solidity
uint160 internal constant MAX_UINT160 = type(uint160).max
```

### MAX_UINT48

```solidity
uint48 internal constant MAX_UINT48 = type(uint48).max
```

### DEFAULT_V3_FEE

```solidity
uint24 internal constant DEFAULT_V3_FEE = 100
```

## Functions

### \_pnkAssetsOrder

Helper: assets array in the exact order expected by the PNK Balancer route

```solidity
function _pnkAssetsOrder() internal pure returns (address[] memory assets);
```

### \_pnkPoolIds

Helper: poolIds array used by the PNK Balancer route (sDAI -> WETH)

```solidity
function _pnkPoolIds() internal pure returns (bytes32[] memory poolIds);
```

### \_buyPnkWithSdai

---

## PNK Buy Flow: sDAI -> WETH (Balancer Vault, single-branch) -> PNK (Swapr)

```solidity
function _buyPnkWithSdai(uint256 amountSdaiIn, uint256 minWethOut, uint256 minPnkOut) internal;
```

### buyPnkWithSdai

```solidity
function buyPnkWithSdai(uint256 amountSdaiIn, uint256 minWethOut, uint256 minPnkOut) external onlyOwner;
```

### \_sellPnkForSdai

---

## PNK Sell Flow: PNK -> WETH (Swapr) -> sDAI (Balancer Vault)

```solidity
function _sellPnkForSdai(uint256 amountPnkIn, uint256 minWethOut, uint256 minSdaiOut) internal;
```

### sellPnkForSdai

```solidity
function sellPnkForSdai(uint256 amountPnkIn, uint256 minWethOut, uint256 minSdaiOut) external onlyOwner;
```

### sell_conditional_arbitrage_pnk

SELL complete arbitrage variant that buys PNK internally (sDAI→WETH→PNK) instead of using Balancer calldata.

Signature mirrors sell_conditional_arbitrage_balancer for compatibility; Step 2 differs only.

```solidity
function sell_conditional_arbitrage_pnk(
    bytes calldata buy_company_ops, // ignored in this variant
    address balancer_router, // ignored for Step 2 (kept for signature compatibility)
    address balancer_vault, // ignored for Step 2 (kept for signature compatibility)
    address comp, // MUST be TOKEN_PNK in this variant
    address cur,
    address futarchy_router,
    address proposal,
    address yes_comp,
    address no_comp,
    address yes_cur,
    address no_cur,
    address swapr_router,
    uint256 amount_sdai_in,
    int256 min_out_final
) external onlyOwner;
```

### buy_conditional_arbitrage_pnk

BUY complete arbitrage variant that sells PNK internally (PNK→WETH→sDAI) instead of using Balancer calldata.

Signature mirrors buy_conditional_arbitrage_balancer for compatibility; only Step 6 differs.

```solidity
function buy_conditional_arbitrage_pnk(
    address comp, // MUST be TOKEN_PNK in this variant
    address cur,
    bool yes_has_higher_price,
    address futarchy_router,
    address proposal,
    address yes_comp,
    address no_comp,
    address yes_cur,
    address no_cur,
    address yes_pool,
    address no_pool,
    address swapr_router,
    uint256 amount_sdai_in,
    int256 min_out_final
) external onlyOwner;
```

### onlyOwner

```solidity
modifier onlyOwner() ;
```

### constructor

```solidity
constructor() ;
```

### \_ensureMaxAllowance

Idempotent ERC20 max-approval (resets to 0 first if needed)

```solidity
function _ensureMaxAllowance(IERC20 token, address spender) internal;
```

### \_ensurePermit2Approvals

Ensure both ERC20->Permit2 and Permit2(owner=this)->router allowances

```solidity
function _ensurePermit2Approvals(IERC20 token, address router) internal;
```

### \_swaprExactIn

Algebra/Swapr: approve and execute exact-input single hop

```solidity
function _swaprExactIn(address swapr_router, address tokenIn, address tokenOut, uint256 amountIn, uint256 minOut)
    internal
    returns (uint256 amountOut);
```

### \_swaprExactOut

Swapr/UniswapV3: approve and execute exact-output single hop (requires fee tier)

```solidity
function _swaprExactOut(
    address swapr_router,
    address tokenIn,
    address tokenOut,
    uint24 fee,
    uint256 amountOut,
    uint256 maxIn
) internal returns (uint256 amountIn);
```

### \_poolFeeOrDefault

```solidity
function _poolFeeOrDefault(address pool) internal view returns (uint24);
```

### buy_conditional_arbitrage_balancer

Symmetric BUY: steps 1–6 already implemented; this patch adds steps 7–8.

Steps 1–3: split sDAI -> conditional collateral; buy YES/NO comps (exact-in + exact-out).
Step 4: merge comps -> COMP; Step 5–6: sell COMP -> sDAI on Balancer.
Step 7: sell remaining single-sided conditional collateral (YES_cur or NO_cur) -> cur on Swapr.
Step 8: on-chain profit check in base-collateral terms against `min_out_final`.

```solidity
function buy_conditional_arbitrage_balancer(
    bytes calldata sell_company_ops, // Balancer BatchRouter.swapExactIn (COMP -> sDAI) calldata
    address balancer_router, // BatchRouter address (expects swapExactIn)
    address balancer_vault, // Vault/V3 (optional; 0 if unused)
    address comp, // Composite token (Company)
    address cur,
    bool yes_has_higher_price,
    address futarchy_router,
    address proposal,
    address yes_comp,
    address no_comp,
    address yes_cur,
    address no_cur,
    address yes_pool,
    address no_pool,
    address swapr_router,
    uint256 amount_sdai_in,
    int256 min_out_final
) external onlyOwner;
```

### sell_conditional_arbitrage_balancer

```solidity
function sell_conditional_arbitrage_balancer(
    bytes calldata buy_company_ops,
    address balancer_router,
    address balancer_vault,
    address comp,
    address cur,
    address futarchy_router,
    address proposal,
    address yes_comp,
    address no_comp,
    address yes_cur,
    address no_cur,
    address swapr_router,
    uint256 amount_sdai_in,
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

### transferOwnership

```solidity
function transferOwnership(address newOwner) external onlyOwner;
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

### Permit2AllowanceEnsured

```solidity
event Permit2AllowanceEnsured(address indexed token, address indexed spender, uint160 amount, uint48 expiration);
```

### BalancerBuyExecuted

```solidity
event BalancerBuyExecuted(address indexed router, bytes buyOps);
```

### BalancerSellExecuted

```solidity
event BalancerSellExecuted(address indexed router, bytes sellOps);
```

### CompositeAcquired

```solidity
event CompositeAcquired(address indexed comp, uint256 amount);
```

### CompositeSplitAttempted

```solidity
event CompositeSplitAttempted(address indexed comp, uint256 amount, bool ok);
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

### ConditionalCollateralMerged

```solidity
event ConditionalCollateralMerged(
    address indexed router, address indexed proposal, address indexed collateral, uint256 amount
);
```

### ConditionalCollateralSplit

```solidity
event ConditionalCollateralSplit(
    address indexed router, address indexed proposal, address indexed collateral, uint256 amount
);
```

### ProfitVerified

```solidity
event ProfitVerified(uint256 initialBalance, uint256 finalBalance, int256 minProfit);
```
