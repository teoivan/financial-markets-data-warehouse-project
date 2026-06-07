import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression
from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, unix_timestamp

from app.database import prediction_results_collection


INPUT_FILE = "data/exports/latest_time_series.json"


def create_spark_session() -> SparkSession:
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    return (
        SparkSession.builder
        .appName("FinancialDwhSparkPrediction")
        .master("local[*]")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .getOrCreate()
    )


def run_spark_prediction_job(
    asset_id: str = "BTCUSD",
    data_source_id: str = "NASDAQ_DATA_LINK_BITFINEX",
) -> dict:
    input_path = Path(INPUT_FILE)

    if not input_path.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} does not exist. "
            "Run: python -m spark_jobs.export_latest_time_series first."
        )

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    df = spark.read.json(INPUT_FILE)

    asset_df = (
        df
        .filter(col("assetId") == asset_id)
        .filter(col("dataSourceId") == data_source_id)
        .filter(col("values.close").isNotNull())
        .withColumn("businessDateParsed", to_date(col("businessDate")))
        .withColumn("dateNumber", unix_timestamp(col("businessDateParsed")))
        .select(
            "assetId",
            "dataSourceId",
            "businessDate",
            "dateNumber",
            col("values.close").alias("close"),
        )
        .orderBy("businessDate")
    )

    record_count = asset_df.count()

    if record_count < 2:
        spark.stop()
        return {
            "jobType": "spark_prediction_job",
            "engine": "Apache Spark MLlib",
            "assetId": asset_id,
            "dataSourceId": data_source_id,
            "recordCount": record_count,
            "message": "Not enough records for Spark ML prediction.",
        }

    assembler = VectorAssembler(
        inputCols=["dateNumber"],
        outputCol="features",
    )

    training_df = assembler.transform(asset_df).select(
        "features",
        col("close").alias("label"),
    )

    model = LinearRegression(
        featuresCol="features",
        labelCol="label",
        predictionCol="prediction",
    )

    fitted_model = model.fit(training_df)

    latest_row = asset_df.orderBy(col("businessDate").desc()).first()
    latest_date_number = latest_row["dateNumber"]
    latest_close = latest_row["close"]

    # Daily data: predict the next day as +86400 seconds.
    next_date_number = latest_date_number + 86400

    prediction_input = spark.createDataFrame(
        [(next_date_number,)],
        ["dateNumber"],
    )

    prediction_features = assembler.transform(prediction_input)
    prediction_row = fitted_model.transform(prediction_features).first()

    predicted_next_close = float(prediction_row["prediction"])

    result = {
        "assetId": asset_id,
        "dataSourceId": data_source_id,
        "model": "spark_mllib_linear_regression",
        "recordCount": record_count,
        "lastClose": float(latest_close),
        "predictedNextClose": round(predicted_next_close, 2),
        "signal": "positive" if predicted_next_close >= latest_close else "negative",
        "computedAt": datetime.now(timezone.utc),
        "computedBy": "pyspark_prediction_job",
        "resultType": "spark_prediction",
        "explanation": (
            "Prediction was computed using Apache Spark MLlib LinearRegression "
            "with business date as the feature and close price as the label."
        ),
    }

    prediction_results_collection.insert_one(result)

    result["_id"] = str(result["_id"])
    result["computedAt"] = result["computedAt"].isoformat()

    spark.stop()

    return {
        "jobType": "spark_prediction_job",
        "engine": "Apache Spark MLlib",
        "result": result,
    }


if __name__ == "__main__":
    output = run_spark_prediction_job()
    print(output)