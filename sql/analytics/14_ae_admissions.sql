SELECT month,sum(admissions_via_ae) AS via_ae,sum(other_admissions) AS other_emergency,sum(emergency_admissions) AS total_emergency,
 sum(dta_4_12) AS dta_4_12,sum(dta_12_plus) AS dta_12_plus FROM analytics.fact_ae GROUP BY month ORDER BY month;
