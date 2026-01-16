# AccountAbstraction
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/SupportingModules.sol)


## Functions
### calculateFee


```solidity
function calculateFee(uint256 gasUsed, uint256 maxFeePerGas) internal pure returns (uint256);
```

### validateUserOp


```solidity
function validateUserOp(UserOperation calldata userOp, mapping(address => uint256) storage nonces)
    internal
    returns (uint256);
```

## Events
### UserOpExecuted

```solidity
event UserOpExecuted(address sender, uint256 nonce, uint256 actualGas);
```

## Errors
### InsufficientFees

```solidity
error InsufficientFees();
```

### InvalidNonce

```solidity
error InvalidNonce();
```

## Structs
### UserOperation

```solidity
struct UserOperation {
    address sender;
    uint256 nonce;
    bytes callData;
    uint256 maxFeePerGas;
    uint256 maxPriorityFeePerGas;
    bytes signature;
}
```

