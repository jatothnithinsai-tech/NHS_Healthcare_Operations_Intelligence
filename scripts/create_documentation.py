"""Create the business contract and KPI catalogue before report generation."""
import json
from src.ingestion.acquire import ROOT


def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


kpis = []


def kpi(name, meaning, numerator, denominator, dataset, grain, filters, caveat, validation):
    kpis.append(dict(id=f'K{len(kpis)+1:02}',name=name,meaning=meaning,numerator=numerator,denominator=denominator,calculation=numerator if denominator=='Not applicable' else f'{numerator} / {denominator}',source=dataset,reporting_grain=grain,time_period='Reporting month; stocks at month end and flows during month as specified',applicable_filters=filters,data_caveats=caveat,validation=validation))

rtt_filter = "Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month"
for name,field,meaning in [
 ('Incomplete RTT pathways','waiting_count','Month-end pathways still waiting; counts pathways, not unique people'),
 ('RTT within 18 weeks','within_18','Incomplete pathways in weekly bands up to and including 18 weeks'),
 ('RTT over 18 weeks','over_18','Incomplete pathways strictly over 18 weeks'),
 ('RTT over 52 weeks','over_52','Incomplete pathways strictly over 52 weeks'),
 ('RTT over 65 weeks','over_65','Incomplete pathways strictly over 65 weeks'),
 ('RTT over 78 weeks','over_78','Incomplete pathways strictly over 78 weeks'),
 ('RTT over 104 weeks','over_104','Incomplete pathways strictly over 104 weeks')]:
    kpi(name,meaning,f'SUM({field})','Not applicable','RTT','Month/provider/specialty',rtt_filter,'Submitted data; excludes missing-trust estimates; geographic parent is a source ICB, not a hospital site','Weekly bands reconcile to Total All and C_999 controls after exclusion of NONC')
kpi('RTT 18-week performance','Share of incomplete pathways waiting within 18 weeks','SUM(within_18)','SUM(waiting_count)','RTT','Month/provider/specialty',rtt_filter,'Weighted ratio; exactly 18 weeks is included; published 92% standard is a benchmark, not a newly inferred target','Python, SQL, Excel and DAX numerator/denominator reconciliation')
kpi('RTT long-wait share','Share strictly over 52 weeks','SUM(over_52)','SUM(waiting_count)','RTT','Month/provider/specialty',rtt_filter,'Volume and rate support different operational questions','Nested-band and denominator controls')
for name,part in [('Admitted completed pathways','Part_1A'),('Non-admitted completed pathways','Part_1B')]:
    kpi(name,'Monthly completed RTT pathways; separate from the month-end incomplete stock','SUM(total_all)','Not applicable','RTT','Month/provider/specialty',f'{part}; exclude C_999 and NONC','Includes completed pathways with unknown start; known-start measures use waiting_count','Total All equals known-start total plus derived unknown-start count')
kpi('Completed pathways with unknown start','Monthly completions where clock start is unknown','SUM(total_all - waiting_count)','Not applicable','RTT','Month/provider/specialty','Part_1A or Part_1B; exclude total specialty and NONC','Unknown-start field is not applicable to incomplete pathways; retain structural NULL there','Difference of published totals checked against populated unknown-start fields')
for name,field,meaning in [('A&E attendances','attendances','All types including separately published booked fields'),('A&E within four hours','within_4','Attendance duration at most four hours from arrival to admission, transfer or discharge'),('A&E over four hours','over_4','Attendance duration over four hours'),('Type 1 attendances','type1_attendances','Major emergency departments, booked and unbooked'),('Emergency admissions','emergency_admissions','Emergency admissions via A&E plus other emergency admissions'),('Emergency admissions via A&E','admissions_via_ae','Admissions via reported A&E departments'),('DTA waits 4–12 hours','dta_4_12','Reported waits from decision to admit to admission'),('DTA waits 12+ hours','dta_12_plus','Reported waits of 12 hours or more from decision to admit')]:
    kpi(name,meaning,f'SUM({field})','Not applicable','A&E','Month/provider','Exclude national TOTAL; provider reporting, not acute-trust attribution footprint','One code can report several sites; DTA waits differ from full attendance duration','Every source numeric column reconciled to national TOTAL')
kpi('A&E four-hour performance','Weighted eligible all-department four-hour performance','SUM(within_4)','SUM(attendances)','A&E','Month/provider/region','All six attendance and all six breach fields; exclude national TOTAL','Do not average provider percentages or blend Type 1 with other department definitions','Within plus over equals attendances, including booked activity')
kpi('Type 1 four-hour performance','Major emergency department four-hour performance','SUM(type1_attendances - type1_over_4)','SUM(type1_attendances)','A&E','Month/provider/region','Type 1 only, booked and unbooked','Zero Type 1 denominator returns missing; no estimate for unreported providers','Type 1 breach counts do not exceed attendance counts')
for name,field,meaning in [('Diagnostic waiting list','waiting_count','Month-end waits for reported diagnostic tests/procedures'),('Diagnostic waits six weeks or more','over_6','Bands beginning at 6 weeks, inclusive'),('Diagnostic waits thirteen weeks or more','over_13','Published 13+ band'),('Diagnostic activity','total_activity','Tests/procedures performed during the month'),('Diagnostic waiting-list activity','waiting_activity','Activity from diagnostic waiting list'),('Diagnostic planned activity','planned_activity','Planned diagnostic activity'),('Diagnostic unscheduled activity','unscheduled_activity','Unscheduled diagnostic activity')]:
    kpi(name,meaning,f'SUM({field})','Not applicable','DM01','Month/provider/test','Exclude test TOTAL; aggregate commissioner records once','Waits and tests are not unique patients; collection definitions may change','14 waiting bands reconcile to Total WL; test categories reconcile to TOTAL; three activity components reconcile')
kpi('Diagnostic six-week rate','Share waiting six weeks or more at month end','SUM(over_6)','SUM(waiting_count)','DM01','Month/provider/test','Selected test/provider/month; exclude TOTAL','Official operational standard is less than 1%; inclusive 6-week boundary differs from RTT strict-over boundaries','Band sums and weighted denominator reconciliation')
kpi('Monthly change','Difference from immediately preceding reporting month','Current month KPI minus prior calendar month KPI','Not applicable','All domains separately','Same domain/provider/service scope','Consecutive months only','Percentage rates use percentage-point difference, not percentage change; missing months remain missing','Join to previous calendar month, not arbitrary prior observation')
kpi('Year-on-year change','Difference versus same calendar month one year earlier','Current KPI minus KPI at month minus 12 months','Prior-year KPI for relative change','All domains separately','Same domain and scope','Identical provider/service filters','Changing coverage and revisions can affect comparisons','Date-based join; no value where prior year absent')
kpi('Latest reporting period','Most recent retained source reporting month','MAX(reporting_month)','Not applicable','Source manifest','Dataset','Dataset-specific date','Never relabel as current live patient data','Internal Period matches catalogue reporting month')
write('config/kpi_catalogue.json',json.dumps(kpis,indent=2,ensure_ascii=False))
lines=['# KPI dictionary','', 'Counts, pathways, attendances, tests and waits are distinct units. Each rate retains its own denominator.','']
for k in kpis:
    lines += [f"## {k['id']} — {k['name']}",'']+[f"- **{key.replace('_',' ').title()}:** {value}" for key,value in k.items() if key not in ('id','name')]+['']
write('docs/kpi_definitions/KPI_DICTIONARY.md','\n'.join(lines))

questions=[
'How have submitted national RTT lists and 18-week rates changed?',
'How does regional A&E four-hour performance vary within each reporting month?',
'Are national rates based on stable reporting-provider coverage?',
'Which domain has the latest reporting month and verified publication date?',
'Which specialties contribute the largest RTT over-52-week volumes?',
'How are incomplete pathways distributed across long-wait bands?',
'Which providers have large RTT lists and low within-18-week rates?',
'Have over-65/78/104-week pathway volumes changed consistently?',
'How do admitted and non-admitted monthly completion volumes differ?',
'Which completed pathways have unknown clock starts?',
'How do A&E attendance volumes and daily averages change by month?',
'How does Type 1 four-hour performance differ from all departments?',
'How do admissions via A&E and other emergency admissions contribute?',
'Where are decision-to-admit waits of twelve hours or more concentrated?',
'Which diagnostic tests account for most six-week-or-more waits?',
'How do diagnostic waiting-list, planned and unscheduled activity differ?',
'Which diagnostic providers have sustained high long-wait rates?',
'How do six-week rates and activity change over comparable months?',
'Which provider codes have three consecutive months of RTT deterioration?',
'How concentrated are RTT long waits among the ten largest contributors?',
'What changes remain visible within a stable-code provider cohort?',
'Which provider comparisons are affected by small denominators or service mix?',
'How do chronological persistence and seasonal-naive baselines compare?',
'What source revisions, missing names and publication-date gaps require review?'
]
write('docs/requirements/BUSINESS_REQUIREMENTS.md', '''# Business Requirements Document

## Business scenario and stakeholders
An NHS operational performance and planning team needs a consistent view of published waiting lists, urgent-care pressure and diagnostic access. Executive directors need a concise position; elective and diagnostic service leads need specialties/test categories; regional planners need valid geography; BI engineers and assurance teams need reproducible lineage and reconciliation.

## Objectives and scope
Produce auditable monthly performance intelligence across RTT, A&E and DM01 using only official aggregate records. Begin at September 2024 and retain the latest available releases, including revisions. Support SQL investigations, descriptive and chronological statistical work, an Excel management workbook and four Power BI pages.

## Exclusions
No clinical diagnosis, patient linkage, unique-patient totals across collections, causal claims, private health records, paid services or unverified operational savings. No silent code merging or assumption that trust, hospital, commissioner and ICB are equivalent.

## Analytical questions
'''+ '\n'.join(f'{i+1}. {q}' for i,q in enumerate(questions))+'''

## Expected dashboards and acceptance
1. Executive performance: separately dated RTT, A&E and diagnostic KPIs and trends.
2. RTT waiting list: bands, specialty/provider comparisons and provider investigation.
3. A&E and diagnostics: attendance, four-hour performance, admissions, test activity and six-week waits.
4. Quality and monitoring: retained releases, source dates, coverage, pipeline status and revision evidence.

Success requires at least 24 consecutive months per domain, genuine immutable source files, reconciliation to source totals, unique fact keys and validated foreign keys, 25+ executed analytical SQL queries, an idempotent rerun, real report formulas and evidence-based findings. Power BI completion requires desktop-open and DAX checks, not just generated files. GitHub publication must use the authorised account and preserve any pre-existing remote content.

## Architecture and controls
Official catalogues → immutable SHA-256 raw files → profiling and strict schema/period checks → grain-aware Parquet → transactional PostgreSQL staging/facts → analytical views → statistics, Excel and Power BI. The manifest, source profiles, audit tables and tests connect each step. Facts are separated by population; aggregate each before any cross-domain join. Public outputs redistribute aggregate official data only, subject to licence verification and attribution.

## Risks and mitigations
Changing schemas fail validation; corrected parsers change the cache version. Revised URLs/content preserve original hashes. Suppression remains NULL; historical blank RTT bands can resolve to zero only if nonnegative observed counts already equal their explicit row total. NONC RTT pathways are excluded in line with official guidance. Provider transfers and new ICB codes are flagged, not merged. Historical publication dates remain unverified until checked against official release evidence. Desktop and authentication limitations are recorded without fabricated completion.

## KPI catalogue and ownership
See the complete KPI dictionary and machine-readable catalogue. BI assurance owns denominator consistency; service leads own interpretation and operational follow-up; the data engineer owns publication checks, immutable provenance and failed refresh handling. Every management recommendation is an investigation supported by calculated evidence, with a proposed owner and monitoring KPI.
''')
write('docs/architecture/ARCHITECTURE.md','''# Architecture and modelling decisions

```mermaid
flowchart LR
  NHS[Official NHS publications] --> C[Link and reporting-month discovery]
  C --> R[Immutable raw files + SHA-256 manifest]
  R --> P[Profile / schema / period / source-total controls]
  P --> S[Parquet cache and PostgreSQL staging]
  S --> F[Three independent fact tables]
  F --> V[Weighted KPI views and 30 SQL analyses]
  V --> ST[Statistics and decision report]
  V --> X[Excel management workbook]
  F --> BI[Power BI import model]
  R --> A[Source and pipeline audit]
```

```mermaid
erDiagram
  DIM_DATE ||--o{ FACT_RTT : month
  DIM_DATE ||--o{ FACT_AE : month
  DIM_DATE ||--o{ FACT_DIAGNOSTICS : month
  DIM_PROVIDER ||--o{ FACT_RTT : provider
  DIM_PROVIDER ||--o{ FACT_AE : provider
  DIM_PROVIDER ||--o{ FACT_DIAGNOSTICS : provider
  DIM_SPECIALTY ||--o{ FACT_RTT : specialty
  DIM_SERVICE ||--o{ FACT_DIAGNOSTICS : test
  DIM_PARENT ||--o{ FACT_RTT : source_parent
  DIM_PARENT ||--o{ FACT_DIAGNOSTICS : source_parent
  DIM_REGION ||--o{ FACT_AE : source_region
  SOURCE_FILE ||--o{ FACT_RTT : checksum
  SOURCE_FILE ||--o{ FACT_AE : checksum
  SOURCE_FILE ||--o{ FACT_DIAGNOSTICS : checksum
```

RTT grain: reporting month/provider/specialty/pathway type. DM01: reporting month/provider/test. A&E: reporting month/provider. Commissioner-level raw rows aggregate once into provider facts. Redundant all-specialty/test/national totals remain controls only. Dates are daily and facts use the first day of the reporting month. Single-direction dimension-to-fact relationships avoid many-to-many inflation.

Provider code is the analytical identifier, not a claim of trust/site equivalence. The provider-name dimension is type 1 with latest source date. Source parent ICB fields stay with the appropriate facts; a current geographic lookup is never backdated. A&E regional analysis uses the source monthly region. Official current A&E mapping is retained for reference only and is not used to manufacture historical regional RTT/DM01 mappings.

Each revised file is immutable and identified by checksum. Changed source month is replaced transactionally after dimension upserts; a successful audit row records parser version and count. Same checksum/version skips the load. Failures roll back the affected month. This favours correctness over unsupported append-only incrementality.
''')
write('docs/data_dictionary/DATA_DICTIONARY.md','''# Data dictionary and source semantics

| Object | Grain / fields | Meaning and control |
|---|---|---|
| raw.source_file | SHA-256; dataset, month, URL, bytes, retrieved_at, publication_date, metadata | One retained version; publication dates can be explicitly unverified |
| audit.loaded_source | dataset/month; SHA-256, parser_version, rows_loaded | Active accepted version; same version skips load |
| audit.pipeline_run | UUID; start/end/status/summary | Actual execution outcomes; interrupted runs are not success |
| dim_date | date | Daily date spine with month and UK financial year |
| dim_provider | provider_code; provider_name, name_as_of | Official source identifier; latest known name; no merger crosswalk inferred |
| dim_parent | parent_code; parent_name | Source provider parent/ICB; no assumption of hospital identity |
| dim_region | region_name | A&E source reporting-region label |
| dim_specialty | specialty_code; specialty_name | RTT treatment function; C_999 excluded from facts |
| dim_service | test_code; test_name | DM01 diagnostic category; TOTAL excluded |
| fact_rtt | month/provider/specialty/pathway | Known-start weekly-band total, Total All, completed unknown-start difference, within18 and over18/52/65/78/104 |
| fact_ae | month/provider | All six attendance/breach fields aggregated, Type1 subsets, via/other/total admissions and DTA waits |
| fact_diagnostics | month/provider/test | Waiting list, 6+/13+ waits, total/waiting-list/planned/unscheduled activity |
| source_sha256 | All fact rows | Foreign key to immutable official source version |

RTT Part_1A=admitted completed; Part_1B=non-admitted completed; Part_2=incomplete. Part_2A is a subset and is excluded from headline totals. Part_3 new periods is outside these three facts. The first weekly band includes zero to one week; exactly 18 weeks belongs to the within18 numerator. Incomplete denominator equals the 105-band sum and Total All. Completed known-start denominator is Total; unknown-start count is Total All minus Total. The raw unknown-start column is structurally inapplicable to incomplete records.

NHS user guidance explicitly excludes Commissioner Org Code NONC from published RTT outputs; this pipeline does too. Raw CSV snapshots include that category, so a naive CSV sum would disagree with publication scope.

Null/suppression conventions: empty, :, -, .., ..., *, x and NA remain missing. RTT blank weekly-band cells are resolved to zero only where nonnegative observed bands already exhaust a published known total; suppression tokens are never changed by that rule. An unknown component makes its aggregate unknown. No missing provider names or organisations are invented.

For DM01, 06 < 07 Weeks through 13+ Weeks form the inclusive six-week-or-more numerator. Three activity types reconcile to Total Activity. For A&E, separately published booked attendance/breach fields must be included in the all-attendance measure. DTA waits start at decision to admit and must not be presented as a full arrival-to-departure wait.
''')
write('docs/runbooks/OPERATIONS.md','''# Local operations and monthly refresh

## Prerequisites and one-command execution
Python 3.11+, PostgreSQL 14+ and a DATABASE_URL for a dedicated `nhs_operations` database. Windows native Excel automation requires installed Excel and an interactive desktop. Desktop Power BI validation requires Power BI Desktop. No paid service is needed.

Create `.venv`, install `requirements.txt`, start the isolated cluster with `scripts/start_postgres.ps1` (defaults to PostgreSQL 18 binaries and loopback port 55473), then run `.venv\\Scripts\\python.exe -m src.pipeline --refresh --reports`. The refresh flag checks official catalogues and revalidates revised files; an unchanged publication is a normal no-op. Without `--refresh`, retained checksums are verified locally. Report construction can be run separately as `python -m src.reporting.build`.

Run native workbook creation with `python -m scripts.build_excel`. Run `python -m scripts.build_powerbi` after exporting data. Power BI's DataRoot parameter must point to the local `powerbi/data` directory. Use `python -m pytest` for unit tests and `NHS_INTEGRATION=1` for authentic-data/database tests. CI uses a temporary PostgreSQL service and official public downloads.

## Refresh stages and failure recovery
1. Discover current official links and compare reporting-month coverage.
2. Download new/revised payloads with timeouts/retries and checksum verification.
3. Parse/version changed files, profile and validate embedded Period and totals.
4. Replace changed dataset/month in one PostgreSQL transaction; retain previous source files.
5. Rebuild SQL results, statistics and management evidence; run regression checks.
6. Rebuild Excel and exported model CSVs. Refresh the Power BI model separately.

If a new schema is rejected, keep the last validated warehouse, inspect the retained file and profile, fix the parser and increment parser_version. A failed file transaction is rolled back. Interrupted runs remain visible in audit; inspect logs before retry. Do not delete raw versions to conceal failures. A missing publisher month is a coverage failure, never a manufactured zero row.

Windows Task Scheduler registration is provided separately. It checks monthly publications; it is not a cloud scheduler. Database updates, workbook regeneration and Power BI model refresh are separate operations. Published monthly observations are not genuine real-time reporting.

## Security
Credentials live only in ignored `.env`; project database listens on 127.0.0.1 and uses SCRAM authentication. Do not export credentials into report metadata, Git or screenshots. Raw files are public aggregates but stay local for repository size; the reproducible manifest is committed. Do not reuse another project's database or kill unrelated desktop processes.
''')
write('docs/business_findings/INTERVIEW_AND_CV.md','''# Interview preparation

- Why separate facts? RTT pathways, A&E attendances and diagnostic waits are different populations and grains. Joining raw facts creates fan-out; aggregate first.
- How are rates calculated? Sum valid numerators and denominators, then divide; never average provider percentages. RTT exactly18 is included, DM01 six weeks is an inclusive breach boundary.
- What was a meaningful source issue? Historical RTT blank bands, structural Total fields, NONC records and a diagnostic link-label year error. Explain the row-total proof used for blank zeros and the embedded-period check.
- How are revisions handled? Immutable checksum files, versioned parser cache and transactional month replacement with load audit. Rerunning accepted files changes no facts.
- What demonstrates SQL depth? CTEs, safe joins, date-based YoY, ROW_NUMBER/RANK/DENSE_RANK, LAG/LEAD, rolling windows, conditional aggregation and percentile outliers across 30 executed analyses. Plans are measured rather than claimed.
- How is provider geography handled? Source ICB and A&E reporting regions are kept distinct. No current lookup is silently applied to historical data. Names are latest-known, codes are not merged.
- What does DAX need? Single-direction star relationships; CALCULATE/FILTER/DIVIDE, explicit incomplete-pathway context, separately dated latest measures, daily date table and valid calendar comparisons.
- Why no decorative hypothesis test? These are serially dependent aggregate reports with changing coverage. Describe observed effects, block-bootstrap uncertainty and chronological naive baseline evaluation; avoid patient-level inference and causal claims.
- How would recommendations be evaluated? Agree operational investigation owners, validate local case mix and monitor the same definitions in future published months. Do not claim savings or implemented improvement from a portfolio analysis.
- What remains limited? Monthly lag, aggregate cohorts, organisation changes, missing-trust estimates outside scope, unverified historical publication dates and any desktop checks still pending in the audit.

## CV bullets — verify against final audit before use
1. Engineered a reproducible Python/PostgreSQL pipeline for 73 official NHS aggregate source files covering 24 RTT and diagnostic months and 25 A&E months, with SHA-256 lineage, source-total reconciliation and revision-aware transactional loading.
2. Implemented 30 advanced PostgreSQL analyses across elective waiting lists, A&E performance and diagnostic access, using window functions, weighted KPIs, percentile comparisons and measured query plans to support operational investigation.
3. Produced an evidence-based executive decision report and reproducible statistical evaluation with chronological forecast baselines; built management-reporting assets whose supported Excel/Power BI validation evidence is recorded in the project audit.
''')
print(f'Created BRD (24 questions), {len(kpis)} KPI definitions and architecture/data/operations/interview documentation')
