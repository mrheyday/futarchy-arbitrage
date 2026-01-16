# FutarchyBatchExecutorUltra
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyBatchExecutorUltra.sol)

**Title:**
FutarchyBatchExecutorUltra

Ultra-simple implementation that avoids all 0xEF triggers

No arrays, no loops, just sequential execution


## Functions
### onlySelf


```solidity
modifier onlySelf() ;
```

### execute2

Execute 2 calls


```solidity
function execute2(address target1, bytes calldata data1, address target2, bytes calldata data2)
    external
    payable
    onlySelf;
```

### execute3

Execute 3 calls


```solidity
function execute3(
    address target1,
    bytes calldata data1,
    address target2,
    bytes calldata data2,
    address target3,
    bytes calldata data3
) external payable onlySelf;
```

### execute5

Execute 5 calls (no loops)


```solidity
function execute5(
    address t1,
    bytes calldata d1,
    address t2,
    bytes calldata d2,
    address t3,
    bytes calldata d3,
    address t4,
    bytes calldata d4,
    address t5,
    bytes calldata d5
) external payable onlySelf;
```

### executeBuy11

Execute 11 calls for buy conditional flow


```solidity
function executeBuy11(
    address t1,
    bytes calldata d1,
    address t2,
    bytes calldata d2,
    address t3,
    bytes calldata d3,
    address t4,
    bytes calldata d4,
    address t5,
    bytes calldata d5,
    address t6,
    bytes calldata d6,
    address t7,
    bytes calldata d7,
    address t8,
    bytes calldata d8,
    address t9,
    bytes calldata d9,
    address t10,
    bytes calldata d10,
    address t11,
    bytes calldata d11
)
    external
    payable
    onlySelf
    returns (bytes memory r1, bytes memory r2, bytes memory r3, bytes memory r4, bytes memory r5, bytes memory r6);
```

### receive


```solidity
receive() external payable;
```

## Events
### Executed

```solidity
event Executed(address target);
```

