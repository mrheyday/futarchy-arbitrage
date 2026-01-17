// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

contract MockBalancerVault {

    mapping(bytes32 => bool) public poolExists;

    function registerPool(bytes32 poolId) external {
        poolExists[poolId] = true;
    }

    function swap(bytes32 poolId, address, address, uint256 amountIn, uint256)
        external
        view
        returns (uint256)
    {
        require(poolExists[poolId], "Pool not registered");
        // Simple 1:1 swap for testing
        return amountIn;
    }

    function batchSwap(
        uint8,
        /*kind*/
        bytes memory,
        /*swaps*/
        address[] memory,
        /*assets*/
        bytes memory,
        /*funds*/
        int256[] memory,
        /*limits*/
        uint256 /*deadline*/
    )
        external
        pure
        returns (int256[] memory)
    {
        int256[] memory deltas = new int256[](2);
        deltas[0] = -1000; // Input
        deltas[1] = 1000; // Output
        return deltas;
    }

}

contract MockSwaprRouter {

    function exactInputSingle(
        address,
        /*tokenIn*/
        address,
        /*tokenOut*/
        address,
        /*recipient*/
        uint256,
        /*deadline*/
        uint256 amountIn,
        uint256,
        /*amountOutMinimum*/
        uint160 /*sqrtPriceLimitX96*/
    )
        external
        pure
        returns (uint256)
    {
        // Simple 1:1 swap
        return amountIn;
    }

    function exactOutputSingle(
        address,
        /*tokenIn*/
        address,
        /*tokenOut*/
        uint24,
        /*fee*/
        address,
        /*recipient*/
        uint256,
        /*deadline*/
        uint256 amountOut,
        uint256,
        /*amountInMaximum*/
        uint160 /*sqrtPriceLimitX96*/
    )
        external
        pure
        returns (uint256)
    {
        // Simple 1:1 swap
        return amountOut;
    }

}

contract MockFutarchyRouter {

    function splitPosition(
        address,
        /*proposal*/
        address,
        /*token*/
        uint256 /*amount*/
    )
        external {
        // No-op for testing
    }

    function mergePositions(
        address,
        /*proposal*/
        address,
        /*token*/
        uint256 /*amount*/
    )
        external {
        // No-op for testing
    }

}

contract MockBalancerBatchRouter {

    function swap(
        bytes memory /*ops*/
    )
        external
        pure
        returns (uint256[] memory)
    {
        uint256[] memory amounts = new uint256[](1);
        amounts[0] = 1000 ether;
        return amounts;
    }

}
