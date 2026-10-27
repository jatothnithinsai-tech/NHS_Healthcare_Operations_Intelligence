# NHS Healthcare Executive Decision Report

Generated from PostgreSQL on 2026-10-27T00:16:00.899872+00:00. Independent portfolio analysis; no NHS endorsement.

## Executive summary

RTT (2026-08) contains **7,158,164 submitted incomplete pathways**, with **65.2%** within 18 weeks and **109,936** over 52 weeks. A&E (2026-09) reports **2,444,743 attendances** with **74.4%** completed within four hours. Diagnostics (2026-08) reports **1,833,070 waits**, of which **452,306 (24.7%)** reached six weeks or more.

These are three different operational populations. They must never be added into a unique-patient total. Source coverage includes 24 RTT months, 25 A&E months and 24 diagnostic months starting September 2024.

## Management questions and methodology

The BRD defines 24 questions spanning volume, performance, specialties, providers, regional A&E patterns, trends and data quality. Immutable official files are profiled, reconciled to their embedded total rows, aggregated over commissioners, loaded transactionally and analysed by 30 executable PostgreSQL queries. RTT specialty `C_999` and diagnostic `TOTAL` rows are controls, excluded from facts. A&E national `TOTAL` is also excluded after reconciliation. Rates use summed numerators divided by summed denominators.

## RTT findings

- The incomplete list changed by **+26,479 pathways** from the previous reporting month; 18-week performance changed by **-0.09 percentage points**.
- The ten provider codes with the largest over-52-week volumes account for **36.7%** of submitted long waits. This supports a focused validation and capacity review, adjusted for provider size and specialty mix.
- **Trauma and Orthopaedic Service** has the largest specialty over-52-week volume, **19,741**. Investigate the waiting-band distribution and local plans before setting intervention targets.
- Incomplete pathways are a month-end stock. Admitted/non-admitted completions are monthly flows; they are not interchangeable patient cohorts. `Part_2A` is a subset and is excluded from total pathway counts.

## A&E findings

- Four-hour performance changed by **-0.68 percentage points** month on month.
- Reported emergency admissions total **536,158**; **50,582** waited 12 hours or more from the decision to admit. This is not the same as total time in the emergency department.
- All-department performance includes booked attendance fields. Type 1 performance is reported separately. The source is provider reporting, not the separately attributed acute-trust footprint series introduced in 2026.
- Use regional comparisons from the reporting-period A&E region field; do not impose a current ICB geography on historical RTT/diagnostic records.

## Diagnostic findings

- Six-week-or-more performance changed by **+1.54 percentage points** month on month.
- **NON_OBSTETRIC_ULTRASOUND** has the largest number of six-week-or-more waits: **140,636**. Review test-level throughput and available slots before drawing conclusions about capacity.
- Monthly diagnostic activity is **2,516,963 tests/procedures**, with waiting-list, planned and unscheduled activity separately retained. Activity is not a count of unique patients.

## Statistical findings and uncertainty

The mean RTT list in the last six months differs from the first six months by **-364,215 pathways**. This descriptive effect spans changing provider coverage and reporting revisions. A reproducible moving-block bootstrap is included as exploratory temporal uncertainty, not a patient-level confidence interval.

National month-to-month RTT and diagnostic list changes have Pearson correlation **-0.214** over **23** aligned changes. Shared operational and reporting factors can create association; this does not establish causation.

Chronological one-step baseline evaluation has **12** origins: persistence MAE **48,384 pathways**; seasonal-naive MAE **257,291 pathways**. No future values enter historical predictions. Two annual cycles do not establish stable seasonality. No confirmatory hypothesis test is claimed because independent-observation assumptions are unsupported.

## Action plan

| Priority | Evidence | Investigation | Owner / proposed review | Monitoring KPI |
|---|---|---|---|---|
| 1 | Top ten codes hold 36.7% of over-52-week RTT waits | Validate case mix, code continuity and long-wait plans | Elective operations / next monthly review | Over-52/65/78/104-week pathway counts |
| 2 | 50,582 decision-to-admit waits of 12+ hours | Review bed flow and discharge interfaces with local evidence | Urgent care operations / next monthly review | DTA 12+ count and Type 1 four-hour rate |
| 3 | NON_OBSTETRIC_ULTRASOUND: 140,636 long waits | Review modality-level throughput, demand and slots | Diagnostic service leads / next monthly review | Six-week rate, waiting list and activity |
| 4 | Dataset releases differ by one month | Display release dates and run validation before refresh | BI/data engineering / each publication | Coverage, source checksums and failed validations |

These are proposed management investigations, not proven causes, savings or implemented improvements.

## Provider comparison limitations

Providers differ in scope, service mix and list size. One identifier is not necessarily one hospital. Names are a latest-known dimension; codes are never silently merged. A stable-code cohort reduces entry/exit effects but cannot resolve all service transfers. Small denominators and coverage changes make league tables unreliable. Aggregate operational measures do not establish clinical quality.

## Reporting limitations

The national RTT analysis is the sum of submitted data, excluding published missing-trust estimates. Some historical publication dates require verification in release archives; they are explicitly null rather than inferred from upload directories. Raw source files remain local and excluded from Git. Power BI validation status, desktop evidence and any remaining checks are recorded separately in the final audit. This is published monthly aggregate intelligence, not real-time patient reporting.

## Reproducibility and query performance

The default PostgreSQL plan for a selected provider/long-wait query has median execution time **0.365 ms** over five executions; the sequential-scan comparison is **69.664 ms**. See recorded JSON plans and buffers. Cache and run-order effects prevent general performance claims.

Source attribution: NHS England, RTT waiting times; A&E Attendances and Emergency Admissions; Monthly Diagnostics Waiting Times and Activity. Links and checksums are in `data/reference/source_manifest.json`.
