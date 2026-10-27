SELECT a.month,d.financial_year,a.attendances,sum(attendances) OVER(PARTITION BY d.financial_year ORDER BY a.month) AS observed_fy_running_total
FROM analytics.ae_national_month a JOIN analytics.dim_date d ON d.date=a.month ORDER BY month;
