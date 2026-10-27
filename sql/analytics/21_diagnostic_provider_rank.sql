SELECT *,rank() OVER(ORDER BY over_6 DESC) AS volume_rank,dense_rank() OVER(ORDER BY over_6_rate DESC) AS rate_rank
FROM analytics.diagnostics_provider_month WHERE month=(SELECT max(month) FROM analytics.diagnostics_provider_month) AND waiting_count>=1000;
