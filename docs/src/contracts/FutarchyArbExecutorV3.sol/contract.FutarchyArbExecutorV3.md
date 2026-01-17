# FutarchyArbExecutorV3

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyArbExecutorV3.sol)

## Functions

### execute10

```solidity
function execute10(address[10] calldata targets, bytes[10] calldata calldatas, uint256 count) external payable;
```

### executeOne

```solidity
function executeOne(address target, bytes calldata data) external payable returns (bytes memory);
```

### sellConditional

Full SELL flow with dynamic merge and optional liquidation into plain sDAI.

Must be invoked via 7702 (so msg.sender == address(this)).

```solidity
function sellConditional(SellParams calldata p) external;
```

### \_ensureAllowance

```solidity
function _ensureAllowance(IERC20 token, address spender, uint256 need) internal;
```

### \_safeCall

```solidity
function _safeCall(address target, bytes memory data, uint256 value) internal;
```

### \_patchedCalldata

```solidity
function _patchedCalldata(
    bytes memory template,
    uint256 amountOffset,
    uint256 amountIn,
    uint256 minOutOffset,
    uint16 slippageBps
) internal pure returns (bytes memory cd);
```

### \_revertWith

```solidity
function _revertWith(bytes memory ret) private pure;
```

### receive

```solidity
receive() external payable;
```

## Events

### SellExecuted

```solidity
event SellExecuted(
    uint256 sdaiSpent,
    uint256 gnoBought,
    uint256 gnoSplit,
    uint256 sdaiYesOut,
    uint256 sdaiNoOut,
    uint256 merged,
    uint256 liqYesIn,
    uint256 liqNoIn,
    uint256 liqYesOut,
    uint256 liqNoOut,
    int256 netSdai
);
```

## Structs

### CalldataPatch

A template for an exact-in swap; the contract will patch `amountIn`
(and optionally `minOut`) at the given byte offsets before calling `target`.

```solidity
struct CalldataPatch {
    address target; // router (e.g., Swapr router)
    bytes data; // pre-encoded call with placeholders (32-byte words) for amount/minOut
    uint256 msgValue; // ETH to send (usually 0)
    uint256 amountOffset; // byte offset in `data` where uint256 amountIn sits
    uint256 minOutOffset; // byte offset where uint256 minOut sits; set to type(uint256).max to skip
    uint16 slippageBps; // if minOutOffset is used: minOut = amountIn * (10000 - bps) / 10000
}
```

### SellParams

```solidity
struct SellParams {
    // Core tokens
    IERC20 sdai; // plain sDAI
    IERC20 gno; // COMPANY token (e.g., GNO)
    IERC20 gnoYes; // COMPANY_YES
    IERC20 gnoNo; // COMPANY_NO
    IERC20 sdaiYes; // SDAI_YES
    IERC20 sdaiNo; // SDAI_NO

    // Futarchy
    IFutarchyRouter futarchyRouter;
    address proposal;

    // ---- Pluggable sDAI -> GNO leg ----
    address sdaiSwapTarget; // router (e.g., Balancer BatchRouter)
    address sdaiSwapSpender; // spender (e.g., Balancer V3 Vault)
    bytes sdaiSwapCalldata; // encoded router calldata (with exact amountIn)
    uint256 sdaiSwapMsgValue; // usually 0
    uint256 sdaiAmountInCap; // cap on sDAI spent
    uint256 minGnoOut; // min GNO expected

    // ---- Split + conditional swaps ----
    uint256 splitGnoAmount; // GNO to split (<= GNO bought)
    address yesSwapTarget; // router for COMPANY_YES -> SDAI_YES
    bytes yesSwapCalldata; // encoded exact-in swap calldata
    address noSwapTarget; // router for COMPANY_NO  -> SDAI_NO
    bytes noSwapCalldata; // encoded exact-in swap calldata
    address swapSpender; // spender for both legs
    uint256 minSdaiYesOut; // min SDAI_YES out
    uint256 minSdaiNoOut; // min SDAI_NO out

    // ---- Post-merge liquidation of leftover conditional sDAI ----
    address liqSwapSpender; // spender for both liquidation swaps (e.g., Swapr router)
    CalldataPatch liqYes; // template for SDAI_YES -> sDAI (recipient MUST be this contract)
    CalldataPatch liqNo; // template for SDAI_NO  -> sDAI (recipient MUST be this contract)

    // ---- Global constraint ----
    int256 minNetSdai; // require(end - start >= minNetSdai)
}
```
