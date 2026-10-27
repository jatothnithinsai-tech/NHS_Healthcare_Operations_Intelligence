SELECT specialty_code,percentile_cont(0.5) WITHIN GROUP(ORDER BY within_18::numeric/nullif(waiting_count,0)) AS median_provider_rate,
percentile_cont(0.9) WITHIN GROUP(ORDER BY waiting_count) AS p90_provider_waiting,count(*) AS observations
FROM analytics.fact_rtt WHERE pathway_type='Part_2' AND month=(SELECT max(month) FROM analytics.fact_rtt) AND waiting_count>=100 GROUP BY specialty_code;
