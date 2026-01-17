// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/// Minimal interfaces
interface IERC20 {
    function balanceOf(address) external view returns (uint256);
    function approve(address, uint256) external returns (bool);
    function allowance(address, address) external view returns (uint256);
    function transfer(address, uint256) external returns (bool);
}

interface IPermit2 { function approve(address, address, uint160, uint48) external; }
interface IFutarchyRouter {
    function splitPosition(address, address, uint256) external;
    function mergePositions(address, address, uint256) external;
}

interface IAlgebraSwapRouter {
    struct ExactInputSingleParams {
        address tokenIn; address tokenOut; address recipient;
        uint256 deadline; uint256 amountIn; uint256 amountOutMinimum; uint160 limitSqrtPrice;
    }
    function exactInputSingle(ExactInputSingleParams calldata) external payable returns (uint256);
}

interface IUniswapV3Pool { function fee() external view returns (uint24); }

interface ISwapRouterV3ExactOutput {
    struct ExactOutputSingleParams {
        address tokenIn; address tokenOut; uint24 fee; address recipient;
        uint256 deadline; uint256 amountOut; uint256 amountInMaximum; uint160 sqrtPriceLimitX96;
    }
    function exactOutputSingle(ExactOutputSingleParams calldata) external payable returns (uint256);
}

interface IUniswapV2Router02 {
    function swapExactTokensForTokens(uint256, uint256, address[] calldata, address, uint256) external returns (uint256[] memory);
}

interface IBalancerBatchRouter {
    struct SwapPathStep { address pool; address tokenOut; bool isBuffer; }
    struct SwapPathExactAmountIn { address tokenIn; SwapPathStep[] steps; uint256 exactAmountIn; uint256 minAmountOut; }
    function swapExactIn(SwapPathExactAmountIn[] calldata, uint256, bool, bytes calldata) external payable returns (uint256[] memory, address[] memory, uint256[] memory);
}

interface IBalancerVault {
    enum SwapKind { GIVEN_IN, GIVEN_OUT }
    struct BatchSwapStep { bytes32 poolId; uint256 assetInIndex; uint256 assetOutIndex; uint256 amount; bytes userData; }
    struct FundManagement { address sender; bool fromInternalBalance; address recipient; bool toInternalBalance; }
    function batchSwap(SwapKind, BatchSwapStep[] calldata, address[] calldata, FundManagement calldata, int256[] calldata, uint256) external returns (int256[] memory);
}

/// @title FutarchyArbExecutorV5
/// @notice Gas-optimized version with reduced bytecode size
contract FutarchyArbExecutorV5 {
    error Err(uint8 code);

    // Constants
    address internal constant SDAI = 0xaf204776c7245bF4147c2612BF6e5972Ee483701;
    address internal constant WETH = 0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1;
    address internal constant PNK = 0x37b60f4E9A31A64cCc0024dce7D0fD07eAA0F7B3;
    address internal constant BAL_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;
    address internal constant SWAPR_V2 = 0xE43e60736b1cb4a75ad25240E2f9a62Bff65c0C0;
    address internal constant PERMIT2 = 0x000000000022D473030F116dDEE9F6B43aC78BA3;

    bytes32 internal constant POOL_3 = 0x40d2cbc586dd8df50001cdba3f65cd4bbc32d596000200000000000000000154;
    bytes32 internal constant POOL_4 = 0x480d4f66cc41a1b6784a53a10890e5ece31d75c000020000000000000000014e;
    bytes32 internal constant POOL_5 = 0xa99fd9950b5d5dceeaf4939e221dca8ca9b938ab000100000000000000000025;

    address public owner;
    
    event Profit(uint256 initial, uint256 final_, int256 min);

    modifier auth() { if (msg.sender != owner) revert Err(1); _; }
    constructor() { owner = msg.sender; }

    // --- Helpers ---
    function _approve(IERC20 t, address s) internal {
        uint256 c = t.allowance(address(this), s);
        if (c != type(uint256).max) {
            if (c != 0) t.approve(s, 0);
            t.approve(s, type(uint256).max);
        }
    }

    function _permit2(IERC20 t, address r) internal {
        _approve(t, PERMIT2);
        IPermit2(PERMIT2).approve(address(t), r, type(uint160).max, type(uint48).max);
    }

    function _swaprIn(address r, address ti, address to, uint256 a) internal returns (uint256) {
        if (a == 0) return 0;
        _approve(IERC20(ti), r);
        return IAlgebraSwapRouter(r).exactInputSingle(IAlgebraSwapRouter.ExactInputSingleParams(ti, to, address(this), block.timestamp, a, 0, 0));
    }

    function _swaprOut(address r, address ti, address to, uint24 f, uint256 ao, uint256 mi) internal returns (uint256) {
        if (ao == 0) return 0;
        _approve(IERC20(ti), r);
        return ISwapRouterV3ExactOutput(r).exactOutputSingle(ISwapRouterV3ExactOutput.ExactOutputSingleParams(ti, to, f, address(this), block.timestamp, ao, mi, 0));
    }

    function _fee(address p) internal view returns (uint24) {
        if (p == address(0)) return 100;
        try IUniswapV3Pool(p).fee() returns (uint24 f) { return f == 0 ? 100 : f; } catch { return 100; }
    }

    function _pnkAssets() internal pure returns (address[] memory a) {
        a = new address[](5);
        a[0] = SDAI; a[1] = 0xC0d871bD13eBdf5c4ff059D8243Fb38210608bD6; a[2] = WETH;
        a[3] = 0xE0eD85F76D9C552478929fab44693E03F0899F23; a[4] = 0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb;
    }

    // --- PNK Buy: sDAI -> WETH -> PNK ---
    function _buyPnk(uint256 amt) internal {
        if (amt == 0) revert Err(2);
        _approve(IERC20(SDAI), BAL_VAULT);

        address[] memory assets = _pnkAssets();
        IBalancerVault.BatchSwapStep[] memory swaps = new IBalancerVault.BatchSwapStep[](3);
        swaps[0] = IBalancerVault.BatchSwapStep(POOL_3, 0, 3, amt, "");
        swaps[1] = IBalancerVault.BatchSwapStep(POOL_4, 3, 4, 0, "");
        swaps[2] = IBalancerVault.BatchSwapStep(POOL_5, 4, 2, 0, "");

        int256[] memory limits = new int256[](5);
        // forge-lint: disable-next-line(unsafe-typecast)
        limits[0] = int256(amt);

        IBalancerVault(BAL_VAULT).batchSwap(
            IBalancerVault.SwapKind.GIVEN_IN, swaps, assets,
            IBalancerVault.FundManagement(address(this), false, address(this), false),
            limits, type(uint256).max
        );

        uint256 weth = IERC20(WETH).balanceOf(address(this));
        if (weth == 0) revert Err(3);

        _approve(IERC20(WETH), SWAPR_V2);
        address[] memory path = new address[](2);
        path[0] = WETH; path[1] = PNK;
        IUniswapV2Router02(SWAPR_V2).swapExactTokensForTokens(weth, 0, path, address(this), type(uint256).max);
    }

    // --- PNK Sell: PNK -> WETH -> sDAI ---
    function _sellPnk(uint256 amt) internal {
        if (amt == 0) revert Err(2);

        _approve(IERC20(PNK), SWAPR_V2);
        address[] memory path = new address[](2);
        path[0] = PNK; path[1] = WETH;
        IUniswapV2Router02(SWAPR_V2).swapExactTokensForTokens(amt, 0, path, address(this), type(uint256).max);

        uint256 weth = IERC20(WETH).balanceOf(address(this));
        if (weth == 0) revert Err(3);

        _approve(IERC20(WETH), BAL_VAULT);
        address[] memory assets = _pnkAssets();

        uint256 h = weth / 2;
        IBalancerVault.BatchSwapStep[] memory swaps = new IBalancerVault.BatchSwapStep[](5);
        swaps[0] = IBalancerVault.BatchSwapStep(0x7e5870ac540adfd01a213c829f2231c309623eb10002000000000000000000e9, 2, 1, h, "");
        swaps[1] = IBalancerVault.BatchSwapStep(0xa91c413d8516164868f6cca19573fe38f88f5982000200000000000000000157, 1, 0, 0, "");
        swaps[2] = IBalancerVault.BatchSwapStep(POOL_5, 2, 4, weth - h, "");
        swaps[3] = IBalancerVault.BatchSwapStep(POOL_4, 4, 3, 0, "");
        swaps[4] = IBalancerVault.BatchSwapStep(POOL_3, 3, 0, 0, "");

        int256[] memory limits = new int256[](5);
        // forge-lint: disable-next-line(unsafe-typecast)
        limits[2] = int256(weth);

        IBalancerVault(BAL_VAULT).batchSwap(
            IBalancerVault.SwapKind.GIVEN_IN, swaps, assets,
            IBalancerVault.FundManagement(address(this), false, address(this), false),
            limits, type(uint256).max
        );
    }

    // --- Public PNK functions ---
    function buyPnkWithSdai(uint256 amt, uint256, uint256) external auth { _buyPnk(amt); }
    function sellPnkForSdai(uint256 amt, uint256, uint256) external auth { _sellPnk(amt); }

    // --- Helper: Merge remaining conditionals ---
    function _mergeRemainingCond(address r, address yt, address nt, address st) internal {
        uint256 yBal = IERC20(yt).balanceOf(address(this));
        uint256 nBal = IERC20(nt).balanceOf(address(this));
        if (yBal > 0 && nBal > 0) {
            uint256 m = yBal < nBal ? yBal : nBal;
            _approve(IERC20(yt), r);
            _approve(IERC20(nt), r);
            IFutarchyRouter(r).mergePositions(address(0), st, m);
        }
    }

    // --- BUY Conditional Arbitrage (Balancer) ---
    function buy_conditional_arbitrage_balancer(
        address proposal, address router, address swaprRouter, address batchRouter,
        address sdaiYes, address sdaiNo, address gnoYes, address gnoNo,
        address balPool, address gno, uint256 amt, int256 minProfit
    ) external auth {
        uint256 init = IERC20(SDAI).balanceOf(address(this));
        _buyBalancerFlow(proposal, router, swaprRouter, batchRouter, sdaiYes, sdaiNo, gnoYes, gnoNo, balPool, gno, amt);
        uint256 fin = IERC20(SDAI).balanceOf(address(this));
        // forge-lint: disable-next-line(unsafe-typecast)
        if (int256(fin) - int256(init) < minProfit) revert Err(4);
        emit Profit(init, fin, minProfit);
    }

    function _buyBalancerFlow(
        address proposal, address router, address swaprRouter, address batchRouter,
        address sdaiYes, address sdaiNo, address gnoYes, address gnoNo,
        address balPool, address gno, uint256 amt
    ) internal {
        // Split sDAI -> YES/NO
        _approve(IERC20(SDAI), router);
        IFutarchyRouter(router).splitPosition(proposal, SDAI, amt);

        // Swap YES/NO sDAI -> YES/NO GNO
        uint256 yesOut = _swaprIn(swaprRouter, sdaiYes, gnoYes, IERC20(sdaiYes).balanceOf(address(this)));
        uint256 noOut = _swaprIn(swaprRouter, sdaiNo, gnoNo, IERC20(sdaiNo).balanceOf(address(this)));

        // Merge GNO conditionals
        uint256 mergeAmt = yesOut < noOut ? yesOut : noOut;
        _approve(IERC20(gnoYes), router);
        _approve(IERC20(gnoNo), router);
        IFutarchyRouter(router).mergePositions(proposal, gno, mergeAmt);

        // Sell GNO on Balancer
        _sellGnoBalancer(batchRouter, balPool, gno);

        // Sell remaining conditionals
        uint256 remYes = IERC20(gnoYes).balanceOf(address(this));
        uint256 remNo = IERC20(gnoNo).balanceOf(address(this));
        if (remYes > 0) _swaprIn(swaprRouter, gnoYes, sdaiYes, remYes);
        if (remNo > 0) _swaprIn(swaprRouter, gnoNo, sdaiNo, remNo);

        // Merge remaining sDAI conditionals
        _mergeRemainingCond(router, sdaiYes, sdaiNo, SDAI);
    }

    function _sellGnoBalancer(address batchRouter, address balPool, address gno) internal {
        _permit2(IERC20(gno), batchRouter);
        IBalancerBatchRouter.SwapPathExactAmountIn[] memory paths = new IBalancerBatchRouter.SwapPathExactAmountIn[](1);
        IBalancerBatchRouter.SwapPathStep[] memory steps = new IBalancerBatchRouter.SwapPathStep[](1);
        steps[0] = IBalancerBatchRouter.SwapPathStep(balPool, SDAI, false);
        paths[0] = IBalancerBatchRouter.SwapPathExactAmountIn(gno, steps, IERC20(gno).balanceOf(address(this)), 0);
        IBalancerBatchRouter(batchRouter).swapExactIn(paths, type(uint256).max, false, "");
    }

    // --- SELL Conditional Arbitrage (Balancer) ---
    function sell_conditional_arbitrage_balancer(
        address proposal, address router, address swaprRouter, address batchRouter,
        address sdaiYes, address sdaiNo, address gnoYes, address gnoNo,
        address balPool, address gno, uint256 amt, int256 minProfit
    ) external auth {
        uint256 init = IERC20(SDAI).balanceOf(address(this));
        _sellBalancerFlow(proposal, router, swaprRouter, batchRouter, sdaiYes, sdaiNo, gnoYes, gnoNo, balPool, gno, amt);
        uint256 fin = IERC20(SDAI).balanceOf(address(this));
        // forge-lint: disable-next-line(unsafe-typecast)
        if (int256(fin) - int256(init) < minProfit) revert Err(4);
        emit Profit(init, fin, minProfit);
    }

    function _sellBalancerFlow(
        address proposal, address router, address swaprRouter, address batchRouter,
        address sdaiYes, address sdaiNo, address gnoYes, address gnoNo,
        address balPool, address gno, uint256 amt
    ) internal {
        // Buy GNO on Balancer
        _buyGnoBalancer(batchRouter, balPool, gno, amt);

        // Split GNO -> YES/NO
        uint256 gnoBal = IERC20(gno).balanceOf(address(this));
        _approve(IERC20(gno), router);
        IFutarchyRouter(router).splitPosition(proposal, gno, gnoBal);

        // Sell YES/NO GNO -> YES/NO sDAI
        _swaprIn(swaprRouter, gnoYes, sdaiYes, IERC20(gnoYes).balanceOf(address(this)));
        _swaprIn(swaprRouter, gnoNo, sdaiNo, IERC20(gnoNo).balanceOf(address(this)));

        // Merge sDAI conditionals
        uint256 yBal = IERC20(sdaiYes).balanceOf(address(this));
        uint256 nBal = IERC20(sdaiNo).balanceOf(address(this));
        uint256 m = yBal < nBal ? yBal : nBal;
        _approve(IERC20(sdaiYes), router);
        _approve(IERC20(sdaiNo), router);
        IFutarchyRouter(router).mergePositions(proposal, SDAI, m);
    }

    function _buyGnoBalancer(address batchRouter, address balPool, address gno, uint256 amt) internal {
        _permit2(IERC20(SDAI), batchRouter);
        IBalancerBatchRouter.SwapPathExactAmountIn[] memory paths = new IBalancerBatchRouter.SwapPathExactAmountIn[](1);
        IBalancerBatchRouter.SwapPathStep[] memory steps = new IBalancerBatchRouter.SwapPathStep[](1);
        steps[0] = IBalancerBatchRouter.SwapPathStep(balPool, gno, false);
        paths[0] = IBalancerBatchRouter.SwapPathExactAmountIn(SDAI, steps, amt, 0);
        IBalancerBatchRouter(batchRouter).swapExactIn(paths, type(uint256).max, false, "");
    }

    // --- BUY Conditional Arbitrage (PNK) ---
    function buy_conditional_arbitrage_pnk(
        address proposal, address router, address swaprRouter,
        address sdaiYes, address sdaiNo, address pnkYes, address pnkNo,
        uint256 amt, int256 minProfit
    ) external auth {
        uint256 init = IERC20(SDAI).balanceOf(address(this));
        _buyPnkFlow(proposal, router, swaprRouter, sdaiYes, sdaiNo, pnkYes, pnkNo, amt);
        uint256 fin = IERC20(SDAI).balanceOf(address(this));
        // forge-lint: disable-next-line(unsafe-typecast)
        if (int256(fin) - int256(init) < minProfit) revert Err(4);
        emit Profit(init, fin, minProfit);
    }

    function _buyPnkFlow(
        address proposal, address router, address swaprRouter,
        address sdaiYes, address sdaiNo, address pnkYes, address pnkNo,
        uint256 amt
    ) internal {
        // Split sDAI -> YES/NO
        _approve(IERC20(SDAI), router);
        IFutarchyRouter(router).splitPosition(proposal, SDAI, amt);

        // Swap YES/NO sDAI -> YES/NO PNK
        uint256 yesOut = _swaprIn(swaprRouter, sdaiYes, pnkYes, IERC20(sdaiYes).balanceOf(address(this)));
        uint256 noOut = _swaprIn(swaprRouter, sdaiNo, pnkNo, IERC20(sdaiNo).balanceOf(address(this)));

        // Merge PNK conditionals
        uint256 mergeAmt = yesOut < noOut ? yesOut : noOut;
        _approve(IERC20(pnkYes), router);
        _approve(IERC20(pnkNo), router);
        IFutarchyRouter(router).mergePositions(proposal, PNK, mergeAmt);

        // Sell PNK for sDAI
        _sellPnk(IERC20(PNK).balanceOf(address(this)));

        // Sell remaining conditionals
        uint256 remYes = IERC20(pnkYes).balanceOf(address(this));
        uint256 remNo = IERC20(pnkNo).balanceOf(address(this));
        if (remYes > 0) _swaprIn(swaprRouter, pnkYes, sdaiYes, remYes);
        if (remNo > 0) _swaprIn(swaprRouter, pnkNo, sdaiNo, remNo);

        // Merge remaining sDAI conditionals
        _mergeRemainingCond(router, sdaiYes, sdaiNo, SDAI);
    }

    // --- SELL Conditional Arbitrage (PNK) ---
    function sell_conditional_arbitrage_pnk(
        address proposal, address router, address swaprRouter,
        address sdaiYes, address sdaiNo, address pnkYes, address pnkNo,
        uint256 amt, int256 minProfit
    ) external auth {
        uint256 init = IERC20(SDAI).balanceOf(address(this));
        _sellPnkFlow(proposal, router, swaprRouter, sdaiYes, sdaiNo, pnkYes, pnkNo, amt);
        uint256 fin = IERC20(SDAI).balanceOf(address(this));
        // forge-lint: disable-next-line(unsafe-typecast)
        if (int256(fin) - int256(init) < minProfit) revert Err(4);
        emit Profit(init, fin, minProfit);
    }

    function _sellPnkFlow(
        address proposal, address router, address swaprRouter,
        address sdaiYes, address sdaiNo, address pnkYes, address pnkNo,
        uint256 amt
    ) internal {
        // Buy PNK with sDAI
        _buyPnk(amt);

        // Split PNK -> YES/NO
        uint256 pnkBal = IERC20(PNK).balanceOf(address(this));
        _approve(IERC20(PNK), router);
        IFutarchyRouter(router).splitPosition(proposal, PNK, pnkBal);

        // Sell YES/NO PNK -> YES/NO sDAI
        _swaprIn(swaprRouter, pnkYes, sdaiYes, IERC20(pnkYes).balanceOf(address(this)));
        _swaprIn(swaprRouter, pnkNo, sdaiNo, IERC20(pnkNo).balanceOf(address(this)));

        // Merge sDAI conditionals
        uint256 yBal = IERC20(sdaiYes).balanceOf(address(this));
        uint256 nBal = IERC20(sdaiNo).balanceOf(address(this));
        uint256 m = yBal < nBal ? yBal : nBal;
        _approve(IERC20(sdaiYes), router);
        _approve(IERC20(sdaiNo), router);
        IFutarchyRouter(router).mergePositions(proposal, SDAI, m);
    }

    // --- Admin functions ---
    function transferOwnership(address newOwner) external auth {
        if (newOwner == address(0)) revert Err(99);
        owner = newOwner;
    }
    function withdrawToken(address t, address to, uint256 a) external auth { if (!IERC20(t).transfer(to, a)) revert Err(50); }
    function sweepToken(address t, address to) external auth { uint256 bal = IERC20(t).balanceOf(address(this)); if (bal > 0 && !IERC20(t).transfer(to, bal)) revert Err(50); }
    function withdrawETH(address to, uint256 a) external auth { (bool ok,) = payable(to).call{value: a}(""); require(ok); }
    receive() external payable {}
}