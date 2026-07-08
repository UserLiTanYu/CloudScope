from decimal import Decimal

from etl.transformers.records import transform_host, transform_metric, transform_tsar


def test_transform_host() -> None:
    record = transform_host(
        {
            "hostid": "host001",
            "hostname": "server-001.hismartlab.cn",
            "owner": "owner",
            "model": "Dell R750",
            "location1": "A",
            "location2": "rack01",
        }
    )

    assert record.hostid == "host001"
    assert record.model == "Dell R750"


def test_transform_metric() -> None:
    record = transform_metric(
        {
            "mod": "cpu_user",
            "type": "pref",
            "desc": "CPU user usage",
            "unit": "%",
            "tag": "cpu_percent",
        }
    )

    assert record.mod == "cpu_user"
    assert record.description == "CPU user usage"


def test_transform_tsar() -> None:
    record = transform_tsar(
        {
            "ts": "1782835200000",
            "hostid": "host001",
            "type": "pref",
            "mod": "cpu_user",
            "value": "21.70",
            "tag": "cpu_percent",
        }
    )

    assert record.value == Decimal("21.70")
    assert record.collect_time.year == 2026
