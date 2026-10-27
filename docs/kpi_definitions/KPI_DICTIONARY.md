# KPI dictionary

Counts, pathways, attendances, tests and waits are distinct units. Each rate retains its own denominator.

## K01 — Incomplete RTT pathways

- **Meaning:** Month-end pathways still waiting; counts pathways, not unique people
- **Numerator:** SUM(waiting_count)
- **Denominator:** Not applicable
- **Calculation:** SUM(waiting_count)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Submitted data; excludes missing-trust estimates; geographic parent is a source ICB, not a hospital site
- **Validation:** Weekly bands reconcile to Total All and C_999 controls after exclusion of NONC

## K02 — RTT within 18 weeks

- **Meaning:** Incomplete pathways in weekly bands up to and including 18 weeks
- **Numerator:** SUM(within_18)
- **Denominator:** Not applicable
- **Calculation:** SUM(within_18)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Submitted data; excludes missing-trust estimates; geographic parent is a source ICB, not a hospital site
- **Validation:** Weekly bands reconcile to Total All and C_999 controls after exclusion of NONC

## K03 — RTT over 18 weeks

- **Meaning:** Incomplete pathways strictly over 18 weeks
- **Numerator:** SUM(over_18)
- **Denominator:** Not applicable
- **Calculation:** SUM(over_18)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Submitted data; excludes missing-trust estimates; geographic parent is a source ICB, not a hospital site
- **Validation:** Weekly bands reconcile to Total All and C_999 controls after exclusion of NONC

## K04 — RTT over 52 weeks

- **Meaning:** Incomplete pathways strictly over 52 weeks
- **Numerator:** SUM(over_52)
- **Denominator:** Not applicable
- **Calculation:** SUM(over_52)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Submitted data; excludes missing-trust estimates; geographic parent is a source ICB, not a hospital site
- **Validation:** Weekly bands reconcile to Total All and C_999 controls after exclusion of NONC

## K05 — RTT over 65 weeks

- **Meaning:** Incomplete pathways strictly over 65 weeks
- **Numerator:** SUM(over_65)
- **Denominator:** Not applicable
- **Calculation:** SUM(over_65)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Submitted data; excludes missing-trust estimates; geographic parent is a source ICB, not a hospital site
- **Validation:** Weekly bands reconcile to Total All and C_999 controls after exclusion of NONC

## K06 — RTT over 78 weeks

- **Meaning:** Incomplete pathways strictly over 78 weeks
- **Numerator:** SUM(over_78)
- **Denominator:** Not applicable
- **Calculation:** SUM(over_78)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Submitted data; excludes missing-trust estimates; geographic parent is a source ICB, not a hospital site
- **Validation:** Weekly bands reconcile to Total All and C_999 controls after exclusion of NONC

## K07 — RTT over 104 weeks

- **Meaning:** Incomplete pathways strictly over 104 weeks
- **Numerator:** SUM(over_104)
- **Denominator:** Not applicable
- **Calculation:** SUM(over_104)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Submitted data; excludes missing-trust estimates; geographic parent is a source ICB, not a hospital site
- **Validation:** Weekly bands reconcile to Total All and C_999 controls after exclusion of NONC

## K08 — RTT 18-week performance

- **Meaning:** Share of incomplete pathways waiting within 18 weeks
- **Numerator:** SUM(within_18)
- **Denominator:** SUM(waiting_count)
- **Calculation:** SUM(within_18) / SUM(waiting_count)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Weighted ratio; exactly 18 weeks is included; published 92% standard is a benchmark, not a newly inferred target
- **Validation:** Python, SQL, Excel and DAX numerator/denominator reconciliation

## K09 — RTT long-wait share

- **Meaning:** Share strictly over 52 weeks
- **Numerator:** SUM(over_52)
- **Denominator:** SUM(waiting_count)
- **Calculation:** SUM(over_52) / SUM(waiting_count)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_2; exclude C_999, Part_2A and NONC; selected provider/specialty/reporting month
- **Data Caveats:** Volume and rate support different operational questions
- **Validation:** Nested-band and denominator controls

## K10 — Admitted completed pathways

- **Meaning:** Monthly completed RTT pathways; separate from the month-end incomplete stock
- **Numerator:** SUM(total_all)
- **Denominator:** Not applicable
- **Calculation:** SUM(total_all)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_1A; exclude C_999 and NONC
- **Data Caveats:** Includes completed pathways with unknown start; known-start measures use waiting_count
- **Validation:** Total All equals known-start total plus derived unknown-start count

## K11 — Non-admitted completed pathways

- **Meaning:** Monthly completed RTT pathways; separate from the month-end incomplete stock
- **Numerator:** SUM(total_all)
- **Denominator:** Not applicable
- **Calculation:** SUM(total_all)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_1B; exclude C_999 and NONC
- **Data Caveats:** Includes completed pathways with unknown start; known-start measures use waiting_count
- **Validation:** Total All equals known-start total plus derived unknown-start count

## K12 — Completed pathways with unknown start

- **Meaning:** Monthly completions where clock start is unknown
- **Numerator:** SUM(total_all - waiting_count)
- **Denominator:** Not applicable
- **Calculation:** SUM(total_all - waiting_count)
- **Source:** RTT
- **Reporting Grain:** Month/provider/specialty
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Part_1A or Part_1B; exclude total specialty and NONC
- **Data Caveats:** Unknown-start field is not applicable to incomplete pathways; retain structural NULL there
- **Validation:** Difference of published totals checked against populated unknown-start fields

## K13 — A&E attendances

- **Meaning:** All types including separately published booked fields
- **Numerator:** SUM(attendances)
- **Denominator:** Not applicable
- **Calculation:** SUM(attendances)
- **Source:** A&E
- **Reporting Grain:** Month/provider
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude national TOTAL; provider reporting, not acute-trust attribution footprint
- **Data Caveats:** One code can report several sites; DTA waits differ from full attendance duration
- **Validation:** Every source numeric column reconciled to national TOTAL

## K14 — A&E within four hours

- **Meaning:** Attendance duration at most four hours from arrival to admission, transfer or discharge
- **Numerator:** SUM(within_4)
- **Denominator:** Not applicable
- **Calculation:** SUM(within_4)
- **Source:** A&E
- **Reporting Grain:** Month/provider
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude national TOTAL; provider reporting, not acute-trust attribution footprint
- **Data Caveats:** One code can report several sites; DTA waits differ from full attendance duration
- **Validation:** Every source numeric column reconciled to national TOTAL

## K15 — A&E over four hours

- **Meaning:** Attendance duration over four hours
- **Numerator:** SUM(over_4)
- **Denominator:** Not applicable
- **Calculation:** SUM(over_4)
- **Source:** A&E
- **Reporting Grain:** Month/provider
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude national TOTAL; provider reporting, not acute-trust attribution footprint
- **Data Caveats:** One code can report several sites; DTA waits differ from full attendance duration
- **Validation:** Every source numeric column reconciled to national TOTAL

## K16 — Type 1 attendances

- **Meaning:** Major emergency departments, booked and unbooked
- **Numerator:** SUM(type1_attendances)
- **Denominator:** Not applicable
- **Calculation:** SUM(type1_attendances)
- **Source:** A&E
- **Reporting Grain:** Month/provider
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude national TOTAL; provider reporting, not acute-trust attribution footprint
- **Data Caveats:** One code can report several sites; DTA waits differ from full attendance duration
- **Validation:** Every source numeric column reconciled to national TOTAL

## K17 — Emergency admissions

- **Meaning:** Emergency admissions via A&E plus other emergency admissions
- **Numerator:** SUM(emergency_admissions)
- **Denominator:** Not applicable
- **Calculation:** SUM(emergency_admissions)
- **Source:** A&E
- **Reporting Grain:** Month/provider
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude national TOTAL; provider reporting, not acute-trust attribution footprint
- **Data Caveats:** One code can report several sites; DTA waits differ from full attendance duration
- **Validation:** Every source numeric column reconciled to national TOTAL

## K18 — Emergency admissions via A&E

- **Meaning:** Admissions via reported A&E departments
- **Numerator:** SUM(admissions_via_ae)
- **Denominator:** Not applicable
- **Calculation:** SUM(admissions_via_ae)
- **Source:** A&E
- **Reporting Grain:** Month/provider
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude national TOTAL; provider reporting, not acute-trust attribution footprint
- **Data Caveats:** One code can report several sites; DTA waits differ from full attendance duration
- **Validation:** Every source numeric column reconciled to national TOTAL

## K19 — DTA waits 4–12 hours

- **Meaning:** Reported waits from decision to admit to admission
- **Numerator:** SUM(dta_4_12)
- **Denominator:** Not applicable
- **Calculation:** SUM(dta_4_12)
- **Source:** A&E
- **Reporting Grain:** Month/provider
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude national TOTAL; provider reporting, not acute-trust attribution footprint
- **Data Caveats:** One code can report several sites; DTA waits differ from full attendance duration
- **Validation:** Every source numeric column reconciled to national TOTAL

## K20 — DTA waits 12+ hours

- **Meaning:** Reported waits of 12 hours or more from decision to admit
- **Numerator:** SUM(dta_12_plus)
- **Denominator:** Not applicable
- **Calculation:** SUM(dta_12_plus)
- **Source:** A&E
- **Reporting Grain:** Month/provider
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude national TOTAL; provider reporting, not acute-trust attribution footprint
- **Data Caveats:** One code can report several sites; DTA waits differ from full attendance duration
- **Validation:** Every source numeric column reconciled to national TOTAL

## K21 — A&E four-hour performance

- **Meaning:** Weighted eligible all-department four-hour performance
- **Numerator:** SUM(within_4)
- **Denominator:** SUM(attendances)
- **Calculation:** SUM(within_4) / SUM(attendances)
- **Source:** A&E
- **Reporting Grain:** Month/provider/region
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** All six attendance and all six breach fields; exclude national TOTAL
- **Data Caveats:** Do not average provider percentages or blend Type 1 with other department definitions
- **Validation:** Within plus over equals attendances, including booked activity

## K22 — Type 1 four-hour performance

- **Meaning:** Major emergency department four-hour performance
- **Numerator:** SUM(type1_attendances - type1_over_4)
- **Denominator:** SUM(type1_attendances)
- **Calculation:** SUM(type1_attendances - type1_over_4) / SUM(type1_attendances)
- **Source:** A&E
- **Reporting Grain:** Month/provider/region
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Type 1 only, booked and unbooked
- **Data Caveats:** Zero Type 1 denominator returns missing; no estimate for unreported providers
- **Validation:** Type 1 breach counts do not exceed attendance counts

## K23 — Diagnostic waiting list

- **Meaning:** Month-end waits for reported diagnostic tests/procedures
- **Numerator:** SUM(waiting_count)
- **Denominator:** Not applicable
- **Calculation:** SUM(waiting_count)
- **Source:** DM01
- **Reporting Grain:** Month/provider/test
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude test TOTAL; aggregate commissioner records once
- **Data Caveats:** Waits and tests are not unique patients; collection definitions may change
- **Validation:** 14 waiting bands reconcile to Total WL; test categories reconcile to TOTAL; three activity components reconcile

## K24 — Diagnostic waits six weeks or more

- **Meaning:** Bands beginning at 6 weeks, inclusive
- **Numerator:** SUM(over_6)
- **Denominator:** Not applicable
- **Calculation:** SUM(over_6)
- **Source:** DM01
- **Reporting Grain:** Month/provider/test
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude test TOTAL; aggregate commissioner records once
- **Data Caveats:** Waits and tests are not unique patients; collection definitions may change
- **Validation:** 14 waiting bands reconcile to Total WL; test categories reconcile to TOTAL; three activity components reconcile

## K25 — Diagnostic waits thirteen weeks or more

- **Meaning:** Published 13+ band
- **Numerator:** SUM(over_13)
- **Denominator:** Not applicable
- **Calculation:** SUM(over_13)
- **Source:** DM01
- **Reporting Grain:** Month/provider/test
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude test TOTAL; aggregate commissioner records once
- **Data Caveats:** Waits and tests are not unique patients; collection definitions may change
- **Validation:** 14 waiting bands reconcile to Total WL; test categories reconcile to TOTAL; three activity components reconcile

## K26 — Diagnostic activity

- **Meaning:** Tests/procedures performed during the month
- **Numerator:** SUM(total_activity)
- **Denominator:** Not applicable
- **Calculation:** SUM(total_activity)
- **Source:** DM01
- **Reporting Grain:** Month/provider/test
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude test TOTAL; aggregate commissioner records once
- **Data Caveats:** Waits and tests are not unique patients; collection definitions may change
- **Validation:** 14 waiting bands reconcile to Total WL; test categories reconcile to TOTAL; three activity components reconcile

## K27 — Diagnostic waiting-list activity

- **Meaning:** Activity from diagnostic waiting list
- **Numerator:** SUM(waiting_activity)
- **Denominator:** Not applicable
- **Calculation:** SUM(waiting_activity)
- **Source:** DM01
- **Reporting Grain:** Month/provider/test
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude test TOTAL; aggregate commissioner records once
- **Data Caveats:** Waits and tests are not unique patients; collection definitions may change
- **Validation:** 14 waiting bands reconcile to Total WL; test categories reconcile to TOTAL; three activity components reconcile

## K28 — Diagnostic planned activity

- **Meaning:** Planned diagnostic activity
- **Numerator:** SUM(planned_activity)
- **Denominator:** Not applicable
- **Calculation:** SUM(planned_activity)
- **Source:** DM01
- **Reporting Grain:** Month/provider/test
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude test TOTAL; aggregate commissioner records once
- **Data Caveats:** Waits and tests are not unique patients; collection definitions may change
- **Validation:** 14 waiting bands reconcile to Total WL; test categories reconcile to TOTAL; three activity components reconcile

## K29 — Diagnostic unscheduled activity

- **Meaning:** Unscheduled diagnostic activity
- **Numerator:** SUM(unscheduled_activity)
- **Denominator:** Not applicable
- **Calculation:** SUM(unscheduled_activity)
- **Source:** DM01
- **Reporting Grain:** Month/provider/test
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Exclude test TOTAL; aggregate commissioner records once
- **Data Caveats:** Waits and tests are not unique patients; collection definitions may change
- **Validation:** 14 waiting bands reconcile to Total WL; test categories reconcile to TOTAL; three activity components reconcile

## K30 — Diagnostic six-week rate

- **Meaning:** Share waiting six weeks or more at month end
- **Numerator:** SUM(over_6)
- **Denominator:** SUM(waiting_count)
- **Calculation:** SUM(over_6) / SUM(waiting_count)
- **Source:** DM01
- **Reporting Grain:** Month/provider/test
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Selected test/provider/month; exclude TOTAL
- **Data Caveats:** Official operational standard is less than 1%; inclusive 6-week boundary differs from RTT strict-over boundaries
- **Validation:** Band sums and weighted denominator reconciliation

## K31 — Monthly change

- **Meaning:** Difference from immediately preceding reporting month
- **Numerator:** Current month KPI minus prior calendar month KPI
- **Denominator:** Not applicable
- **Calculation:** Current month KPI minus prior calendar month KPI
- **Source:** All domains separately
- **Reporting Grain:** Same domain/provider/service scope
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Consecutive months only
- **Data Caveats:** Percentage rates use percentage-point difference, not percentage change; missing months remain missing
- **Validation:** Join to previous calendar month, not arbitrary prior observation

## K32 — Year-on-year change

- **Meaning:** Difference versus same calendar month one year earlier
- **Numerator:** Current KPI minus KPI at month minus 12 months
- **Denominator:** Prior-year KPI for relative change
- **Calculation:** Current KPI minus KPI at month minus 12 months / Prior-year KPI for relative change
- **Source:** All domains separately
- **Reporting Grain:** Same domain and scope
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Identical provider/service filters
- **Data Caveats:** Changing coverage and revisions can affect comparisons
- **Validation:** Date-based join; no value where prior year absent

## K33 — Latest reporting period

- **Meaning:** Most recent retained source reporting month
- **Numerator:** MAX(reporting_month)
- **Denominator:** Not applicable
- **Calculation:** MAX(reporting_month)
- **Source:** Source manifest
- **Reporting Grain:** Dataset
- **Time Period:** Reporting month; stocks at month end and flows during month as specified
- **Applicable Filters:** Dataset-specific date
- **Data Caveats:** Never relabel as current live patient data
- **Validation:** Internal Period matches catalogue reporting month
