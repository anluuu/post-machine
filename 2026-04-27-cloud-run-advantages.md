# Why I'm Still Using Cloud Run in 2026

Three years ago, I migrated our entire backend from on-prem to Google Cloud. Cloud Run was a nice-to-have. Now it's the foundation.

**Why Cloud Run stays on my stack:**

**1. Scale-to-zero for variable workloads**
- We have job-based processing (data syncs, reports, transformations)
- Most services sit idle 90%+ of the time
- No need to provision for peak - the platform handles it

**2. Long-running jobs without complexity**
- Cloud Run Jobs: 60 minute timeout, up to 10k parallel tasks
- Perfect for ETL, data processing, batch operations
- No infrastructure to manage, just define the container

**3. Developer experience**
- `gcloud builds submit` → done
- Automatic TLS, logging, monitoring, traffic splitting
- Same container image runs locally and in production

**4. Cost predictability**
- Pay per execution, no idle costs
- Free tier is generous
- Easy to model and compare against VMs

**When I wouldn't use it:**
- Low-latency APIs (cold starts still add ~200-400ms)
- Long-running stateful services
- When you need tight integration with AWS services

For most stateless workloads, I can't think of a better balance of simplicity, performance, and cost.

#CloudRun #GCP #Serverless
