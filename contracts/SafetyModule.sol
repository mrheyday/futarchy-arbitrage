// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/**
 * @title SafetyModule
 * @notice Circuit breakers and emergency controls for arbitrage executors
 * @dev Provides:
 *      - Price deviation limits (max slippage)
 *      - Gas price ceiling (pause if gas too high)
 *      - Daily loss limits (pause if cumulative loss exceeds threshold)
 *      - Cooldown periods between large trades
 *      - Emergency pause mechanism
 */
contract SafetyModule {

    // ============================================
    // ERRORS
    // ============================================

    error Paused();
    error SlippageExceeded(uint256 actual, uint256 max);
    error GasPriceTooHigh(uint256 actual, uint256 max);
    error DailyLossLimitExceeded(int256 totalLoss, uint256 limit);
    error CooldownActive(uint256 timeRemaining);
    error OnlyOwner();
    error InvalidParameter();

    // ============================================
    // EVENTS
    // ============================================

    event EmergencyPause(address indexed triggeredBy, string reason);
    event EmergencyUnpause(address indexed triggeredBy);
    event SlippageCircuitTripped(uint256 slippage, uint256 limit);
    event GasCircuitTripped(uint256 gasPrice, uint256 limit);
    event DailyLossCircuitTripped(int256 loss, uint256 limit);
    event ParametersUpdated(uint256 maxSlippage, uint256 maxGasPrice, uint256 dailyLossLimit, uint256 cooldownSeconds);
    event TradeRecorded(int256 profitLoss, uint256 timestamp);

    // ============================================
    // STATE
    // ============================================

    address public owner;
    bool public paused;

    // Circuit breaker parameters
    uint256 public maxSlippageBps; // Max slippage in basis points (e.g., 500 = 5%)
    uint256 public maxGasPrice; // Max gas price in wei (e.g., 100 gwei)
    uint256 public dailyLossLimit; // Max loss per day in wei
    uint256 public cooldownSeconds; // Cooldown between large trades

    // Trading state
    uint256 public lastTradeTimestamp;
    int256 public dailyProfitLoss; // Can be negative
    uint256 public dailyResetTimestamp;

    // Constants
    uint256 private constant BPS_DENOMINATOR = 10000;
    uint256 private constant ONE_DAY = 86400;

    // ============================================
    // CONSTRUCTOR
    // ============================================

    constructor() {
        owner = msg.sender;

        // Default parameters (conservative)
        maxSlippageBps = 500; // 5% max slippage
        maxGasPrice = 100 gwei; // 100 gwei max
        dailyLossLimit = 10 ether; // 10 ETH equivalent max loss per day
        cooldownSeconds = 60; // 1 minute between trades

        dailyResetTimestamp = block.timestamp + ONE_DAY;
    }

    // ============================================
    // MODIFIERS
    // ============================================

    modifier onlyOwner() {
        if (msg.sender != owner) revert OnlyOwner();
        _;
    }

    modifier whenNotPaused() {
        if (paused) revert Paused();
        _;
    }

    // ============================================
    // CIRCUIT BREAKER CHECKS
    // ============================================

    /**
     * @notice Check if trade can proceed based on all circuit breaker conditions
     * @param expectedOutput Expected output amount from trade
     * @param minOutput Minimum acceptable output (accounting for slippage)
     * @param profitLoss Estimated profit/loss from trade (can be negative)
     */
    function checkTradeAllowed(uint256 expectedOutput, uint256 minOutput, int256 profitLoss) external whenNotPaused {
        // Check slippage
        uint256 slippageBps = ((expectedOutput - minOutput) * BPS_DENOMINATOR) / expectedOutput;
        if (slippageBps > maxSlippageBps) {
            emit SlippageCircuitTripped(slippageBps, maxSlippageBps);
            revert SlippageExceeded(slippageBps, maxSlippageBps);
        }

        // Check gas price
        if (tx.gasprice > maxGasPrice) {
            emit GasCircuitTripped(tx.gasprice, maxGasPrice);
            revert GasPriceTooHigh(tx.gasprice, maxGasPrice);
        }

        // Reset daily counter if needed
        if (block.timestamp >= dailyResetTimestamp) {
            dailyProfitLoss = 0;
            dailyResetTimestamp = block.timestamp + ONE_DAY;
        }

        // Check daily loss limit
        int256 newDailyTotal = dailyProfitLoss + profitLoss;
        // forge-lint: disable-next-line(unsafe-typecast)
        if (newDailyTotal < 0 && uint256(-newDailyTotal) > dailyLossLimit) {
            emit DailyLossCircuitTripped(newDailyTotal, dailyLossLimit);
            revert DailyLossLimitExceeded(newDailyTotal, dailyLossLimit);
        }

        // Check cooldown (skip on first trade)
        if (lastTradeTimestamp > 0 && block.timestamp < lastTradeTimestamp + cooldownSeconds) {
            uint256 timeRemaining = (lastTradeTimestamp + cooldownSeconds) - block.timestamp;
            revert CooldownActive(timeRemaining);
        }

        // All checks passed - record trade
        dailyProfitLoss = newDailyTotal;
        lastTradeTimestamp = block.timestamp;

        emit TradeRecorded(profitLoss, block.timestamp);
    }

    // ============================================
    // PARAMETER MANAGEMENT
    // ============================================

    /**
     * @notice Update circuit breaker parameters
     * @param _maxSlippageBps Max slippage in basis points (10000 = 100%)
     * @param _maxGasPrice Max gas price in wei
     * @param _dailyLossLimit Max daily loss in wei
     * @param _cooldownSeconds Seconds between trades
     */
    function updateParameters(
        uint256 _maxSlippageBps,
        uint256 _maxGasPrice,
        uint256 _dailyLossLimit,
        uint256 _cooldownSeconds
    ) external onlyOwner {
        if (_maxSlippageBps > BPS_DENOMINATOR) revert InvalidParameter();

        maxSlippageBps = _maxSlippageBps;
        maxGasPrice = _maxGasPrice;
        dailyLossLimit = _dailyLossLimit;
        cooldownSeconds = _cooldownSeconds;

        emit ParametersUpdated(_maxSlippageBps, _maxGasPrice, _dailyLossLimit, _cooldownSeconds);
    }

    // ============================================
    // EMERGENCY CONTROLS
    // ============================================

    /**
     * @notice Emergency pause - stops all trading
     * @param reason Reason for pause (for logging)
     */
    function emergencyPause(string calldata reason) external onlyOwner {
        paused = true;
        emit EmergencyPause(msg.sender, reason);
    }

    /**
     * @notice Unpause trading
     */
    function unpause() external onlyOwner {
        paused = false;
        emit EmergencyUnpause(msg.sender);
    }

    /**
     * @notice Reset daily profit/loss counter (emergency use)
     */
    function resetDailyCounter() external onlyOwner {
        dailyProfitLoss = 0;
        dailyResetTimestamp = block.timestamp + ONE_DAY;
    }

    /**
     * @notice Transfer ownership
     */
    function transferOwnership(address newOwner) external onlyOwner {
        if (newOwner == address(0)) revert InvalidParameter();
        owner = newOwner;
    }

    // ============================================
    // VIEW FUNCTIONS
    // ============================================

    /**
     * @notice Get current safety status
     */
    function getSafetyStatus()
        external
        view
        returns (bool isPaused, uint256 timeUntilNextTrade, int256 currentDailyPL, uint256 timeUntilDailyReset)
    {
        isPaused = paused;

        if (lastTradeTimestamp > 0 && block.timestamp < lastTradeTimestamp + cooldownSeconds) {
            timeUntilNextTrade = (lastTradeTimestamp + cooldownSeconds) - block.timestamp;
        } else {
            timeUntilNextTrade = 0;
        }

        currentDailyPL = dailyProfitLoss;

        if (block.timestamp < dailyResetTimestamp) timeUntilDailyReset = dailyResetTimestamp - block.timestamp;
        else timeUntilDailyReset = 0;
    }

    /**
     * @notice Calculate slippage from expected and actual output
     */
    function calculateSlippage(uint256 expected, uint256 actual) public pure returns (uint256) {
        if (expected == 0) return 0;
        if (actual >= expected) return 0;
        return ((expected - actual) * BPS_DENOMINATOR) / expected;
    }

}
