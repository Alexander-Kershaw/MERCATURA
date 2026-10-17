import json
from datetime import UTC, datetime
from importlib.metadata import version


def build_smoke_test_report() -> dict[str, str]:

    return {
        "application": "mercatura",
        "version": version(distribution_name="mercatura"),
        "status": "ok",
        "executed_at_utc": datetime.now(tz=UTC).isoformat(),
    }


def main() -> None:
    report: dict[str, str] = build_smoke_test_report()
    print(json.dumps(obj=report, sort_keys=True, indent=4))


if __name__ == "__main__":
    main()
