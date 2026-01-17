// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import {IERC20, PredictionArbExecutorV1} from "../contracts/PredictionArbExecutorV1.sol";
import {MockERC20} from "./mocks/MockERC20.sol";
import {MockFutarchyRouter, MockSwaprRouter} from "./mocks/MockProtocols.sol";
import {Test} from "forge-std/Test.sol";

contract PredictionArbExecutorV1Test is Test {

    PredictionArbExecutorV1 public executor;
    MockERC20 public mockSdai;
    MockERC20 public mockYesCurrency;
    MockERC20 public mockNoCurrency;
    MockSwaprRouter public mockSwaprRouter;
    MockFutarchyRouter public mockFutarchyRouter;

    address public owner;
    address public user;

    // Allow test contract to receive ETH
    receive() external payable {}

    function setUp() public {
        owner = address(this);
        user = address(0x9999);

        // Deploy mock ERC20
        mockSdai = new MockERC20("Mock sDAI", "sDAI");
        mockYesCurrency = new MockERC20("Mock YES Currency", "YES_CUR");
        mockNoCurrency = new MockERC20("Mock NO Currency", "NO_CUR");

        // Deploy mock protocols
        mockSwaprRouter = new MockSwaprRouter();
        mockFutarchyRouter = new MockFutarchyRouter();

        executor = new PredictionArbExecutorV1();

        vm.label(address(executor), "PredictionArbExecutorV1");
        vm.label(address(mockSdai), "MockSDAI");
        vm.label(address(mockYesCurrency), "MockYesCurrency");
        vm.label(address(mockNoCurrency), "MockNoCurrency");
        vm.label(owner, "Owner");
        vm.label(user, "User");

        // Mint initial balances
        mockSdai.mint(address(executor), 10000 ether);
        mockYesCurrency.mint(address(executor), 1000 ether);
        mockNoCurrency.mint(address(executor), 1000 ether);
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
    // WITHDRAW TESTS
    // ========================================

    function testWithdrawETH() public {
        vm.deal(address(executor), 5 ether);

        uint256 balanceBefore = owner.balance;
        executor.withdrawETH(payable(owner), 5 ether);

        assertEq(owner.balance, balanceBefore + 5 ether);
        assertEq(address(executor).balance, 0);
    }

    function testWithdrawToken() public {
        // Mint tokens to executor first
        mockSdai.mint(address(executor), 500 ether);

        // Withdraw tokens to owner
        executor.withdrawToken(IERC20(address(mockSdai)), owner, 500 ether);

        // Verify withdrawal (owner gets 500, executor should have 10000 initial - 500 = 9500)
        assertEq(mockSdai.balanceOf(owner), 500 ether);
        assertEq(mockSdai.balanceOf(address(executor)), 10000 ether);
    }

    function testNonOwnerCannotWithdrawETH() public {
        vm.deal(address(executor), 5 ether);

        vm.prank(user);
        vm.expectRevert();
        executor.withdrawETH(payable(owner), 5 ether);
    }

    function testNonOwnerCannotWithdrawToken() public {
        mockSdai.mint(address(executor), 500 ether);

        vm.prank(user);
        vm.expectRevert();
        executor.withdrawToken(IERC20(address(mockSdai)), owner, 500 ether);
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

    function testFuzzWithdrawToken(uint256 amount) public {
        vm.assume(amount > 0 && amount <= 10000 ether); // Can't withdraw more than initial balance

        // Withdraw from initial balance
        executor.withdrawToken(IERC20(address(mockSdai)), owner, amount);

        // Verify withdrawal
        assertEq(mockSdai.balanceOf(owner), amount);
        assertEq(mockSdai.balanceOf(address(executor)), 10000 ether - amount);
    }

    // ========================================
    // ARBITRAGE FLOW TESTS
    // ========================================
    // Note: These are placeholder tests for actual arbitrage logic
    // which would require mocking Balancer, Swapr, and Futarchy contracts

    function testReceiveETH() public {
        (bool success,) = address(executor).call{value: 1 ether}("");
        assertTrue(success);
        assertEq(address(executor).balance, 1 ether);
    }

    function testExecutorCanHoldTokens() public {
        mockSdai.mint(address(executor), 1000 ether);
        assertEq(mockSdai.balanceOf(address(executor)), 11000 ether); // 10000 + 1000
    }

    // ========================================
    // EDGE CASE TESTS
    // ========================================

    function testWithdrawZeroETH() public {
        vm.deal(address(executor), 10 ether);

        uint256 balanceBefore = owner.balance;
        executor.withdrawETH(payable(owner), 0);

        assertEq(owner.balance, balanceBefore);
    }

    function testWithdrawZeroTokens() public {
        mockSdai.mint(address(executor), 100 ether);

        uint256 balanceBefore = mockSdai.balanceOf(owner);
        executor.withdrawToken(IERC20(address(mockSdai)), owner, 0);

        assertEq(mockSdai.balanceOf(owner), balanceBefore);
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

    function testWithdrawInsufficientETH() public {
        vm.deal(address(executor), 1 ether);

        vm.expectRevert();
        executor.withdrawETH(payable(owner), 10 ether);
    }

    function testWithdrawInsufficientTokens() public {
        // Executor has 10000 ether initial balance, try to withdraw more
        vm.expectRevert();
        executor.withdrawToken(IERC20(address(mockSdai)), owner, 20000 ether);
    }

    // ========================================
    // ACCESS CONTROL TESTS
    // ========================================

    function testOnlyOwnerCanWithdrawETH() public {
        vm.deal(address(executor), 10 ether);

        vm.prank(user);
        vm.expectRevert();
        executor.withdrawETH(payable(user), 1 ether);

        // But owner can
        executor.withdrawETH(payable(owner), 1 ether);
        assertTrue(true);
    }

    function testOnlyOwnerCanWithdrawTokens() public {
        mockSdai.mint(address(executor), 100 ether);

        vm.prank(user);
        vm.expectRevert();
        executor.withdrawToken(IERC20(address(mockSdai)), user, 10 ether);

        // But owner can
        executor.withdrawToken(IERC20(address(mockSdai)), owner, 10 ether);
        assertTrue(true);
    }

    function testOnlyOwnerCanTransferOwnership() public {
        vm.prank(user);
        vm.expectRevert();
        executor.transferOwnership(user);

        // But owner can
        executor.transferOwnership(user);
        assertEq(executor.owner(), user);
    }

    // ========================================
    // GAS OPTIMIZATION TESTS
    // ========================================

    function testGasEfficientETHWithdrawal() public {
        vm.deal(address(executor), 10 ether);

        uint256 gasBefore = gasleft();
        executor.withdrawETH(payable(owner), 1 ether);
        uint256 gasUsed = gasBefore - gasleft();

        assertLt(gasUsed, 50000, "ETH withdrawal should be gas efficient");
    }

    function testGasEfficientTokenWithdrawal() public {
        mockSdai.mint(address(executor), 100 ether);

        uint256 gasBefore = gasleft();
        executor.withdrawToken(IERC20(address(mockSdai)), owner, 50 ether);
        uint256 gasUsed = gasBefore - gasleft();

        assertLt(gasUsed, 100000, "Token withdrawal should be gas efficient");
    }

    // ========================================
    // FUZZ TESTS (EXPANDED)
    // ========================================

    function testFuzzWithdrawETHBounds(uint96 amount) public {
        vm.assume(amount > 0 && amount <= 100 ether);

        vm.deal(address(executor), amount);
        uint256 balanceBefore = owner.balance;

        executor.withdrawETH(payable(owner), amount);

        assertEq(owner.balance, balanceBefore + amount);
        assertEq(address(executor).balance, 0);
    }

    function testFuzzWithdrawTokenBounds(uint256 amount) public {
        vm.assume(amount > 0 && amount <= 100000 ether);

        mockSdai.mint(address(executor), amount);

        executor.withdrawToken(IERC20(address(mockSdai)), owner, amount);

        assertGe(mockSdai.balanceOf(owner), amount);
    }

    function testFuzzTransferOwnership(address newOwner) public {
        vm.assume(newOwner != address(0));
        vm.assume(newOwner != owner);

        executor.transferOwnership(newOwner);
        assertEq(executor.owner(), newOwner);
    }

}

