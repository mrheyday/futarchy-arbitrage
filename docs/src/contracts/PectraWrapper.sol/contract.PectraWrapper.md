# PectraWrapper
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/PectraWrapper.sol)

**Title:**
PectraWrapper

Wrapper contract to execute batched calls without EIP-7702

This contract allows bundled execution of arbitrage operations


## State Variables
### owner

```solidity
address public immutable owner
```


## Functions
### constructor


```solidity
constructor() ;
```

### onlyOwner


```solidity
modifier onlyOwner() ;
```

### execute10

Execute up to 10 calls in a batch

Similar interface to FutarchyBatchExecutorMinimal but callable by owner


```solidity
function execute10(address[10] calldata targets, bytes[10] calldata calldatas, uint256 count)
    external
    payable
    onlyOwner;
```

### executeOne

Execute a single call


```solidity
function executeOne(address target, bytes calldata data) external payable onlyOwner returns (bytes memory);
```

### rescueToken

Rescue stuck tokens


```solidity
function rescueToken(address token, uint256 amount) external onlyOwner;
```

### receive


```solidity
receive() external payable;
```

## Events
### CallExecuted

```solidity
event CallExecuted(address indexed target, bytes data, bool success);
```

### BatchExecuted

```solidity
event BatchExecuted(uint256 callsExecuted);
```

## Errors
### OnlyOwner

```solidity
error OnlyOwner();
```

### CallFailed

```solidity
error CallFailed(uint256 index, bytes returnData);
```

