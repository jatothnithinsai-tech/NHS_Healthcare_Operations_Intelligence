WITH eligible AS (SELECT provider_code FROM analytics.rtt_provider_month GROUP BY provider_code HAVING count(*)=(SELECT count(*) FROM analytics.rtt_national_month))
SELECT month,sum(waiting_count) AS stable_code_waiting,sum(within_18)::numeric/nullif(sum(waiting_count),0) AS within_18_rate,count(*) AS providers
FROM analytics.rtt_provider_month WHERE provider_code IN(SELECT provider_code FROM eligible) GROUP BY month ORDER BY month;
