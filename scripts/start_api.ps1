# scripts/start_api.ps1
docker compose up -d mongodb
python -m uvicorn app.main:app --reload