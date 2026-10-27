from __future__ import annotations
from datetime import datetime, timezone
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from src.analytics.run_sql import execute_analyses, optimisation
from src.database.warehouse import query_frame
from src.ingestion.acquire import ROOT
from src.statistics.analysis import analyse


def export_frame(name, query):
    frame = query_frame(query)
    frame.to_csv(ROOT / "powerbi/data" / (name + ".csv"), index=False)
    return frame


def plain(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def chart(national):
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold"})
    fig, axes = plt.subplots(3, 1, figsize=(12, 10), sharex=True)
    months = pd.to_datetime(national.month)
    panels = [("rtt_waiting", "Incomplete RTT pathways (submitted data)", 1e6, "Million pathways"), ("within_4_rate", "A&E attendances completed within four hours", .01, "Percent"), ("over_6_rate", "Diagnostic waits of six weeks or more", .01, "Percent")]
    for ax, (col, title, divisor, unit) in zip(axes, panels):
        ax.plot(months, pd.to_numeric(national[col]) / divisor, color="#007F86", lw=2.5, marker="o", markersize=3)
        ax.set_title(title, loc="left", color="#123047", pad=14)
        ax.set_ylabel(unit)
        ax.grid(axis="y", alpha=.18)
    axes[-1].set_xlabel("Reporting month · monthly published aggregate observations")
    fig.suptitle("NHS Healthcare Operations & Performance Intelligence", x=.125, ha="left", color="#123047", fontsize=17, fontweight="bold")
    fig.text(.125,.015,"Source: NHS England. Separate populations and release periods; RTT excludes estimates for missing trusts. Independent portfolio analysis.", fontsize=8,color="#526575")
    fig.tight_layout(rect=[0,.035,1,.95])
    fig.savefig(ROOT / "reports/figures/national_trends.png", dpi=150)
    plt.close(fig)


def write_findings(national, rtt, ae, diag, provider, stats, opt):
    r,a,g = rtt.iloc[-1],ae.iloc[-1],diag.iloc[-1]
    prev_r, prev_a, prev_g = rtt.iloc[-2],ae.iloc[-2],diag.iloc[-2]
    priority = provider.sort_values("over_52", ascending=False).head(10)
    total = float(r.over_52)
    share = float(pd.to_numeric(priority.over_52).sum()) / total if total else 0
    special = query_frame((ROOT / "sql/analytics/05_rtt_specialty.sql").read_text())
    tests = query_frame((ROOT / "sql/analytics/19_diagnostic_tests.sql").read_text())
    def month(x):
        return str(x)[:7]
    text = f"""# NHS Healthcare Executive Decision Report

Generated from PostgreSQL on {datetime.now(timezone.utc).isoformat()}. Independent portfolio analysis; no NHS endorsement.

## Executive summary

RTT ({month(r.month)}) contains **{int(r.waiting_count):,} submitted incomplete pathways**, with **{float(r.within_18_rate):.1%}** within 18 weeks and **{int(r.over_52):,}** over 52 weeks. A&E ({month(a.month)}) reports **{int(a.attendances):,} attendances** with **{float(a.within_4_rate):.1%}** completed within four hours. Diagnostics ({month(g.month)}) reports **{int(g.waiting_count):,} waits**, of which **{int(g.over_6):,} ({float(g.over_6_rate):.1%})** reached six weeks or more.

These are three different operational populations. They must never be added into a unique-patient total. Source coverage includes 24 RTT months, 25 A&E months and 24 diagnostic months starting September 2024.

## Management questions and methodology

The BRD defines 24 questions spanning volume, performance, specialties, providers, regional A&E patterns, trends and data quality. Immutable official files are profiled, reconciled to their embedded total rows, aggregated over commissioners, loaded transactionally and analysed by 30 executable PostgreSQL queries. RTT specialty `C_999` and diagnostic `TOTAL` rows are controls, excluded from facts. A&E national `TOTAL` is also excluded after reconciliation. Rates use summed numerators divided by summed denominators.

## RTT findings

- The incomplete list changed by **{int(r.waiting_count)-int(prev_r.waiting_count):+,} pathways** from the previous reporting month; 18-week performance changed by **{100*(float(r.within_18_rate)-float(prev_r.within_18_rate)):+.2f} percentage points**.
- The ten provider codes with the largest over-52-week volumes account for **{share:.1%}** of submitted long waits. This supports a focused validation and capacity review, adjusted for provider size and specialty mix.
- **{special.iloc[0].specialty_name}** has the largest specialty over-52-week volume, **{int(special.iloc[0].over_52):,}**. Investigate the waiting-band distribution and local plans before setting intervention targets.
- Incomplete pathways are a month-end stock. Admitted/non-admitted completions are monthly flows; they are not interchangeable patient cohorts. `Part_2A` is a subset and is excluded from total pathway counts.

## A&E findings

- Four-hour performance changed by **{100*(float(a.within_4_rate)-float(prev_a.within_4_rate)):+.2f} percentage points** month on month.
- Reported emergency admissions total **{int(a.emergency_admissions):,}**; **{int(a.dta_12_plus):,}** waited 12 hours or more from the decision to admit. This is not the same as total time in the emergency department.
- All-department performance includes booked attendance fields. Type 1 performance is reported separately. The source is provider reporting, not the separately attributed acute-trust footprint series introduced in 2026.
- Use regional comparisons from the reporting-period A&E region field; do not impose a current ICB geography on historical RTT/diagnostic records.

## Diagnostic findings

- Six-week-or-more performance changed by **{100*(float(g.over_6_rate)-float(prev_g.over_6_rate)):+.2f} percentage points** month on month.
- **{tests.iloc[0].test_name}** has the largest number of six-week-or-more waits: **{int(tests.iloc[0].over_6):,}**. Review test-level throughput and available slots before drawing conclusions about capacity.
- Monthly diagnostic activity is **{int(g.total_activity):,} tests/procedures**, with waiting-list, planned and unscheduled activity separately retained. Activity is not a count of unique patients.

## Statistical findings and uncertainty

The mean RTT list in the last six months differs from the first six months by **{stats['rtt_first_last_six_months']['mean_change_pathways']:+,.0f} pathways**. This descriptive effect spans changing provider coverage and reporting revisions. A reproducible moving-block bootstrap is included as exploratory temporal uncertainty, not a patient-level confidence interval.

National month-to-month RTT and diagnostic list changes have Pearson correlation **{stats['monthly_change_correlation']['pearson_r']:.3f}** over **{stats['monthly_change_correlation']['n']}** aligned changes. Shared operational and reporting factors can create association; this does not establish causation.

Chronological one-step baseline evaluation has **{stats['chronological_forecast_evaluation']['origins']}** origins: persistence MAE **{stats['chronological_forecast_evaluation']['persistence_mae']:,.0f} pathways**; seasonal-naive MAE **{stats['chronological_forecast_evaluation']['seasonal_naive_mae']:,.0f} pathways**. No future values enter historical predictions. Two annual cycles do not establish stable seasonality. No confirmatory hypothesis test is claimed because independent-observation assumptions are unsupported.

## Action plan

| Priority | Evidence | Investigation | Owner / proposed review | Monitoring KPI |
|---|---|---|---|---|
| 1 | Top ten codes hold {share:.1%} of over-52-week RTT waits | Validate case mix, code continuity and long-wait plans | Elective operations / next monthly review | Over-52/65/78/104-week pathway counts |
| 2 | {int(a.dta_12_plus):,} decision-to-admit waits of 12+ hours | Review bed flow and discharge interfaces with local evidence | Urgent care operations / next monthly review | DTA 12+ count and Type 1 four-hour rate |
| 3 | {tests.iloc[0].test_name}: {int(tests.iloc[0].over_6):,} long waits | Review modality-level throughput, demand and slots | Diagnostic service leads / next monthly review | Six-week rate, waiting list and activity |
| 4 | Dataset releases differ by one month | Display release dates and run validation before refresh | BI/data engineering / each publication | Coverage, source checksums and failed validations |

These are proposed management investigations, not proven causes, savings or implemented improvements.

## Provider comparison limitations

Providers differ in scope, service mix and list size. One identifier is not necessarily one hospital. Names are a latest-known dimension; codes are never silently merged. A stable-code cohort reduces entry/exit effects but cannot resolve all service transfers. Small denominators and coverage changes make league tables unreliable. Aggregate operational measures do not establish clinical quality.

## Reporting limitations

The national RTT analysis is the sum of submitted data, excluding published missing-trust estimates. Some historical publication dates require verification in release archives; they are explicitly null rather than inferred from upload directories. Raw source files remain local and excluded from Git. Power BI validation status, desktop evidence and any remaining checks are recorded separately in the final audit. This is published monthly aggregate intelligence, not real-time patient reporting.

## Reproducibility and query performance

The default PostgreSQL plan for a selected provider/long-wait query has median execution time **{opt['planner_default']['median_ms']:.3f} ms** over five executions; the sequential-scan comparison is **{opt['sequential_scan_comparison']['median_ms']:.3f} ms**. See recorded JSON plans and buffers. Cache and run-order effects prevent general performance claims.

Source attribution: NHS England, RTT waiting times; A&E Attendances and Emergency Admissions; Monthly Diagnostics Waiting Times and Activity. Links and checksums are in `data/reference/source_manifest.json`.
"""
    (ROOT / "reports/NHS_Healthcare_Executive_Decision_Report.md").write_text(text, encoding="utf-8")
    brief = f"""# Stakeholder briefing — NHS operational performance

## Slide 1 — Current published position
RTT {month(r.month)}: {int(r.waiting_count):,} incomplete pathways; {float(r.within_18_rate):.1%} within 18 weeks.  
A&E {month(a.month)}: {float(a.within_4_rate):.1%} within four hours across {int(a.attendances):,} attendances.  
Diagnostics {month(g.month)}: {float(g.over_6_rate):.1%} waiting six weeks or more.

## Slide 2 — Focus the investigation
The ten largest long-wait provider codes account for {share:.1%} of submitted RTT waits over 52 weeks. {special.iloc[0].specialty_name} has {int(special.iloc[0].over_52):,} such waits. Review size and specialty mix before prioritising support.

## Slide 3 — Urgent and diagnostic care
Review {int(a.dta_12_plus):,} A&E decision-to-admit waits of 12+ hours. {tests.iloc[0].test_name} has {int(tests.iloc[0].over_6):,} diagnostic waits of six weeks or more. These figures suggest investigations, not causes.

## Slide 4 — Decisions for the next review
Agree named elective, urgent-care and diagnostic investigation owners. Refresh after official publication, rerun reconciliation and review changes in coverage. Monitor each domain with its own denominator and reporting month.

## Slide 5 — Evidence and limits
73 official files; 24/25/24 months; 30 executable SQL analyses. Three populations, changing provider scope and monthly reporting lag. No patient-level, clinical-quality or causal claims. Full report and validation evidence accompany this briefing.
"""
    (ROOT / "reports/Stakeholder_Briefing.md").write_text(brief, encoding="utf-8")


def build_all():
    for p in ("powerbi/data", "reports/figures", "reports/validation", "excel"):
        (ROOT / p).mkdir(parents=True, exist_ok=True)
    execute_analyses()
    opt = optimisation()
    frames = {}
    for name, query in {
        "Date": "SELECT date AS month,year,month_number,month_name,financial_year FROM analytics.dim_date WHERE date>=date_trunc('year',(SELECT min(month) FROM audit.loaded_source)) AND date<date_trunc('year',(SELECT max(month) FROM audit.loaded_source))+interval '1 year'",
        "Provider": "SELECT provider_code,coalesce(provider_name,provider_code||' (name unreported)') AS provider_name FROM analytics.dim_provider",
        "Specialty": "SELECT * FROM analytics.dim_specialty",
        "Service": "SELECT * FROM analytics.dim_service",
        "Region": "SELECT * FROM analytics.dim_region",
        "Parent": "SELECT * FROM analytics.dim_parent",
        "RTT": "SELECT * FROM analytics.fact_rtt ORDER BY month,provider_code,specialty_code,pathway_type",
        "AE": "SELECT * FROM analytics.fact_ae ORDER BY month,provider_code",
        "Diagnostics": "SELECT * FROM analytics.fact_diagnostics ORDER BY month,provider_code,test_code",
        "National": "SELECT * FROM analytics.executive_month ORDER BY month",
        "Priorities": "SELECT * FROM analytics.operational_priorities ORDER BY over_52 DESC",
        "Sources": "SELECT dataset,month,publication_date,retrieved_at,sha256,bytes,url,coalesce((metadata->>'publisher_revision_label')::boolean,false) AS publisher_revision_label,metadata->>'download_status' AS download_status FROM raw.source_file ORDER BY dataset,month",
        "Pipeline": "SELECT run_id,started_at,finished_at,status,summary->>'loaded' AS loaded_files,summary->>'skipped' AS unchanged_files FROM audit.pipeline_run ORDER BY started_at",
        "Quality": "SELECT c->>'check' AS check_name,c->>'status' AS status,(c->>'months')::integer AS months,(c->>'rows')::bigint AS row_count FROM (SELECT summary FROM audit.pipeline_run WHERE status='success' ORDER BY started_at DESC LIMIT 1) p CROSS JOIN LATERAL jsonb_array_elements(p.summary->'checks') c",
    }.items():
        frames[name] = export_frame(name, query)
    national = frames["National"]
    rtt = query_frame("SELECT * FROM analytics.rtt_national_month ORDER BY month")
    ae = query_frame("SELECT * FROM analytics.ae_national_month ORDER BY month")
    diag = query_frame("SELECT * FROM analytics.diagnostics_national_month ORDER BY month")
    provider = frames["Priorities"]
    statistics = analyse(national, provider)
    (ROOT / "reports/statistical_analysis.json").write_text(json.dumps(statistics, indent=2, default=str), encoding="utf-8")
    chart(national)
    write_findings(national,rtt,ae,diag,provider,statistics,opt)
    payload = {"national": plain(national), "rtt": plain(rtt), "ae": plain(ae), "diagnostics": plain(diag), "providers": plain(provider), "sources": plain(frames["Sources"]), "quality": json.loads((ROOT / "reports/validation/pipeline_summary.json").read_text()), "definitions": json.loads((ROOT / "config/kpi_catalogue.json").read_text())}
    (ROOT / "excel/report_payload.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("SQL results, statistical analysis, figures, executive reports and model exports rebuilt")


if __name__ == "__main__":
    build_all()
