# Cloud Run Jobs: Serverless Batch Processing in 2026

I've been using Cloud Run Jobs for data processing all year. Here's what it does well:

**The big feature: 10,000 parallel tasks**
- Each task gets `CLOUD_RUN_TASK_INDEX` and `CLOUD_RUN_TASK_COUNT`
- Perfect for splitting large workloads
- Up to 7 days timeout per task

**What I use it for:**
- ETL jobs (extract, transform, load to BigQuery)
- Daily report generation
- Vector embedding generation at scale
- RAG pipelines with AlloyDB
- Pub/Sub queue draining

**Why I choose it over VMs:**
- Serverless = no infrastructure to manage
- Pay only for execution time
- Automatic retries (up to 10 attempts)
- Integrates with Cloud Scheduler for cron jobs

**Example workflow:**
1. Cloud Scheduler triggers job daily at 2 AM UTC
2. Cloud Run Job reads from Pub/Sub (10K messages)
3. Each task processes ~1K messages in parallel
4. Results written to BigQuery
5. Email notification on success/failure

**Cost example:**
- 1M records, 50ms processing each
- ~$5-10/month (vs $50+ for equivalent VMs)

For batch processing that doesn't need low latency, Cloud Run Jobs is hard to beat.

#GCP #CloudRun #BatchProcessing
