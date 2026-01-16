# FutarchyArbExecutorV4
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyArbExecutorV4.sol)


## State Variables
### runner

```solidity
address public immutable runner
```


### PATCH_NONE

```solidity
uint8 constant PATCH_NONE = type(uint8).max
```


## Functions
### onlyRunner


```solidity
modifier onlyRunner() ;
```

### constructor


```solidity
constructor(address _runner) ;
```

### execute10


```solidity
function execute10(address[10] calldata targets, bytes[10] calldata calldatas, uint256 count) external payable;
```

### executeOne


```solidity
function executeOne(address target, bytes calldata data) external payable returns (bytes memory);
```

### runSell


```solidity
function runSell(SellArgs calldata a) external onlyRunner;
```

### runBuy


```solidity
function runBuy(BuyArgs calldata a) external onlyRunner;
```

### runTrade

Execute a single execute10 batch (e.g., CUR -> COMP via Balancer) with delta checks.

External only for the configured runner; internally uses the same self-call pattern as sell/buy flows.


```solidity
function runTrade(Execute10Batch calldata b) external onlyRunner returns (uint256 out);
```

### _runExecute10Checked


```solidity
function _runExecute10Checked(
    Execute10Batch calldata b,
    uint256 overrideAmountIn // 0 => use b.amountIn; non-zero => use this (e.g., mergeAmt)
)
    internal
    returns (uint256 outReceived);
```

### sell_conditional_arbitrage


```solidity
function sell_conditional_arbitrage(SellArgs calldata a) external;
```

### buy_conditional_arbitrage


```solidity
function buy_conditional_arbitrage(BuyArgs calldata a) external;
```

### _ensureAllowance


```solidity
function _ensureAllowance(IERC20 token, address spender, uint256 need) internal;
```

### _safeCall


```solidity
function _safeCall(address target, bytes memory data, uint256 value) internal;
```

### _patchedCalldata


```solidity
function _patchedCalldata(
    bytes memory template,
    uint256 amountOffset,
    uint256 amountIn,
    uint256 minOutOffset,
    uint16 slippageBps
) internal pure returns (bytes memory cd);
```

### _revertWith


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
    uint256 curSpent,
    uint256 compBought,
    uint256 compSplit,
    uint256 yesCurOut,
    uint256 noCurOut,
    uint256 mergedCur,
    uint256 liqYesIn,
    uint256 liqYesOut,
    uint256 liqNoIn,
    uint256 liqNoOut,
    int256 netCur
);
```

### BuyExecuted

```solidity
event BuyExecuted(
    uint256 curSplit,
    uint256 yesCompOut,
    uint256 noCompOut,
    uint256 mergedComp,
    uint256 compSold,
    uint256 curReceived,
    uint256 liqCompYesIn,
    uint256 liqCompYesOut,
    uint256 liqCompNoIn,
    uint256 liqCompNoOut,
    uint256 liqYesIn,
    uint256 liqYesOut,
    uint256 liqNoIn,
    uint256 liqNoOut,
    int256 netCur
);
```

### TradeExecuted

```solidity
event TradeExecuted(address indexed tokenIn, address indexed tokenOut, uint256 amountIn, uint256 amountOut);
```

## Structs
### Tokens

```solidity
struct Tokens {
    IERC20 comp; // GNO
    IERC20 cur; // sDAI
    IERC20 yesComp; // GNO_YES
    IERC20 noComp; // GNO_NO
    IERC20 yesCur; // SDAI_YES
    IERC20 noCur; // SDAI_NO
}
```

### Futarchy

```solidity
struct Futarchy {
    IFutarchyRouter router;
    address proposal;
}
```

### Pools

```solidity
struct Pools {
    address yesPool; // COMP_YES <-> CUR_YES
    address noPool; // COMP_NO  <-> CUR_NO
    address predYesPool; // CUR_YES  <-> CUR
    address predNoPool; // CUR_NO   <-> CUR
}
```

### Execute10Batch

```solidity
struct Execute10Batch {
    // Raw x10 payload
    address[10] targets;
    bytes[10] calldatas;
    uint256 count;

    // Delta checks
    address tokenIn; // must decrease exactly by amountInUsed
    address tokenOut; // must increase by >= minOutUsed
    address spender; // entity that will pull tokenIn
    uint256 amountIn; // nominal input (overridable on-chain)
    uint256 minOut; // absolute floor (optional)

    // Runtime patching of one calldata item
    uint8 patchIndex; // 0..9; use type(uint8).max to skip
    uint256 amountOffset; // byte offset of uint256 amountIn within calldatas[patchIndex]
    uint256 minOutOffset; // byte offset of uint256 minOut within calldatas[patchIndex]; set to type(uint256).max to skip
    uint16 slippageBps; // if minOut==0 && minOutOffset!=max => minOut = amountInUsed*(10000-bps)/10000
}
```

### CalldataPatch

```solidity
struct CalldataPatch {
    address target;
    bytes data;
    uint256 msgValue; // usually 0
    uint256 amountOffset; // uint256 amountIn offset
    uint256 minOutOffset; // uint256 minOut offset, or type(uint256).max
    uint16 slippageBps; // if used & minOut not prefilled
}
```

### SellArgs

```solidity
struct SellArgs {
    Tokens t;
    Futarchy f;
    Pools p; // optional; events only

    // ❶ Cross-asset leg: CUR -> COMP via execute10
    Execute10Batch buyCompanyOps;
    uint256 amountCurIn; // desired CUR spend
    uint256 minCompOut; // optional extra guard

    // ❷ Conditional COMP -> conditional CUR (exact-in, both legs)
    address yesSwapTarget;
    bytes yesSwapData;
    address noSwapTarget;
    bytes noSwapData;
    address swapSpender;
    uint256 minYesCurOut;
    uint256 minNoCurOut;

    // ❸ Leftover liquidation (CUR_YES/NO -> CUR)
    address liqSpender;
    CalldataPatch predYes;
    CalldataPatch predNo;

    // ❹ Profit constraint on CUR
    int256 minNetCur;
}
```

### BuyArgs

```solidity
struct BuyArgs {
    Tokens t;
    Futarchy f;
    Pools p; // optional; events only

    uint256 amountCurIn; // CUR to split initially

    // ❶ Conditional CUR -> conditional COMP (exact-in)
    address yesBuyTarget;
    bytes yesBuyData;
    address noBuyTarget;
    bytes noBuyData;
    address buySpender;
    uint256 minYesCompOut;
    uint256 minNoCompOut;

    // ❷ Merge COMP and sell COMP -> CUR via execute10 (amountIn patched to mergeAmt)
    Execute10Batch sellCompanyOps;

    // ❸ Optional leftover clean-up (COMP side then pred pools)
    address liqSpender;
    CalldataPatch compYesToCurYes;
    CalldataPatch compNoToCurNo;
    CalldataPatch predYes; // CUR_YES -> CUR
    CalldataPatch predNo; // CUR_NO  -> CUR

    // ❹ Profit constraint on CUR
    int256 minNetCur;
}
```

