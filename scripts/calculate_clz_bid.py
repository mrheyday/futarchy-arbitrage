#!/usr/bin/env python3
"""
Script to calculate the effective bid using CLZ (Count Leading Zeros) logic
as implemented in the InstitutionalSolverSystem smart contracts.

Usage:
    python scripts/calculate_clz_bid.py <raw_bid_value>
"""

import sys
import argparse
import math

def clz_256(value: int) -> int:
    """
    Count leading zeros for a 256-bit integer.
    Mimics Solady's LibBit.clz(value).
    """
    if value == 0:
        return 256
    if value < 0:
        raise ValueError("Value must be non-negative")
    if value >= 2**256:
        raise ValueError("Value exceeds 256 bits")
        
    # Python's bit_length() returns the number of bits required to represent 
    # an integer in binary, excluding the sign and leading zeros.
    return 256 - value.bit_length()

def calculate_effective_bid(raw_bid: int):
    """
    Calculate effective bid using CLZ log-scaling logic.
    
    Solidity Logic from InstitutionalSolverSystem.sol:
        uint256 leadingZeros = LibBit.clz_(bid.revealValue);
        uint256 logApprox = 255 - leadingZeros;
        uint256 effectiveBid = bid.revealValue.mulDiv(logApprox, 256);
    """
    if raw_bid == 0:
        # In Solidity, 255 - 256 would underflow/revert
        raise ValueError("Bid value cannot be 0 (causes underflow in contract logic)")

    leading_zeros = clz_256(raw_bid)
    log_approx = 255 - leading_zeros
    
    # mulDiv(a, b, c) is (a * b) / c
    effective_bid = (raw_bid * log_approx) // 256
    
    return effective_bid, leading_zeros, log_approx

def analyze_dust_protection(threshold=2000):
    print(f"\n{'='*60}")
    print(f"DUST PROTECTION ANALYSIS (0 to {threshold})")
    print(f"{'='*60}")
    print(f"{'Raw Bid':<10} | {'LogApprox':<10} | {'Effective':<10} | {'Efficiency':<10}")
    print("-" * 60)
    
    test_values = [1, 10, 50, 100, 127, 128, 255, 256, 500, 511, 512, 1000, 1023, 1024]
    
    for val in test_values:
        if val > threshold: continue
        eff, _, log = calculate_effective_bid(val)
        ratio = (eff / val * 100) if val > 0 else 0
        print(f"{val:<10} | {log:<10} | {eff:<10} | {ratio:.2f}%")
    print("-" * 60)
    print("Observation: Small bids suffer heavy penalties due to low LogApprox.")

def analyze_whale_dominance():
    print(f"\n{'='*60}")
    print(f"WHALE DOMINANCE ANALYSIS")
    print(f"{'='*60}")
    print(f"{'Raw Bid (ETH)':<15} | {'Raw (Wei)':<12} | {'Log':<4} | {'Effective':<12} | {'Efficiency':<10}")
    print("-" * 70)
    
    eth_values = [0.001, 0.01, 0.1, 1, 10, 100, 1000, 10000]
    
    for eth in eth_values:
        wei = int(eth * 10**18)
        eff, _, log = calculate_effective_bid(wei)
        efficiency = (eff / wei * 100) if wei > 0 else 0
        
        wei_str = f"10^{int(math.log10(wei))}" if wei > 0 else "0"
        eff_str = f"10^{int(math.log10(eff))}" if eff > 0 else "0"
        
        print(f"{eth:<15} | {wei_str:<12} | {log:<4} | {eff_str:<12} | {efficiency:.2f}%")
    print("-" * 70)
    print("Observation: Larger capital commitments achieve higher efficiency per unit.")

def find_winning_bid(competitor_raw: int):
    if competitor_raw <= 0:
        print("Competitor bid must be > 0")
        return

    competitor_eff, _, current_log = calculate_effective_bid(competitor_raw)
    print(f"\n{'='*60}")
    print(f"BIDDING STRATEGY: Beating {competitor_raw}")
    print(f"{'='*60}")
    print(f"Competitor Raw:       {competitor_raw}")
    print(f"Competitor Effective: {competitor_eff}")
    
    # 1. Linear Increment (1%)
    linear_bid = int(competitor_raw * 1.01)
    linear_eff, _, _ = calculate_effective_bid(linear_bid)
    
    print(f"\n[Scenario 1] Linear Increment (+1%)")
    print(f"Bid: {linear_bid}")
    print(f"Effective: {linear_eff}")
    print(f"Result: {'WIN' if linear_eff > competitor_eff else 'LOSE'}")
    
    # 2. Next Power of 2 Jump
    next_pow2 = 1 << (current_log + 1)
    jump_eff, _, _ = calculate_effective_bid(next_pow2)
    
    print(f"\n[Scenario 2] Power-of-2 Jump")
    print(f"Bid: {next_pow2} (Jump to 2^{current_log + 1})")
    print(f"Effective: {jump_eff}")
    print(f"Result: {'WIN' if jump_eff > competitor_eff else 'LOSE'}")
    
    # 3. Find Minimal Winning Bid
    print(f"\n[Optimization] Finding Minimal Winning Bid...")
    
    # Check if we can win in current bucket
    max_val_in_bucket = (1 << (current_log + 1)) - 1
    max_eff_in_bucket, _, _ = calculate_effective_bid(max_val_in_bucket)
    
    if max_eff_in_bucket <= competitor_eff:
        print(f"  -> Impossible to win in current bucket (Max Eff: {max_eff_in_bucket}). Jumping...")
        winning_bid = next_pow2
    else:
        # Solve: raw * k // 256 > competitor_eff
        target_raw = (competitor_eff * 256) // current_log + 1
        winning_bid = max(competitor_raw + 1, target_raw)
        
    final_eff, _, _ = calculate_effective_bid(winning_bid)
    print(f"Minimal Winning Bid: {winning_bid}")
    print(f"Effective: {final_eff}")
    print(f"Delta: +{winning_bid - competitor_raw} raw units")

def main():
    parser = argparse.ArgumentParser(description="Calculate effective bid using CLZ logic.")
    parser.add_argument("bid", nargs="?", type=str, help="Raw bid value (integer or hex string)")
    parser.add_argument("--analyze-dust", action="store_true", help="Analyze dust protection")
    parser.add_argument("--analyze-whale", action="store_true", help="Analyze whale dominance")
    parser.add_argument("--beat", type=str, help="Calculate bid to beat this raw value")
    
    args = parser.parse_args()
    
    try:
        if args.analyze_dust:
            analyze_dust_protection()
            return
            
        if args.analyze_whale:
            analyze_whale_dominance()
            return
            
        if args.beat:
            raw_input = args.beat
            if raw_input.lower().startswith("0x"):
                raw_bid = int(raw_input, 16)
            else:
                raw_bid = int(raw_input)
            find_winning_bid(raw_bid)
            return

        if not args.bid:
            parser.print_help()
            return

        raw_input = args.bid
        if raw_input.lower().startswith("0x"):
            raw_bid = int(raw_input, 16)
        else:
            raw_bid = int(raw_input)
            
        print(f"\n{'='*40}")
        print(f"CLZ Effective Bid Calculator")
        print(f"{'='*40}")
        print(f"Raw Bid Input: {raw_bid}")
        print(f"Hex Value:     {hex(raw_bid)}")
        print(f"Bit Length:    {raw_bid.bit_length()}")
        print(f"{'-'*40}")
        
        effective_bid, leading_zeros, log_approx = calculate_effective_bid(raw_bid)
        
        print(f"Leading Zeros (CLZ):    {leading_zeros}")
        print(f"Log Approx (255-CLZ):   {log_approx}")
        print(f"Scaling Factor:         {log_approx}/256 (~{log_approx/256:.4f})")
        print(f"{'-'*40}")
        print(f"Effective Bid:          {effective_bid}")
        print(f"{'='*40}\n")
        
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()