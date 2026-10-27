SELECT p.provider_name,r.*,rank() OVER(ORDER BY over_52 DESC) AS long_wait_rank,dense_rank() OVER(ORDER BY within_18_rate) AS performance_rank
FROM analytics.rtt_provider_month r JOIN analytics.dim_provider p USING(provider_code)
WHERE month=(SELECT max(month) FROM analytics.rtt_provider_month) AND waiting_count>=1000;
