import json
from collections import Counter
from src.ingestion.acquire import ROOT

profiles=json.loads((ROOT/'reports/validation/source_profiles.json').read_text())
issues=json.loads((ROOT/'reports/validation/data_quality_issues.json').read_text())
manifest=json.loads((ROOT/'data/reference/source_manifest.json').read_text())
lines=['# Executed data profiling and quality report','','## Coverage and row-count reconciliation','','| Dataset | Files / months | Raw rows including controls | Fact rows | Latest reporting month |','|---|---:|---:|---:|---|']
for domain in ['rtt','ae','diagnostics']:
    rows=[p for p in profiles if p['dataset']==domain]
    lines.append(f"| {domain} | {len(rows)} | {sum(p['rows'] for p in rows):,} | {sum(p['transformed_rows'] for p in rows):,} | {max(p['reporting_month'] for p in rows)} |")
lines+=['','## Actual findings','']
for key,count in Counter(x['issue'] for x in issues).items():
    lines.append(f'- {key}: {count} source/month issue records. See the JSON for cell/row counts and handling.')
lines += [f"- Raw duplicate rows reported by full-row profiling: {sum(p['duplicate_rows'] for p in profiles):,}. Duplicate fact grains fail before load.",f"- Exact historical publication dates remain unverified for {sum(not s.get('publication_date') for s in manifest)} source/months; retained source URLs, retrieval timestamps, Last-Modified headers, checksums and publisher revision labels are still captured.",'','## Executed controls','','- Period values inside every source file match the selected reporting month; invalid dates fail.','- 105 RTT and 14 DM01 waiting bands are schema checked; unexpected numeric tokens and fractional/negative counts fail.','- Source all-specialty/test/national totals are reconciled before they are excluded from facts.','- NONC RTT records are excluded using the official publication scope.','- Blanks and suppression remain missing except proven-zero RTT blank bands; unknown-start fields are structurally inapplicable to incomplete pathways.','- Provider identifiers retain their source codes; missing provider names are not invented.','- PostgreSQL primary keys, foreign keys, nonnegative and nested-band constraints enforce warehouse integrity.','- Missing months fail coverage checks. Geographic names are native source attributes; the current official mapping is reference-only.','','## Detailed machine-readable evidence','','`reports/validation/source_profiles.json` includes row counts, schemas, types, column-level missing counts, provider counts, period values and transformed ranges. Earlier cache profiles may predate the additional transformed-range annotation; warehouse ranges remain queryable. `data_quality_issues.json` records each source/month convention or missing-name issue. The pipeline summary records actual warehouse count checks.','']
(ROOT/'docs/testing').mkdir(parents=True,exist_ok=True)
(ROOT/'docs/testing/DATA_PROFILING_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
print('Data profiling and quality report generated')
