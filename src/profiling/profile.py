from __future__ import annotations
import pandas as pd


def profile(frame: pd.DataFrame, source: dict) -> dict:
    return {"dataset": source["dataset"], "reporting_month": source["reporting_month"], "sha256": source["sha256"], "rows": len(frame), "columns": list(frame.columns), "dtypes": {str(k): str(v) for k, v in frame.dtypes.items()}, "missing": {str(k): int(v) for k, v in frame.isna().sum().items()}, "duplicate_rows": int(frame.duplicated().sum()), "period_values": frame["Period"].dropna().unique().tolist(), "provider_codes": int(frame.get("Provider Org Code", frame.get("Org Code")).nunique()), "numeric_ranges": {c: {"min": float(frame[c].min()), "max": float(frame[c].max())} for c in frame.select_dtypes("number") if frame[c].notna().any()}}
