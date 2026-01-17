// SPDX-License-Identifier: MIT
pragma solidity ^0.8.33;

import "forge-std/Script.sol";
import "../contracts/FutarchyArbExecutorV5.sol";
import "../contracts/SafetyModule.sol";
import "../contracts/PectraWrapper.sol";

/**
 * @title MultiChainDeployment
 * @notice Deploys Futarchy arbitrage contracts to Base and Polygon networks
 * 
 * Usage:
 * - Base: forge script scripts/deploy_multi_chain.sol:BaseDeployment --rpc-url $BASE_RPC_URL --broadcast
 * - Polygon: forge script scripts/deploy_multi_chain.sol:PolygonDeployment --rpc-url $POLYGON_RPC_URL --broadcast
 */

abstract contract ChainDeployment is Script {
    // Contract addresses that will be set during deployment
    address public executorV5;
    address public safetyModule;
    address public pectraWrapper;

    // Network-specific configuration (to be set by child contracts)
    address public futarchyRouter;
    address public balancerRouter;
    address public swaprRouter;
    address public owner;

    function deploy() public {
        vm.startBroadcast();

        // 1. Deploy SafetyModule
        safetyModule = address(new SafetyModule());
        console.log("SafetyModule deployed at:", safetyModule);

        // 2. Deploy PectraWrapper (EIP-7702 delegation)
        pectraWrapper = address(new PectraWrapper());
        console.log("PectraWrapper deployed at:", pectraWrapper);

        // 3. Deploy FutarchyArbExecutorV5
        executorV5 = address(new FutarchyArbExecutorV5(
            futarchyRouter,
            balancerRouter,
            swaprRouter
        ));
        console.log("FutarchyArbExecutorV5 deployed at:", executorV5);

        // 4. Transfer ownership if needed
        if (owner != address(0)) {
            FutarchyArbExecutorV5(executorV5).transferOwnership(owner);
            console.log("Ownership transferred to:", owner);
        }

        vm.stopBroadcast();

        // Log deployment summary
        logDeploymentSummary();
    }

    function logDeploymentSummary() internal view {
        console.log("\n=== Deployment Summary ===");
        console.log("SafetyModule:", safetyModule);
        console.log("PectraWrapper:", pectraWrapper);
        console.log("FutarchyArbExecutorV5:", executorV5);
        console.log("========================\n");
    }

    function setNetworkConfig(
        address _futarchyRouter,
        address _balancerRouter,
        address _swaprRouter,
        address _owner
    ) internal {
        futarchyRouter = _futarchyRouter;
        balancerRouter = _balancerRouter;
        swaprRouter = _swaprRouter;
        owner = _owner;
    }
}

/**
 * @notice Base Network Deployment
 * Chain ID: 8453
 * RPC: https://mainnet.base.org
 */
contract BaseDeployment is ChainDeployment {
    function setUp() public {
        // Base network configuration
        // Update these addresses with actual Base deployments
        address futarchyRouter = 0x1111111254fb6c44bAC0bed2854e76F90643097d; // Placeholder
        address balancerRouter = 0xBA12222222228d8Ba445958a75a0704d566BF2C8; // Placeholder
        address swaprRouter = 0x6131B5fAe19EA4f9D964eAc0408E3616eDA97B7f; // Placeholder
        address owner = msg.sender;

        setNetworkConfig(futarchyRouter, balancerRouter, swaprRouter, owner);
    }

    function run() public {
        deploy();
    }
}

/**
 * @notice Polygon Network Deployment
 * Chain ID: 137
 * RPC: https://polygon-rpc.com
 */
contract PolygonDeployment is ChainDeployment {
    function setUp() public {
        // Polygon network configuration
        // Update these addresses with actual Polygon deployments
        address futarchyRouter = 0x1111111254fb6c44bAC0bed2854e76F90643097d; // Placeholder
        address balancerRouter = 0xBA12222222228d8Ba445958a75a0704d566BF2C8; // Placeholder
        address swaprRouter = 0x6131B5fAe19EA4f9D964eAc0408E3616eDA97B7f; // Placeholder
        address owner = msg.sender;

        setNetworkConfig(futarchyRouter, balancerRouter, swaprRouter, owner);
    }

    function run() public {
        deploy();
    }
}

/**
 * @notice Testnet Deployment (for testing before mainnet)
 * Useful for Base Sepolia or Polygon Mumbai
 */
contract TestnetDeployment is ChainDeployment {
    function setUp() public {
        // Testnet configuration
        address futarchyRouter = address(0);
        address balancerRouter = address(0);
        address swaprRouter = address(0);
        address owner = msg.sender;

        setNetworkConfig(futarchyRouter, balancerRouter, swaprRouter, owner);
    }

    function run() public {
        deploy();
    }
}
