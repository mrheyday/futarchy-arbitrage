// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import "forge-std/Test.sol";
import "../contracts/InstitutionalSolverSystem.sol";

contract InstitutionalSolverSystemEventsTest is Test {
    InstitutionalSolverSystem public system;
    address public owner;
    address public user;

    // Events to test
    event ZKVerifierUpdated(address indexed newVerifier);
    event PaymasterUpdated(address indexed newPaymaster);
    event FlashloanProviderAdded(address indexed provider);
    event ComplianceFlagsSet(address indexed entity, uint256 flags);
    event TreasuryAccessAuthorized(address indexed account);
    event BLSKeyRegistered(address indexed account, uint256[2] pubKey);
    event P256KeyRegistered(address indexed account, uint256 x, uint256 y);

    function setUp() public {
        owner = address(this);
        user = makeAddr("user");
        address[] memory providers = new address[](0);
        system = new InstitutionalSolverSystem(address(0), address(0), providers);
    }

    function test_Event_FlashloanProviderAdded() public {
        address provider = makeAddr("provider");
        
        vm.expectEmit(true, false, false, true);
        emit FlashloanProviderAdded(provider);
        
        system.addFlashloanProvider(provider);
    }

    function test_Event_ComplianceFlagsSet() public {
        uint256 flags = 1 | 2; // KYC | Accredited
        
        vm.expectEmit(true, false, false, true);
        emit ComplianceFlagsSet(user, flags);
        
        system.setComplianceFlags(user, flags);
    }

    function test_Event_TreasuryAccessAuthorized() public {
        vm.expectEmit(true, false, false, true);
        emit TreasuryAccessAuthorized(user);
        
        system.authorizeTreasuryAccess(user);
    }

    function test_Event_ZKVerifierUpdated() public {
        address newVerifier = makeAddr("verifier");
        
        vm.expectEmit(true, false, false, true);
        emit ZKVerifierUpdated(newVerifier);
        
        system.updateZKVerifier(newVerifier);
    }

    function test_Event_PaymasterUpdated() public {
        address newPaymaster = makeAddr("paymaster");
        
        vm.expectEmit(true, false, false, true);
        emit PaymasterUpdated(newPaymaster);
        
        system.updatePaymaster(newPaymaster);
    }

    function test_Event_BLSKeyRegistered() public {
        uint256[2] memory pubKey = [uint256(123), uint256(456)];
        
        vm.prank(user);
        vm.expectEmit(true, false, false, true);
        emit BLSKeyRegistered(user, pubKey);
        
        system.registerBLSKey(pubKey);
    }

    function test_Event_P256KeyRegistered() public {
        uint256 x = 0xABC;
        uint256 y = 0xDEF;
        
        vm.prank(user);
        vm.expectEmit(true, false, false, true);
        emit P256KeyRegistered(user, x, y);
        
        system.registerP256Key(x, y);
    }

    // Helper to receive ETH if needed
    receive() external payable {}
}