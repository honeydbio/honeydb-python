# Test fixtures

Trimmed HoneyDB API responses used by `tests/test_asn_risk_fixtures.py`. They
were derived on 2026-10-08 from the published monthly ASN risk reports and hold
public report data only. Row lists are trimmed with `limit`; refresh the files
if the API contract changes.

| File | Request |
| --- | --- |
| `asn_risk_2026-08_ranking.json` | `GET /api/asn-risk?period=2026-08&limit=3` |
| `asn_risk_2026-08_scanners_only.json` | `GET /api/asn-risk?period=2026-08&limit=3&scanners=only` |
| `asn_risk_2026-07_ranking.json` | `GET /api/asn-risk?period=2026-07&limit=3` |
| `asn_risk_2026-07_scanners_only.json` | `GET /api/asn-risk?period=2026-07&scanners=only` |
| `asn_risk_history_398324.json` | `GET /api/asn/398324/risk` — a known scanner |
| `asn_risk_history_203451.json` | `GET /api/asn/203451/risk` — a ranked ASN |
| `asn_risk_history_42969.json` | `GET /api/asn/42969/risk` — a known scanner absent from one month |
