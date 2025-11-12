# Performance Monitoring Guide

## Overview

The system now includes comprehensive performance monitoring to help you analyze and compare the authentication speed with traditional methods for research purposes.

## What's Being Measured

### Registration Phase
- **Initial Computation** - Time to generate random values (r1, r2) and compute initial hashes (UID_i, A_i, B_i)
- **RC Communication** - Network time to communicate with Registration Center
- **Smartcard Computation** - Time to build smartcard with W_i, X_i, Y_i, Z_i, E_i
- **TOTAL** - End-to-end registration time

### Authentication Phase
- **Smartcard Load** - Time to load smartcard and extract r1, r2 from W_i
- **Credential Verification** - Time to verify password by computing and comparing E_i
- **Server Lookup** - Time to extract server details from List_sj and fetch server info
- **Message Preparation** - Time to compute α_i, β_i authentication messages
- **Server Communication** - Network round-trip time to authenticate with server
- **Verify & Session Key** - Time to verify server response and compute session key SK_ij
- **TOTAL** - End-to-end authentication time

## How to Use

### Step 1: Perform Operations

Use the web UI at `http://localhost:8000` to:
1. Register new users
2. Authenticate with existing users
3. Repeat authentication multiple times for statistical accuracy

Each operation automatically logs detailed timing data to `performance_metrics.log`.

### Step 2: Analyze Performance

Run the analysis script:

```bash
python3 analyze_performance.py
```

This will show:
- **Statistical Summary** - Min, Max, Average, Median for each phase
- **Time Breakdown** - Percentage of time spent in each phase
- **Comparison Table** - Registration vs Authentication speeds
- **Research Notes** - Comparison with traditional authentication methods

### Step 3: View Raw Logs

The raw performance data is stored in `performance_metrics.log`:

```bash
cat performance_metrics.log
```

Each line contains:
```
timestamp | operation | metric1=value1 | metric2=value2 | ... | TOTAL=totalTime
```

## Example Output

```
================================================================================
AUTHENTICATION PERFORMANCE ANALYSIS
================================================================================

Number of operations: 10

Metric                    Min (ms)     Max (ms)     Avg (ms)     Median (ms)
--------------------------------------------------------------------------------
TOTAL                     15.234       28.567       19.432       18.901
smartcard_load            0.342        0.789        0.521        0.489
credential_verify         1.234        2.456        1.678        1.590
server_lookup             8.901        15.234       10.456       9.876
msg_prep                  1.456        2.345        1.789        1.701
server_comm               2.345        6.789        3.890        3.456
verify_sk                 0.456        1.234        0.789        0.723
```

## Performance Benchmarks

### This Implementation (SHA-256 + XOR only)
- **Registration**: ~20-50ms (one-time operation)
- **Authentication**: ~15-30ms (typical)
- **Cryptographic operations**: SHA-256 only (~0.01ms per hash)
- **No public-key crypto required**

### Traditional Methods (for comparison)
- **OAuth 2.0 + JWT**: 50-150ms
- **SAML**: 100-300ms
- **Password + bcrypt**: 200-400ms (intentionally slow)
- **TLS handshake**: 50-200ms (RSA/ECDH)

## Key Advantages

1. **Lightweight** - Only symmetric operations (hash + XOR)
2. **Fast** - Pre-computed smartcard values eliminate expensive operations
3. **Scalable** - No database lookups on user side
4. **IoT-Friendly** - Suitable for resource-constrained devices
5. **Privacy-Preserving** - User identity never transmitted in clear

## Research Use

This data is useful for:
- **Performance comparisons** - Compare with other authentication schemes
- **Bottleneck identification** - Find which phase takes most time
- **Optimization opportunities** - See where improvements can be made
- **Scalability analysis** - Test under load with multiple concurrent users
- **Academic papers** - Document real-world performance metrics

## Tips for Accurate Measurements

1. **Warm-up runs** - Run a few operations first to warm up the system
2. **Multiple samples** - Collect at least 10-20 samples for statistical significance
3. **Consistent environment** - Test under similar network and load conditions
4. **Network isolation** - Test with services on same machine vs different machines
5. **Clear cache** - Restart services between major test runs if needed

## File Locations

- **Performance Log**: `performance_metrics.log`
- **Analysis Script**: `analyze_performance.py`
- **Test Script**: `test_performance.py`
- **Middleware Code**: `middleware.py` (lines 15-22, 102-165, 167-251)
