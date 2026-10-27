from __future__ import annotations
from datetime import datetime, timezone
import json
from statistics import median
from src.database.warehouse import connect, query_frame
from src.ingestion.acquire import ROOT


def execute_analyses():
    out = ROOT / "reports/sql_results"
    out.mkdir(parents=True, exist_ok=True)
    evidence = []
    for path in sorted((ROOT / "sql/analytics").glob("*.sql")):
        frame = query_frame(path.read_text(encoding="utf-8"))
        frame.to_csv(out / (path.stem + ".csv"), index=False)
        evidence.append({"query": path.name, "status": "PASS", "rows": len(frame), "columns": list(frame.columns)})
    (ROOT / "reports/validation/sql_execution.json").write_text(json.dumps({"executed_at": datetime.now(timezone.utc).isoformat(), "passed": len(evidence), "failed": 0, "queries": evidence}, indent=2))
    return evidence


def optimisation():
    provider = query_frame("SELECT provider_code FROM analytics.rtt_provider_month ORDER BY month DESC,waiting_count DESC LIMIT 1").iloc[0, 0]
    query = "SELECT month,sum(over_52) FROM analytics.fact_rtt WHERE pathway_type='Part_2' AND provider_code=%s GROUP BY month"
    result = {"query": query, "provider_code": provider, "method": "5 executions per plan setting; cache/order effects remain; diagnostic comparison, not a benchmark"}
    with connect() as conn:
        for label, settings in (("planner_default", "SET LOCAL enable_indexscan=on; SET LOCAL enable_bitmapscan=on"), ("sequential_scan_comparison", "SET LOCAL enable_indexscan=off; SET LOCAL enable_bitmapscan=off")):
            conn.execute(settings)
            plans = [conn.execute("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + query, (provider,)).fetchone()[0][0] for _ in range(5)]
            result[label] = {"execution_ms": [p["Execution Time"] for p in plans], "median_ms": median(p["Execution Time"] for p in plans), "plan": plans[-1]}
    (ROOT / "reports/validation/explain_analyze.json").write_text(json.dumps(result, indent=2))
    return result
