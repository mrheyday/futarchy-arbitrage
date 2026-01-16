# ComplianceModule
[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/SupportingModules.sol)


## State Variables
### KYC_VERIFIED

```solidity
uint256 constant KYC_VERIFIED = 1 << 0
```


### ACCREDITED

```solidity
uint256 constant ACCREDITED = 1 << 1
```


### SANCTIONS_CLEAR

```solidity
uint256 constant SANCTIONS_CLEAR = 1 << 2
```


### REGION_ALLOWED

```solidity
uint256 constant REGION_ALLOWED = 1 << 3
```


## Functions
### setFlags


```solidity
function setFlags(ComplianceState storage state, address entity, uint256 flags) internal;
```

### checkCompliance


```solidity
function checkCompliance(ComplianceState storage state, address entity, uint256 requiredFlags)
    internal
    view
    returns (bool);
```

## Events
### ComplianceChecked

```solidity
event ComplianceChecked(address entity, uint256 flags);
```

## Errors
### ComplianceViolation

```solidity
error ComplianceViolation();
```

## Structs
### ComplianceState

```solidity
struct ComplianceState {
    mapping(address => uint256) flags;
}
```

