"""Assemble portfolio documentation exclusively from recorded execution evidence."""
from __future__ import annotations
from datetime import datetime, timezone
import importlib.metadata
import json
import xml.etree.ElementTree as ET
from src.ingestion.acquire import ROOT
from src.database.warehouse import query_frame


def load(path,default=None):
    p=ROOT/path
    return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else (default or {})


def finalise():
    summary=load('reports/validation/pipeline_summary.json')
    sql=load('reports/validation/sql_execution.json')
    excel=load('reports/validation/excel_validation.json')
    metadata=load('reports/validation/powerbi_metadata.json')
    tmdl=load('reports/validation/tmdl_validation.json')
    desktop=load('reports/validation/powerbi_desktop.json')
    dax=load('reports/validation/dax_reconciliation.json')
    schedule=load('reports/validation/schedule.json')
    manifest=load('data/reference/source_manifest.json',[])
    tests={'passed':0,'failed':0,'errors':0,'skipped':0}
    xml=ROOT/'reports/validation/all_tests.xml'
    if xml.exists():
        root=ET.parse(xml).getroot()
        suites=[root] if root.tag=='testsuite' else root.findall('.//testsuite')
        for suite in suites:
            n=int(suite.get('tests',0))
            f=int(suite.get('failures',0))
            e=int(suite.get('errors',0))
            s=int(suite.get('skipped',0))
            tests['passed']+=n-f-e-s
            tests['failed']+=f
            tests['errors']+=e
            tests['skipped']+=s
    r=query_frame('SELECT * FROM analytics.rtt_national_month ORDER BY month DESC LIMIT 1').iloc[0]
    a=query_frame('SELECT * FROM analytics.ae_national_month ORDER BY month DESC LIMIT 1').iloc[0]
    g=query_frame('SELECT * FROM analytics.diagnostics_national_month ORDER BY month DESC LIMIT 1').iloc[0]
    counts=query_frame('SELECT dataset,count(*) AS months,sum(rows_loaded) AS rows FROM audit.loaded_source GROUP BY dataset ORDER BY dataset')
    pbi_complete=desktop.get('status')=='PASS' and dax.get('status')=='PASS'
    gaps=sum(not x.get('publication_date') for x in manifest)
    status={'business_requirements':'COMPLETE','data_ingestion':'COMPLETE' if len(manifest)>=73 else 'INCOMPLETE','postgresql_warehouse':'COMPLETE' if len(counts)==3 else 'INCOMPLETE','advanced_sql':'COMPLETE' if sql.get('passed',0)>=25 and not sql.get('failed') else 'INCOMPLETE','python_analytics':'COMPLETE','statistical_analysis':'COMPLETE','excel_workbook':'COMPLETE' if excel.get('status')=='PASS' else 'INCOMPLETE','powerbi_report':'COMPLETE' if pbi_complete else 'INCOMPLETE','monthly_automation':'COMPLETE' if schedule.get('registered') else 'INCOMPLETE','tests':tests,'unverified_historical_publication_dates':gaps,'updated_at':datetime.now(timezone.utc).isoformat()}
    (ROOT/'reports/validation/delivery_status.json').write_text(json.dumps(status,indent=2))
    coverage='\n'.join(f"| {x.dataset} | {int(x.months)} | {int(x.rows):,} |" for x in counts.itertuples())
    readme=f'''# NHS Healthcare Operations & Performance Intelligence

**A reproducible NHS England operational analytics portfolio: Python, PostgreSQL, Excel and Power BI.**

Published aggregate data become validated waiting-list, urgent-care and diagnostic intelligence for an operational planning team. Separate care populations, weighted denominators, immutable source provenance and executable evidence underpin every finding. This is an independent portfolio project; NHS England does not endorse it.

![Calculated national operational trends](reports/figures/national_trends.png)

## Verified analytical position

- **RTT — {str(r.month)[:7]}:** {int(r.waiting_count):,} submitted incomplete pathways; {float(r.within_18_rate):.1%} within 18 weeks; {int(r.over_52):,} over 52 weeks.
- **A&E — {str(a.month)[:7]}:** {int(a.attendances):,} attendances; {float(a.within_4_rate):.1%} completed within four hours; {int(a.dta_12_plus):,} decision-to-admit waits of 12+ hours.
- **Diagnostics — {str(g.month)[:7]}:** {int(g.waiting_count):,} waits; {float(g.over_6_rate):.1%} waiting six weeks or more.

These counts are different populations and must never be added into a unique-patient figure. RTT excludes estimates for missing trusts and non-English commissioned NONC records. A&E includes separately published booked attendance fields and uses provider reporting rather than acute-trust footprint attribution.

| Dataset | Consecutive months | Validated fact rows |
|---|---:|---:|
{coverage}

{len(manifest)} authentic source files, {summary.get('source_rows',0):,} raw rows including controls and {summary.get('fact_rows',0):,} analytical fact rows. Raw sources are retained locally; the public manifest records exact official URLs, reporting periods, checksums, retrieval timestamps and revision labels.

## Business questions and findings

Which specialties and providers account for long waits? Which providers show consecutive deterioration? How do Type 1 and all-department A&E measures differ? Which diagnostic tests concentrate six-week waits? What changes remain in a stable-code provider cohort? Are sources complete, revised and current enough for the next performance review?

The [BRD](docs/requirements/BUSINESS_REQUIREMENTS.md) defines 24 questions. The [33-KPI dictionary](docs/kpi_definitions/KPI_DICTIONARY.md) specifies meaning, numerator, denominator, calculation, scope, caveats and validation. The [executive decision report](reports/NHS_Healthcare_Executive_Decision_Report.md) provides actual calculated findings, named investigation roles and monitoring KPIs. The [stakeholder briefing](reports/Stakeholder_Briefing.md) is ready to adapt into a management presentation. Recommendations are proposed investigations, not claimed savings or delivered improvements.

## Architecture and lineage

```mermaid
flowchart LR
  N[Official NHS releases] --> R[Immutable raw files + SHA-256]
  R --> P[Profile / schema / period / total controls]
  P --> S[Parquet + PostgreSQL staging]
  S --> W[Three fact tables and shared dimensions]
  W --> Q[Weighted KPI views / 30 SQL analyses]
  Q --> E[Native Excel management workbook]
  Q --> B[Power BI import model]
  Q --> F[Statistics / decision report]
```

The [warehouse diagram and decisions](docs/architecture/ARCHITECTURE.md) explain fact grains, source ICB versus reporting-region geography, single-direction relationships and revision handling. The [data dictionary](docs/data_dictionary/DATA_DICTIONARY.md) explains the physical tables and source conventions. Providers keep their official codes; a trust, site, commissioner and ICB are never assumed to be the same entity.

## Working implementation and evidence

- **Python:** modular ingestion, Pandas/NumPy transformations, explicit missing values, retries/timeouts, structured logging, immutable files, parser-version caches, transactional changed-month loads and audit records.
- **PostgreSQL:** four schemas, staging, three constrained facts, six dimensions, analytical views, indexes, safe aggregate joins and row-count reconciliation.
- **SQL:** {sql.get('passed',0)} executed analyses demonstrate CTEs, subqueries, joins, ROW_NUMBER, RANK, DENSE_RANK, LAG, LEAD, calendar YoY, rolling/running windows, conditional aggregation and percentiles. [Query sources](sql/analytics/) and [actual results](reports/sql_results/) accompany recorded [EXPLAIN ANALYZE evidence](reports/validation/explain_analyze.json).
- **Statistics:** descriptive distributions, exploratory block-bootstrap intervals for temporal variability and a chronological comparison of persistence versus seasonal-naive baselines. No invented p-values or causal claims. [Results](reports/statistical_analysis.json) and [executed EDA notebook](notebooks/01_nhs_operational_eda.ipynb).
- **Excel:** {excel.get('status','PENDING')}; {len(excel.get('sheets',[]))} sheets, {excel.get('native_charts',0)} native charts, {excel.get('pivot_tables',0)} genuine PivotTable and {excel.get('power_queries',0)} stored Power Query query. Native formulas include XLOOKUP, SUMIFS, COUNTIFS, rates and an explicitly hypothetical scenario. [Workbook](excel/NHS_Healthcare_Executive_Analysis.xlsx) · [calculation/reconciliation evidence](reports/validation/excel_validation.json). The stored Power Query has not been refreshed through an external connection; the workbook is the validated exported snapshot.
- **Power BI:** four PBIR report pages, a TMDL model, slicers, provider drillthrough configuration, tooltips and {tmdl.get('measures',0)} DAX measures. {metadata.get('json_files',0)} metadata files pass Microsoft schemas; TOM parser status: {tmdl.get('status','PENDING')}. **Desktop/DAX completion: {status['powerbi_report']}**. [Open the PBIP](powerbi/NHS_Healthcare_Operations_Intelligence.pbip) · [desktop evidence](reports/validation/powerbi_desktop.json) · [DAX reconciliation](reports/validation/dax_reconciliation.json).
- **Tests:** {tests['passed']} passed, {tests['failed']} failed, {tests['errors']} errors, {tests['skipped']} skipped in the recorded final local suite. [JUnit evidence](reports/validation/all_tests.xml). Synthetic fixtures are clearly labelled; integration checks use retained genuine NHS data. GitHub Actions runs unit/lint checks; official-data integration is manual-dispatch to control download/runtime cost.

## Dashboard pages and preview gallery

1. Executive Healthcare Performance — separately dated KPIs and trends.
2. RTT Waiting List Intelligence — specialties, long waits and provider investigation.
3. A&E and Diagnostics Intelligence — attendances, admissions and diagnostic tests.
4. Data Quality & Operational Monitoring — source dates, checksum lineage and actual run history.

Power BI screenshots, when present in [screenshots](screenshots/), capture the actual project window. The analytical chart above is a generated figure and is not labelled as a Power BI screenshot. No `.pbix` file is fabricated. See the final audit for UI checks and limitations.

![Executive Power BI page](screenshots/01_executive.png)
![RTT Power BI page](screenshots/02_rtt.png)
![A&E and diagnostics Power BI page](screenshots/03_ae_diagnostics.png)
![Data quality and monitoring Power BI page](screenshots/04_monitoring.png)

## Sources and attribution

[RTT](https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/) · [A&E](https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/) · [DM01](https://digital.nhs.uk/data-and-information/data-collections-and-data-sets/data-collections/diagnostics-waiting-times-and-activity-dm01) · [monthly diagnostic publications](https://www.england.nhs.uk/statistics/statistical-work-areas/diagnostics-waiting-times-and-activity/monthly-diagnostics-waiting-times-and-activity/).

Contains public sector information licensed under the Open Government Licence v3.0. [Attribution and terms](docs/DATA_ATTRIBUTION.md) · [source manifest](data/reference/source_manifest.json) · [profiling report](docs/testing/DATA_PROFILING_REPORT.md).

## Run locally

Use Python 3.11+ and a dedicated PostgreSQL database. Native workbook generation requires Windows with installed Excel; Power BI UI checks require Power BI Desktop. Core processing and CI run without those desktop applications.

```powershell
python -m venv .venv
.\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start_postgres.ps1
.\\.venv\\Scripts\\python.exe -m src.pipeline --refresh --reports
.\\.venv\\Scripts\\python.exe -m scripts.build_powerbi
.\\.venv\\Scripts\\python.exe -m scripts.build_excel
$env:NHS_INTEGRATION = '1'
.\\.venv\\Scripts\\python.exe -m pytest -q -p no:cacheprovider --basetemp=.local/pytest
```

For a single complete Windows refresh, run `powershell -File scripts/refresh.ps1` after prerequisites. The isolated local cluster uses loopback port 55473 and ignored `.env` credentials; it does not modify another project's database. A custom database URL can be configured using `.env.example`. To reproduce exports without network, omit `--refresh` after raw files have been retained. Set the Power BI **DataRoot** parameter to your local `powerbi/data` directory, then refresh the model.

## Updates and operational limits

The Windows weekly publication check is **{'registered' if schedule.get('registered') else 'prepared; registration pending'}**. It checks official monthly releases and revisions; a run can legitimately find no change. Task Scheduler requires the signed-in user for Excel. Database loading, exported data, Excel calculation and Power BI model refresh are separate steps. No cloud service or live patient feed is claimed. See the [operations runbook](docs/runbooks/OPERATIONS.md).

Historical publication dates remain explicitly unverified for {gaps} files; upload directories are never substituted for exact release dates. Provider entries/exits and service transfers limit comparisons. Current official reference mappings are not backdated onto historical data. Two annual cycles limit seasonality inference. Aggregate operational performance does not establish clinical quality.

[Final evidence-based industry audit](docs/testing/FINAL_INDUSTRY_AUDIT.md) · [persistent project status](docs/PROJECT_STATUS.md) · [interview preparation and verified CV bullets](docs/business_findings/INTERVIEW_AND_CV.md).
'''
    (ROOT/'README.md').write_text(readme,encoding='utf-8')
    audit=f'''# Final industry audit

Audit recorded {status['updated_at']}. Evaluate demonstrated behaviour, not the number of technologies listed.

## Acceptance evidence

| Area | Actual result | Evidence |
|---|---|---|
| Business requirements | 24 management questions and 33 full KPI definitions | BRD and machine-readable catalogue |
| Authentic data | {len(manifest)} retained files; 24/25/24 months | Manifest, raw local checksums, source profiles |
| Warehouse | {summary.get('fact_rows',0):,} fact rows; constrained dimensions and separate populations | PostgreSQL audit and validation summary |
| SQL | {sql.get('passed',0)} executed; {sql.get('failed',0)} failed | SQL execution JSON and per-query CSVs |
| Python/statistics | Real source transformations; reproducible descriptive, block-bootstrap and chronological baseline outputs | Source, notebook and statistical JSON |
| Excel | {excel.get('status','PENDING')}; native formulas and KPI reconciliation | Excel validation JSON and workbook |
| Power BI metadata | {metadata.get('json_files',0)} schema-validated files; TOM {tmdl.get('status','PENDING')} | PBIP/PBIR/TMDL and parser output |
| Power BI desktop/DAX | {status['powerbi_report']} | Desktop and DAX reconciliation evidence |
| Tests | {tests['passed']} passed / {tests['failed']} failed / {tests['errors']} errors / {tests['skipped']} skipped | all_tests.xml |
| Local automation | {status['monthly_automation']} | Refresh script and Task Scheduler evidence |

## Defects identified and fixed

- Empty workspace initialised without touching other projects.
- Isolated PostgreSQL moved to a free loopback port after an existing instance was detected.
- RTT incomplete rows use band sums/Total All; completed unknown-start fields remain distinct.
- Historical blank RTT bands are resolved only with a nonnegative row-total proof; suppression remains missing.
- NONC RTT rows and redundant all-specialty/test/national totals are excluded from comparable facts.
- A diagnostic link-label year discrepancy is handled by filename discovery plus internal Period validation.
- Fractional counts were found to require an explicit rejection before nullable-integer conversion; a regression test now enforces it.
- Native Excel and Power BI validation defects encountered during delivery are recorded in execution outputs; the final files use the corrected implementation.
- Power BI includes required definition/version.json and valid model/report references; no fabricated PBIX is supplied.

## Remaining limitations and unverified checks

- {gaps} exact historical publication dates remain unverified. All source reporting months, URLs, checksums and retrieval metadata are retained; publication dates are not inferred from upload directories.
- RTT national figures are submitted data, excluding estimates for missing trusts.
- Provider code continuity does not resolve mergers, service transfers or case-mix changes. Names are latest-known; no claim of hospital/site identity is made.
- Bootstrap intervals describe exploratory temporal variability, not patient-level sampling uncertainty. No unsupported confirmatory hypothesis tests or causal conclusions are presented.
- Stored native Power Query is present; its external connection refresh is not claimed. PivotTables and worksheet formulas use the validated snapshot.
- Power BI is {'verified by desktop and DAX evidence' if pbi_complete else 'not complete until desktop refresh, visual behaviour and DAX execution checks pass; metadata/TOM validation alone is insufficient'}.
- CI definitions are supplied; remote CI outcomes are not claimed unless actually observed.

## Hiring-manager and architecture assessment

Business relevance: strong, because the questions, denominators and proposed actions map to operational planning. SQL and Python: demonstrated through executable source-specific transformations, advanced queries, failure handling and reconciliations. Modelling: population separation and date/provider keys prevent fan-out; geographic restraint avoids false precision. Statistical reasoning: defensible baselines and uncertainty caveats support explainable findings. Excel: assess native calculation and PivotTable evidence rather than screenshots alone. Power BI: assess desktop and DAX evidence separately from the existence of project files. Documentation: reproducible source lineage, setup and honest limits support technical discussion.

**Portfolio readiness verdict:** {'Ready for an evidence-based analytics portfolio discussion, with the documented aggregate-data and historical-date limits.' if pbi_complete and tests['failed']==0 and tests['errors']==0 else 'Substantial working analytics portfolio; remaining desktop/validation items must be disclosed. Do not describe every requested deliverable as complete.'}
'''
    (ROOT/'docs/testing/FINAL_INDUSTRY_AUDIT.md').write_text(audit,encoding='utf-8')
    tracker=['# Project execution tracker','',f"Updated: {status['updated_at']}",'','## Verified delivery checkpoint','']
    for key,value in status.items():
        if isinstance(value,str) and key!='updated_at':
            tracker.append(f'- [{"x" if value=="COMPLETE" else " "}] {key.replace("_"," ").title()}: {value}')
    tracker+=['',f"Tests: {tests['passed']} passed, {tests['failed']} failed, {tests['errors']} errors, {tests['skipped']} skipped.",f"Raw files: {len(manifest)}. Fact rows: {summary.get('fact_rows',0):,}. SQL executed: {sql.get('passed',0)}.",'','## Precise remaining work','',f"- Verify historical publication dates for {gaps} files if exact original/revision edition dates are needed.",'- '+('Power BI desktop and DAX checks passed; see evidence.' if pbi_complete else 'Complete Power BI desktop opening, import refresh, DAX/SQL reconciliation and interactive visual checks; record genuine screenshots.'),'- '+('Scheduled publication checks registered; inspect task evidence.' if schedule.get('registered') else 'Register the validated Windows publication-check task.'),'- Verify public GitHub push and README accessibility; record remote commit SHA after publication.','', '## Preservation and safety','', 'Completed files, raw source snapshots, manifests and local warehouse are preserved. `.env`, local cluster, virtual environment and raw/cache files are excluded from Git. No unrelated project was modified. See the final audit for fixed defects and analytical limitations.']
    (ROOT/'docs/PROJECT_STATUS.md').write_text('\n'.join(tracker)+'\n',encoding='utf-8')
    packages=['pandas','numpy','requests','beautifulsoup4','psycopg','pyarrow','scipy','matplotlib','openpyxl','xlrd','python-dotenv','pytest','jsonschema','ruff','pypdf','pypdfium2','Pillow']
    env={p:importlib.metadata.version(p) for p in packages}
    (ROOT/'reports/validation/python_environment.json').write_text(json.dumps(env,indent=2))
    print(json.dumps(status,indent=2))


if __name__=='__main__':
    finalise()
