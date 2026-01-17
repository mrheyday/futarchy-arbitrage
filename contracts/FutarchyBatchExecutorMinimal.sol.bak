// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/**
 * @title FutarchyBatchExecutorMinimal
 * @notice Ultra-minimal implementation for EIP-7702 testing
 * @dev Avoids all complex features that might generate 0xEF
 */
contract FutarchyBatchExecutorMinimal {

    // Custom errors
    error OnlySelf();
    error TooManyCalls();
    error CallFailed();

    /**
     * @notice Execute up to 10 calls in a batch
     * @dev Fixed-size approach to avoid dynamic array issues
     */
    function execute10(address[10] calldata targets, bytes[10] calldata calldatas, uint256 count) external payable {
        if (msg.sender != address(this)) revert OnlySelf();
        if (count > 10) revert TooManyCalls();

        for (uint256 i = 0; i < count;) {
            if (targets[i] != address(0)) {
                (bool success,) = targets[i].call(calldatas[i]);
                if (!success) revert CallFailed();
            }
            unchecked {
                ++i;
            }
        }
    }

    /**
     * @notice Execute a single call (most minimal)
     */
    function executeOne(address target, bytes calldata data) external payable returns (bytes memory) {
        if (msg.sender != address(this)) revert OnlySelf();
        (bool success, bytes memory result) = target.call{value: msg.value}(data);
        if (!success) revert CallFailed();
        return result;
    }

    receive() external payable {}

}
