# Business Requirements Document

## Business scenario and stakeholders
An NHS operational performance and planning team needs a consistent view of published waiting lists, urgent-care pressure and diagnostic access. Executive directors need a concise position; elective and diagnostic service leads need specialties/test categories; regional planners need valid geography; BI engineers and assurance teams need reproducible lineage and reconciliation.

## Objectives and scope
Produce auditable monthly performance intelligence across RTT, A&E and DM01 using only official aggregate records. Begin at September 2024 and retain the latest available releases, including revisions. Support SQL investigations, descriptive and chronological statistical work, an Excel management workbook and four Power BI pages.

## Exclusions
No clinical diagnosis, patient linkage, unique-patient totals across collections, causal claims, private health records, paid services or unverified operational savings. No silent code merging or assumption that trust, hospital, commissioner and ICB are equivalent.

## Analytical questions
1. How have submitted national RTT lists and 18-week rates changed?
2. How does regional A&E four-hour performance vary within each reporting month?
3. Are national rates based on stable reporting-provider coverage?
4. Which domain has the latest reporting month and verified publication date?
5. Which specialties contribute the largest RTT over-52-week volumes?
6. How are incomplete pathways distributed across long-wait bands?
7. Which providers have large RTT lists and low within-18-week rates?
8. Have over-65/78/104-week pathway volumes changed consistently?
9. How do admitted and non-admitted monthly completion volumes differ?
10. Which completed pathways have unknown clock starts?
11. How do A&E attendance volumes and daily averages change by month?
12. How does Type 1 four-hour performance differ from all departments?
13. How do admissions via A&E and other emergency admissions contribute?
14. Where are decision-to-admit waits of twelve hours or more concentrated?
15. Which diagnostic tests account for most six-week-or-more waits?
16. How do diagnostic waiting-list, planned and unscheduled activity differ?
17. Which diagnostic providers have sustained high long-wait rates?
18. How do six-week rates and activity change over comparable months?
19. Which provider codes have three consecutive months of RTT deterioration?
20. How concentrated are RTT long waits among the ten largest contributors?
21. What changes remain visible within a stable-code provider cohort?
22. Which provider comparisons are affected by small denominators or service mix?
23. How do chronological persistence and seasonal-naive baselines compare?
24. What source revisions, missing names and publication-date gaps require review?

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
