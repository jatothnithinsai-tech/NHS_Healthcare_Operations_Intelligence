WITH counts AS (SELECT 'RTT' AS dataset,month,count(DISTINCT provider_code) AS providers FROM analytics.fact_rtt GROUP BY month
UNION ALL SELECT 'A&E',month,count(DISTINCT provider_code) FROM analytics.fact_ae GROUP BY month
UNION ALL SELECT 'Diagnostics',month,count(DISTINCT provider_code) FROM analytics.fact_diagnostics GROUP BY month)
SELECT *,providers-lag(providers) OVER(PARTITION BY dataset ORDER BY month) AS coverage_change FROM counts ORDER BY dataset,month;
