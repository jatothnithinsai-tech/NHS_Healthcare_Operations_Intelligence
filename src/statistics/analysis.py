from __future__ import annotations
import numpy as np
import pandas as pd
from scipy import stats


def block_indices(n: int, block: int, rng: np.random.Generator) -> np.ndarray:
    starts = rng.integers(0, n, size=int(np.ceil(n / block)))
    return np.concatenate([(s + np.arange(block)) % n for s in starts])[:n]


def chronological_baselines(values: np.ndarray, minimum_train: int = 12) -> dict:
    """One-step origins; neither baseline sees its target observation."""
    values = np.asarray(values, dtype=float)
    if len(values) <= minimum_train:
        raise ValueError("Insufficient history for chronological evaluation")
    actual = values[minimum_train:]
    persistence = values[minimum_train - 1:-1]
    seasonal = values[minimum_train - 12:-12]
    return {"origins": len(actual), "minimum_training_months": minimum_train, "persistence_mae": float(np.abs(actual - persistence).mean()), "seasonal_naive_mae": float(np.abs(actual - seasonal).mean()), "persistence_bias": float((persistence - actual).mean()), "horizon": "one reporting month", "predictions": [{"index": i + minimum_train, "actual": float(a), "persistence": float(p), "seasonal_naive": float(s)} for i, (a, p, s) in enumerate(zip(actual, persistence, seasonal))]}


def analyse(national: pd.DataFrame, provider: pd.DataFrame) -> dict:
    national = national.copy()
    numeric_cols = [c for c in national if c != "month"]
    national[numeric_cols] = national[numeric_cols].apply(pd.to_numeric)
    common = national[["rtt_waiting", "diagnostic_waiting"]].dropna().diff().dropna()
    rng = np.random.default_rng(20261026)
    x, y = common.rtt_waiting.to_numpy(), common.diagnostic_waiting.to_numpy()
    coefficient = float(stats.pearsonr(x, y).statistic)
    boot = []
    for _ in range(2000):
        idx = block_indices(len(x), 3, rng)
        if np.std(x[idx]) and np.std(y[idx]):
            boot.append(float(np.corrcoef(x[idx], y[idx])[0, 1]))
    rates = pd.to_numeric(provider.loc[provider.waiting_count >= 1000, "within_18_rate"]).dropna()
    latest = national.rtt_waiting.dropna().to_numpy(dtype=float)
    start, end = latest[:6], latest[-6:]
    changes = [end[block_indices(6, 3, rng)].mean() - start[block_indices(6, 3, rng)].mean() for _ in range(2000)]
    return {
        "national_descriptive": national[numeric_cols].describe().to_dict(),
        "provider_rate_distribution": {"eligible_providers": len(rates), "median": float(rates.median()), "q1": float(rates.quantile(.25)), "q3": float(rates.quantile(.75)), "min": float(rates.min()), "max": float(rates.max())},
        "monthly_change_correlation": {"n": len(x), "pearson_r": coefficient, "block_bootstrap_95_interval": np.quantile(boot, [.025, .975]).tolist(), "block_length": 3, "replicates": 2000, "interpretation": "Exploratory association of national monthly changes; interval describes temporal process variability, not patient sampling uncertainty. Differencing mitigates shared trends but does not establish causality."},
        "rtt_first_last_six_months": {"mean_change_pathways": float(end.mean() - start.mean()), "relative_change": float(end.mean() / start.mean() - 1), "block_bootstrap_95_interval": np.quantile(changes, [.025, .975]).tolist(), "caveat": "Only six observations per window; block sensitivity and structural changes limit inference. Descriptive effect, not intervention impact."},
        "chronological_forecast_evaluation": chronological_baselines(latest),
        "hypothesis_testing": "No confirmatory p-values: aggregate census-style reporting, serial dependence and changing provider coverage do not support an independent-observation test without stronger assumptions.",
        "seasonality": "At most two annual cycles: month-of-year patterns are descriptive; no stable seasonal effect is claimed.",
        "seed": 20261026,
    }
