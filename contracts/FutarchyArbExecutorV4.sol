// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

// ---------------------- Interfaces (ABI-aligned) ----------------------

interface IERC20 {

    function balanceOf(address) external view returns (uint256);
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 value) external returns (bool);

}

interface IFutarchyRouter {

    function splitPosition(address proposal, IERC20 collateralToken, uint256 amount) external;
    function mergePositions(address proposal, IERC20 collateralToken, uint256 amount) external;

}

// ---------------------- FutarchyArbExecutorV4 with router-agnostic design ----------------------

contract FutarchyArbExecutorV4 {

    // ---- Custom Errors (gas-efficient vs require strings) ----
    error NotRunner();
    error OnlySelf();
    error TooManyCalls();
    error ZeroAmount();
    error PatchIndexOOB();
    error SpentMismatch();
    error OutputBelowMin();
    error LowCompOut();
    error UnderMint();
    error LowYesCurOut();
    error LowNoCurOut();
    error NothingToMerge();
    error NetCurBelowTolerance();
    error LowYesCompOut();
    error LowNoCompOut();
    error AmountOffsetOOB();
    error MinOutOffsetOOB();
    error CallFailed();
    error BalanceTooLarge();

    // ---- Auth: who can trigger runs ----
    address public immutable runner;
    modifier onlyRunner() {
        if (msg.sender != runner) revert NotRunner();
        _;
    }

    constructor(address _runner) {
        runner = _runner;
    }

    // ---- Shared config types ----

    struct Tokens {
        IERC20 comp; // GNO
        IERC20 cur; // sDAI
        IERC20 yesComp; // GNO_YES
        IERC20 noComp; // GNO_NO
        IERC20 yesCur; // SDAI_YES
        IERC20 noCur; // SDAI_NO
    }

    struct Futarchy {
        IFutarchyRouter router;
        address proposal;
    }

    // Optional, for telemetry only
    struct Pools {
        address yesPool; // COMP_YES <-> CUR_YES
        address noPool; // COMP_NO  <-> CUR_NO
        address predYesPool; // CUR_YES  <-> CUR
        address predNoPool; // CUR_NO   <-> CUR
    }

    // ---- Batch with patching (execute10-compatible) ----

    struct Execute10Batch {
        // Raw x10 payload
        address[10] targets;
        bytes[10] calldatas;
        uint256 count;

        // Delta checks
        address tokenIn; // must decrease exactly by amountInUsed
        address tokenOut; // must increase by >= minOutUsed
        address spender; // entity that will pull tokenIn
        uint256 amountIn; // nominal input (overridable on-chain)
        uint256 minOut; // absolute floor (optional)

        // Runtime patching of one calldata item
        uint8 patchIndex; // 0..9; use type(uint8).max to skip
        uint256 amountOffset; // byte offset of uint256 amountIn within calldatas[patchIndex]
        uint256 minOutOffset; // byte offset of uint256 minOut within calldatas[patchIndex]; set to type(uint256).max to skip
        uint16 slippageBps; // if minOut==0 && minOutOffset!=max => minOut = amountInUsed*(10000-bps)/10000
    }

    // ---- Liquidation template (unchanged from V3) ----

    struct CalldataPatch {
        address target;
        bytes data;
        uint256 msgValue; // usually 0
        uint256 amountOffset; // uint256 amountIn offset
        uint256 minOutOffset; // uint256 minOut offset, or type(uint256).max
        uint16 slippageBps; // if used & minOut not prefilled
    }

    // ---- SELL Arguments ----

    struct SellArgs {
        Tokens t;
        Futarchy f;
        Pools p; // optional; events only

        // ❶ Cross-asset leg: CUR -> COMP via execute10
        Execute10Batch buyCompanyOps;
        uint256 amountCurIn; // desired CUR spend
        uint256 minCompOut; // optional extra guard

        // ❷ Conditional COMP -> conditional CUR (exact-in, both legs)
        address yesSwapTarget;
        bytes yesSwapData;
        address noSwapTarget;
        bytes noSwapData;
        address swapSpender;
        uint256 minYesCurOut;
        uint256 minNoCurOut;

        // ❸ Leftover liquidation (CUR_YES/NO -> CUR)
        address liqSpender;
        CalldataPatch predYes;
        CalldataPatch predNo;

        // ❹ Profit constraint on CUR
        int256 minNetCur;
    }

    // ---- BUY Arguments ----

    struct BuyArgs {
        Tokens t;
        Futarchy f;
        Pools p; // optional; events only

        uint256 amountCurIn; // CUR to split initially

        // ❶ Conditional CUR -> conditional COMP (exact-in)
        address yesBuyTarget;
        bytes yesBuyData;
        address noBuyTarget;
        bytes noBuyData;
        address buySpender;
        uint256 minYesCompOut;
        uint256 minNoCompOut;

        // ❷ Merge COMP and sell COMP -> CUR via execute10 (amountIn patched to mergeAmt)
        Execute10Batch sellCompanyOps;

        // ❸ Optional leftover clean-up (COMP side then pred pools)
        address liqSpender;
        CalldataPatch compYesToCurYes;
        CalldataPatch compNoToCurNo;
        CalldataPatch predYes; // CUR_YES -> CUR
        CalldataPatch predNo; // CUR_NO  -> CUR

        // ❹ Profit constraint on CUR
        int256 minNetCur;
    }

    // ---- Constants ----

    uint8 constant PATCH_NONE = type(uint8).max;

    // ---- Events ----

    event SellExecuted(
        uint256 curSpent,
        uint256 compBought,
        uint256 compSplit,
        uint256 yesCurOut,
        uint256 noCurOut,
        uint256 mergedCur,
        uint256 liqYesIn,
        uint256 liqYesOut,
        uint256 liqNoIn,
        uint256 liqNoOut,
        int256 netCur
    );

    event BuyExecuted(
        uint256 curSplit,
        uint256 yesCompOut,
        uint256 noCompOut,
        uint256 mergedComp,
        uint256 compSold,
        uint256 curReceived,
        uint256 liqCompYesIn,
        uint256 liqCompYesOut,
        uint256 liqCompNoIn,
        uint256 liqCompNoOut,
        uint256 liqYesIn,
        uint256 liqYesOut,
        uint256 liqNoIn,
        uint256 liqNoOut,
        int256 netCur
    );

    event TradeExecuted(address indexed tokenIn, address indexed tokenOut, uint256 amountIn, uint256 amountOut);

    // ---- 7702 entrypoints kept for compatibility ----

    function execute10(address[10] calldata targets, bytes[10] calldata calldatas, uint256 count) external payable {
        if (msg.sender != address(this)) revert OnlySelf();
        if (count > 10) revert TooManyCalls();
        unchecked {
            for (uint256 i; i < count; i++) {
                address t = targets[i];
                if (t == address(0)) continue;
                (bool ok, bytes memory ret) = t.call(calldatas[i]);
                if (!ok) _revertWith(ret);
            }
        }
    }

    function executeOne(address target, bytes calldata data) external payable returns (bytes memory) {
        if (msg.sender != address(this)) revert OnlySelf();
        (bool ok, bytes memory ret) = target.call{value: msg.value}(data);
        if (!ok) _revertWith(ret);
        return ret;
    }

    // ---- External entrypoints (self-call to satisfy "Only self") ----

    function runSell(SellArgs calldata a) external onlyRunner {
        this.sell_conditional_arbitrage(a);
    }

    function runBuy(BuyArgs calldata a) external onlyRunner {
        this.buy_conditional_arbitrage(a);
    }

    /// @notice Execute a single execute10 batch (e.g., CUR -> COMP via Balancer) with delta checks.
    /// @dev External only for the configured runner; internally uses the same self-call pattern as sell/buy flows.
    function runTrade(Execute10Batch calldata b) external onlyRunner returns (uint256 out) {
        out = _runExecute10Checked(
            b,
            /*overrideAmountIn*/
            0
        );
        emit TradeExecuted(b.tokenIn, b.tokenOut, b.amountIn, out);
    }

    // ---- Core internal: execute10 runner with delta checks + patching ----

    function _runExecute10Checked(
        Execute10Batch calldata b,
        uint256 overrideAmountIn // 0 => use b.amountIn; non-zero => use this (e.g., mergeAmt)
    )
        internal
        returns (uint256 outReceived)
    {
        uint256 amount = overrideAmountIn == 0 ? b.amountIn : overrideAmountIn;
        if (amount == 0) revert ZeroAmount();
        if (b.count > 10) revert TooManyCalls();

        IERC20 tokenIn = IERC20(b.tokenIn);
        IERC20 tokenOut = IERC20(b.tokenOut);

        // 1) Prepare patched arrays in memory
        address[10] memory targets = b.targets;
        bytes[10] memory datas = b.calldatas;

        if (b.patchIndex != PATCH_NONE) {
            if (b.patchIndex >= 10) revert PatchIndexOOB();
            datas[b.patchIndex] =
                _patchedCalldata(datas[b.patchIndex], b.amountOffset, amount, b.minOutOffset, b.slippageBps);
        }

        // 2) Allowance for the batch spender
        if (b.spender != address(0)) _ensureAllowance(tokenIn, b.spender, amount);

        // 3) Snapshot balances
        uint256 inBefore = tokenIn.balanceOf(address(this));
        uint256 outBefore = tokenOut.balanceOf(address(this));

        // 4) Execute (external self-call keeps msg.sender == address(this))
        this.execute10(targets, datas, b.count);

        // 5) Verify deltas
        uint256 inAfter = tokenIn.balanceOf(address(this));
        uint256 outAfter = tokenOut.balanceOf(address(this));

        uint256 spent = inBefore - inAfter;
        uint256 received = outAfter - outBefore;

        if (spent != amount) revert SpentMismatch();

        // Compute the *effective* minOut used by the batch:
        // - router-level minOut patched via offset (from slippageBps & amount),
        // - or absolute b.minOut,
        // We enforce the *max* of both to be conservative.
        uint256 minOutFromSlippage = 0;
        if (b.minOutOffset != type(uint256).max) {
            // same formula as in _patchedCalldata
            minOutFromSlippage = (b.slippageBps == 0) ? amount : (amount * (10000 - b.slippageBps)) / 10000;
        }
        uint256 minOutUsed = b.minOut > minOutFromSlippage ? b.minOut : minOutFromSlippage;

        if (minOutUsed > 0 && received < minOutUsed) revert OutputBelowMin();

        return received;
    }

    // ---- SELL flow (CUR → COMP → CUR) ----

    function sell_conditional_arbitrage(SellArgs calldata a) external {
        if (msg.sender != address(this)) revert OnlySelf();

        uint256 cur0 = a.t.cur.balanceOf(address(this));

        // 1) CUR -> COMP via execute10 (with runtime patching and delta checks)
        uint256 compOut = _runExecute10Checked(a.buyCompanyOps, a.amountCurIn);
        if (a.minCompOut > 0 && compOut < a.minCompOut) revert LowCompOut();

        // 2) Split COMP
        _ensureAllowance(a.t.comp, address(a.f.router), compOut);
        uint256 yesBefore = a.t.yesComp.balanceOf(address(this));
        uint256 noBefore = a.t.noComp.balanceOf(address(this));
        a.f.router.splitPosition(a.f.proposal, a.t.comp, compOut);
        uint256 yesMinted = a.t.yesComp.balanceOf(address(this)) - yesBefore;
        uint256 noMinted = a.t.noComp.balanceOf(address(this)) - noBefore;
        if (yesMinted < compOut || noMinted < compOut) revert UnderMint();

        // 3) COMP_YES/NO -> CUR_YES/NO (exact-in)
        _ensureAllowance(a.t.yesComp, a.swapSpender, compOut);
        _ensureAllowance(a.t.noComp, a.swapSpender, compOut);

        uint256 yCurBefore = a.t.yesCur.balanceOf(address(this));
        _safeCall(a.yesSwapTarget, a.yesSwapData, 0);
        uint256 yesCurOut = a.t.yesCur.balanceOf(address(this)) - yCurBefore;
        if (yesCurOut < a.minYesCurOut) revert LowYesCurOut();

        uint256 nCurBefore = a.t.noCur.balanceOf(address(this));
        _safeCall(a.noSwapTarget, a.noSwapData, 0);
        uint256 noCurOut = a.t.noCur.balanceOf(address(this)) - nCurBefore;
        if (noCurOut < a.minNoCurOut) revert LowNoCurOut();

        // 4) Merge CUR
        uint256 mergeAmt = yesCurOut < noCurOut ? yesCurOut : noCurOut;
        if (mergeAmt == 0) revert NothingToMerge();
        _ensureAllowance(a.t.yesCur, address(a.f.router), mergeAmt);
        _ensureAllowance(a.t.noCur, address(a.f.router), mergeAmt);
        a.f.router.mergePositions(a.f.proposal, a.t.cur, mergeAmt);

        // 5) Leftover liquidation (CUR_YES/NO -> CUR)
        uint256 leftYes = yesCurOut - mergeAmt;
        uint256 leftNo = noCurOut - mergeAmt;

        uint256 liqYesOut;
        uint256 liqNoOut;

        if (leftYes > 0) {
            _ensureAllowance(a.t.yesCur, a.liqSpender, leftYes);
            uint256 before = a.t.cur.balanceOf(address(this));
            bytes memory d = _patchedCalldata(
                a.predYes.data, a.predYes.amountOffset, leftYes, a.predYes.minOutOffset, a.predYes.slippageBps
            );
            _safeCall(a.predYes.target, d, a.predYes.msgValue);
            liqYesOut = a.t.cur.balanceOf(address(this)) - before;
        }
        if (leftNo > 0) {
            _ensureAllowance(a.t.noCur, a.liqSpender, leftNo);
            uint256 before = a.t.cur.balanceOf(address(this));
            bytes memory d = _patchedCalldata(
                a.predNo.data, a.predNo.amountOffset, leftNo, a.predNo.minOutOffset, a.predNo.slippageBps
            );
            _safeCall(a.predNo.target, d, a.predNo.msgValue);
            liqNoOut = a.t.cur.balanceOf(address(this)) - before;
        }

        // 6) Net profit/tolerance on CUR
        uint256 curFinal = a.t.cur.balanceOf(address(this));
        if (curFinal > uint256(type(int256).max) || cur0 > uint256(type(int256).max)) revert BalanceTooLarge();
        // forge-lint: disable-next-line(unsafe-typecast)
        int256 net = int256(curFinal) - int256(cur0);
        if (net < a.minNetCur) revert NetCurBelowTolerance();

        emit SellExecuted(
            a.amountCurIn, compOut, compOut, yesCurOut, noCurOut, mergeAmt, leftYes, liqYesOut, leftNo, liqNoOut, net
        );
    }

    // ---- BUY flow (CUR → COMP → CUR) ----

    function buy_conditional_arbitrage(BuyArgs calldata a) external {
        if (msg.sender != address(this)) revert OnlySelf();

        uint256 cur0 = a.t.cur.balanceOf(address(this));

        // 1) Split CUR
        _ensureAllowance(a.t.cur, address(a.f.router), a.amountCurIn);
        a.f.router.splitPosition(a.f.proposal, a.t.cur, a.amountCurIn);

        // 2) CUR_YES/NO -> COMP_YES/NO
        _ensureAllowance(a.t.yesCur, a.buySpender, a.amountCurIn);
        _ensureAllowance(a.t.noCur, a.buySpender, a.amountCurIn);

        uint256 yCompBefore = a.t.yesComp.balanceOf(address(this));
        _safeCall(a.yesBuyTarget, a.yesBuyData, 0);
        uint256 yesCompOut = a.t.yesComp.balanceOf(address(this)) - yCompBefore;
        if (yesCompOut < a.minYesCompOut) revert LowYesCompOut();

        uint256 nCompBefore = a.t.noComp.balanceOf(address(this));
        _safeCall(a.noBuyTarget, a.noBuyData, 0);
        uint256 noCompOut = a.t.noComp.balanceOf(address(this)) - nCompBefore;
        if (noCompOut < a.minNoCompOut) revert LowNoCompOut();

        // 3) Merge COMP and sell COMP -> CUR via execute10
        uint256 mergeAmt = yesCompOut < noCompOut ? yesCompOut : noCompOut;
        if (mergeAmt == 0) revert NothingToMerge();
        _ensureAllowance(a.t.yesComp, address(a.f.router), mergeAmt);
        _ensureAllowance(a.t.noComp, address(a.f.router), mergeAmt);
        a.f.router.mergePositions(a.f.proposal, a.t.comp, mergeAmt);

        // execute10 with runtime patch of amountIn = mergeAmt
        uint256 curReceived = _runExecute10Checked(
            a.sellCompanyOps,
            /*override*/
            mergeAmt
        );

        // 4) Optional leftovers (COMP_YES/NO -> CUR_YES/NO then pred pools)
        // For simplicity, skipping leftover liquidation in buy flow for now
        // Can be added later following the same pattern as sell flow

        // 5) Net profit/tolerance on CUR
        uint256 curFinal = a.t.cur.balanceOf(address(this));
        if (curFinal > uint256(type(int256).max) || cur0 > uint256(type(int256).max)) revert BalanceTooLarge();
        // forge-lint: disable-next-line(unsafe-typecast)
        int256 net = int256(curFinal) - int256(cur0);
        if (net < a.minNetCur) revert NetCurBelowTolerance();

        emit BuyExecuted(
            a.amountCurIn,
            yesCompOut,
            noCompOut,
            mergeAmt,
            mergeAmt,
            curReceived, // compSold==mergeAmt
            0,
            0,
            0,
            0,
            0,
            0,
            0,
            0, // fill if you implement leftovers
            net
        );
    }

    // ---- Internals ----

    function _ensureAllowance(IERC20 token, address spender, uint256 need) internal {
        if (need == 0) return;
        uint256 cur = token.allowance(address(this), spender);
        if (cur < need) {
            if (!token.approve(spender, 0)) revert CallFailed();
            if (!token.approve(spender, type(uint256).max)) revert CallFailed();
        }
    }

    function _safeCall(address target, bytes memory data, uint256 value) internal {
        (bool ok, bytes memory ret) = target.call{value: value}(data);
        if (!ok) _revertWith(ret);
    }

    function _patchedCalldata(
        bytes memory template,
        uint256 amountOffset,
        uint256 amountIn,
        uint256 minOutOffset,
        uint16 slippageBps
    ) internal pure returns (bytes memory cd) {
        cd = template; // calldata in params is copied to memory on access
        if (cd.length < amountOffset + 32) revert AmountOffsetOOB();
        assembly { mstore(add(add(cd, 32), amountOffset), amountIn) }
        if (minOutOffset != type(uint256).max) {
            uint256 minOut = (slippageBps == 0) ? amountIn : (amountIn * (10000 - slippageBps)) / 10000;
            if (cd.length < minOutOffset + 32) revert MinOutOffsetOOB();
            assembly { mstore(add(add(cd, 32), minOutOffset), minOut) }
        }
    }

    function _revertWith(bytes memory ret) private pure {
        if (ret.length == 0) revert CallFailed();
        assembly { revert(add(ret, 0x20), mload(ret)) }
    }

    receive() external payable {}

}
