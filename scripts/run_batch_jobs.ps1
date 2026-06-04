# scripts/run_batch_jobs.ps1
python -m batch_jobs.yearly_aggregation_job
python -m batch_jobs.activity_aggregation_job