// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/**
 * @title FutarchyBatchExecutorSimple
 * @notice Simplified implementation contract for EIP-7702 batched futarchy arbitrage operations
 * @dev This is a minimal version that avoids features that generate 0xEF opcodes
 */
contract FutarchyBatchExecutorSimple {

    // Custom errors
    error OnlySelf();
    error LengthMismatch();
    error CallFailed();

    // Events
    event CallExecuted(uint256 index, bool success);
    event BatchExecuted(uint256 callsExecuted);

    /**
     * @notice Execute a batch of calls using separate arrays
     * @dev Avoiding struct arrays which may trigger 0xEF generation
     * @param targets Array of target addresses
     * @param values Array of ETH values
     * @param calldatas Array of calldata
     */
    function execute(address[] calldata targets, uint256[] calldata values, bytes[] calldata calldatas)
        external
        payable
    {
        // Ensure the caller is the contract itself (EIP-7702 self-execution)
        if (msg.sender != address(this)) revert OnlySelf();

        // Ensure arrays have same length
        if (targets.length != values.length) revert LengthMismatch();
        if (targets.length != calldatas.length) revert LengthMismatch();

        // Execute all calls
        for (uint256 i = 0; i < targets.length;) {
            (bool success,) = targets[i].call{value: values[i]}(calldatas[i]);
            if (!success) revert CallFailed();
            emit CallExecuted(i, success);
            unchecked {
                ++i;
            }
        }

        emit BatchExecuted(targets.length);
    }

    /**
     * @notice Execute a batch of calls with results (simplified)
     * @param targets Array of target addresses
     * @param values Array of ETH values
     * @param calldatas Array of calldata
     * @return results Array of return data
     */
    function executeWithResults(address[] calldata targets, uint256[] calldata values, bytes[] calldata calldatas)
        external
        payable
        returns (bytes[] memory results)
    {
        if (msg.sender != address(this)) revert OnlySelf();
        if (targets.length != values.length) revert LengthMismatch();
        if (targets.length != calldatas.length) revert LengthMismatch();

        results = new bytes[](targets.length);

        for (uint256 i = 0; i < targets.length;) {
            (bool success, bytes memory result) = targets[i].call{value: values[i]}(calldatas[i]);
            if (!success) revert CallFailed();
            results[i] = result;
            emit CallExecuted(i, success);
            unchecked {
                ++i;
            }
        }

        emit BatchExecuted(targets.length);
    }

    /**
     * @notice Simple receive function
     */
    receive() external payable {}

}
