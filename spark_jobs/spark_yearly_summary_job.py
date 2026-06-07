import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, col, count, lit, max, min, round as spark_round

from app.database import analytics_summaries_collection


INPUT_FILE = "data/exports/latest_time_series.json"


def create_spark_session() -> SparkSession:
    os.environ["PYSPARK_PYTHON"] = sys.executable
    os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

    return (
        SparkSession.builder
        .appName("FinancialDwhSparkYearlySummary")
        .master("local[*]")
        .config("spark.pyspark.python", sys.executable)
        .config("spark.pyspark.driver.python", sys.executable)
        .getOrCreate()
    )


def rows_to_dicts(rows):
    return [row.asDict(recursive=True) for row in rows]


def persist_results(results: list[dict]) -> None:
    if not results:
        return

    analytics_summaries_collection.insert_many(results)


def run_spark_yearly_summary_job() -> dict:
    input_path = Path(INPUT_FILE)

    if not input_path.exists():
        raise FileNotFoundError(
            f"{INPUT_FILE} does not exist. "
            "Run: python -m spark_jobs.export_latest_time_series first."
        )

    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    df = spark.read.json(INPUT_FILE)

    close_df = df.filter(col("values.close").isNotNull())

    close_summary_df = (
        close_df
        .groupBy("assetId", "dataSourceId", "businessYear")
        .agg(
            count("*").alias("recordCount"),
            min(col("values.close")).alias("minClose"),
            max(col("values.close")).alias("maxClose"),
            spark_round(avg(col("values.close")), 2).alias("avgClose"),
            min(col("values.volume")).alias("minVolume"),
            max(col("values.volume")).alias("maxVolume"),
            spark_round(avg(col("values.volume")), 2).alias("avgVolume"),
        )
        .withColumn("computedAt", lit(datetime.now(timezone.utc).isoformat()))
        .withColumn("computedBy", lit("pyspark_yearly_summary_job"))
        .withColumn("resultType", lit("spark_yearly_close_summary"))
    )

    activity_df = df.filter(col("values.activity").isNotNull())

    activity_summary_df = (
        activity_df
        .groupBy("assetId", "dataSourceId", "businessYear")
        .agg(
            count("*").alias("recordCount"),
            min(col("values.activity")).alias("minActivity"),
            max(col("values.activity")).alias("maxActivity"),
            spark_round(avg(col("values.activity")), 6).alias("avgActivity"),
        )
        .withColumn("computedAt", lit(datetime.now(timezone.utc).isoformat()))
        .withColumn("computedBy", lit("pyspark_yearly_summary_job"))
        .withColumn("resultType", lit("spark_yearly_activity_summary"))
    )

    close_results = rows_to_dicts(close_summary_df.collect())
    activity_results = rows_to_dicts(activity_summary_df.collect())

    persist_results(close_results)
    persist_results(activity_results)

    close_count = len(close_results)
    activity_count = len(activity_results)

    spark.stop()

    return {
        "jobType": "spark_yearly_summary_job",
        "engine": "Apache Spark / PySpark",
        "inputFile": INPUT_FILE,
        "targetCollection": "analytics_summaries",
        "closeGroupsComputed": close_count,
        "activityGroupsComputed": activity_count,
    }


if __name__ == "__main__":
    result = run_spark_yearly_summary_job()
    print(result)