# Final industry audit

Audit recorded 2026-10-27T00:41:57.393829+00:00. Evaluate demonstrated behaviour, not the number of technologies listed.

## Acceptance evidence

| Area | Actual result | Evidence |
|---|---|---|
| Business requirements | 24 management questions and 33 full KPI definitions | BRD and machine-readable catalogue |
| Authentic data | 73 retained files; 24/25/24 months | Manifest, raw local checksums, source profiles |
| Warehouse | 403,839 fact rows; constrained dimensions and separate populations | PostgreSQL audit and validation summary |
| SQL | 30 executed; 0 failed | SQL execution JSON and per-query CSVs |
| Python/statistics | Real source transformations; reproducible descriptive, block-bootstrap and chronological baseline outputs | Source, notebook and statistical JSON |
| Excel | PASS; native formulas and KPI reconciliation | Excel validation JSON and workbook |
| Power BI metadata | 59 schema-validated files; TOM PASS | PBIP/PBIR/TMDL and parser output |
| Power BI desktop/DAX | COMPLETE | Desktop and DAX reconciliation evidence |
| Tests | 47 passed / 0 failed / 0 errors / 0 skipped | all_tests.xml |
| Local automation | COMPLETE | Refresh script and Task Scheduler evidence |

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

- 24 exact historical publication dates remain unverified. All source reporting months, URLs, checksums and retrieval metadata are retained; publication dates are not inferred from upload directories.
- RTT national figures are submitted data, excluding estimates for missing trusts.
- Provider code continuity does not resolve mergers, service transfers or case-mix changes. Names are latest-known; no claim of hospital/site identity is made.
- Bootstrap intervals describe exploratory temporal variability, not patient-level sampling uncertainty. No unsupported confirmatory hypothesis tests or causal conclusions are presented.
- Stored native Power Query is present; its external connection refresh is not claimed. PivotTables and worksheet formulas use the validated snapshot.
- Power BI is verified by desktop and DAX evidence.
- CI definitions are supplied; remote CI outcomes are not claimed unless actually observed.

## Hiring-manager and architecture assessment

The authorised repository was created as public at https://github.com/jatothnithinsai-tech/NHS_Healthcare_Operations_Intelligence. Initial content commit `ca202b01095847db77ca1a67dd4fad426b48b012` was verified against the remote, its README returned HTTP 200 and the required public artifact paths were verified. See `reports/validation/github_publication.json`. The committed PBIR source deliberately uses public schema versions successfully opened by installed Desktop; see `POWER_BI_VALIDATION.md` for the newer Desktop Save format's unavailable schema endpoint.

Business relevance: strong, because the questions, denominators and proposed actions map to operational planning. SQL and Python: demonstrated through executable source-specific transformations, advanced queries, failure handling and reconciliations. Modelling: population separation and date/provider keys prevent fan-out; geographic restraint avoids false precision. Statistical reasoning: defensible baselines and uncertainty caveats support explainable findings. Excel: assess native calculation and PivotTable evidence rather than screenshots alone. Power BI: assess desktop and DAX evidence separately from the existence of project files. Documentation: reproducible source lineage, setup and honest limits support technical discussion.

**Portfolio readiness verdict:** Ready for an evidence-based analytics portfolio discussion, with the documented aggregate-data and historical-date limits.
