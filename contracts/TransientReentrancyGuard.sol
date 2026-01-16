// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/**
 * @title TransientReentrancyGuard
 * @notice Gas-efficient reentrancy protection using EIP-1153 transient storage.
 * @dev Implements a mutex using TLOAD/TSTORE opcodes.
 */
abstract contract TransientReentrancyGuard {

    error NonReentrant();

    modifier nonReentrant() {
        assembly {
            // Compute slot: keccak256("REENTRANCY_GUARD")
            mstore(0x00, "REENTRANCY_GUARD")
            let slot := keccak256(0x00, 0x10)

            // Check if the guard is already set (non-zero)
            if tload(slot) {
                // Store the error selector for NonReentrant()
                // Selector: bytes4(keccak256("NonReentrant()")) = 0x732f9c96
                mstore(0x00, 0x732f9c9600000000000000000000000000000000000000000000000000000000)
                revert(0x00, 0x04)
            }
            // Lock: Store 1 in the transient slot
            tstore(slot, 1)
        }

        _;

        assembly {
            // Compute slot again for unlock
            mstore(0x00, "REENTRANCY_GUARD")
            let slot := keccak256(0x00, 0x10)
            // Unlock: Store 0 in the transient slot
            tstore(slot, 0)
        }
    }

}
