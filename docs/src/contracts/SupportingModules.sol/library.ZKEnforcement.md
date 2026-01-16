# ZKEnforcement
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/SupportingModules.sol)


## Functions
### verifyProof


```solidity
function verifyProof(address verifier, bytes calldata proof) internal returns (bool);
```

## Events
### ProofVerified

```solidity
event ProofVerified(address verifier, bytes32 proofHash);
```

## Errors
### InvalidZKProof

```solidity
error InvalidZKProof();
```

