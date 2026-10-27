-- Safe joining only after each domain is aggregated to provider/month.
SELECT r.month,r.provider_code,r.waiting_count AS rtt_pathways,a.attendances AS ae_attendances,d.waiting_count AS diagnostic_waits
FROM analytics.rtt_provider_month r LEFT JOIN analytics.fact_ae a USING(month,provider_code)
LEFT JOIN analytics.diagnostics_provider_month d USING(month,provider_code)
WHERE r.month=(SELECT max(month) FROM analytics.rtt_provider_month) ORDER BY r.waiting_count DESC;
