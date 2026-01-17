// SPDX-License-Identifier: MIT
pragma solidity 0.8.33;

/**
 * @title FutarchyBatchExecutorUltra
 * @notice Ultra-simple implementation that avoids all 0xEF triggers
 * @dev No arrays, no loops, just sequential execution
 */
contract FutarchyBatchExecutorUltra {

    // Custom errors
    error OnlySelf();
    error Call1Failed();
    error Call2Failed();
    error Call3Failed();
    error Call4Failed();
    error Call5Failed();
    error Call6Failed();
    error Call7Failed();
    error Call8Failed();
    error Call9Failed();
    error Call10Failed();
    error Call11Failed();

    event Executed(address target);

    modifier onlySelf() {
        if (msg.sender != address(this)) revert OnlySelf();
        _;
    }

    /**
     * @notice Execute 2 calls
     */
    function execute2(address target1, bytes calldata data1, address target2, bytes calldata data2)
        external
        payable
        onlySelf
    {
        (bool s1,) = target1.call(data1);
        if (!s1) revert Call1Failed();
        emit Executed(target1);

        (bool s2,) = target2.call(data2);
        if (!s2) revert Call2Failed();
        emit Executed(target2);
    }

    /**
     * @notice Execute 3 calls
     */
    function execute3(
        address target1,
        bytes calldata data1,
        address target2,
        bytes calldata data2,
        address target3,
        bytes calldata data3
    ) external payable onlySelf {
        (bool s1,) = target1.call(data1);
        if (!s1) revert Call1Failed();

        (bool s2,) = target2.call(data2);
        if (!s2) revert Call2Failed();

        (bool s3,) = target3.call(data3);
        if (!s3) revert Call3Failed();
    }

    /**
     * @notice Execute 5 calls (no loops)
     */
    function execute5(
        address t1,
        bytes calldata d1,
        address t2,
        bytes calldata d2,
        address t3,
        bytes calldata d3,
        address t4,
        bytes calldata d4,
        address t5,
        bytes calldata d5
    ) external payable onlySelf {
        (bool s,) = t1.call(d1);
        if (!s) revert Call1Failed();

        (s,) = t2.call(d2);
        if (!s) revert Call2Failed();

        (s,) = t3.call(d3);
        if (!s) revert Call3Failed();

        (s,) = t4.call(d4);
        if (!s) revert Call4Failed();

        (s,) = t5.call(d5);
        if (!s) revert Call5Failed();
    }

    /**
     * @notice Execute 11 calls for buy conditional flow
     */
    function executeBuy11(
        address t1,
        bytes calldata d1,
        address t2,
        bytes calldata d2,
        address t3,
        bytes calldata d3,
        address t4,
        bytes calldata d4,
        address t5,
        bytes calldata d5,
        address t6,
        bytes calldata d6,
        address t7,
        bytes calldata d7,
        address t8,
        bytes calldata d8,
        address t9,
        bytes calldata d9,
        address t10,
        bytes calldata d10,
        address t11,
        bytes calldata d11
    )
        external
        payable
        onlySelf
        returns (bytes memory r1, bytes memory r2, bytes memory r3, bytes memory r4, bytes memory r5, bytes memory r6)
    {
        bool s;
        (s, r1) = t1.call(d1);
        if (!s) revert Call1Failed();

        (s,) = t2.call(d2);
        if (!s) revert Call2Failed();

        (s,) = t3.call(d3);
        if (!s) revert Call3Failed();

        (s, r2) = t4.call(d4);
        if (!s) revert Call4Failed();

        (s,) = t5.call(d5);
        if (!s) revert Call5Failed();

        (s, r3) = t6.call(d6);
        if (!s) revert Call6Failed();

        (s,) = t7.call(d7);
        if (!s) revert Call7Failed();

        (s,) = t8.call(d8);
        if (!s) revert Call8Failed();

        (s, r4) = t9.call(d9);
        if (!s) revert Call9Failed();

        (s,) = t10.call(d10);
        if (!s) revert Call10Failed();

        (s, r5) = t11.call(d11);
        if (!s) revert Call11Failed();

        r6 = r5; // Just to use the variable
    }

    receive() external payable {}

}
