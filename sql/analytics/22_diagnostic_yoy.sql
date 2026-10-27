SELECT a.month,a.waiting_count,b.waiting_count AS prior_year,a.over_6_rate-b.over_6_rate AS annual_rate_change
FROM analytics.diagnostics_national_month a LEFT JOIN analytics.diagnostics_national_month b ON b.month=a.month-interval '1 year' ORDER BY a.month;
