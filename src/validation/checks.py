from __future__ import annotations
import pandas as pd
from src.database.warehouse import query_frame


def validate_frame(frame: pd.DataFrame, domain: str) -> list[dict]:
    keys = {"rtt": ["month", "provider_code", "specialty_code", "pathway_type"], "ae": ["month", "provider_code"], "diagnostics": ["month", "provider_code", "test_code"]}[domain]
    if frame.duplicated(keys).any():
        raise ValueError(f"Duplicate {domain} grain")
    if frame["provider_code"].isna().any() or not frame["provider_code"].str.fullmatch(r"[A-Z0-9]{3,6}").all():
        raise ValueError("Invalid/missing official provider code")
    nums = frame.select_dtypes("number")
    if (nums < 0).any().any():
        raise ValueError("Negative transformed count")
    return [{"check": "unique_grain", "status": "PASS", "rows": len(frame)}, {"check": "provider_code_format", "status": "PASS"}]


def warehouse_checks() -> list[dict]:
    checks = []
    for domain, fact in (("rtt", "fact_rtt"), ("ae", "fact_ae"), ("diagnostics", "fact_diagnostics")):
        df = query_frame(f"SELECT month,count(*) AS rows FROM analytics.{fact} GROUP BY month ORDER BY month")
        expected = pd.date_range(df.month.min(), df.month.max(), freq="MS")
        checks.append({"check": f"{domain}_consecutive_months", "status": "PASS" if len(df) == len(expected) and len(df) >= 24 else "FAIL", "months": len(df)})
        checks.append({"check": f"{domain}_audit_row_counts", "status": "PASS" if int(df.rows.sum()) == int(query_frame(f"SELECT sum(rows_loaded) AS n FROM audit.loaded_source WHERE dataset='{domain}'").iloc[0, 0]) else "FAIL", "rows": int(df.rows.sum())})
    if any(x["status"] == "FAIL" for x in checks):
        raise ValueError(f"Warehouse validation failed: {checks}")
    return checks
