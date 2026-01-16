# IBalancerVault

[Git Source](https://github.com/mrheyday/futarchy-arbitrage/blob/3f6e42fea160d7850ce3871a8e0a54ee09ce7bfa/contracts/FutarchyArbExecutorV5.sol)

---

## Balancer Vault (batchSwap) – used in PNK flows

## Functions

### batchSwap

```solidity
function batchSwap(
    SwapKind kind,
    BatchSwapStep[] calldata swaps,
    address[] calldata assets,
    FundManagement calldata funds,
    int256[] calldata limits,
    uint256 deadline
) external returns (int256[] memory assetDeltas);
```

## Structs

### BatchSwapStep

```solidity
struct BatchSwapStep {
    bytes32 poolId;
    uint256 assetInIndex;
    uint256 assetOutIndex;
    uint256 amount; // amount for GIVEN_IN on the first step of each branch; 0 for subsequent chained steps
    bytes userData;
}
```

### FundManagement

```solidity
struct FundManagement {
    address sender;
    bool fromInternalBalance;
    address recipient;
    bool toInternalBalance;
}
```

## Enums

### SwapKind

```solidity
enum SwapKind {
    GIVEN_IN,
    GIVEN_OUT
}
```
