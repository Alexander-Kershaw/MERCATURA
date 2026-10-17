import json
from importlib import import_module
from pathlib import Path
from typing import Any

CATALOG = "mercatura_dev"
SCHEMA = "landing"
VOLUME = "source_files"

VOLUME_PATH = Path(f"/Volumes/{CATALOG}/{SCHEMA}/{VOLUME}")


def get_spark_session() -> Any:
    pyspark_sql_module = import_module(name="pyspark.sql")
    return pyspark_sql_module.SparkSession.builder.getOrCreate()


def build_catalog_smoke_test_report() -> dict[str, object]:
    spark = get_spark_session()

    spark.sql(f"USE CATALOG {CATALOG}")
    spark.sql(f"USE SCHEMA {SCHEMA}")

    spark_context = spark.sql(
        """
        SELECT
            current_catalog() AS catalog,
            current_schema() AS schema
        """
    ).first()

    spark.sql(f"DESCRIBE VOLUME {CATALOG}.{SCHEMA}.{VOLUME}").collect()

    entries: list[Path] = list(VOLUME_PATH.iterdir())

    return {
        "status": "ok",
        "catalog": spark_context.catalog,
        "schema": spark_context.schema,
        "volume": VOLUME,
        "volume_path": str(object=VOLUME_PATH),
        "volume_readable": True,
        "volume_entry_count": len(entries),
    }


def main() -> None:
    report: dict[str, object] = build_catalog_smoke_test_report()
    print(json.dumps(report, sort_keys=True, indent=4))


if __name__ == "__main__":
    main()
