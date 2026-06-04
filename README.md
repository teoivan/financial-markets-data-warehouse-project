# Financial Markets Data Warehouse

A NoSQL data warehouse platform for financial markets data. The project supports external provider ingestion, temporal storage, heterogeneous financial indicators, REST API access, analytics, batch processing, and MCP-based LLM assistant integration.

The system was developed for a fictional company, Acme Ltd, that wants to ingest market data, preserve data history, trace provenance, and provide insights such as trends, comparisons, forecasts, and activity summaries.

---

## 1. Main Features

### Data ingestion

The platform supports two ingestion modes:

1. **CSV ingestion**

   * Loads reproducible demo data for crypto assets.
   * Assets: `BTCUSD`, `ETHUSD`
   * Data shape: OHLCV values: `open`, `high`, `low`, `close`, `volume`

2. **Nasdaq Data Link ingestion**

   * Loads real external financial data from Nasdaq Data Link.
   * Dataset: `NDAQ/RTAT10`
   * Assets: `AAPL_NASDAQ`, `MSFT_NASDAQ`, `TSLA_NASDAQ`, `GOOGL_NASDAQ`
   * Data shape: retail trading `activity`

Each ingested record stores provenance, including provider, dataset, source URL, ingestion mode, and ingestion timestamp.

---

### REST API

The REST API is implemented with FastAPI and exposes:

* Asset discovery
* Asset details
* Data source discovery
* Data source details
* Time-series retrieval
* Temporal historical queries using `asOfSystemTime`
* Analytics summaries
* Asset comparison
* Simple prediction
* Nasdaq activity analytics
* Persisted analytics results

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

---

### Temporal warehouse behavior

The system follows a temporal data warehouse approach:

* Existing records are not overwritten.
* Corrections are stored as new versions.
* Deletions are represented using temporal marker records with `deleted = true`.
* Current queries return the latest non-deleted version.
* Historical queries can be made using `asOfSystemTime`.

Example:

```text
GET /api/v1/data?assetId=BTCUSD&dataSourceId=NASDAQ_DATA_LINK_BITFINEX&startBusinessDate=2024-01-01&endBusinessDate=2024-01-03&asOfSystemTime=2026-05-30T17:10:00
```

This returns what the warehouse knew at that system time.

---

### Analytics

The platform includes multiple analytics features:

* Close-price summary
* Asset comparison
* Simple next-close prediction
* Nasdaq activity summary
* Persisted analytics results
* Batch yearly close-price aggregation
* Batch yearly activity aggregation

Batch results are stored back into MongoDB in the `analytics_summaries` collection.

---

### MCP / LLM assistant integration

The project includes MCP tools that allow an LLM assistant to call the platform capabilities.

Available MCP-style tool functions include:

* `list_assets`
* `get_asset_details`
* `list_data_sources`
* `get_data_source_details`
* `get_time_series_data`
* `summarize_asset`
* `compare_assets`
* `predict_next_close`
* `summarize_activity`
* `list_persisted_summaries`
* `list_persisted_predictions`

A demo MCP workflow is provided in:

```text
demo/mcp_demo_workflow.py
```

---

## 2. Technology Stack

* Python
* FastAPI
* MongoDB
* Docker Compose
* PyMongo
* Pydantic
* python-dotenv
* pytest
* MCP-compatible tool layer
* Optional Spark/PySpark workload support can be added under `spark_jobs/`

---

## 3. Project Structure

```text
financial_project/
│
├── app/
│   ├── api/                 REST API endpoints
│   ├── models/              Pydantic request/data models
│   ├── repositories/        MongoDB access and temporal logic
│   ├── services/            Ingestion and analytics services
│   ├── config.py            Environment configuration
│   ├── database.py          MongoDB connection and collections
│   ├── main.py              FastAPI app entry point
│   └── mcp_server.py        MCP tool definitions
│
├── batch_jobs/
│   ├── yearly_aggregation_job.py
│   └── activity_aggregation_job.py
│
├── data/
│   └── sample_market_data.csv
│
├── demo/
│   ├── mcp_demo_workflow.py
│   └── assistant_prompts.md
│
├── scripts/
│   ├── start_api.ps1
│   ├── run_ingestion.ps1
│   ├── run_batch_jobs.ps1
│   ├── run_tests.ps1
│   └── run_mcp_demo.ps1
│
├── tests/
│   └── test_analytics_service.py
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Setup Instructions

### 4.1 Clone the repository

```powershell
git clone <your-github-repository-url>
cd financial_project
```

---

### 4.2 Create and activate virtual environment

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

### 4.3 Install dependencies

```powershell
pip install -r requirements.txt
```

---

### 4.4 Create `.env`

Create a file named:

```text
.env
```

in the project root.

Use this structure:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=financial_dwh
NASDAQ_DATA_LINK_API_KEY=your_api_key_here
```

A template is provided in:

```text
.env.example
```

Do not commit the real `.env` file to GitHub.

---

### 4.5 Start MongoDB

```powershell
docker compose up -d mongodb
```

Check that MongoDB is running:

```powershell
docker compose ps
```

---

## 5. Running the API

Start FastAPI:

```powershell
python -m uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## 6. Running Ingestion

### 6.1 CSV ingestion

```powershell
python -m app.services.csv_ingestion_service
```

This loads demo OHLCV crypto data for:

```text
BTCUSD
ETHUSD
```

---

### 6.2 Nasdaq Data Link ingestion

Make sure `.env` contains a valid Nasdaq Data Link API key.

Then run:

```powershell
python -m app.services.nasdaq_ingestion_service
```

This loads Nasdaq RTAT10 retail activity data for:

```text
AAPL_NASDAQ
MSFT_NASDAQ
TSLA_NASDAQ
GOOGL_NASDAQ
```

Expected output includes:

```text
totalStoredRecords: 150
totalFailedRecords: 0
```

---

## 7. REST API Examples

### Q1: List available assets

```http
GET /api/v1/assets
```

Expected active demo assets:

```text
BTCUSD
ETHUSD
AAPL_NASDAQ
MSFT_NASDAQ
TSLA_NASDAQ
GOOGL_NASDAQ
```

---

### Q2: Get asset details

```http
GET /api/v1/assets/BTCUSD
```

---

### Q3: List data sources

```http
GET /api/v1/data-sources
```

---

### Q4: Get data source details

```http
GET /api/v1/data-sources/NASDAQ_DATA_LINK_RTAT10
```

---

### Q5: Get time-series data

```http
GET /api/v1/data
```

Example parameters:

```text
assetId: BTCUSD
dataSourceId: NASDAQ_DATA_LINK_BITFINEX
startBusinessDate: 2024-01-01
endBusinessDate: 2024-01-06
includeAttributes: true
```

---

### Historical temporal query

```text
assetId: BTCUSD
dataSourceId: NASDAQ_DATA_LINK_BITFINEX
startBusinessDate: 2024-01-01
endBusinessDate: 2024-01-03
includeAttributes: true
asOfSystemTime: 2026-05-30T17:10:00
```

This returns the state of the warehouse as of that system time.

---

## 8. Analytics Endpoints

### Close-price summary

```http
GET /api/v1/analytics/summary
```

Example:

```text
assetId: BTCUSD
dataSourceId: NASDAQ_DATA_LINK_BITFINEX
startBusinessDate: 2024-01-01
endBusinessDate: 2024-01-06
```

---

### Compare two assets

```http
GET /api/v1/analytics/compare
```

Example:

```text
assetId1: BTCUSD
assetId2: ETHUSD
dataSourceId: NASDAQ_DATA_LINK_BITFINEX
startBusinessDate: 2024-01-01
endBusinessDate: 2024-01-06
```

---

### Predict next close

```http
GET /api/v1/analytics/predict
```

Example:

```text
assetId: ETHUSD
dataSourceId: NASDAQ_DATA_LINK_BITFINEX
startBusinessDate: 2024-01-01
endBusinessDate: 2024-01-06
```

---

### Nasdaq activity summary

```http
GET /api/v1/analytics/activity-summary
```

Example:

```text
assetId: AAPL_NASDAQ
dataSourceId: NASDAQ_DATA_LINK_RTAT10
startBusinessDate: 2024-03-25
endBusinessDate: 2024-03-29
```

---

### Persisted summaries

```http
GET /api/v1/analytics/summary/results
```

---

### Persisted predictions

```http
GET /api/v1/analytics/prediction/results
```

---

## 9. Batch Analytics Jobs

Run yearly close-price aggregation:

```powershell
python -m batch_jobs.yearly_aggregation_job
```

Run yearly activity aggregation:

```powershell
python -m batch_jobs.activity_aggregation_job
```

These jobs read the latest temporal time-series records and persist analytical summaries into MongoDB.

Expected result types:

```text
yearly_close_summary
yearly_activity_summary
```

---

## 10. MCP Demo Workflow

Make sure FastAPI is running:

```powershell
python -m uvicorn app.main:app --reload
```

Then run:

```powershell
python -m demo.mcp_demo_workflow
```

The workflow demonstrates:

1. Listing assets
2. Inspecting asset details
3. Fetching time-series data
4. Fetching historical as-of data
5. Summarizing trends
6. Comparing assets
7. Predicting next close
8. Summarizing Nasdaq activity
9. Listing persisted analytics
10. Listing persisted predictions

Example assistant prompts are available in:

```text
demo/assistant_prompts.md
```

---

## 11. Running Tests

Make sure MongoDB is running:

```powershell
docker compose up -d mongodb
```

Run:

```powershell
pytest
```

The tests cover:

* Summary calculation
* Prediction calculation
* Asset comparison
* Temporal latest-version logic
* Activity summary
* Batch close aggregation
* Batch activity aggregation
* Temporal asset deactivation marker
* Temporal data source deactivation marker
* Historical `asOfSystemTime` query behavior

---

## 12. Useful Scripts

If the `scripts/` folder is available, common commands can be run with:

```powershell
.\scripts\start_api.ps1
.\scripts\run_ingestion.ps1
.\scripts\run_batch_jobs.ps1
.\scripts\run_tests.ps1
.\scripts\run_mcp_demo.ps1
```

---

## 13. Data Model Overview

### Asset

Stores financial instrument metadata:

```text
assetId
symbol
name
assetClass
region
description
attributes
systemTime
deleted
```

### Data source

Stores provider metadata:

```text
dataSourceId
provider
dataset
description
apiEndpoint
supportedAttributes
attributes
systemTime
deleted
```

### Time-series record

Stores financial observations over time:

```text
assetId
dataSourceId
businessDate
values
provenance
businessYear
systemTime
deleted
```

The `values` field is flexible, allowing heterogeneous indicators:

```json
{
  "open": 42000,
  "high": 43000,
  "low": 41000,
  "close": 42500,
  "volume": 1200
}
```

or:

```json
{
  "activity": 0.0191
}
```

---

## 14. Temporal Design

The system does not overwrite existing records.

When a correction is made, a new record is inserted with a newer `systemTime`.

When an asset or data source is deactivated, the system inserts a marker record:

```json
{
  "deleted": true,
  "deletionReason": "Cleanup old experimental asset before final demo",
  "attributes": {
    "deactivationType": "temporal_marker"
  }
}
```

Current queries return only the latest non-deleted records.

Historical queries can use `asOfSystemTime` to retrieve the state of the warehouse at a previous system time.

---

## 15. Final Demo Flow

Recommended 3-minute video flow:

1. Start MongoDB and FastAPI.
2. Show MongoDB collections.
3. Run CSV ingestion.
4. Run Nasdaq Data Link ingestion.
5. Use Swagger to show:

   * asset list
   * asset details
   * data source details
   * time-series data
6. Show temporal correction using `asOfSystemTime`.
7. Run analytics:

   * summary
   * comparison
   * prediction
   * activity summary
8. Run batch jobs.
9. Show persisted analytics.
10. Run MCP demo workflow.

---

## 16. Notes

* The project uses a local MongoDB instance through Docker Compose.
* The real Nasdaq Data Link API key must be configured locally in `.env`.
* The `.env` file should not be committed.
* CSV ingestion is included to make the demo reproducible even if the live provider is unavailable.
* Nasdaq Data Link ingestion demonstrates real external provider ingestion and provenance tracking.
