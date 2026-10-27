-- Every result should return zero violating rows.
SELECT month,provider_code,specialty_code,pathway_type
FROM analytics.fact_rtt
WHERE within_18+over_18<>waiting_count OR over_104>over_78 OR over_78>over_65 OR over_65>over_52 OR over_52>over_18;
SELECT month,provider_code FROM analytics.fact_ae
WHERE within_4+over_4<>attendances OR emergency_admissions<>admissions_via_ae+other_admissions;
SELECT month,provider_code,test_code FROM analytics.fact_diagnostics
WHERE over_13>over_6 OR over_6>waiting_count OR total_activity<>waiting_activity+planned_activity+unscheduled_activity;
