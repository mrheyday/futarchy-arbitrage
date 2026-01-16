# ReputationSystem
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/InstitutionalSolverCore.sol)


## State Variables
### MIN_REPUTATION

```solidity
uint256 internal constant MIN_REPUTATION = 100
```


### SLASH_FACTOR

```solidity
uint256 internal constant SLASH_FACTOR = 50
```


## Functions
### updateReputation


```solidity
function updateReputation(ReputationState storage state, address solver, int256 delta) internal;
```

### gateSolver


```solidity
function gateSolver(ReputationState storage state, address solver) internal view;
```

### verifyZKReputation


```solidity
function verifyZKReputation(bytes calldata proof) internal pure;
```

## Events
### ReputationUpdated

```solidity
event ReputationUpdated(address solver, int256 delta);
```

### Slashed

```solidity
event Slashed(address solver, uint256 amount);
```

## Errors
### ReputationSlash

```solidity
error ReputationSlash();
```

### InvalidProof

```solidity
error InvalidProof();
```

## Structs
### ReputationState

```solidity
struct ReputationState {
    mapping(address => int256) reputation;
}
```

