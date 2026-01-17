// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

interface IERC20 {

    function transfer(address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);

}

/**
 * @title FutarchyArbitrageExecutorV2
 * @notice Simplified multicall contract for arbitrage execution
 * @dev Only owner can execute functions. Focuses on safety and simplicity.
 */
contract FutarchyArbitrageExecutorV2 {

    address public immutable owner;

    struct Call {
        address target;
        bytes callData;
    }

    // Custom errors
    error OnlyOwner();
    error ZeroAddress();
    error CallFailed();
    error InsufficientProfit();
    error InsufficientBalance();
    error TransferFailed();
    error EthTransferFailed();

    event ArbitrageExecuted(uint256 profit);
    event TokensWithdrawn(address indexed token, uint256 amount);

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    constructor(address _owner) {
        if (_owner == address(0)) revert ZeroAddress();
        owner = _owner;
    }

    /**
     * @notice Execute multiple calls in a single transaction
     * @param calls Array of calls to execute
     */
    function multicall(Call[] calldata calls) external onlyOwner {
        for (uint256 i = 0; i < calls.length;) {
            (bool success, bytes memory result) = calls[i].target.call(calls[i].callData);
            if (!success) {
                // If the call failed, revert with the error message
                if (result.length > 0) {
                    assembly {
                        let size := mload(result)
                        revert(add(32, result), size)
                    }
                } else {
                    revert CallFailed();
                }
            }
            unchecked {
                ++i;
            }
        }
    }

    /**
     * @notice Execute arbitrage with profit verification
     * @param calls Array of calls to execute
     * @param profitToken Token to measure profit in
     * @param minProfit Minimum required profit
     * @return profit Actual profit achieved
     */
    function executeArbitrage(Call[] calldata calls, address profitToken, uint256 minProfit)
        external
        onlyOwner
        returns (uint256 profit)
    {
        // Record initial balance
        uint256 balanceBefore = IERC20(profitToken).balanceOf(address(this));

        // Execute all calls
        for (uint256 i = 0; i < calls.length;) {
            (bool success, bytes memory result) = calls[i].target.call(calls[i].callData);
            if (!success) {
                if (result.length > 0) {
                    assembly {
                        let size := mload(result)
                        revert(add(32, result), size)
                    }
                } else {
                    revert CallFailed();
                }
            }
            unchecked {
                ++i;
            }
        }

        // Calculate profit
        uint256 balanceAfter = IERC20(profitToken).balanceOf(address(this));
        profit = balanceAfter > balanceBefore ? balanceAfter - balanceBefore : 0;

        // Verify minimum profit
        if (profit < minProfit) revert InsufficientProfit();

        // Send all profit token balance to owner
        if (balanceAfter > 0) if (!IERC20(profitToken).transfer(owner, balanceAfter)) revert TransferFailed();

        emit ArbitrageExecuted(profit);
    }

    /**
     * @notice Withdraw tokens from contract
     * @param token Token address
     * @param amount Amount to withdraw (0 = all)
     */
    function withdrawToken(address token, uint256 amount) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));

        if (amount == 0) amount = balance;
        else if (amount > balance) revert InsufficientBalance();

        if (amount > 0) {
            if (!IERC20(token).transfer(owner, amount)) revert TransferFailed();
            emit TokensWithdrawn(token, amount);
        }
    }

    /**
     * @notice Withdraw ETH from contract
     */
    function withdrawETH() external onlyOwner {
        uint256 balance = address(this).balance;
        if (balance > 0) {
            (bool success,) = payable(owner).call{value: balance}("");
            if (!success) revert EthTransferFailed();
        }
    }

    /**
     * @notice Check token balance
     * @param token Token address
     * @return Token balance
     */
    function getBalance(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }

    /**
     * @notice Approve token spending
     * @param token Token address
     * @param spender Spender address
     * @param amount Amount to approve
     */
    function approveToken(address token, address spender, uint256 amount) external onlyOwner {
        IERC20(token).approve(spender, amount);
    }

    // Accept ETH
    receive() external payable {}

}
