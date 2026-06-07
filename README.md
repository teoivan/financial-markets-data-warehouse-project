# Financial Markets Data Warehouse

A NoSQL financial data warehouse platform built with Python, FastAPI, MongoDB, Apache Spark/PySpark, and MCP tools for LLM assistant integration.

The project supports external financial data ingestion, temporal data warehouse behavior, heterogeneous financial attributes, REST API access, analytics, Spark-based aggregation, Spark ML prediction, persisted analytical results, and natural-language exploration through MCP-compatible tools.

---

## 1. Project Overview

This project implements a financial markets data warehouse for storing and analyzing market-related time-series data.

The system supports:

* Financial asset discovery
* Data source discovery
* Time-series storage and retrieval
* External provider ingestion
* Provenance tracking
* Temporal versioning and historical queries
* Heterogeneous data attributes
* REST API access
* Interactive analytics
* Batch analytics
* Apache Spark analytics
* Spark MLlib prediction
* MCP-based LLM assistant tools

The implementation uses MongoDB as the mandatory NoSQL database.

---

## 2. Main Features

### Data ingestion

The project supports two ingestion modes:

1. **CSV ingestion**

   * Loads reproducible local demo data.
   * Assets:

     * `BTCUSD`
     * `ETHUSD`
   * Data shape:

     * `open`
     * `high`
     * `low`
     * `close`
     * `volume`

2. **Nasdaq Data Link ingestion**

   * Loads real external provider data from Nasdaq Data Link.
   * Configured dataset:

     * `NDAQ/RTAT10`
   * Warehouse data source:

     * `NASDAQ_DATA_LINK_RTAT10`
   * Assets:

     * `AAPL_NASDAQ`
     * `MSFT_NASDAQ`
     * `TSLA_NASDAQ`
     * `GOOGL_NASDAQ`
   * Data shape:

     * `activity`

Each ingested time-series record stores provenance, including provider, dataset, source URL, provider symbol, ingestion mode, and ingestion timestamp.

---

## 3. Technology Stack

* Python
* FastAPI
* MongoDB
* PyMongo
* Pydantic
* Docker Compose
* pytest
* Apache Spark / PySpark
* Spark MLlib
* MCP tools
* PowerShell scripts for local execution

---

## 4. Project Structure

```text
financial_project/
│
├── app/
│   ├── api/                         REST API endpoints
│   ├── models/                      Pydantic data models
│   ├── repositories/                MongoDB repository layer
│   ├── services/                    Ingestion and analytics services
│   ├── config.py                    Environment configuration
│   ├── database.py                  MongoDB connection and indexes
│   ├── main.py                      FastAPI application entry point
│   └── mcp_server.py                MCP tool definitions
│
├── batch_jobs/
│   ├── yearly_aggregation_job.py    Python batch close-price aggregation
│   └── activity_aggregation_job.py  Python batch activity aggregation
│
├── spark_jobs/
│   ├── export_latest_time_series.py
│   ├── spark_yearly_summary_job.py
│   └── spark_prediction_job.py
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
│   ├── run_spark_jobs.ps1
│   ├── run_tests.ps1
│   └── run_mcp_demo.ps1
│
├── tests/
│   ├── test_analytics_service.py
│   └── test_ingestion_service.py
│
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 5. Data Model

### Asset

Assets represent financial instruments.

Main fields:

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

Examples:

```text
BTCUSD
ETHUSD
AAPL_NASDAQ
MSFT_NASDAQ
TSLA_NASDAQ
GOOGL_NASDAQ
```

---

### Data Source

Data sources represent providers or datasets.

Main fields:

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

Examples:

```text
NASDAQ_DATA_LINK_BITFINEX
NASDAQ_DATA_LINK_RTAT10
```

---

### Time-Series Record

Time-series records store observations over business dates.

Main fields:

```text
assetId
dataSourceId
businessDate
businessYear
values
provenance
systemTime
deleted
```

The `values` field is flexible, allowing heterogeneous financial data.

Example OHLCV record:

```json
{
  "open": 42000,
  "high": 43000,
  "low": 41000,
  "close": 42500,
  "volume": 1200
}
```

Example Nasdaq activity record:

```json
{
  "activity": 0.0191
}
```

---

## 6. Temporal Warehouse Design

The platform follows a temporal data warehouse approach.

Rules:

* Records are not overwritten in place.
* Corrections are inserted as new versions with newer `systemTime`.
* Deletions are represented by marker records with `deleted = true`.
* Current queries return the latest non-deleted version.
* Historical queries can use `asOfSystemTime`.

Example historical query:

```text
GET /api/v1/data?assetId=BTCUSD&dataSourceId=NASDAQ_DATA_LINK_BITFINEX&startBusinessDate=2024-01-01&endBusinessDate=2024-01-03&asOfSystemTime=2026-05-30T17:10:00
```

This returns what the warehouse knew at that specific system time.

---

## 7. NoSQL Storage and Indexing

MongoDB is used as the mandatory NoSQL storage system.

Collections:

```text
assets
data_sources
time_series
analytics_summaries
prediction_results
```

The warehouse uses compound indexes for efficient latest-version retrieval and historical queries.

Important time-series indexes include:

```text
assetId + dataSourceId + businessDate + systemTime
businessYear + assetId + dataSourceId
```

The `businessYear` field supports yearly aggregation and provides a future partition-growth strategy.

In this local implementation, all time-series records are stored in one MongoDB collection. For larger deployments, the same model can be extended to:

* year-based physical collections such as `time_series_2024`, `time_series_2025`
* MongoDB sharding using `businessYear` and `assetId`
* Spark jobs processing data by year partitions

This keeps the local project simple while preserving a clear path for scaling.

---

## 8. Setup Instructions

### 8.1 Clone the repository

```powershell
git clone <your-github-repository-url>
cd financial_project
```

---

### 8.2 Create virtual environment

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

---

### 8.3 Install dependencies

```powershell
pip install -r requirements.txt
```

---

### 8.4 Configure environment variables

Create a `.env` file in the project root.

Use `.env.example` as a template:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=financial_dwh
NASDAQ_DATA_LINK_API_KEY=your_api_key_here
```

Do not commit the real `.env` file.

---

### 8.5 Start MongoDB

```powershell
docker compose up -d mongodb
```

---

## 9. Running the API

Start FastAPI:

```powershell
python -m uvicorn app.main:app --reload
```

Open Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

## 10. Running Ingestion

### CSV ingestion

```powershell
python -m app.services.ingestion_service
```

This loads reproducible OHLCV demo data for:

```text
BTCUSD
ETHUSD
```

---

### Nasdaq Data Link ingestion

Make sure `.env` contains:

```env
NASDAQ_DATA_LINK_API_KEY=your_api_key_here
```

Then run:

```powershell
python -m app.services.nasdaq_ingestion_service
```

This loads Nasdaq Data Link RTAT10 retail activity data for:

```text
AAPL_NASDAQ
MSFT_NASDAQ
TSLA_NASDAQ
GOOGL_NASDAQ
```

The configured external dataset is:

```text
NDAQ/RTAT10
```

The project uses this as a configured provider integration. Additional Nasdaq tables can be added by defining new data source metadata, table code, asset mapping, and field mapping without changing the warehouse model.

---

## 11. REST API

Swagger UI is available at:

```text
http://127.0.0.1:8000/docs
```

### Q1: List assets

```http
GET /api/v1/assets
```

Returns active financial assets available in the warehouse.

---

### Q2: Get asset details

```http
GET /api/v1/assets/{asset_id}
```

Example:

```text
GET /api/v1/assets/BTCUSD
```

---

### Q3: List data sources

```http
GET /api/v1/data-sources
```

Returns financial data providers and datasets available in the warehouse.

---

### Q4: Get data source details

```http
GET /api/v1/data-sources/{data_source_id}
```

Example:

```text
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

### Historical as-of query

```text
assetId: BTCUSD
dataSourceId: NASDAQ_DATA_LINK_BITFINEX
startBusinessDate: 2024-01-01
endBusinessDate: 2024-01-03
asOfSystemTime: 2026-05-30T17:10:00
```

This demonstrates temporal warehouse behavior by returning the state of the data as known at the selected system time.

---

## 12. Interactive Analytics Endpoints

### Close-price summary

```http
GET /api/v1/analytics/summary
```

Example parameters:

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

Example parameters:

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

Example parameters:

```text
assetId: ETHUSD
dataSourceId: NASDAQ_DATA_LINK_BITFINEX
startBusinessDate: 2024-01-01
endBusinessDate: 2024-01-06
```

This endpoint provides a lightweight interactive prediction using average daily close-price change.

The project also includes a separate Apache Spark MLlib prediction workflow described below.

---

### Nasdaq activity summary

```http
GET /api/v1/analytics/activity-summary
```

Example parameters:

```text
assetId: AAPL_NASDAQ
dataSourceId: NASDAQ_DATA_LINK_RTAT10
startBusinessDate: 2024-03-25
endBusinessDate: 2024-03-29
```

This demonstrates analytics on heterogeneous data because it uses `activity` rather than OHLCV fields.

---

### Persisted analytics summaries

```http
GET /api/v1/analytics/summary/results
```

This returns persisted Python batch and PySpark summary results.

Look for Spark results with:

```text
computedBy: pyspark_yearly_summary_job
resultType: spark_yearly_close_summary
resultType: spark_yearly_activity_summary
```

---

### Persisted predictions

```http
GET /api/v1/analytics/prediction/results
```

This returns persisted prediction results.

Look for Spark MLlib results with:

```text
computedBy: pyspark_prediction_job
model: spark_mllib_linear_regression
resultType: spark_prediction
```

---

## 13. Python Batch Jobs

The project includes Python batch jobs for persisted warehouse summaries.

Run yearly close-price aggregation:

```powershell
python -m batch_jobs.yearly_aggregation_job
```

Run yearly activity aggregation:

```powershell
python -m batch_jobs.activity_aggregation_job
```

These jobs persist results into:

```text
analytics_summaries
```

Expected result types:

```text
yearly_close_summary
yearly_activity_summary
```

---

## 14. Apache Spark Workloads

The project includes Apache Spark workloads under:

```text
spark_jobs/
```

The Spark workflows use exported latest temporal warehouse records as input. This keeps the local setup simple and avoids requiring a MongoDB Spark connector, while still using Spark for the actual analytical computation.

### Spark export step

```powershell
python -m spark_jobs.export_latest_time_series
```

This exports the latest non-deleted temporal time-series view to:

```text
data/exports/latest_time_series.json
```

---

### Spark aggregation workflow

```powershell
python -m spark_jobs.spark_yearly_summary_job
```

This job uses PySpark DataFrames to compute yearly summaries for:

1. OHLCV close-price data:

   * `minClose`
   * `maxClose`
   * `avgClose`
   * `minVolume`
   * `maxVolume`
   * `avgVolume`

2. Nasdaq RTAT10 activity data:

   * `minActivity`
   * `maxActivity`
   * `avgActivity`

Results are written back to MongoDB collection:

```text
analytics_summaries
```

Expected Spark result types:

```text
spark_yearly_close_summary
spark_yearly_activity_summary
```

---

### Spark MLlib prediction workflow

```powershell
python -m spark_jobs.spark_prediction_job
```

This job uses Spark MLlib `LinearRegression` to train a simple prediction model using:

```text
business date as feature
close price as label
```

It predicts the next close price and stores the result in:

```text
prediction_results
```

Expected Spark ML result:

```text
model: spark_mllib_linear_regression
computedBy: pyspark_prediction_job
resultType: spark_prediction
```

---

### Run all Spark jobs

```powershell
.\scripts\run_spark_jobs.ps1
```

Equivalent manual commands:

```powershell
python -m spark_jobs.export_latest_time_series
python -m spark_jobs.spark_yearly_summary_job
python -m spark_jobs.spark_prediction_job
```

If Java is not detected automatically on Windows, update `scripts/run_spark_jobs.ps1` with the correct `JAVA_HOME` path.

---

## 15. MCP / LLM Assistant Integration

The platform includes MCP-compatible tools in:

```text
app/mcp_server.py
```

Available tool functions include:

```text
list_assets
get_asset_details
list_data_sources
get_data_source_details
get_time_series_data
summarize_asset
compare_assets
predict_next_close
summarize_activity
list_persisted_summaries
list_persisted_predictions
```

These tools call the platform’s REST API, so answers are grounded in warehouse data rather than generic finance text.

---

### MCP demo workflow

Make sure FastAPI is running:

```powershell
python -m uvicorn app.main:app --reload
```

Then run:

```powershell
python -m demo.mcp_demo_workflow
```

The demo workflow shows:

* asset discovery
* asset details
* time-series retrieval
* historical as-of query
* trend summary
* asset comparison
* prediction
* Nasdaq activity summary
* persisted analytics summaries
* persisted prediction results

Example assistant prompts are available in:

```text
demo/assistant_prompts.md
```

---

## 16. Running Tests

Make sure MongoDB is running:

```powershell
docker compose up -d mongodb
```

Run:

```powershell
pytest
```

The tests cover:

* summary calculation
* prediction calculation
* asset comparison
* temporal latest-version logic
* historical `asOfSystemTime` behavior
* temporal asset deactivation markers
* temporal data source deactivation markers
* activity analytics
* batch close aggregation
* batch activity aggregation
* CSV ingestion
* mocked Nasdaq ingestion


---
