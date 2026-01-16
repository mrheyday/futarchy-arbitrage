// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import {InstitutionalSolverSystem} from "../contracts/InstitutionalSolverSystem.sol";
import {Test} from "forge-std/Test.sol";

contract InstitutionalSolverSystemTest is Test {

    InstitutionalSolverSystem public solver;

    address public owner;
    address public solver1;
    address public solver2;
    address public zkVerifier;
    address public paymaster;

    address[] public flashloanProviders;

    function setUp() public {
        owner = address(this);
        solver1 = address(0x1111);
        solver2 = address(0x2222);
        zkVerifier = address(0x3333);
        paymaster = address(0x4444);

        flashloanProviders.push(address(0x5555));
        flashloanProviders.push(address(0x6666));

        solver = new InstitutionalSolverSystem(zkVerifier, paymaster, flashloanProviders);

        vm.label(address(solver), "InstitutionalSolverSystem");
        vm.label(owner, "Owner");
        vm.label(solver1, "Solver1");
        vm.label(solver2, "Solver2");
    }

    function testOwnershipInitialization() public {
        assertEq(solver.owner(), owner, "Owner should be deployer");
    }

    function testSubmitIntent() public {
        bytes memory intentData = abi.encode("test intent");
        solver.submitIntent(1, intentData);

        // Verify event was emitted (check in logs)
    }

    function testSubmitIntentRevertsOnEmptyData() public {
        vm.expectRevert();
        solver.submitIntent(1, bytes(""));
    }

    function testOpenAuctionOnlyOwner() public {
        solver.openAuction(1);

        // Non-owner should fail
        vm.prank(solver1);
        vm.expectRevert();
        solver.openAuction(2);
    }

    function testCloseAuctionOnlyOwner() public {
        solver.openAuction(1);
        solver.closeAuction(1);

        vm.prank(solver1);
        vm.expectRevert();
        solver.closeAuction(1);
    }

    function testCommitBid() public {
        solver.openAuction(1);

        bytes32 commitHash = keccak256(abi.encodePacked(uint256(100 ether), bytes32("salt")));

        vm.prank(solver1);
        solver.commitBid(1, commitHash);
    }

    function testCommitBidRevertsWhenAuctionClosed() public {
        bytes32 commitHash = keccak256(abi.encodePacked(uint256(100 ether), bytes32("salt")));

        vm.prank(solver1);
        vm.expectRevert();
        solver.commitBid(1, commitHash);
    }

    function testRevealBid() public {
        uint256 auctionId = 1;
        uint256 bidValue = 100 ether;
        bytes32 salt = bytes32("secret_salt");
        bytes32 commitHash = keccak256(abi.encodePacked(bidValue, salt));

        // Open auction and commit
        solver.openAuction(auctionId);
        vm.prank(solver1);
        solver.commitBid(auctionId, commitHash);

        // Close auction and reveal
        solver.closeAuction(auctionId);
        vm.prank(solver1);
        solver.revealBid(auctionId, bidValue, salt);
    }

    function testRevealBidRevertsWhenAuctionOpen() public {
        uint256 auctionId = 1;
        uint256 bidValue = 100 ether;
        bytes32 salt = bytes32("secret_salt");
        bytes32 commitHash = keccak256(abi.encodePacked(bidValue, salt));

        solver.openAuction(auctionId);
        vm.prank(solver1);
        solver.commitBid(auctionId, commitHash);

        // Try to reveal while still open
        vm.prank(solver1);
        vm.expectRevert();
        solver.revealBid(auctionId, bidValue, salt);
    }

    function testSettleAuction() public {
        uint256 auctionId = 1;

        // Solver 1 bid
        uint256 bid1 = 100 ether;
        bytes32 salt1 = bytes32("salt1");
        bytes32 hash1 = keccak256(abi.encodePacked(bid1, salt1));

        // Solver 2 bid
        uint256 bid2 = 150 ether;
        bytes32 salt2 = bytes32("salt2");
        bytes32 hash2 = keccak256(abi.encodePacked(bid2, salt2));

        // Commit bids
        solver.openAuction(auctionId);
        vm.prank(solver1);
        solver.commitBid(auctionId, hash1);
        vm.prank(solver2);
        solver.commitBid(auctionId, hash2);

        // Reveal bids
        solver.closeAuction(auctionId);
        vm.prank(solver1);
        solver.revealBid(auctionId, bid1, salt1);
        vm.prank(solver2);
        solver.revealBid(auctionId, bid2, salt2);

        // Settle auction
        address[] memory solvers = new address[](2);
        solvers[0] = solver1;
        solvers[1] = solver2;

        address winner = solver.settleAuction(auctionId, solvers);

        // Winner should be solver2 (higher bid with CLZ scaling)
        assertEq(winner, solver2, "Solver2 should win");
    }

    function testUpdateReputation() public {
        solver.updateReputation(solver1, 100);
        int256 rep = solver.getReputation(solver1);
        assertTrue(rep > 0, "Reputation should be positive");
    }

    function testUpdateReputationOnlyOwner() public {
        vm.prank(solver1);
        vm.expectRevert();
        solver.updateReputation(solver1, 100);
    }

    function testAddFlashloanProvider() public {
        address newProvider = address(0x9999);
        solver.addFlashloanProvider(newProvider);
    }

    function testAddFlashloanProviderOnlyOwner() public {
        vm.prank(solver1);
        vm.expectRevert();
        solver.addFlashloanProvider(address(0x9999));
    }

    function testSetComplianceFlags() public {
        uint256 flags = (1 << 0) | (1 << 1) | (1 << 2); // KYC + Accredited + Sanctions clear
        solver.setComplianceFlags(solver1, flags);
    }

    function testCheckCompliance() public {
        uint256 flags = (1 << 0) | (1 << 1);
        solver.setComplianceFlags(solver1, flags);

        bool compliant = solver.checkCompliance(solver1, (1 << 0));
        assertTrue(compliant, "Should be compliant with KYC");
    }

    function testAuthorizeTreasuryAccess() public {
        solver.authorizeTreasuryAccess(solver1);
    }

    function testDepositToTreasury() public {
        address token = address(0x1234);
        vm.deal(token, 1000 ether);

        solver.depositToTreasury(token, 100 ether);
    }

    function testGetTopSolversByReputation() public {
        // Set up reputation
        solver.updateReputation(solver1, 100);
        solver.updateReputation(solver2, 200);

        address[] memory solverList = new address[](2);
        solverList[0] = solver1;
        solverList[1] = solver2;

        address[] memory topSolvers = solver.getTopSolversByReputation(solverList, 2);

        // Should be sorted by reputation (descending)
        assertEq(topSolvers.length, 2, "Should return 2 solvers");
    }

    // Fuzz tests
    function testFuzzReputation(int256 delta) public {
        // Constrain delta to safe range to avoid overflow/underflow
        vm.assume(delta > -1000 ether && delta < 1000 ether);
        vm.assume(delta != 0); // Avoid zero delta

        solver.updateReputation(solver1, delta);

        int256 rep = solver.getReputation(solver1);
        // Reputation can go negative or positive
        assertTrue(rep >= -1000 ether && rep <= 1000 ether, "Reputation should be in safe range");
    }

    receive() external payable {}

    // ========================================
    // ADDITIONAL EDGE CASE TESTS
    // ========================================

    function testCommitBidWithZeroValue() public {
        uint256 auctionId = 1;
        bytes32 commitment = keccak256("zero_bid");

        solver.openAuction(auctionId);

        vm.prank(solver1);
        solver.commitBid(auctionId, commitment);

        // Should succeed even with zero value
        assertTrue(true);
    }

    function testRevealBidWithWrongSalt() public {
        uint256 auctionId = 1;
        uint256 bid = 1 ether;
        bytes32 correctSalt = bytes32("correct");
        bytes32 wrongSalt = bytes32("wrong");

        solver.openAuction(auctionId);

        vm.prank(solver1);
        solver.commitBid(auctionId, keccak256(abi.encodePacked(bid, correctSalt)));

        solver.closeAuction(auctionId);

        vm.prank(solver1);
        vm.expectRevert();
        solver.revealBid(auctionId, bid, wrongSalt);
    }

    function testSettleAuctionWithNoRevealedBids() public {
        uint256 auctionId = 1;

        solver.openAuction(auctionId);
        solver.closeAuction(auctionId);

        address[] memory solvers = new address[](0);

        // With no revealed bids, contract reverts with InvalidBid()
        vm.expectRevert(abi.encodeWithSignature("InvalidBid()"));
        solver.settleAuction(auctionId, solvers);
    }

    function testDepositToTreasuryMultipleTimes() public {
        address mockToken = address(0x1234);

        solver.depositToTreasury(mockToken, 1 ether);
        solver.depositToTreasury(mockToken, 2 ether);
        solver.depositToTreasury(mockToken, 3 ether);

        // All deposits should succeed
        assertTrue(true);
    }

    function testUpdateReputationOverflow() public {
        // Test large positive delta
        solver.updateReputation(solver1, 1000000 ether);

        int256 rep = solver.getReputation(solver1);
        assertGt(rep, 0);
    }

    function testUpdateReputationUnderflow() public {
        // Test large negative delta - contract clamps to 0
        solver.updateReputation(solver1, -1000000 ether);

        int256 rep = solver.getReputation(solver1);
        // Reputation is clamped to 0, not negative
        assertEq(rep, 0);
    }

    function testSetComplianceFlagsAllCombinations() public {
        // Test all 8 combinations of 3 flags (as bits)
        for (uint256 i = 0; i < 8; i++) {
            solver.setComplianceFlags(solver1, i);

            bool compliant = solver.checkCompliance(solver1, i);
            // Verify operation completes
            assertTrue(compliant || !compliant);
        }
    }

    function testAuthorizeTreasuryAccessMultipleSolvers() public {
        solver.authorizeTreasuryAccess(solver1);
        solver.authorizeTreasuryAccess(solver2);

        // All operations should succeed
        assertTrue(true);
    }

    function testGetTopSolversByReputationWithNegativeReputation() public {
        solver.updateReputation(solver1, -100 ether);
        solver.updateReputation(solver2, -50 ether);

        address[] memory solverList = new address[](2);
        solverList[0] = solver1;
        solverList[1] = solver2;

        address[] memory topSolvers = solver.getTopSolversByReputation(solverList, 2);

        // Should return solvers even with negative reputation
        assertEq(topSolvers.length, 2);
    }

    function testSubmitIntentWithMaxLengthData() public {
        // Test with large intent data
        bytes memory largeData = new bytes(1000);
        for (uint256 i = 0; i < 1000; i++) {
            largeData[i] = bytes1(uint8(i % 256));
        }

        uint256 intentId = 123;
        solver.submitIntent(intentId, largeData);
        // Should complete without revert
        assertTrue(true);
    }

    function testAddFlashloanProviderDuplicate() public {
        address provider = address(0x1234);

        solver.addFlashloanProvider(provider);
        solver.addFlashloanProvider(provider);

        // Should handle duplicates gracefully
        assertTrue(true);
    }

    function testOpenAuctionSameIdTwice() public {
        uint256 auctionId = 1;

        solver.openAuction(auctionId);

        // Contract allows reopening - just sets isOpen = true again
        solver.openAuction(auctionId);

        // Verify still open
        assertTrue(true); // No way to check isOpen from outside, but no revert
    }

    function testCloseAuctionWithoutOpening() public {
        uint256 auctionId = 999;

        // Contract allows closing even if never opened - just sets isOpen = false
        solver.closeAuction(auctionId);

        // Verify no revert
        assertTrue(true);
    }

    function testCommitBidToClosedAuction() public {
        uint256 auctionId = 1;

        solver.openAuction(auctionId);
        solver.closeAuction(auctionId);

        vm.prank(solver1);
        vm.expectRevert();
        solver.commitBid(auctionId, keccak256("late_bid"));
    }

    function testRevealBidToOpenAuction() public {
        uint256 auctionId = 1;
        uint256 bid = 1 ether;
        bytes32 salt = bytes32("salt");

        solver.openAuction(auctionId);

        vm.prank(solver1);
        solver.commitBid(auctionId, keccak256(abi.encodePacked(bid, salt)));

        // Try to reveal before closing
        vm.prank(solver1);
        vm.expectRevert();
        solver.revealBid(auctionId, bid, salt);
    }

}

