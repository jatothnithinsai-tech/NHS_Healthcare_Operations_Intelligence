WITH history AS (SELECT provider_code,month,within_18_rate,lag(within_18_rate) OVER(PARTITION BY provider_code ORDER BY month) AS prior_rate,
lead(within_18_rate) OVER(PARTITION BY provider_code ORDER BY month) AS following_rate FROM analytics.rtt_provider_month)
SELECT *,100*(within_18_rate-prior_rate) AS change_pp FROM history ORDER BY provider_code,month;
