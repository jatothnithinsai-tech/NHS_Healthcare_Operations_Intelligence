WITH ranked AS (SELECT *,row_number() OVER(PARTITION BY month ORDER BY over_52 DESC,provider_code) AS rn FROM analytics.rtt_provider_month)
SELECT month,sum(over_52) FILTER(WHERE rn<=10) AS top10_over52,sum(over_52) AS total_over52,
 sum(over_52) FILTER(WHERE rn<=10)::numeric/nullif(sum(over_52),0) AS share FROM ranked GROUP BY month ORDER BY month;
