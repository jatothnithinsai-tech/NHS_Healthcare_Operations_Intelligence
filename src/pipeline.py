"""One-command offline or publication-refresh pipeline."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import logging
import time
import pandas as pd
from src.database.warehouse import initialise, load_frame, start_run, finish_run, connect
from src.ingestion.acquire import ROOT, acquire
from src.monitoring.logging_config import configure_logging
from src.transformation.parsers import parse
from src.validation.checks import validate_frame, warehouse_checks


def run(refresh=False, reports=False):
    configure_logging()
    started = time.perf_counter()
    initialise()
    lock = connect()
    if not lock.execute("SELECT pg_try_advisory_lock(68420261026)").fetchone()[0]:
        lock.close()
        raise RuntimeError("Another project pipeline run holds the warehouse lock")
    with connect() as conn:
        conn.execute("UPDATE audit.pipeline_run SET status='abandoned',summary=summary||'{\"audit_note\":\"Previous run ended without final status; detected after acquiring exclusive pipeline lock\"}'::jsonb WHERE status='running'")
    run_id = start_run()
    summary = {"run_id": run_id, "started_at": datetime.now(timezone.utc).isoformat(), "loaded": 0, "skipped": 0}
    try:
        manifest = acquire(refresh=refresh)
        config = json.loads((ROOT / "config/settings.json").read_text())
        profiles, issues = [], []
        for source in manifest:
            path = ROOT / "data/processed" / source["dataset"] / f"{source['sha256']}-{config['parser_version']}.parquet"
            profile_path = path.with_suffix(".profile.json")
            if path.exists() and profile_path.exists():
                frame = pd.read_parquet(path)
                detail = json.loads(profile_path.read_text())
                prof, warnings = detail["profile"], detail["issues"]
            else:
                frame, prof, warnings = parse(source)
                validate_frame(frame, source["dataset"])
                path.parent.mkdir(parents=True, exist_ok=True)
                frame.to_parquet(path, index=False)
                profile_path.write_text(json.dumps({"profile": prof, "issues": warnings}, indent=2), encoding="utf-8")
            validate_frame(frame, source["dataset"])
            changed = load_frame(frame, source, config["parser_version"])
            summary["loaded" if changed else "skipped"] += 1
            profiles.append(prof)
            issues.extend(warnings)
            logging.info("%s %s %s rows=%d", source["dataset"], source["reporting_month"], "loaded" if changed else "unchanged", len(frame))
        summary["checks"] = warehouse_checks()
        with connect() as conn:
            for table in ("fact_rtt", "fact_ae", "fact_diagnostics"):
                conn.execute("ANALYZE analytics." + table)
        summary["seconds"] = round(time.perf_counter() - started, 3)
        summary["source_files"] = len(manifest)
        summary["source_rows"] = sum(x["rows"] for x in profiles)
        summary["fact_rows"] = sum(x["transformed_rows"] for x in profiles)
        summary["issues"] = len(issues)
        out = ROOT / "reports/validation"
        out.mkdir(parents=True, exist_ok=True)
        (out / "source_profiles.json").write_text(json.dumps(profiles, indent=2), encoding="utf-8")
        (out / "data_quality_issues.json").write_text(json.dumps(issues, indent=2), encoding="utf-8")
        (out / "pipeline_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        (out / "runs").mkdir(exist_ok=True)
        (out / "runs" / f"{run_id}.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
        finish_run(run_id, "success", summary)
        if reports:
            from src.reporting.build import build_all
            build_all()
        print(json.dumps(summary, indent=2))
        return summary
    except BaseException as exc:
        summary["error_type"] = type(exc).__name__
        finish_run(run_id, "interrupted" if isinstance(exc,KeyboardInterrupt) else "failed", summary)
        logging.exception("Pipeline failed; affected file load rolled back")
        raise
    finally:
        lock.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="Check official publications and revisions over the network")
    parser.add_argument("--reports", action="store_true", help="Rebuild analytical and management outputs")
    args = parser.parse_args()
    run(refresh=args.refresh, reports=args.reports)
