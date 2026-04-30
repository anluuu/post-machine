# Cloud Run Pricing Calculator for 2026

Here's how I actually calculate Cloud Run costs before deployment:

**Current Pricing (us-central1, Tier 1 - 2026):**
- CPU: $0.000024 per vCPU-second
- Memory: $0.0000025 per GiB-second
- Requests: $0.40 per 1,000,000 requests
- Ephemeral Storage: $0.000109589 per GiB-second

**Formula (Request-based billing):**
```
CPU cost = requests × avg_duration_sec × vCPU × $0.000024
Memory cost = requests × avg_duration_sec × memory_gb × $0.0000025
Request cost = requests / 1M × $0.40
```

**Example: 10M requests, 200ms, 512MiB, 1 vCPU**
```
CPU:    10M × 0.2s × $0.000024 = $48.00
Memory: 10M × 0.2s × 0.5GB × $0.0000025 = $2.50
Request: 10M ÷ 1M × $0.40 = $4.00
─────────────────────────────────
Total:                                  $54.50
Free tier credit:                       -$2.50
Net cost:                               $52.00
```

**Free Tier (monthly, aggregated):**
- 2M requests
- 360K vCPU-seconds
- 450K GiB-seconds
- 384K vCPU-seconds (Worker Pools)

**Pro Tips:**
1. Use Committed Use Discounts (CUD) for predictable workloads - 1yr = ~20% off, 3yr = 50-65% off
2. Min instances run at reduced rates - good for hot paths
3. Tier 2 regions are slightly more expensive (asia-southeast1, australia-southeast1, etc.)

**When not to use Cloud Run:**
- Low-latency APIs (cold starts add 200-500ms)
- Long-running stateful services
- When AWS integration is required (Lambda + ecosystem)

I always run this calculation before spinning up a new service. It's faster than waiting for the bill.

#GCP #CloudRun #CostOptimization #CloudPricing
