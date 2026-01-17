// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import "forge-std/Test.sol";
import "../contracts/InstitutionalSolverSystem.sol";
import "../contracts/LibP256.sol";
import "../contracts/LibBLS.sol";

contract CryptoIntegrationTest is Test {
    InstitutionalSolverSystem public system;
    address public owner;
    address public solver;

    // Precompile Addresses
    address constant P256_VERIFY = address(0x100);
    address constant BLS12_G1ADD = address(0x0b);
    address constant BLS12_PAIRING_CHECK = address(0x11);

    function setUp() public {
        owner = makeAddr("owner");
        solver = makeAddr("solver");
        
        address[] memory providers = new address[](0);
        vm.prank(owner);
        system = new InstitutionalSolverSystem(address(0), address(0), providers);
    }

    // ============ P256 Tests (EIP-7212) ============

    function test_P256_RegistrationAndVerification() public {
        uint256 x = 0x1234;
        uint256 y = 0x5678;

        // 1. Register
        vm.prank(solver);
        system.registerP256Key(x, y);

        (uint256 storedX, uint256 storedY) = system.p256PublicKeys(solver);
        assertEq(storedX, x);
        assertEq(storedY, y);

        // 2. Verify (Mock Precompile)
        // RIP-7212 returns 1 (as 32-byte word) for valid
        vm.mockCall(P256_VERIFY, abi.encode(uint256(1)));

        bool valid = system.verifySolverP256(solver, bytes32(0), 0, 0);
        assertTrue(valid);
    }

    function test_P256_Verification_Invalid() public {
        uint256 x = 0x1234;
        uint256 y = 0x5678;
        vm.prank(solver);
        system.registerP256Key(x, y);

        // Mock Precompile returning 0 (invalid)
        vm.mockCall(P256_VERIFY, abi.encode(uint256(0)));

        bool valid = system.verifySolverP256(solver, bytes32(0), 0, 0);
        assertFalse(valid);
    }

    // ============ BLS Tests (EIP-2537) ============

    function test_BLS_RegistrationAndVerification() public {
        uint256[2] memory pubKey = [uint256(1), uint256(2)];

        // 1. Register
        vm.prank(solver);
        system.registerBLSKey(pubKey);

        (uint256 px, uint256 py) = system.blsPublicKeys(solver);
        assertEq(px, 1);
        assertEq(py, 2);

        // 2. Verify (Mock Precompile)
        // Pairing check returns boolean (as 32-byte word 0/1 or bool)
        vm.mockCall(BLS12_PAIRING_CHECK, abi.encode(true));

        uint256[4] memory sig;
        uint256[4] memory msgHash;
        bool valid = system.verifySolverBLS(solver, sig, msgHash);
        assertTrue(valid);
    }

    function test_BLS_BatchVerification() public {
        address solver2 = makeAddr("solver2");
        uint256[2] memory pk1 = [uint256(10), uint256(20)];
        uint256[2] memory pk2 = [uint256(30), uint256(40)];

        vm.prank(solver);
        system.registerBLSKey(pk1);
        vm.prank(solver2);
        system.registerBLSKey(pk2);

        // Mock G1ADD for aggregation
        vm.mockCall(BLS12_G1ADD, abi.encode(uint256(40), uint256(60)));
        // Mock Pairing Check
        vm.mockCall(BLS12_PAIRING_CHECK, abi.encode(true));

        address[] memory solvers = new address[](2);
        solvers[0] = solver;
        solvers[1] = solver2;

        uint256[4] memory aggSig;
        uint256[4] memory msgHash;

        bool valid = system.verifyBatchBLS(solvers, aggSig, msgHash);
        assertTrue(valid);
    }
}