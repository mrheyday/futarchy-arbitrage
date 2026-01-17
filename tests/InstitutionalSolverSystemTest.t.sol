// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import "forge-std/Test.sol";
import "../contracts/InstitutionalSolverSystem.sol";

contract InstitutionalSolverSystemTest is Test {
    InstitutionalSolverSystem public system;
    
    address public owner;
    address public zkVerifier;
    address public paymaster;
    address[] public flashloanProviders;
    
    address public solver1;
    address public solver2;
    address public solver3;
    
    function setUp() public {
        owner = address(this);
        zkVerifier = address(0);  // Disabled for tests
        paymaster = address(0);
        
        // Mock flashloan providers
        flashloanProviders.push(makeAddr("aave"));
        flashloanProviders.push(makeAddr("balancer"));
        flashloanProviders.push(makeAddr("morpho"));
        
        // Deploy system
        system = new InstitutionalSolverSystem(
            zkVerifier,
            paymaster,
            flashloanProviders
        );
        
        // Create solver addresses
        solver1 = makeAddr("solver1");
        solver2 = makeAddr("solver2");
        solver3 = makeAddr("solver3");
    }
    
    // ========== Intent Tests ==========
    
    function test_SubmitIntent() public {
        uint256 intentId = 1;
        bytes memory intentData = abi.encode("test intent");
        
        vm.expectEmit(true, true, false, false);
        emit InstitutionalSolverSystem.IntentSubmitted(intentId, address(this));
        
        system.submitIntent(intentId, intentData);
    }
    
    function testFail_SubmitEmptyIntent() public {
        system.submitIntent(1, "");
    }
    
    // ========== Auction Tests ==========
    
    function test_OpenCloseAuction() public {
        uint256 auctionId = 1;
        
        system.openAuction(auctionId);
        system.closeAuction(auctionId);
    }
    
    function test_CommitBid() public {
        uint256 auctionId = 1;
        uint256 bidValue = 1000;
        bytes32 salt = keccak256("salt");
        bytes32 commitHash = keccak256(abi.encodePacked(bidValue, salt));
        
        system.openAuction(auctionId);
        
        vm.prank(solver1);
        vm.expectEmit(true, true, false, true);
        emit InstitutionalSolverSystem.BidCommitted(auctionId, solver1, commitHash);
        
        system.commitBid(auctionId, commitHash);
    }
    
    function testFail_CommitBidClosedAuction() public {
        uint256 auctionId = 1;
        bytes32 commitHash = keccak256("test");
        
        // Auction not opened
        vm.prank(solver1);
        system.commitBid(auctionId, commitHash);
    }
    
    function test_RevealBid() public {
        uint256 auctionId = 1;
        uint256 bidValue = 1000;
        bytes32 salt = keccak256("salt");
        bytes32 commitHash = keccak256(abi.encodePacked(bidValue, salt));
        
        // Open auction, commit bid, close auction
        system.openAuction(auctionId);
        
        vm.prank(solver1);
        system.commitBid(auctionId, commitHash);
        
        system.closeAuction(auctionId);
        
        // Reveal bid
        vm.prank(solver1);
        vm.expectEmit(true, true, false, true);
        emit InstitutionalSolverSystem.BidRevealed(auctionId, solver1, bidValue);
        
        system.revealBid(auctionId, bidValue, salt);
    }
    
    function testFail_RevealBidWrongValue() public {
        uint256 auctionId = 1;
        uint256 bidValue = 1000;
        uint256 wrongValue = 2000;
        bytes32 salt = keccak256("salt");
        bytes32 commitHash = keccak256(abi.encodePacked(bidValue, salt));
        
        system.openAuction(auctionId);
        vm.prank(solver1);
        system.commitBid(auctionId, commitHash);
        system.closeAuction(auctionId);
        
        // Try to reveal with wrong value
        vm.prank(solver1);
        system.revealBid(auctionId, wrongValue, salt);
    }
    
    function test_SettleAuctionSingleBid() public {
        uint256 auctionId = 1;
        uint256 bidValue = 1000;
        bytes32 salt = keccak256("salt");
        bytes32 commitHash = keccak256(abi.encodePacked(bidValue, salt));
        
        // Setup auction
        system.openAuction(auctionId);
        vm.prank(solver1);
        system.commitBid(auctionId, commitHash);
        system.closeAuction(auctionId);
        vm.prank(solver1);
        system.revealBid(auctionId, bidValue, salt);
        
        // Settle
        address[] memory solvers = new address[](1);
        solvers[0] = solver1;
        
        address winner = system.settleAuction(auctionId, solvers);
        
        assertEq(winner, solver1);
    }
    
    function test_SettleAuctionMultipleBids() public {
        uint256 auctionId = 1;
        
        // Setup auction
        system.openAuction(auctionId);
        
        // Solver 1: bid 1000
        uint256 bid1 = 1000;
        bytes32 salt1 = keccak256("salt1");
        vm.prank(solver1);
        system.commitBid(auctionId, keccak256(abi.encodePacked(bid1, salt1)));
        
        // Solver 2: bid 2000 (higher)
        uint256 bid2 = 2000;
        bytes32 salt2 = keccak256("salt2");
        vm.prank(solver2);
        system.commitBid(auctionId, keccak256(abi.encodePacked(bid2, salt2)));
        
        // Solver 3: bid 1500
        uint256 bid3 = 1500;
        bytes32 salt3 = keccak256("salt3");
        vm.prank(solver3);
        system.commitBid(auctionId, keccak256(abi.encodePacked(bid3, salt3)));
        
        system.closeAuction(auctionId);
        
        // Reveal all bids
        vm.prank(solver1);
        system.revealBid(auctionId, bid1, salt1);
        vm.prank(solver2);
        system.revealBid(auctionId, bid2, salt2);
        vm.prank(solver3);
        system.revealBid(auctionId, bid3, salt3);
        
        // Settle
        address[] memory solvers = new address[](3);
        solvers[0] = solver1;
        solvers[1] = solver2;
        solvers[2] = solver3;
        
        address winner = system.settleAuction(auctionId, solvers);
        
        // Solver 2 should win (highest bid with CLZ scaling)
        // Note: CLZ scaling might affect this, but higher raw bids should still win
        assertEq(winner, solver2);
    }
    
    // ========== Reputation Tests ==========
    
    function test_UpdateReputation() public {
        int256 delta = 100;
        
        vm.expectEmit(true, false, false, false);
        emit InstitutionalSolverSystem.ReputationUpdated(solver1, delta);
        
        system.updateReputation(solver1, delta);
        
        int256 reputation = system.getReputation(solver1);
        assertTrue(reputation > 0, "Reputation should be positive");
    }
    
    function test_ReputationGate() public {
        // Set low reputation
        system.updateReputation(solver1, -200);
        
        // Should be below minimum
        int256 reputation = system.getReputation(solver1);
        assertTrue(reputation < 100, "Reputation should be below minimum");
    }
    
    // ========== Compliance Tests ==========
    
    function test_SetComplianceFlags() public {
        uint256 flags = 1 << 0 | 1 << 1 | 1 << 2;  // KYC + Accredited + Sanctions Clear
        
        system.setComplianceFlags(solver1, flags);
        
        // Should pass compliance check
        bool compliant = system.checkCompliance(solver1, flags);
        assertTrue(compliant);
    }
    
    function testFail_ComplianceViolation() public {
        uint256 flags = 1 << 0;  // Only KYC
        uint256 required = 1 << 0 | 1 << 1;  // KYC + Accredited
        
        system.setComplianceFlags(solver1, flags);
        
        // Should fail - missing Accredited flag
        system.checkCompliance(solver1, required);
    }
    
    // ========== Treasury Tests ==========
    
    function test_DepositToTreasury() public {
        address token = makeAddr("token");
        uint256 amount = 1000;
        
        system.depositToTreasury(token, amount);
    }
    
    function test_AuthorizeTreasuryAccess() public {
        system.authorizeTreasuryAccess(solver1);
    }
    
    // ========== Utility Tests ==========
    
    function test_SealExecution() public {
        uint256 intentId = 1;
        
        bytes32 seal = system.sealExecution(intentId);
        
        assertTrue(seal != bytes32(0), "Seal should not be empty");
    }
    
    function test_UpdateZKVerifier() public {
        address newVerifier = makeAddr("newVerifier");
        
        system.updateZKVerifier(newVerifier);
    }
    
    function test_UpdatePaymaster() public {
        address newPaymaster = makeAddr("newPaymaster");
        
        system.updatePaymaster(newPaymaster);
    }
    
    // ========== Access Control Tests ==========
    
    function testFail_UnauthorizedAuctionOpen() public {
        vm.prank(solver1);
        system.openAuction(1);
    }
    
    function testFail_UnauthorizedReputationUpdate() public {
        vm.prank(solver1);
        system.updateReputation(solver2, 100);
    }
    
    function testFail_UnauthorizedComplianceSet() public {
        vm.prank(solver1);
        system.setComplianceFlags(solver2, 1);
    }
}
