#!/usr/bin/env python3
"""
Performance Analysis Script for Privacy-Preserving Authentication
Analyzes timing data from performance_metrics.log
"""

import re
import statistics
from collections import defaultdict

def parse_log_line(line):
    """Parse a single log line and extract metrics."""
    try:
        # Split timestamp and content
        parts = line.split(' | ')
        if len(parts) < 2:
            return None

        timestamp = parts[0]
        operation = parts[1]

        metrics = {}
        # Extract all timing values
        for part in parts[2:]:
            if '=' in part:
                key, value = part.split('=')
                if 'ms' in value:
                    metrics[key.strip()] = float(value.replace('ms', ''))

        return {
            'timestamp': timestamp,
            'operation': operation,
            'metrics': metrics
        }
    except Exception as e:
        print(f"Error parsing line: {e}")
        return None

def analyze_performance_log(log_file='performance_metrics.log'):
    """Analyze the performance log file."""

    # Storage for different operation types
    registration_times = defaultdict(list)
    authentication_times = defaultdict(list)

    try:
        with open(log_file, 'r') as f:
            for line in f:
                parsed = parse_log_line(line.strip())
                if not parsed:
                    continue

                operation = parsed['operation']
                metrics = parsed['metrics']

                if 'REGISTRATION' in operation:
                    for key, value in metrics.items():
                        registration_times[key].append(value)
                elif 'AUTHENTICATION' in operation:
                    for key, value in metrics.items():
                        authentication_times[key].append(value)

    except FileNotFoundError:
        print(f"Log file '{log_file}' not found. Run some operations first.")
        return None, None

    return registration_times, authentication_times

def print_statistics(times_dict, operation_name):
    """Print statistics for a given operation."""
    print(f"\n{'='*80}")
    print(f"{operation_name} PERFORMANCE ANALYSIS")
    print(f"{'='*80}\n")

    if not times_dict:
        print("No data available yet. Please run some operations first.\n")
        return

    print(f"Number of operations: {len(times_dict.get('TOTAL', []))}\n")

    # Sort keys to show TOTAL first, then alphabetically
    sorted_keys = sorted(times_dict.keys(), key=lambda x: (x != 'TOTAL', x))

    print(f"{'Metric':<25} {'Min (ms)':<12} {'Max (ms)':<12} {'Avg (ms)':<12} {'Median (ms)':<12}")
    print("-" * 80)

    for metric in sorted_keys:
        values = times_dict[metric]
        if values:
            min_val = min(values)
            max_val = max(values)
            avg_val = statistics.mean(values)
            median_val = statistics.median(values)

            print(f"{metric:<25} {min_val:<12.3f} {max_val:<12.3f} {avg_val:<12.3f} {median_val:<12.3f}")

    print()

def print_comparison_table(reg_times, auth_times):
    """Print a comparison table between registration and authentication."""
    print(f"\n{'='*80}")
    print("REGISTRATION vs AUTHENTICATION COMPARISON")
    print(f"{'='*80}\n")

    reg_total = reg_times.get('TOTAL', [])
    auth_total = auth_times.get('TOTAL', [])

    if not reg_total or not auth_total:
        print("Insufficient data for comparison. Run both operations first.\n")
        return

    print(f"{'Operation':<30} {'Count':<10} {'Avg Time (ms)':<15}")
    print("-" * 55)
    print(f"{'Registration':<30} {len(reg_total):<10} {statistics.mean(reg_total):<15.3f}")
    print(f"{'Authentication':<30} {len(auth_total):<10} {statistics.mean(auth_total):<15.3f}")

    speedup = statistics.mean(reg_total) / statistics.mean(auth_total) if auth_total else 0
    print(f"\nRegistration is {speedup:.2f}x slower than Authentication")
    print()

def print_detailed_breakdown(times_dict, operation_name):
    """Print detailed percentage breakdown of where time is spent."""
    print(f"\n{'='*80}")
    print(f"{operation_name} - TIME BREAKDOWN (% of total)")
    print(f"{'='*80}\n")

    total_times = times_dict.get('TOTAL', [])
    if not total_times:
        print("No data available.\n")
        return

    avg_total = statistics.mean(total_times)

    # Calculate percentages for each phase
    print(f"{'Phase':<30} {'Avg Time (ms)':<15} {'% of Total':<15}")
    print("-" * 60)

    for metric, values in sorted(times_dict.items()):
        if metric != 'TOTAL' and values:
            avg_time = statistics.mean(values)
            percentage = (avg_time / avg_total) * 100
            print(f"{metric:<30} {avg_time:<15.3f} {percentage:<15.1f}%")

    print()

def main():
    """Main function to run the analysis."""
    print("\n" + "="*80)
    print("PRIVACY-PRESERVING AUTHENTICATION - PERFORMANCE ANALYSIS")
    print("="*80)

    reg_times, auth_times = analyze_performance_log()

    if reg_times is not None:
        print_statistics(reg_times, "REGISTRATION")
        print_detailed_breakdown(reg_times, "REGISTRATION")

    if auth_times is not None:
        print_statistics(auth_times, "AUTHENTICATION")
        print_detailed_breakdown(auth_times, "AUTHENTICATION")

    if reg_times and auth_times:
        print_comparison_table(reg_times, auth_times)

    print("\n" + "="*80)
    print("RESEARCH NOTES:")
    print("="*80)
    print("""
This authentication method uses only lightweight operations:
- SHA-256 hashing
- XOR operations
- No public-key cryptography

Typical authentication methods for comparison:
- OAuth 2.0 + JWT: 50-150ms (includes token validation, signature verification)
- SAML: 100-300ms (XML parsing, digital signatures)
- Password + bcrypt: 200-400ms (intentionally slow for security)
- TLS handshake: 50-200ms (RSA/ECDH key exchange)

This method should be significantly faster due to:
1. Pre-computed smartcard values
2. Only symmetric operations (hash + XOR)
3. Minimal network round-trips
4. No database lookups on user side
    """)
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
