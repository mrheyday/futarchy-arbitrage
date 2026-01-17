// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import "forge-std/Test.sol";
import "../contracts/InstitutionalSolverSystem.sol";

contract InstitutionalSolverSystemIntegrationTest is Test {
    InstitutionalSolverSystem public system;
    address public owner;
    address public solver;
    address public user;

    // Mock Intent Data
    uint256 constant INTENT_ID = 1;
    bytes constant INTENT_DATA = hex"1234";
    
    // Events to check
    event IntentSubmitted(uint256 indexed intentId, address indexed submitter);
    event IntentResolved(uint256 indexed intentId, address indexed solver, uint256 value);
    event AuctionSettled(uint256 indexed auctionId, address indexed winner, uint256 winningBid);

    function setUp() public {
        owner = address(this);
        solver = makeAddr("solver");
        user = makeAddr("user");
        
        address[] memory providers = new address[](0);
        system = new InstitutionalSolverSystem(address(0), address(0), providers);
        
        // Setup Solver Reputation
        system.updateReputation(solver, 200); // Min is 100
    }

    function test_FullFlow_IntentResolution() public {
        // 1. User submits intent
        vm.prank(user);
        vm.expectEmit(true, true, false, true);
        emit IntentSubmitted(INTENT_ID, user);
        system.submitIntent(INTENT_ID, INTENT_DATA);

        // 2. Solver resolves intent
        // We need a valid execData. Since the system does delegatecall(execData),
        // we can pass empty data or data that calls a function on the system itself (careful with reentrancy)
        // or just a no-op. For this test, we'll use empty bytes which succeeds but does nothing.
        bytes memory execData = "";
        
        vm.prank(solver);
        vm.expectEmit(true, true, false, true);
        emit IntentResolved(INTENT_ID, solver, execData.length);
        system.resolveIntent(INTENT_ID, solver, execData);
        
        // Verify reputation increased
        int256 rep = system.getReputation(solver);
        assertTrue(rep > 200, "Reputation should increase after resolution");
    }

    function test_FullFlow_AuctionSettlement() public {
        uint256 auctionId = 99;
        
        // 1. Open Auction
        system.openAuction(auctionId);
        
        // 2. Commit Bids
        // Solver 1
        address solver1 = makeAddr("solver1");
        system.updateReputation(solver1, 200);
        uint256 bid1 = 1000;
        bytes32 salt1 = keccak256("salt1");
        bytes32 commit1 = keccak256(abi.encodePacked(bid1, salt1));
        
        vm.prank(solver1);
        system.commitBid(auctionId, commit1);
        
        // Solver 2 (Higher Bid)
        address solver2 = makeAddr("solver2");
        system.updateReputation(solver2, 200);
        uint256 bid2 = 2000;
        bytes32 salt2 = keccak256("salt2");
        bytes32 commit2 = keccak256(abi.encodePacked(bid2, salt2));
        
        vm.prank(solver2);
        system.commitBid(auctionId, commit2);
        
        // 3. Close Auction
        system.closeAuction(auctionId);
        
        // 4. Reveal Bids
        vm.prank(solver1);
        system.revealBid(auctionId, bid1, salt1);
        
        vm.prank(solver2);
        system.revealBid(auctionId, bid2, salt2);
        
        // 5. Settle Auction
        address[] memory solvers = new address[](2);
        solvers[0] = solver1;
        solvers[1] = solver2;
        
        vm.expectEmit(true, true, false, true);
        emit AuctionSettled(auctionId, solver2, 78); // 2000 scaled by CLZ logic: 2000 * 10 / 256 = 78
        
        address winner = system.settleAuction(auctionId, solvers);
        assertEq(winner, solver2, "Highest bidder should win");
    }
}