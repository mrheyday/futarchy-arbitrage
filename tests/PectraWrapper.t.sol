// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import "forge-std/Test.sol";
import "../contracts/PectraWrapper.sol";

contract PectraWrapperTest is Test {
    PectraWrapper public wrapper;
    address public owner;
    address public user;

    event CallExecuted(address indexed target, bytes data, bool success);
    event BatchExecuted(uint256 callsExecuted);

    function setUp() public {
        owner = address(this);
        user = makeAddr("user");
        wrapper = new PectraWrapper();
    }

    function test_OwnerCanExecute() public {
        address[10] memory targets;
        targets[0] = address(0x1);
        
        bytes[10] memory calldatas;
        calldatas[0] = hex"112233";

        vm.expectEmit(true, false, false, true);
        emit CallExecuted(address(0x1), hex"112233", true);
        
        wrapper.execute10(targets, calldatas, 1);
    }

    function test_EIP7702_Delegation_Simulation() public {
        // 1. Simulate EIP-7702 by etching the wrapper's runtime code onto the user's address
        // This mimics the user delegating their code to PectraWrapper via an auth signature
        bytes memory code = address(wrapper).code;
        vm.etch(user, code);

        // 2. Prepare batch data
        address[10] memory targets;
        targets[0] = address(0xCAFE);
        targets[1] = address(0xBABE);
        
        bytes[10] memory datas;
        datas[0] = hex"aabbccdd";
        datas[1] = hex"11223344";

        // 3. User calls themselves (EIP-7702 transaction style)
        // The 'onlyOwner' modifier should pass because msg.sender (user) == address(this) (user)
        vm.prank(user);
        
        // We cast user to PectraWrapper interface because they now hold that code
        PectraWrapper(payable(user)).execute10(targets, datas, 2);
    }

    function test_RevertIf_NotSelf_Or_Owner() public {
        // Etch code to user
        vm.etch(user, address(wrapper).code);

        // Try to call user from a third party (attacker)
        address attacker = makeAddr("attacker");
        vm.prank(attacker);
        
        vm.expectRevert(PectraWrapper.OnlyOwner.selector);
        PectraWrapper(payable(user)).execute10([address(0),address(0),address(0),address(0),address(0),address(0),address(0),address(0),address(0),address(0)], [bytes(""),"","","","","","","","",""], 0);
    }
}