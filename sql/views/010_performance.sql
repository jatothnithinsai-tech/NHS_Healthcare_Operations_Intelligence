CREATE OR REPLACE VIEW analytics.rtt_provider_month AS
SELECT month,provider_code,
 CASE WHEN count(waiting_count)=count(*) THEN sum(waiting_count) END AS waiting_count,
 CASE WHEN count(total_all)=count(*) THEN sum(total_all) END AS total_all,
 CASE WHEN count(unknown_start)=count(*) THEN sum(unknown_start) END AS unknown_start,
 CASE WHEN count(within_18)=count(*) THEN sum(within_18) END AS within_18,
 CASE WHEN count(over_52)=count(*) THEN sum(over_52) END AS over_52,
 CASE WHEN count(over_65)=count(*) THEN sum(over_65) END AS over_65,
 CASE WHEN count(over_78)=count(*) THEN sum(over_78) END AS over_78,
 CASE WHEN count(over_104)=count(*) THEN sum(over_104) END AS over_104,
 CASE WHEN count(within_18)=count(*) AND count(waiting_count)=count(*) THEN sum(within_18)::numeric/nullif(sum(waiting_count),0) END AS within_18_rate
FROM analytics.fact_rtt WHERE pathway_type='Part_2' GROUP BY month,provider_code;

CREATE OR REPLACE VIEW analytics.rtt_national_month AS
SELECT month, sum(waiting_count) AS waiting_count, sum(total_all) AS total_all,
 sum(unknown_start) AS unknown_start,sum(within_18) AS within_18,sum(over_52) AS over_52,
 sum(over_65) AS over_65,sum(over_78) AS over_78,sum(over_104) AS over_104,
 sum(within_18)::numeric/nullif(sum(waiting_count),0) AS within_18_rate,
 count(DISTINCT provider_code) AS providers
FROM analytics.rtt_provider_month GROUP BY month
HAVING count(waiting_count)=count(*) AND count(within_18)=count(*);

CREATE OR REPLACE VIEW analytics.ae_national_month AS
SELECT month,sum(attendances) AS attendances,sum(over_4) AS over_4,sum(within_4) AS within_4,
 sum(within_4)::numeric/nullif(sum(attendances),0) AS within_4_rate,
 sum(type1_attendances) AS type1_attendances,
 (sum(type1_attendances)-sum(type1_over_4))::numeric/nullif(sum(type1_attendances),0) AS type1_within_4_rate,
 sum(emergency_admissions) AS emergency_admissions,sum(dta_12_plus) AS dta_12_plus,
 count(*) AS providers
FROM analytics.fact_ae GROUP BY month HAVING count(attendances)=count(*) AND count(within_4)=count(*);

CREATE OR REPLACE VIEW analytics.diagnostics_provider_month AS
SELECT month,provider_code,
 CASE WHEN count(waiting_count)=count(*) THEN sum(waiting_count) END AS waiting_count,
 CASE WHEN count(over_6)=count(*) THEN sum(over_6) END AS over_6,
 CASE WHEN count(over_13)=count(*) THEN sum(over_13) END AS over_13,
 CASE WHEN count(total_activity)=count(*) THEN sum(total_activity) END AS total_activity,
 CASE WHEN count(over_6)=count(*) AND count(waiting_count)=count(*) THEN sum(over_6)::numeric/nullif(sum(waiting_count),0) END AS over_6_rate
FROM analytics.fact_diagnostics GROUP BY month,provider_code;

CREATE OR REPLACE VIEW analytics.diagnostics_national_month AS
SELECT month,sum(waiting_count) AS waiting_count,sum(over_6) AS over_6,sum(over_13) AS over_13,
 sum(total_activity) AS total_activity,sum(over_6)::numeric/nullif(sum(waiting_count),0) AS over_6_rate,
 count(*) AS providers
FROM analytics.diagnostics_provider_month GROUP BY month
HAVING count(waiting_count)=count(*) AND count(over_6)=count(*);

-- Monthly aggregate joins are safe: one row per dataset/month; fact-to-fact joins are prohibited.
CREATE OR REPLACE VIEW analytics.executive_month AS
SELECT d.date AS month,r.waiting_count AS rtt_waiting,r.within_18_rate,r.over_52,
 a.attendances,a.within_4_rate,a.emergency_admissions,a.dta_12_plus,
 g.waiting_count AS diagnostic_waiting,g.over_6,g.over_6_rate,g.total_activity
FROM analytics.dim_date d
LEFT JOIN analytics.rtt_national_month r ON r.month=d.date
LEFT JOIN analytics.ae_national_month a ON a.month=d.date
LEFT JOIN analytics.diagnostics_national_month g ON g.month=d.date
WHERE r.month IS NOT NULL OR a.month IS NOT NULL OR g.month IS NOT NULL;

CREATE OR REPLACE VIEW analytics.operational_priorities AS
WITH lagged AS (
 SELECT *,lag(within_18_rate) OVER(PARTITION BY provider_code ORDER BY month) AS previous_rate,
 lag(month) OVER(PARTITION BY provider_code ORDER BY month) AS previous_month
 FROM analytics.rtt_provider_month
), signals AS (
 SELECT *, CASE WHEN previous_month=month-interval '1 month' AND within_18_rate<previous_rate THEN 1 ELSE 0 END AS deteriorated
 FROM lagged
), rolling AS (
 SELECT *,sum(deteriorated) OVER(PARTITION BY provider_code ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS deterioration_months,
 min(month) OVER(PARTITION BY provider_code ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS window_start
 FROM signals
)
SELECT r.*,p.provider_name,
 CASE WHEN deterioration_months=3 AND window_start=month-interval '2 months' THEN 'Review sustained deterioration'
 WHEN over_52>=1000 THEN 'Review long-wait volume' ELSE 'Monitor' END AS priority_reason
FROM rolling r JOIN analytics.dim_provider p USING(provider_code)
WHERE month=(SELECT max(month) FROM analytics.rtt_provider_month) AND waiting_count>=1000;
