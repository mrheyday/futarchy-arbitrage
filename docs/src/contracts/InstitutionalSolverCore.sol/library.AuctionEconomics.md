# AuctionEconomics

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/InstitutionalSolverCore.sol)

## Functions

### commitBid

```solidity
function commitBid(AuctionState storage auction, address solver, bytes32 commitHash) internal;
```

### revealBid

```solidity
function revealBid(AuctionState storage auction, address solver, uint256 value, bytes32 salt) internal;
```

### settleAuction

```solidity
function settleAuction(AuctionState storage auction, address[] memory solvers) internal returns (address winner);
```

## Events

### BidCommitted

```solidity
event BidCommitted(address solver, bytes32 commitHash);
```

### BidRevealed

```solidity
event BidRevealed(address solver, uint256 bidValue);
```

### AuctionSettled

```solidity
event AuctionSettled(address winner, uint256 winningBid);
```

## Errors

### InvalidBid

```solidity
error InvalidBid();
```

### AuctionClosed

```solidity
error AuctionClosed();
```

### TieBreakFailed

```solidity
error TieBreakFailed();
```

## Structs

### Bid

```solidity
struct Bid {
    bytes32 commitHash;
    uint256 revealValue;
    bool revealed;
}
```

### AuctionState

```solidity
struct AuctionState {
    mapping(address => Bid) bids;
    bool isOpen;
    address winner;
}
```
