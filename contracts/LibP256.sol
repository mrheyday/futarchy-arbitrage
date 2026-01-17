// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/**
 * @title LibP256
 * @notice Wrapper for EIP-7212 (secp256r1) Precompile
 * @dev Enables verification of WebAuthn/Passkeys and HSM signatures.
 *      Target Address: 0x100 (Common for RIP-7212 implementations like Gnosis/Base/Arbitrum)
 */
library LibP256 {

    // Precompile address for P256 verification (RIP-7212)
    address constant P256_VERIFY = address(0x100);

    error InvalidP256Signature();

    /**
     * @notice Verify a secp256r1 (P-256) signature
     * @param hash The 32-byte message hash
     * @param r The r component of the signature (32 bytes)
     * @param s The s component of the signature (32 bytes)
     * @param x The x coordinate of the public key (32 bytes)
     * @param y The y coordinate of the public key (32 bytes)
     * @return valid True if the signature is valid
     */
    function verifySignature(bytes32 hash, uint256 r, uint256 s, uint256 x, uint256 y) internal view returns (bool) {
        // Input layout: hash (32) | r (32) | s (32) | x (32) | y (32)
        bytes memory input = abi.encodePacked(hash, r, s, x, y);

        // Call precompile
        (bool success, bytes memory ret) = P256_VERIFY.staticcall(input);

        // Check execution success and return value
        // Returns 1 (32 bytes) for valid, 0 or empty for invalid
        if (!success || ret.length == 0) return false;

        return abi.decode(ret, (uint256)) == 1;
    }

}
