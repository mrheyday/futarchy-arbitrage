# FutarchyBatchExecutorV2
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyBatchExecutorV2.sol)

**Title:**
FutarchyBatchExecutorV2

Implementation contract for EIP-7702 batched futarchy arbitrage operations

Redesigned to avoid dynamic arrays which generate 0xEF opcodes
This version uses a hybrid approach:
- Fixed-size arrays for common operations (up to 20 calls)
- Specialized functions for futarchy-specific operations


## Functions
### onlySelf


```solidity
modifier onlySelf() ;
```

### execute20

Execute up to 20 calls in a batch

Uses fixed-size arrays to avoid 0xEF generation


```solidity
function execute20(
    uint256 count,
    address[20] calldata targets,
    uint256[20] calldata values,
    bytes[20] calldata calldatas
) external payable onlySelf;
```
**Parameters**

|Name|Type|Description|
|----|----|-----------|
|`count`|`uint256`|Number of calls to execute (max 20)|
|`targets`|`address[20]`|Array of 20 target addresses (use address(0) for unused slots)|
|`values`|`uint256[20]`|Array of 20 ETH values|
|`calldatas`|`bytes[20]`|Array of 20 calldata|


### execute20WithResults

Execute up to 20 calls and return results


```solidity
function execute20WithResults(
    uint256 count,
    address[20] calldata targets,
    uint256[20] calldata values,
    bytes[20] calldata calldatas
) external payable onlySelf returns (bool[20] memory success, bytes[20] memory results);
```
**Parameters**

|Name|Type|Description|
|----|----|-----------|
|`count`|`uint256`|Number of calls to execute|
|`targets`|`address[20]`|Array of 20 target addresses|
|`values`|`uint256[20]`|Array of 20 ETH values|
|`calldatas`|`bytes[20]`|Array of 20 calldata|

**Returns**

|Name|Type|Description|
|----|----|-----------|
|`success`|`bool[20]`|Array of success flags|
|`results`|`bytes[20]`|Array of return data (only valid entries up to count)|


### executeBuyConditional

Specialized function for buy conditional flow (11 operations)

Optimized for the specific sequence of operations in buy flow


```solidity
function executeBuyConditional(
    address[11] calldata targets,
    uint256[11] calldata values,
    bytes[11] calldata calldatas
) external payable onlySelf returns (bytes[11] memory results);
```

### setApprovals

Set multiple token approvals


```solidity
function setApprovals(
    address[5] calldata tokens,
    address[5] calldata spenders,
    uint256[5] calldata amounts,
    uint256 count
) external onlySelf;
```
**Parameters**

|Name|Type|Description|
|----|----|-----------|
|`tokens`|`address[5]`|Array of token addresses|
|`spenders`|`address[5]`|Array of spender addresses|
|`amounts`|`uint256[5]`|Array of amounts to approve|
|`count`|`uint256`||


### _approve

Internal function to handle token approvals


```solidity
function _approve(address token, address spender, uint256 amount) internal;
```

### executeOne

Execute a single call (for simple operations)


```solidity
function executeOne(address target, uint256 value, bytes calldata data)
    external
    payable
    onlySelf
    returns (bytes memory);
```

### receive

Receive ETH


```solidity
receive() external payable;
```

## Events
### CallExecuted

```solidity
event CallExecuted(uint256 index, address target, bool success);
```

### BatchExecuted

```solidity
event BatchExecuted(uint256 callsExecuted);
```

### ApprovalSet

```solidity
event ApprovalSet(address indexed token, address indexed spender, uint256 amount);
```

## Errors
### OnlySelf

```solidity
error OnlySelf();
```

### CallFailed

```solidity
error CallFailed(uint256 index);
```

### InvalidCount

```solidity
error InvalidCount();
```

