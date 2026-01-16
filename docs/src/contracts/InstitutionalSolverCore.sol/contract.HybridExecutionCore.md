# HybridExecutionCore

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/InstitutionalSolverCore.sol)

## State Variables

### owner

```solidity
address public immutable owner
```

### reentrancyGuard

```solidity
uint256 private reentrancyGuard = 1
```

### intents

```solidity
mapping(uint256 => bytes) internal intents
```

### resolvers

```solidity
mapping(uint256 => address) internal resolvers
```

### auctions

```solidity
mapping(uint256 => AuctionEconomics.AuctionState) internal auctions
```

### reputationState

```solidity
ReputationSystem.ReputationState internal reputationState
```

### zkVerifier

```solidity
address public zkVerifier
```

### paymaster

```solidity
address public paymaster
```

### flashloanProviders

```solidity
address[] public flashloanProviders
```

## Functions

### onlyOwner

```solidity
modifier onlyOwner() ;
```

### nonReentrant

```solidity
modifier nonReentrant() ;
```

### constructor

```solidity
constructor(address _zkVerifier, address _paymaster, address[] memory _providers) ;
```

### submitIntent

```solidity
function submitIntent(uint256 intentId, bytes calldata intentData) external;
```

### resolveIntent

```solidity
function resolveIntent(uint256 intentId, address solver, bytes calldata execData) external nonReentrant;
```

### batchResolve

```solidity
function batchResolve(uint256[] calldata intentIds, address[] calldata solvers) external nonReentrant;
```

### failoverRoute

```solidity
function failoverRoute(uint256 intentId, address venue) external onlyOwner;
```

### sealExecution

```solidity
function sealExecution(uint256 intentId) external view returns (bytes32 seal);
```

### openAuction

```solidity
function openAuction(uint256 auctionId) external onlyOwner;
```

### closeAuction

```solidity
function closeAuction(uint256 auctionId) external onlyOwner;
```

### commitBid

```solidity
function commitBid(uint256 auctionId, bytes32 commitHash) external;
```

### revealBid

```solidity
function revealBid(uint256 auctionId, uint256 value, bytes32 salt) external;
```

### settleAuction

```solidity
function settleAuction(uint256 auctionId, address[] memory solvers) external returns (address winner);
```

## Events

### IntentResolved

```solidity
event IntentResolved(uint256 intentId, address solver, uint256 value);
```

### BatchExecuted

```solidity
event BatchExecuted(uint256 batchId, address[] solvers);
```

## Errors

### ExecutionFailed

```solidity
error ExecutionFailed();
```

### InvalidIntent

```solidity
error InvalidIntent();
```

### NonReentrant

```solidity
error NonReentrant();
```

### Unauthorized

```solidity
error Unauthorized();
```
