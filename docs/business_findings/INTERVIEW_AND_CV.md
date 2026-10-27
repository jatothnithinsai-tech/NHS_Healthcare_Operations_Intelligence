# Interview preparation

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
