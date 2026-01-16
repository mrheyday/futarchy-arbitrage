// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/**
 * @title PectraWrapper
 * @notice Wrapper contract to execute batched calls without EIP-7702
 * @dev This contract allows bundled execution of arbitrage operations
 */
contract PectraWrapper {

    // Events
    event CallExecuted(address indexed target, bytes data, bool success);
    event BatchExecuted(uint256 callsExecuted);

    // Owner who can execute batches
    address public immutable owner;

    // Custom errors
    error OnlyOwner();
    error CallFailed(uint256 index, bytes returnData);
    error TooManyCalls();
    error SingleCallFailed();
    error EthTransferFailed();
    error TransferFailed();

    constructor() {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        // Allow owner OR self-call (EIP-7702 delegation where address(this) == msg.sender)
        if (msg.sender != owner && msg.sender != address(this)) revert OnlyOwner();
        _;
    }

    /**
     * @notice Execute up to 10 calls in a batch
     * @dev Similar interface to FutarchyBatchExecutorMinimal but callable by owner
     */
    function execute10(address[10] calldata targets, bytes[10] calldata calldatas, uint256 count)
        external
        payable
        onlyOwner
    {
        if (count > 10) revert TooManyCalls();

        for (uint256 i = 0; i < count;) {
            if (targets[i] != address(0)) {
                (bool success, bytes memory returnData) = targets[i].call(calldatas[i]);
                if (!success) revert CallFailed(i, returnData);
                emit CallExecuted(targets[i], calldatas[i], success);
            }
            unchecked {
                ++i;
            }
        }

        emit BatchExecuted(count);
    }

    /**
     * @notice Execute a single call
     */
    function executeOne(address target, bytes calldata data) external payable onlyOwner returns (bytes memory) {
        (bool success, bytes memory result) = target.call{value: msg.value}(data);
        if (!success) revert SingleCallFailed();
        emit CallExecuted(target, data, success);
        return result;
    }

    /**
     * @notice Rescue stuck tokens
     */
    function rescueToken(address token, uint256 amount) external onlyOwner {
        if (token == address(0)) {
            (bool sent,) = payable(owner).call{value: amount}("");
            if (!sent) revert EthTransferFailed();
        } else {
            // Use low-level call to handle non-standard tokens
            (bool success,) = token.call(abi.encodeWithSignature("transfer(address,uint256)", owner, amount));
            if (!success) revert TransferFailed();
        }
    }

    receive() external payable {}

}
