SELECT a.month,a.waiting_count,b.waiting_count AS prior_year,100.0*(a.waiting_count-b.waiting_count)/nullif(b.waiting_count,0) AS yoy_pct
FROM analytics.rtt_national_month a LEFT JOIN analytics.rtt_national_month b ON b.month=a.month-interval '1 year' ORDER BY a.month;
