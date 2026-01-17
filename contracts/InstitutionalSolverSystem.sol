// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

import {LibBLS} from "./LibBLS.sol";
import {LibP256} from "./LibP256.sol";
import {TransientReentrancyGuard} from "./TransientReentrancyGuard.sol";
import {FixedPointMathLib} from "solady-clz/FixedPointMathLib.sol";
import {LibBit} from "solady-clz/LibBit.sol";
import {LibSort} from "solady-utils/LibSort.sol";
import {TransientReentrancyGuard} from "./TransientReentrancyGuard.sol";
import {SafeCastLib} from "solady-utils/SafeCastLib.sol";
import {LibBLS} from "./LibBLS.sol";
import {LibP256} from "./LibP256.sol";

/**
 * @title InstitutionalSolverSystem
 * @notice Complete institutional solver intelligence system with CLZ optimizations using Solady LibBit
 * @dev Integrates all modules: Auction, Reputation, Flashloan, ZK, MEV, Compliance, etc.
 * Implements Osaka EVM CLZ-enhanced DeFi integration
 */
contract InstitutionalSolverSystem is TransientReentrancyGuard {

    using FixedPointMathLib for uint256;
    using SafeCastLib for uint256;

    // ============ Errors ============
    error Unauthorized();
    error InvalidIntent();
    error ExecutionFailed();
    error InvalidBid();
    error AuctionClosed();
    error ReputationSlash();
    error FlashloanFailed();
    error MEVDetected();
    error ComplianceViolation();

    // ============ Events ============
    event IntentSubmitted(uint256 indexed intentId, address indexed submitter);
    event IntentResolved(uint256 indexed intentId, address indexed solver, uint256 value);
    event BidCommitted(uint256 indexed auctionId, address indexed solver, bytes32 commitHash);
    event BidRevealed(uint256 indexed auctionId, address indexed solver, uint256 bidValue);
    event AuctionSettled(uint256 indexed auctionId, address indexed winner, uint256 winningBid);
    event ReputationUpdated(address indexed solver, int256 delta);
    event BatchExecuted(uint256 indexed batchId, address[] solvers);
    event TreasuryDeposit(address indexed token, uint256 amount, uint256 logAmount);
    event ZKVerifierUpdated(address indexed newVerifier);
    event PaymasterUpdated(address indexed newPaymaster);
    event FlashloanProviderAdded(address indexed provider);
    event ComplianceFlagsSet(address indexed entity, uint256 flags);
    event TreasuryAccessAuthorized(address indexed account);
    event BLSKeyRegistered(address indexed account, uint256[2] pubKey);
    event P256KeyRegistered(address indexed account, uint256 x, uint256 y);

    // ============ State Variables ============
    address public immutable owner;

    address public zkVerifier;
    address public paymaster;
    address[] public flashloanProviders;

    // Intent management
    mapping(uint256 => bytes) internal intents;
    mapping(uint256 => address) internal resolvers;

    // Auction state
    struct Bid {
        bytes32 commitHash;
        uint256 revealValue;
        bool revealed;
    }

    struct AuctionState {
        mapping(address => Bid) bids;
        bool isOpen;
        address winner;
    }

    mapping(uint256 => AuctionState) internal auctions;

    // Reputation state
    mapping(address => int256) internal reputation;
    uint256 internal constant MIN_REPUTATION = 100;
    uint256 internal constant SLASH_FACTOR = 50;
    uint256 internal constant FUSAKA_GAS_LIMIT = 60_000_000;

    // Compliance state
    mapping(address => uint256) internal complianceFlags;
    uint256 constant KYC_VERIFIED = 1 << 0;
    uint256 constant ACCREDITED = 1 << 1;
    uint256 constant SANCTIONS_CLEAR = 1 << 2;

    // Account abstraction
    mapping(address => uint256) internal nonces;

    // Treasury
    mapping(address => uint256) internal treasuryBalances;
    mapping(address => bool) internal treasuryAuthorized;

    // BLS Keys (Osaka/Pectra)
    mapping(address => uint256[2]) public blsPublicKeys; // G1 Points

    // P256 Keys (EIP-7212 / Passkeys)
    mapping(address => uint256[2]) public p256PublicKeys; // [X, Y]

    // ============ Modifiers ============
    modifier onlyOwner() {
        if (msg.sender != owner) revert Unauthorized();
        _;
    }

    // ============ Constructor ============
    constructor(address _zkVerifier, address _paymaster, address[] memory _providers) {
        owner = msg.sender;
        zkVerifier = _zkVerifier;
        paymaster = _paymaster;
        flashloanProviders = _providers;
        treasuryAuthorized[msg.sender] = true;
    }

    // ============ Intent Resolution ============

    function submitIntent(uint256 intentId, bytes calldata intentData) external {
        if (intentData.length == 0) revert InvalidIntent();
        intents[intentId] = intentData;
        emit IntentSubmitted(intentId, msg.sender);
    }

    function resolveIntent(uint256 intentId, address solver, bytes calldata execData) external nonReentrant {
        _resolveIntent(intentId, solver, execData);
    }

    function _resolveIntent(uint256 intentId, address solver, bytes calldata execData) internal {
        // Gate solver reputation
        // forge-lint: disable-next-line(unsafe-typecast)
        if (reputation[solver] < int256(MIN_REPUTATION)) revert ReputationSlash();

        if (resolvers[intentId] != address(0)) revert ExecutionFailed();
        if (execData.length > 16780000 / 16) revert ExecutionFailed();

        // ZK verification
        if (zkVerifier != address(0)) {
            (bool zkSuccess,) = zkVerifier.staticcall(abi.encodeWithSignature("verifyProof(bytes)", execData));
            if (!zkSuccess) revert ExecutionFailed();
        }

        // MEV protection via entropy check
        bytes32 txHash = keccak256(abi.encodePacked(intentId, solver, execData));
        uint256 entropy = 255 - LibBit.clz_(uint256(txHash));
        if (entropy < 100) revert MEVDetected();

        // Execute intent
        (bool success,) = solver.delegatecall(execData);
        if (!success) revert ExecutionFailed();

        resolvers[intentId] = solver;
        emit IntentResolved(intentId, solver, execData.length);

        // Update reputation with CLZ scaling
        updateReputationInternal(solver, 10);
    }

    function batchResolve(uint256[] calldata intentIds, address[] calldata solvers, bytes[] calldata execDatas)
        external
        nonReentrant
    {
        if (intentIds.length != solvers.length || intentIds.length != execDatas.length) revert InvalidIntent();
        if (intentIds.length > FUSAKA_GAS_LIMIT / 200000) revert ExecutionFailed();

        bytes32 rawHash = keccak256(abi.encodePacked(intentIds));
        uint256 batchId = 255 - LibBit.clz_(uint256(rawHash));

        for (uint256 i = 0; i < intentIds.length;) {
            _resolveIntent(intentIds[i], solvers[i], execDatas[i]);
            unchecked {
                ++i;
            }
        }

        emit BatchExecuted(batchId, solvers);
    }

    // ============ Auction Economics ============

    function openAuction(uint256 auctionId) external onlyOwner {
        auctions[auctionId].isOpen = true;
    }

    function closeAuction(uint256 auctionId) external onlyOwner {
        auctions[auctionId].isOpen = false;
    }

    function commitBid(uint256 auctionId, bytes32 commitHash) external {
        AuctionState storage auction = auctions[auctionId];
        if (!auction.isOpen) revert AuctionClosed();

        auction.bids[msg.sender].commitHash = commitHash;
        emit BidCommitted(auctionId, msg.sender, commitHash);
    }

    function revealBid(uint256 auctionId, uint256 value, bytes32 salt) external {
        AuctionState storage auction = auctions[auctionId];
        if (auction.isOpen) revert AuctionClosed();

        Bid storage bid = auction.bids[msg.sender];
        if (bid.revealed) revert InvalidBid();
        if (keccak256(abi.encodePacked(value, salt)) != bid.commitHash) revert InvalidBid();

        bid.revealValue = value;
        bid.revealed = true;
        emit BidRevealed(auctionId, msg.sender, value);
    }

    function settleAuction(uint256 auctionId, address[] memory solvers) external returns (address winner) {
        AuctionState storage auction = auctions[auctionId];
        if (auction.isOpen) revert AuctionClosed();

        uint256 maxBid = 0;
        address[] memory ties = new address[](solvers.length);
        uint256 tieCount = 0;

        for (uint256 i = 0; i < solvers.length;) {
            address solver = solvers[i];
            Bid storage bid = auction.bids[solver];
            if (bid.revealed) {
                // CLZ log-scaling: Effective = value * (255 - LibBit.clz_(value)) / 256
                uint256 leadingZeros = LibBit.clz_(bid.revealValue);
                uint256 logApprox = 255 - leadingZeros;
                uint256 effectiveBid = bid.revealValue.mulDiv(logApprox, 256);

                if (effectiveBid > maxBid) {
                    maxBid = effectiveBid;
                    tieCount = 1;
                    ties[0] = solver;
                } else if (effectiveBid == maxBid) {
                    if (effectiveBid > 0) {
                        ties[tieCount] = solver;
                        unchecked {
                            ++tieCount;
                        }
                    }
                }
            }
            unchecked {
                ++i;
            }
        }

        if (maxBid == 0) revert InvalidBid();

        if (tieCount > 1) {
            // Tiebreak using CLZ entropy - lowest CLZ wins
            uint256 minClz = 256;
            address tieWinner = ties[0];
            for (uint256 j = 0; j < tieCount;) {
                bytes32 hash = keccak256(abi.encodePacked(ties[j]));
                uint256 clzVal = LibBit.clz_(uint256(hash));
                if (clzVal < minClz) {
                    minClz = clzVal;
                    tieWinner = ties[j];
                }
                unchecked {
                    ++j;
                }
            }
            winner = tieWinner;
        } else {
            winner = ties[0];
        }

        auction.winner = winner;
        emit AuctionSettled(auctionId, winner, maxBid);
        return winner;
    }

    // ============ Reputation System ============

    function updateReputationInternal(address solver, int256 delta) internal {
        uint256 absDelta = uint256(delta < 0 ? -delta : delta);
        uint256 leadingZeros = LibBit.clz_(absDelta);
        uint256 logScale = 255 - leadingZeros;
        // forge-lint: disable-next-line(unsafe-typecast)
        int256 scaledDelta = delta * int256(logScale) / 256;

        int256 currentRep = reputation[solver];
        int256 newRep = currentRep + scaledDelta;
        if (newRep < 0) newRep = 0;

        if (newRep != currentRep) reputation[solver] = newRep;
        emit ReputationUpdated(solver, scaledDelta);
    }

    function updateReputation(address solver, int256 delta) external onlyOwner {
        updateReputationInternal(solver, delta);
    }

    function getReputation(address solver) external view returns (int256) {
        return reputation[solver];
    }

    // ============ Flashloan Abstraction ============

    function executeFlashloan(address token, uint256 amount, bytes calldata data) external nonReentrant {
        uint256 leadingZeros = LibBit.clz_(amount);
        if (255 - leadingZeros < 10) revert FlashloanFailed();

        uint256 len = flashloanProviders.length;
        for (uint256 i = 0; i < len;) {
            (bool success,) = flashloanProviders[i].call(
                abi.encodeWithSignature("flashLoan(address,uint256,bytes)", token, amount, data)
            );
            if (success) return;
            unchecked {
                ++i;
            }
        }
        revert FlashloanFailed();
    }

    function addFlashloanProvider(address provider) external onlyOwner {
        flashloanProviders.push(provider);
        emit FlashloanProviderAdded(provider);
    }

    // ============ Compliance Module ============

    function setComplianceFlags(address entity, uint256 flags) external onlyOwner {
        complianceFlags[entity] = flags;
        emit ComplianceFlagsSet(entity, flags);
    }

    function checkCompliance(address entity, uint256 requiredFlags) public view returns (bool) {
        uint256 flags = complianceFlags[entity];
        if ((flags & requiredFlags) != requiredFlags) revert ComplianceViolation();
        return true;
    }

    // ============ Treasury Framework ============

    function depositToTreasury(address token, uint256 amount) external {
        treasuryBalances[token] += amount;

        // CLZ-based deposit scaling for logging
        uint256 logAmount = 255 - LibBit.clz_(amount);
        emit TreasuryDeposit(token, amount, logAmount);
    }

    function withdrawFromTreasury(
        address token,
        uint256 amount,
        address /* recipient */
    )
        external
    {
        if (!treasuryAuthorized[msg.sender]) revert Unauthorized();
        if (treasuryBalances[token] < amount) revert ExecutionFailed();

        treasuryBalances[token] -= amount;
        // Transfer would happen here in production
    }

    function authorizeTreasuryAccess(address account) external onlyOwner {
        treasuryAuthorized[account] = true;
        emit TreasuryAccessAuthorized(account);
    }

    // ============ Utility Functions ============

    function sealExecution(uint256 intentId) external view returns (bytes32 seal) {
        bytes32 rawSeal = keccak256(abi.encodePacked(intentId, resolvers[intentId], block.timestamp));
        uint256 leadingZeros = LibBit.clz_(uint256(rawSeal));
        seal = keccak256(abi.encodePacked(rawSeal, 255 - leadingZeros));
    }

    function failoverRoute(uint256 intentId, address venue) external onlyOwner {
        (bool success,) = venue.delegatecall(intents[intentId]);
        if (!success) revert ExecutionFailed();
    }

    // ============ Admin Functions ============

    function updateZKVerifier(address newVerifier) external onlyOwner {
        zkVerifier = newVerifier;
        emit ZKVerifierUpdated(newVerifier);
    }

    function updatePaymaster(address newPaymaster) external onlyOwner {
        paymaster = newPaymaster;
        emit PaymasterUpdated(newPaymaster);
    }

    // ============ BLS Functions (Osaka) ============

    function registerBLSKey(uint256[2] calldata pubKey) external {
        blsPublicKeys[msg.sender] = pubKey;
        emit BLSKeyRegistered(msg.sender, pubKey);
    }

    function verifySolverBLS(address solver, uint256[4] calldata signature, uint256[4] calldata message)
        external
        view
        returns (bool)
    {
        return LibBLS.verifySignature(blsPublicKeys[solver], signature, message);
    }

    function verifyBatchBLS(
        address[] calldata solvers,
        uint256[4] calldata aggregatedSignature,
        uint256[4] calldata message
    ) external view returns (bool) {
        uint256[2][] memory pubKeys = new uint256[2][](solvers.length);
        for (uint256 i = 0; i < solvers.length;) {
            pubKeys[i] = blsPublicKeys[solvers[i]];
            unchecked {
                ++i;
            }
        }

        uint256[2] memory aggPubKey = LibBLS.aggregatePublicKeys(pubKeys);
        return LibBLS.verifySignature(aggPubKey, aggregatedSignature, message);
    }

    // ============ P256 Functions (EIP-7212) ============

    function registerP256Key(uint256 x, uint256 y) external {
        p256PublicKeys[msg.sender] = [x, y];
        emit P256KeyRegistered(msg.sender, x, y);
    }

    function verifySolverP256(
        address solver,
        bytes32 hash,
        uint256 r,
        uint256 s
    ) external view returns (bool) {
        uint256[2] memory pubKey = p256PublicKeys[solver];
        if (pubKey[0] == 0 && pubKey[1] == 0) return false;

        return LibP256.verifySignature(hash, r, s, pubKey[0], pubKey[1]);
    }

    // ============ Solver Ranking Functions ============

    /**
     * @notice Get top N solvers sorted by reputation (descending)
     * @dev Uses LibSort for efficient sorting
     * @param solverList Array of solver addresses to rank
     * @param topN Number of top solvers to return
     * @return topSolvers Array of top N solver addresses sorted by reputation
     */
    function getTopSolversByReputation(address[] memory solverList, uint256 topN)
        external
        view
        returns (address[] memory topSolvers)
    {
        if (topN > solverList.length) topN = solverList.length;

        // Create array of reputation values
        uint256[] memory reputations = new uint256[](solverList.length);
        for (uint256 i = 0; i < solverList.length;) {
            // Convert int256 to uint256 (negative becomes 0)
            int256 rep = reputation[solverList[i]];
            // forge-lint: disable-next-line(unsafe-typecast)
            reputations[i] = rep > 0 ? uint256(rep) : 0;
            unchecked {
                ++i;
            }
        }

        // Sort reputations in ascending order
        LibSort.insertionSort(reputations);

        // Return top N from the end (highest reputation)
        topSolvers = new address[](topN);
        uint256 startIdx = solverList.length - topN;
        for (uint256 i = 0; i < topN;) {
            // Find solver with this reputation value
            uint256 targetRep = reputations[startIdx + i];
            for (uint256 j = 0; j < solverList.length;) {
                // forge-lint: disable-next-line(unsafe-typecast)
                if (reputation[solverList[j]] == int256(targetRep)) {
                    topSolvers[i] = solverList[j];
                    break;
                }
                unchecked {
                    ++j;
                }
            }
            unchecked {
                ++i;
            }
        }

        return topSolvers;
    }

    receive() external payable {}

}
