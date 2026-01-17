# FutarchyBatchExecutor

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyBatchExecutor.sol)

**Title:**
FutarchyBatchExecutor

Implementation contract for EIP-7702 batched futarchy arbitrage operations

This contract is designed to be used with EIP-7702 where an EOA delegates to this implementation
to execute multiple operations atomically in a single transaction.
The contract supports:

- Batch execution of arbitrary calls
- Token approvals management
- Specialized futarchy operations (split/merge positions)
- Integration with Swapr and Balancer protocols

## Functions

### execute

Execute a batch of calls

Can only be called by the EOA itself (when using EIP-7702)

```solidity
function execute(Call[] calldata calls) external payable;
```

**Parameters**

| Name    | Type     | Description                        |
| ------- | -------- | ---------------------------------- |
| `calls` | `Call[]` | Array of calls to execute in order |

### executeWithResults

Execute a batch of calls with return value tracking

This variant returns the results of each call for more complex arbitrage logic

```solidity
function executeWithResults(Call[] calldata calls) external payable returns (bytes[] memory results);
```

**Parameters**

| Name    | Type     | Description               |
| ------- | -------- | ------------------------- |
| `calls` | `Call[]` | Array of calls to execute |

**Returns**

| Name      | Type      | Description                         |
| --------- | --------- | ----------------------------------- |
| `results` | `bytes[]` | Array of return data from each call |

### setApprovals

Helper function to set multiple token approvals

Useful for setting up all necessary approvals before arbitrage operations

```solidity
function setApprovals(address[] calldata tokens, address[] calldata spenders, uint256[] calldata amounts) external;
```

**Parameters**

| Name       | Type        | Description                                            |
| ---------- | ----------- | ------------------------------------------------------ |
| `tokens`   | `address[]` | Array of token addresses                               |
| `spenders` | `address[]` | Array of spender addresses (must match tokens length)  |
| `amounts`  | `uint256[]` | Array of amounts to approve (must match tokens length) |

### executeBuyConditional

Execute arbitrage: Buy conditional tokens

Specialized function for the buy conditional flow

```solidity
function executeBuyConditional(
    bytes calldata /* params */
)
    external
    payable;
```

### executeSellConditional

Execute arbitrage: Sell conditional tokens

Specialized function for the sell conditional flow

```solidity
function executeSellConditional(
    bytes calldata /* params */
)
    external
    payable;
```

### \_executeBatch

Internal function to execute a batch of calls

```solidity
function _executeBatch(Call[] calldata calls) internal;
```

**Parameters**

| Name    | Type     | Description               |
| ------- | -------- | ------------------------- |
| `calls` | `Call[]` | Array of calls to execute |

### \_executeCall

Internal function to execute a single call

```solidity
function _executeCall(Call memory call) internal returns (bool success, bytes memory returnData);
```

**Parameters**

| Name   | Type   | Description         |
| ------ | ------ | ------------------- |
| `call` | `Call` | The call to execute |

**Returns**

| Name         | Type    | Description                   |
| ------------ | ------- | ----------------------------- |
| `success`    | `bool`  | Whether the call succeeded    |
| `returnData` | `bytes` | The return data from the call |

### \_approve

Internal function to approve tokens

```solidity
function _approve(address token, address spender, uint256 amount) internal;
```

**Parameters**

| Name      | Type      | Description            |
| --------- | --------- | ---------------------- |
| `token`   | `address` | The token to approve   |
| `spender` | `address` | The address to approve |
| `amount`  | `uint256` | The amount to approve  |

### receive

Fallback function to receive ETH

```solidity
receive() external payable;
```

### fallback

Fallback function for unknown function calls

```solidity
fallback() external payable;
```

## Events

### CallExecuted

```solidity
event CallExecuted(address indexed target, uint256 value, bytes data, bool success);
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

### CallFailed

```solidity
error CallFailed(uint256 index, bytes returnData);
```

### InvalidAuthority

```solidity
error InvalidAuthority();
```

### InsufficientBalance

```solidity
error InsufficientBalance();
```

## Structs

### Call

```solidity
struct Call {
    address target;
    uint256 value;
    bytes data;
}
```
