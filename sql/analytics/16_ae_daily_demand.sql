SELECT month,attendances,attendances::numeric/extract(day FROM month+interval '1 month'-interval '1 day') AS attendances_per_calendar_day
FROM analytics.ae_national_month ORDER BY month;
