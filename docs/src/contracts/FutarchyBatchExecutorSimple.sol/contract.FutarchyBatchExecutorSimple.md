# FutarchyBatchExecutorSimple

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyBatchExecutorSimple.sol)

**Title:**
FutarchyBatchExecutorSimple

Simplified implementation contract for EIP-7702 batched futarchy arbitrage operations

This is a minimal version that avoids features that generate 0xEF opcodes

## Functions

### execute

Execute a batch of calls using separate arrays

Avoiding struct arrays which may trigger 0xEF generation

```solidity
function execute(address[] calldata targets, uint256[] calldata values, bytes[] calldata calldatas)
    external
    payable;
```

**Parameters**

| Name        | Type        | Description               |
| ----------- | ----------- | ------------------------- |
| `targets`   | `address[]` | Array of target addresses |
| `values`    | `uint256[]` | Array of ETH values       |
| `calldatas` | `bytes[]`   | Array of calldata         |

### executeWithResults

Execute a batch of calls with results (simplified)

```solidity
function executeWithResults(address[] calldata targets, uint256[] calldata values, bytes[] calldata calldatas)
    external
    payable
    returns (bytes[] memory results);
```

**Parameters**

| Name        | Type        | Description               |
| ----------- | ----------- | ------------------------- |
| `targets`   | `address[]` | Array of target addresses |
| `values`    | `uint256[]` | Array of ETH values       |
| `calldatas` | `bytes[]`   | Array of calldata         |

**Returns**

| Name      | Type      | Description          |
| --------- | --------- | -------------------- |
| `results` | `bytes[]` | Array of return data |

### receive

Simple receive function

```solidity
receive() external payable;
```

## Events

### CallExecuted

```solidity
event CallExecuted(uint256 index, bool success);
```

### BatchExecuted

```solidity
event BatchExecuted(uint256 callsExecuted);
```
