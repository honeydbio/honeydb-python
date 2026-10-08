"""Tests pinning the ASN risk response contract against trimmed API fixtures."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from honeydb import Client, cli

BASE = "https://honeydb.io/api"
CREDS = ["--api-id", "id", "--api-key", "key"]
FIXTURES = Path(__file__).parent / "fixtures"

AUG_RANKING = "asn_risk_2026-08_ranking.json"
AUG_SCANNERS = "asn_risk_2026-08_scanners_only.json"
JUL_RANKING = "asn_risk_2026-07_ranking.json"
JUL_SCANNERS = "asn_risk_2026-07_scanners_only.json"
HISTORY_SCANNER = "asn_risk_history_398324.json"
HISTORY_RANKED = "asn_risk_history_203451.json"
HISTORY_GAP = "asn_risk_history_42969.json"

# fixture -> (asn_risk() kwargs, query string the client must send)
REPORTS = {
    AUG_RANKING: (
        {"period": "2026-08", "limit": 3},
        {"period": ["2026-08"], "limit": ["3"]},
    ),
    AUG_SCANNERS: (
        {"period": "2026-08", "limit": 3, "scanners": "only"},
        {"period": ["2026-08"], "limit": ["3"], "scanners": ["only"]},
    ),
    JUL_RANKING: (
        {"period": "2026-07", "limit": 3},
        {"period": ["2026-07"], "limit": ["3"]},
    ),
    JUL_SCANNERS: (
        {"period": "2026-07", "scanners": "only"},
        {"period": ["2026-07"], "scanners": ["only"]},
    ),
}
HISTORIES = {
    HISTORY_SCANNER: 398324,
    HISTORY_RANKED: 203451,
    HISTORY_GAP: 42969,
}

SCORE_KEYS = ("risk_score", "rank", "percentile")
ACTIVITY_KEYS = {
    "asn",
    "entity",
    "scanner",
    "observed_ips",
    "announced_ipv4_space",
    "density",
    "days_seen",
    "services_seen",
}
RANKED_ONLY_KEYS = {"risk_score", "rank", "percentile", "components", "prior"}


def load(name):
    return json.loads((FIXTURES / name).read_text())


def help_text(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        cli.main([*argv, "--help"])
    assert exit_info.value.code == 0
    return " ".join(capsys.readouterr().out.split())


@pytest.fixture
def client():
    with Client("test-id", "test-key") as c:
        yield c


# -- pass-through -----------------------------------------------------------


@pytest.mark.parametrize("name", REPORTS)
def test_asn_risk_returns_fixture_unchanged(client, requests_mock, name):
    kwargs, query = REPORTS[name]
    m = requests_mock.get(f"{BASE}/asn-risk", json=load(name))
    assert client.asn_risk(**kwargs) == load(name)
    assert m.last_request.path == "/api/asn-risk"
    assert m.last_request.qs == query


@pytest.mark.parametrize("name", HISTORIES)
def test_asn_risk_history_returns_fixture_unchanged(client, requests_mock, name):
    asn = HISTORIES[name]
    m = requests_mock.get(f"{BASE}/asn/{asn}/risk", json=load(name))
    assert client.asn_risk_history(asn) == load(name)
    assert m.last_request.path == f"/api/asn/{asn}/risk"


@pytest.mark.parametrize(
    ("name", "argv"),
    [
        (AUG_RANKING, ["asn-risk", "--period", "2026-08", "--limit", "3"]),
        (
            AUG_SCANNERS,
            ["asn-risk", "--period", "2026-08", "--limit", "3", "--scanners", "only"],
        ),
    ],
)
def test_cli_asn_risk_emits_fixture_unchanged(capsys, requests_mock, name, argv):
    requests_mock.get(f"{BASE}/asn-risk", json=load(name))
    assert cli.main([*CREDS, *argv]) == 0
    assert json.loads(capsys.readouterr().out) == load(name)


def test_cli_asn_risk_flag_emits_fixture_unchanged(capsys, requests_mock):
    requests_mock.get(f"{BASE}/asn/398324/risk", json=load(HISTORY_SCANNER))
    assert cli.main([*CREDS, "asn", "398324", "--risk"]) == 0
    assert json.loads(capsys.readouterr().out) == load(HISTORY_SCANNER)


# -- /asn-risk: split-shape month (August 2026) -----------------------------


def test_split_month_ranking_contract():
    report = load(AUG_RANKING)
    assert report["methodology"]["version"] == "2.0"
    assert report["methodology"]["scanner_handling"] == "separate_report"
    assert report["asns_report"] == "ranking"
    assert report["asns_total"] == 3218
    assert report["asns_returned"] == len(report["asns"]) == 3
    for row in report["asns"]:
        assert all(key in row for key in SCORE_KEYS)
        assert row["scanner"] is None
    assert report["summary"]["scanners_tagged"] is None


def test_split_month_scanners_only_returns_activity_rows():
    report = load(AUG_SCANNERS)
    assert report["asns_report"] == "scanners"
    assert report["asns_total"] == 10
    assert report["asns_returned"] == len(report["asns"]) == 3
    for row in report["asns"]:
        assert set(row) == ACTIVITY_KEYS
        assert not RANKED_ONLY_KEYS & set(row)
        assert set(row["scanner"]) == {"name", "url"}


@pytest.mark.parametrize("name", [AUG_RANKING, AUG_SCANNERS])
def test_scanner_report_is_on_every_split_month_response(name):
    report = load(name)
    scanner_report = report["scanner_report"]
    assert set(scanner_report) == {
        "risk_assessment",
        "statement",
        "scanner_list_version",
        "asns_observed",
        "asns",
    }
    assert scanner_report["risk_assessment"] == "benign"
    assert scanner_report["statement"]
    assert (
        len(scanner_report["asns"])
        == scanner_report["asns_observed"]
        == report["summary"]["scanners_observed"]
        == 10
    )


def test_limit_does_not_cap_the_scanner_report():
    report = load(AUG_SCANNERS)
    assert report["filters"]["limit"] == 3
    assert report["asns"] == report["scanner_report"]["asns"][:3]
    assert len(report["scanner_report"]["asns"]) > len(report["asns"])


# -- /asn-risk: methodology 1.0 month (July 2026) ---------------------------


@pytest.mark.parametrize("name", [JUL_RANKING, JUL_SCANNERS])
def test_v1_month_has_no_scanner_report(name):
    report = load(name)
    assert report["methodology"]["version"] == "1.0"
    assert "scanner_handling" not in report["methodology"]
    assert "scanner_report" not in report
    assert report["asns_report"] == "ranking"
    assert report["asns_total"] == 1977
    assert report["summary"]["scanners_observed"] is None


def test_v1_month_ranking_rows_are_scored():
    report = load(JUL_RANKING)
    assert report["asns_returned"] == len(report["asns"]) == 3
    for row in report["asns"]:
        assert "risk_score" in row and "rank" in row


def test_v1_month_scanners_only_is_an_empty_ranking():
    report = load(JUL_SCANNERS)
    assert report["asns"] == []
    assert report["asns_returned"] == 0


# -- /asn/{asn}/risk --------------------------------------------------------


@pytest.mark.parametrize("name", HISTORIES)
def test_history_top_level_keys(name):
    assert set(load(name)) == {
        "asn",
        "entity",
        "latest_month",
        "latest",
        "known_scanner",
        "months_checked",
        "history",
    }


def test_history_for_a_known_scanner():
    result = load(HISTORY_SCANNER)
    known = result["known_scanner"]
    assert set(known) == {
        "name",
        "url",
        "risk_assessment",
        "statement",
        "scanner_list_version",
        "period",
    }
    assert known["risk_assessment"] == "benign"
    assert known["period"] in result["months_checked"]
    assert not any(key in result["latest"] for key in SCORE_KEYS)

    for entry in result["history"]:
        assert isinstance(entry["known_scanner"], bool)
        if entry["known_scanner"]:
            assert all(entry[key] is None for key in SCORE_KEYS)

    july = result["history"][-1]
    assert july["period"] == "2026-07"
    assert july["known_scanner"] is False
    assert (july["rank"], july["risk_score"]) == (8, 83.4)


def test_history_for_a_ranked_asn():
    result = load(HISTORY_RANKED)
    assert result["known_scanner"] is None
    assert "risk_score" in result["latest"]
    assert all(entry["known_scanner"] is False for entry in result["history"])


def test_history_omits_months_the_asn_was_in_neither_list():
    result = load(HISTORY_GAP)
    assert len(result["months_checked"]) == 3
    assert [entry["period"] for entry in result["history"]] == ["2026-09", "2026-07"]
    assert result["known_scanner"]["period"] == result["latest_month"] == "2026-09"

    september, july = result["history"]
    assert september["known_scanner"] is True
    assert september["rank"] is None and september["risk_score"] is None
    assert july["known_scanner"] is False
    assert (july["rank"], july["risk_score"]) == (145, 65.0)


# -- CLI help ---------------------------------------------------------------


def test_asn_risk_help_describes_the_scanner_report(capsys):
    text = help_text(["asn-risk"], capsys)
    assert "excluded from the ranking" in text
    assert "benign" in text
    assert "internet-scanner flag" not in text


def test_asn_help_mentions_known_scanner_status(capsys):
    assert "known-scanner" in help_text(["asn"], capsys)
