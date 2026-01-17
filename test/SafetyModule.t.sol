// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import {SafetyModule} from "../contracts/SafetyModule.sol";
import {Test} from "forge-std/Test.sol";

contract SafetyModuleTest is Test {

    SafetyModule public safety;
    address public owner;
    address public user;

    function setUp() public {
        owner = address(this);
        user = address(0x1234);

        safety = new SafetyModule();

        vm.label(address(safety), "SafetyModule");
        vm.label(owner, "Owner");
        vm.label(user, "User");
    }

    function testInitialParameters() public {
        assertEq(safety.owner(), owner);
        assertEq(safety.paused(), false);
        assertEq(safety.maxSlippageBps(), 500); // 5%
        assertEq(safety.maxGasPrice(), 100 gwei);
        assertEq(safety.dailyLossLimit(), 10 ether);
        assertEq(safety.cooldownSeconds(), 60);
    }

    function testCheckTradeAllowed() public {
        // Should pass with normal parameters
        safety.checkTradeAllowed(
            100 ether, // expected
            98 ether, // min (2% slippage)
            1 ether // profit
        );
    }

    function testSlippageCircuitBreaker() public {
        // Should revert with >5% slippage
        vm.expectRevert(abi.encodeWithSignature("SlippageExceeded(uint256,uint256)", 600, 500));
        safety.checkTradeAllowed(
            100 ether, // expected
            94 ether, // min (6% slippage)
            1 ether
        );
    }

    function testGasCircuitBreaker() public {
        // Set high gas price
        vm.txGasPrice(150 gwei);

        vm.expectRevert(abi.encodeWithSignature("GasPriceTooHigh(uint256,uint256)", 150 gwei, 100 gwei));
        safety.checkTradeAllowed(100 ether, 98 ether, 1 ether);
    }

    function testDailyLossLimit() public {
        // Make losing trades up to limit
        safety.checkTradeAllowed(100 ether, 98 ether, -5 ether);

        // Wait for cooldown
        vm.warp(block.timestamp + 61);
        safety.checkTradeAllowed(100 ether, 98 ether, -5 ether);

        // Wait for cooldown
        vm.warp(block.timestamp + 61);

        // Next losing trade should trip circuit breaker
        vm.expectRevert();
        safety.checkTradeAllowed(100 ether, 98 ether, -1 ether);
    }

    function testCooldownPeriod() public {
        // First trade succeeds
        safety.checkTradeAllowed(100 ether, 98 ether, 1 ether);

        // Immediate second trade should fail
        vm.expectRevert();
        safety.checkTradeAllowed(100 ether, 98 ether, 1 ether);

        // After cooldown, should succeed
        vm.warp(block.timestamp + 61);
        safety.checkTradeAllowed(100 ether, 98 ether, 1 ether);
    }

    function testEmergencyPause() public {
        safety.emergencyPause("Market manipulation detected");

        assertTrue(safety.paused());

        vm.expectRevert(abi.encodeWithSignature("Paused()"));
        safety.checkTradeAllowed(100 ether, 98 ether, 1 ether);
    }

    function testUnpause() public {
        safety.emergencyPause("Test pause");
        safety.unpause();

        assertFalse(safety.paused());
        safety.checkTradeAllowed(100 ether, 98 ether, 1 ether);
    }

    function testUpdateParameters() public {
        safety.updateParameters(
            1000, // 10% slippage
            200 gwei, // 200 gwei gas
            20 ether, // 20 ETH loss limit
            120 // 2 min cooldown
        );

        assertEq(safety.maxSlippageBps(), 1000);
        assertEq(safety.maxGasPrice(), 200 gwei);
        assertEq(safety.dailyLossLimit(), 20 ether);
        assertEq(safety.cooldownSeconds(), 120);
    }

    function testOnlyOwnerCanPause() public {
        vm.prank(user);
        vm.expectRevert(abi.encodeWithSignature("OnlyOwner()"));
        safety.emergencyPause("Unauthorized");
    }

    function testOnlyOwnerCanUpdateParameters() public {
        vm.prank(user);
        vm.expectRevert(abi.encodeWithSignature("OnlyOwner()"));
        safety.updateParameters(1000, 200 gwei, 20 ether, 120);
    }

    function testGetSafetyStatus() public {
        (bool isPaused, uint256 timeUntil, int256 dailyPL, uint256 resetTime) = safety.getSafetyStatus();

        assertEq(isPaused, false);
        assertEq(timeUntil, 0);
        assertEq(dailyPL, 0);
        assertGt(resetTime, 0);
    }

    function testCalculateSlippage() public {
        uint256 slippage = safety.calculateSlippage(100 ether, 95 ether);
        assertEq(slippage, 500); // 5% = 500 bps

        slippage = safety.calculateSlippage(100 ether, 100 ether);
        assertEq(slippage, 0); // No slippage

        slippage = safety.calculateSlippage(100 ether, 105 ether);
        assertEq(slippage, 0); // Positive slippage = 0
    }

}
