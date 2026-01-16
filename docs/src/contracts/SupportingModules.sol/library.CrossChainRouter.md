# CrossChainRouter
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/SupportingModules.sol)


## Functions
### encodeChainMessage


```solidity
function encodeChainMessage(uint256 destChainId, address target, bytes memory data)
    internal
    pure
    returns (bytes32);
```

### routeMessage


```solidity
function routeMessage(uint256 chainId, address bridge, bytes memory message) internal;
```

## Events
### CrossChainMessage

```solidity
event CrossChainMessage(uint256 chainId, bytes32 messageHash);
```

## Errors
### InvalidChain

```solidity
error InvalidChain();
```

### BridgeFailed

```solidity
error BridgeFailed();
```

