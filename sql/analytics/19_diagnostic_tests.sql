SELECT f.test_code,s.test_name,sum(waiting_count) AS waiting,sum(over_6) AS over_6,
 sum(over_6)::numeric/nullif(sum(waiting_count),0) AS over_6_rate,sum(total_activity) AS activity
FROM analytics.fact_diagnostics f JOIN analytics.dim_service s USING(test_code)
WHERE month=(SELECT max(month) FROM analytics.fact_diagnostics) GROUP BY f.test_code,s.test_name ORDER BY over_6 DESC;
