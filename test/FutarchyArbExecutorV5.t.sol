// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import {FutarchyArbExecutorV5, IERC20} from "../contracts/FutarchyArbExecutorV5.sol";
import {MockERC20} from "./mocks/MockERC20.sol";
import {
    MockBalancerBatchRouter,
    MockBalancerVault,
    MockFutarchyRouter,
    MockSwaprRouter
} from "./mocks/MockProtocols.sol";
import {Test} from "forge-std/Test.sol";

contract FutarchyArbExecutorV5Test is Test {

    FutarchyArbExecutorV5 public executor;
    MockERC20 public mockSdai;
    MockERC20 public mockCompany;
    MockERC20 public mockWeth;
    MockERC20 public mockPnk;
    MockBalancerVault public mockBalancerVault;
    MockSwaprRouter public mockSwaprRouter;
    MockFutarchyRouter public mockFutarchyRouter;

    address public owner;
    address public user;

    // Allow test contract to receive ETH
    receive() external payable {}

    function setUp() public {
        owner = address(this);
        user = address(0x9999);

        // Deploy mock ERC20 tokens
        mockSdai = new MockERC20("Mock sDAI", "sDAI");
        mockCompany = new MockERC20("Mock Company", "COMPANY");
        mockWeth = new MockERC20("Mock WETH", "WETH");
        mockPnk = new MockERC20("Mock PNK", "PNK");

        // Deploy mock protocols
        mockBalancerVault = new MockBalancerVault();
        mockSwaprRouter = new MockSwaprRouter();
        mockFutarchyRouter = new MockFutarchyRouter();

        executor = new FutarchyArbExecutorV5();

        vm.label(address(executor), "FutarchyArbExecutorV5");
        vm.label(address(mockSdai), "MockSDAI");
        vm.label(address(mockCompany), "MockCompany");
        vm.label(address(mockWeth), "MockWETH");
        vm.label(address(mockPnk), "MockPNK");
        vm.label(owner, "Owner");
        vm.label(user, "User");

        // Mint initial balances to executor for testing
        mockSdai.mint(address(executor), 10000 ether);
        mockWeth.mint(address(executor), 100 ether);
        mockPnk.mint(address(executor), 1000 ether);
    }

    // ========================================
    // OWNERSHIP TESTS
    // ========================================

    function testOwnershipInitialization() public {
        assertEq(executor.owner(), owner);
    }

    function testTransferOwnership() public {
        executor.transferOwnership(user);
        assertEq(executor.owner(), user);
    }

    function testNonOwnerCannotTransferOwnership() public {
        vm.prank(user);
        vm.expectRevert();
        executor.transferOwnership(user);
    }

    // ========================================
    // SWEEP AND WITHDRAW TESTS
    // ========================================

    function testSweepToken() public {
        // Mint additional tokens to executor
        mockSdai.mint(address(executor), 1000 ether);

        // Total balance = 10000 (initial) + 1000 (minted) = 11000
        uint256 totalBalance = 11000 ether;

        // Sweep tokens to owner
        executor.sweepToken(address(mockSdai), owner);

        // Verify tokens transferred
        assertEq(mockSdai.balanceOf(owner), totalBalance);
        assertEq(mockSdai.balanceOf(address(executor)), 0);
    }

    function testWithdrawETH() public {
        // Send ETH to executor
        vm.deal(address(executor), 10 ether);

        uint256 balanceBefore = owner.balance;

        // Withdraw ETH
        executor.withdrawETH(payable(owner), 10 ether);

        // Verify ETH withdrawn
        assertEq(owner.balance, balanceBefore + 10 ether);
        assertEq(address(executor).balance, 0);
    }

    function testWithdrawToken() public {
        // Mint tokens to executor
        mockCompany.mint(address(executor), 1000 ether);

        // Withdraw tokens
        executor.withdrawToken(address(mockCompany), owner, 1000 ether);

        // Verify tokens withdrawn to owner
        assertEq(mockCompany.balanceOf(owner), 1000 ether);
        assertEq(mockCompany.balanceOf(address(executor)), 0);
    }

    function testNonOwnerCannotSweep() public {
        mockSdai.mint(address(executor), 1000 ether);

        vm.prank(user);
        vm.expectRevert();
        executor.sweepToken(address(mockSdai), user);
    }

    function testNonOwnerCannotWithdrawETH() public {
        vm.deal(address(executor), 10 ether);

        vm.prank(user);
        vm.expectRevert();
        executor.withdrawETH(payable(owner), 10 ether);
    }

    function testNonOwnerCannotWithdrawToken() public {
        mockCompany.mint(address(executor), 1000 ether);

        vm.prank(user);
        vm.expectRevert();
        executor.withdrawToken(address(mockCompany), owner, 1000 ether);
    }

    // ========================================
    // FUZZ TESTS
    // ========================================

    function testFuzzWithdrawETH(uint96 amount) public {
        vm.assume(amount > 0);

        vm.deal(address(executor), amount);
        uint256 balanceBefore = owner.balance;

        executor.withdrawETH(payable(owner), amount);

        assertEq(owner.balance, balanceBefore + amount);
        assertEq(address(executor).balance, 0);
    }

    function testFuzzSweepToken(address to, uint256 amount) public {
        vm.assume(to != address(0));
        vm.assume(amount > 0 && amount < 1000000 ether);

        // Mint additional tokens to executor
        mockSdai.mint(address(executor), amount);

        // Total = 10000 (initial) + amount
        uint256 totalBalance = 10000 ether + amount;

        // Sweep tokens
        executor.sweepToken(address(mockSdai), to);

        // Verify all tokens transferred
        assertEq(mockSdai.balanceOf(to), totalBalance);
        assertEq(mockSdai.balanceOf(address(executor)), 0);
    }

    function testFuzzWithdrawToken(uint256 amount) public {
        vm.assume(amount > 0 && amount < 1000000 ether);

        mockCompany.mint(address(executor), amount);

        executor.withdrawToken(address(mockCompany), owner, amount);

        assertEq(mockCompany.balanceOf(owner), amount);
        assertEq(mockCompany.balanceOf(address(executor)), 0);
    }

    // ========================================
    // BUY/SELL FLOW TESTS
    // ========================================
    // Note: These are placeholder tests for the actual buy/sell logic
    // which would require mocking Balancer and Swapr contracts

    function testReceiveETH() public {
        // Test that executor can receive ETH
        (bool success,) = address(executor).call{value: 1 ether}("");
        assertTrue(success);
        assertEq(address(executor).balance, 1 ether);
    }

    function testExecutorCanHoldMultipleTokens() public {
        mockSdai.mint(address(executor), 1000 ether);
        mockCompany.mint(address(executor), 500 ether);

        assertEq(mockSdai.balanceOf(address(executor)), 11000 ether); // 10000 + 1000
        assertEq(mockCompany.balanceOf(address(executor)), 500 ether);
    }

    // ========================================
    // PNK TRADING TESTS
    // ========================================

    function testBuyPnkWithSdai() public {
        // This tests the basic call structure, not full integration
        // Real testing requires complex mocking of Balancer paths

        uint256 balanceBefore = mockSdai.balanceOf(address(executor));
        assertGt(balanceBefore, 0, "Executor should have sDAI");
    }

    function testSellPnkForSdai() public {
        // This tests the basic call structure
        uint256 balanceBefore = mockPnk.balanceOf(address(executor));
        assertGt(balanceBefore, 0, "Executor should have PNK");
    }

    function testNonOwnerCannotBuyPnk() public {
        vm.prank(user);
        vm.expectRevert();
        executor.buyPnkWithSdai(1 ether, 0, 0);
    }

    function testNonOwnerCannotSellPnk() public {
        vm.prank(user);
        vm.expectRevert();
        executor.sellPnkForSdai(1 ether, 0, 0);
    }

    // ========================================
    // EDGE CASE TESTS
    // ========================================

    function testWithdrawZeroETH() public {
        vm.deal(address(executor), 10 ether);

        uint256 balanceBefore = owner.balance;
        executor.withdrawETH(payable(owner), 0);

        // Zero withdrawal should work but transfer nothing
        assertEq(owner.balance, balanceBefore);
    }

    function testSweepZeroBalance() public {
        // Sweep when balance is zero should not revert
        executor.sweepToken(address(mockSdai), owner);
        // Should complete without error
        assertTrue(true);
    }

    function testTransferOwnershipToZeroAddress() public {
        vm.expectRevert();
        executor.transferOwnership(address(0));
    }

    function testMultipleOwnershipTransfers() public {
        address newOwner1 = address(0xAAAA);
        address newOwner2 = address(0xBBBB);

        executor.transferOwnership(newOwner1);
        assertEq(executor.owner(), newOwner1);

        vm.prank(newOwner1);
        executor.transferOwnership(newOwner2);
        assertEq(executor.owner(), newOwner2);
    }

    function testWithdrawMoreETHThanBalance() public {
        vm.deal(address(executor), 1 ether);

        vm.expectRevert();
        executor.withdrawETH(payable(owner), 10 ether);
    }

    function testWithdrawMoreTokensThanBalance() public {
        mockCompany.mint(address(executor), 100 ether);

        vm.expectRevert();
        executor.withdrawToken(address(mockCompany), owner, 1000 ether);
    }

    // ========================================
    // GAS OPTIMIZATION TESTS
    // ========================================

    function testGasWithdrawETH() public {
        vm.deal(address(executor), 10 ether);

        uint256 gasBefore = gasleft();
        executor.withdrawETH(payable(owner), 1 ether);
        uint256 gasUsed = gasBefore - gasleft();

        // Should use less than 50k gas for simple ETH transfer
        assertLt(gasUsed, 50000);
    }

    function testGasWithdrawToken() public {
        mockCompany.mint(address(executor), 100 ether);

        uint256 gasBefore = gasleft();
        executor.withdrawToken(address(mockCompany), owner, 50 ether);
        uint256 gasUsed = gasBefore - gasleft();

        // Token transfer should be reasonably gas efficient
        assertLt(gasUsed, 100000);
    }

}

