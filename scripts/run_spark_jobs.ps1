# scripts/run_spark_jobs.ps1
docker compose up -d mongodb
python -m spark_jobs.export_latest_time_series
python -m spark_jobs.spark_yearly_summary_job
python -m spark_jobs.spark_prediction_job