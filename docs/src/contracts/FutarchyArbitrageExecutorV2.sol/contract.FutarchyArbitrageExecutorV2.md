# FutarchyArbitrageExecutorV2

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyArbitrageExecutorV2.sol)

**Title:**
FutarchyArbitrageExecutorV2

Simplified multicall contract for arbitrage execution

Only owner can execute functions. Focuses on safety and simplicity.

## State Variables

### owner

```solidity
address public immutable owner
```

## Functions

### onlyOwner

```solidity
modifier onlyOwner() ;
```

### constructor

```solidity
constructor(address _owner) ;
```

### multicall

Execute multiple calls in a single transaction

```solidity
function multicall(Call[] calldata calls) external onlyOwner;
```

**Parameters**

| Name    | Type     | Description               |
| ------- | -------- | ------------------------- |
| `calls` | `Call[]` | Array of calls to execute |

### executeArbitrage

Execute arbitrage with profit verification

```solidity
function executeArbitrage(Call[] calldata calls, address profitToken, uint256 minProfit)
    external
    onlyOwner
    returns (uint256 profit);
```

**Parameters**

| Name          | Type      | Description                |
| ------------- | --------- | -------------------------- |
| `calls`       | `Call[]`  | Array of calls to execute  |
| `profitToken` | `address` | Token to measure profit in |
| `minProfit`   | `uint256` | Minimum required profit    |

**Returns**

| Name     | Type      | Description            |
| -------- | --------- | ---------------------- |
| `profit` | `uint256` | Actual profit achieved |

### withdrawToken

Withdraw tokens from contract

```solidity
function withdrawToken(address token, uint256 amount) external onlyOwner;
```

**Parameters**

| Name     | Type      | Description                  |
| -------- | --------- | ---------------------------- |
| `token`  | `address` | Token address                |
| `amount` | `uint256` | Amount to withdraw (0 = all) |

### withdrawETH

Withdraw ETH from contract

```solidity
function withdrawETH() external onlyOwner;
```

### getBalance

Check token balance

```solidity
function getBalance(address token) external view returns (uint256);
```

**Parameters**

| Name    | Type      | Description   |
| ------- | --------- | ------------- |
| `token` | `address` | Token address |

**Returns**

| Name     | Type      | Description   |
| -------- | --------- | ------------- |
| `<none>` | `uint256` | Token balance |

### approveToken

Approve token spending

```solidity
function approveToken(address token, address spender, uint256 amount) external onlyOwner;
```

**Parameters**

| Name      | Type      | Description       |
| --------- | --------- | ----------------- |
| `token`   | `address` | Token address     |
| `spender` | `address` | Spender address   |
| `amount`  | `uint256` | Amount to approve |

### receive

```solidity
receive() external payable;
```

## Events

### ArbitrageExecuted

```solidity
event ArbitrageExecuted(uint256 profit);
```

### TokensWithdrawn

```solidity
event TokensWithdrawn(address indexed token, uint256 amount);
```

## Structs

### Call

```solidity
struct Call {
    address target;
    bytes callData;
}
```
