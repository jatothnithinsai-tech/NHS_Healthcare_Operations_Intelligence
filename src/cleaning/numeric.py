from __future__ import annotations
import pandas as pd

MISSING = {"", ":", "-", "..", "...", "*", "x", "X", "NA", "N/A", "n/a", "NULL"}


def numeric(frame: pd.DataFrame) -> pd.DataFrame:
    """Preserve published missing/suppressed values as nullable counts."""
    cleaned = frame.apply(lambda s: s.astype("string").str.strip())
    invalid = cleaned.notna() & ~cleaned.isin(MISSING) & cleaned.apply(lambda s: pd.to_numeric(s, errors="coerce").isna())
    if invalid.any().any():
        raise ValueError(f"Unexpected numeric tokens: {cleaned.where(invalid).stack().unique().tolist()[:12]}")
    converted = cleaned.mask(cleaned.isin(MISSING)).apply(pd.to_numeric, errors="raise")
    if ((converted % 1) != 0).fillna(False).any().any():
        raise ValueError("Fractional source counts")
    result = converted.astype("Int64")
    if (result < 0).any().any():
        raise ValueError("Negative source counts")
    return result


def strict_sum(frame: pd.DataFrame, columns: list[str]) -> pd.Series:
    return frame[columns].sum(axis=1, min_count=len(columns)).astype("Int64")
