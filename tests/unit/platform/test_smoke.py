from mercatura.platform.smoke import build_smoke_test_report


def test_build_smoke_test_report() -> None:

    report: dict[str, str] = build_smoke_test_report()

    assert report["application"] == "mercatura"
    assert report["version"] is not None
    assert report["status"] == "ok"
    assert report["executed_at_utc"] is not None
