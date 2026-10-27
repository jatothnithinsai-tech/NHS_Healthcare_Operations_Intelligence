# Data dictionary and source semantics

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
