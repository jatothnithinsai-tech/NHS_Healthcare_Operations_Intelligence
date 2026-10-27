SELECT month,provider_code,within_18_rate,100.0*(within_18_rate-0.92) AS gap_to_92pp
FROM analytics.rtt_provider_month WHERE month=(SELECT max(month) FROM analytics.rtt_provider_month) AND waiting_count>=1000 ORDER BY gap_to_92pp;
