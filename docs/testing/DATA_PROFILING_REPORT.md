# Executed data profiling and quality report

## Coverage and row-count reconciliation

| Dataset | Files / months | Raw rows including controls | Fact rows | Latest reporting month |
|---|---:|---:|---:|---|
| rtt | 24 | 4,399,627 | 236,171 | 2026-08-01 |
| ae | 25 | 4,943 | 4,918 | 2026-09-01 |
| diagnostics | 24 | 3,513,536 | 162,750 | 2026-08-01 |

## Actual findings

- structural_blank_bands_proven_zero: 24 source/month issue records. See the JSON for cell/row counts and handling.
- empty_trailing_csv_columns: 1 source/month issue records. See the JSON for cell/row counts and handling.
- missing_provider_names: 1 source/month issue records. See the JSON for cell/row counts and handling.
- Raw duplicate rows reported by full-row profiling: 0. Duplicate fact grains fail before load.
- Exact historical publication dates remain unverified for 24 source/months; retained source URLs, retrieval timestamps, Last-Modified headers, checksums and publisher revision labels are still captured.

## Executed controls

- Period values inside every source file match the selected reporting month; invalid dates fail.
- 105 RTT and 14 DM01 waiting bands are schema checked; unexpected numeric tokens and fractional/negative counts fail.
- Source all-specialty/test/national totals are reconciled before they are excluded from facts.
- NONC RTT records are excluded using the official publication scope.
- Blanks and suppression remain missing except proven-zero RTT blank bands; unknown-start fields are structurally inapplicable to incomplete pathways.
- Provider identifiers retain their source codes; missing provider names are not invented.
- PostgreSQL primary keys, foreign keys, nonnegative and nested-band constraints enforce warehouse integrity.
- Missing months fail coverage checks. Geographic names are native source attributes; the current official mapping is reference-only.

## Detailed machine-readable evidence

`reports/validation/source_profiles.json` includes row counts, schemas, types, column-level missing counts, provider counts, period values and transformed ranges. Earlier cache profiles may predate the additional transformed-range annotation; warehouse ranges remain queryable. `data_quality_issues.json` records each source/month convention or missing-name issue. The pipeline summary records actual warehouse count checks.
