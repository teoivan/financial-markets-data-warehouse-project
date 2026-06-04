# scripts/run_ingestion.ps1
docker compose up -d mongodb
python -m app.services.csv_ingestion_service
python -m app.services.nasdaq_ingestion_service