# SimpleEIP7702Test

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/SimpleEIP7702Test.sol)

**Title:**
SimpleEIP7702Test

Minimal implementation contract for testing EIP-7702

## Functions

### test

Simple test function

```solidity
function test() external payable;
```

### execute

Execute a single call

```solidity
function execute(address target, uint256 value, bytes calldata data) external payable returns (bytes memory);
```

## Events

### TestExecuted

```solidity
event TestExecuted(address caller, uint256 value);
```
