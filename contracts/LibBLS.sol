// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/**
 * @title LibBLS
 * @notice Wrapper for EIP-2537 BLS12-381 Precompiles (Osaka/Pectra Upgrade)
 * @dev Addresses are based on the EIP-2537 specification.
 */
library LibBLS {

    // Precompile Addresses
    address constant BLS12_G1ADD = address(0x0b);
    address constant BLS12_G1MUL = address(0x0c);
    address constant BLS12_G1MSM = address(0x0d);
    address constant BLS12_G2ADD = address(0x0e);
    address constant BLS12_G2MUL = address(0x0f);
    address constant BLS12_G2MSM = address(0x10);
    address constant BLS12_PAIRING_CHECK = address(0x11);
    address constant BLS12_MAP_FP_TO_G1 = address(0x12);
    address constant BLS12_MAP_FP2_TO_G2 = address(0x13);

    error BLSVerificationFailed();
    error InvalidPoint();

    /**
     * @notice Verify a BLS signature: e(g1, signature) == e(pubKey, hashToPoint(message))
     * @dev Performs a pairing check: e(g1, signature) * e(pubKey, -hash) == 1
     * @param pubKey The public key on G1 (2 words: X, Y)
     * @param signature The signature on G2 (4 words: X1, X2, Y1, Y2)
     * @param message The message hash mapped to G2 (4 words) - simplified for example
     */
    function verifySignature(uint256[2] memory pubKey, uint256[4] memory signature, uint256[4] memory message)
        internal
        view
        returns (bool)
    {
        // Input for Pairing Check (0x11):
        // List of (G1_Point, G2_Point) pairs.
        // We want to check: e(G1_Generator, Signature) == e(PubKey, Message)
        // Equivalent to: e(-G1_Generator, Signature) * e(PubKey, Message) == 1

        // 1. Negate G1 Generator (simplified constant for example)
        // In production, use G1MUL(G1, scalar_field_modulus - 1) or precomputed negative G1
        uint256[2] memory negG1 = [
            uint256(0x0000000000000000000000000000000000000000000000000000000000000000), // Placeholder
            uint256(0x0000000000000000000000000000000000000000000000000000000000000000) // Placeholder
        ];

        // 2. Construct Input: [negG1, Signature, PubKey, Message]
        // Size: (2 + 4) * 2 = 12 words = 384 bytes
        uint256[] memory input = new uint256[](12);

        input[0] = negG1[0];
        input[1] = negG1[1];
        input[2] = signature[0];
        input[3] = signature[1];
        input[4] = signature[2];
        input[5] = signature[3];

        input[6] = pubKey[0];
        input[7] = pubKey[1];
        input[8] = message[0];
        input[9] = message[1];
        input[10] = message[2];
        input[11] = message[3];

        // 3. Call Precompile
        (bool success, bytes memory result) = BLS12_PAIRING_CHECK.staticcall(abi.encodePacked(input));

        // Result should be 1 (true) or 0 (false)
        return success && result.length > 0 && abi.decode(result, (bool));
    }

    /**
     * @notice Aggregate multiple BLS public keys into one (G1 point addition)
     * @param pubKeys Array of public keys (G1 points)
     * @return aggregatedKey The sum of all public keys
     */
    function aggregatePublicKeys(uint256[2][] memory pubKeys) internal view returns (uint256[2] memory aggregatedKey) {
        uint256 len = pubKeys.length;
        if (len == 0) return [uint256(0), uint256(0)];

        aggregatedKey = pubKeys[0];
        for (uint256 i = 1; i < len;) {
            (bool success, bytes memory result) =
                BLS12_G1ADD.staticcall(abi.encode(aggregatedKey[0], aggregatedKey[1], pubKeys[i][0], pubKeys[i][1]));
            if (!success) revert BLSVerificationFailed();
            aggregatedKey = abi.decode(result, (uint256[2]));
            unchecked {
                ++i;
            }
        }
    }

}
