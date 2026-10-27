SELECT *,100.0*(over_6_rate-lag(over_6_rate) OVER(ORDER BY month)) AS mom_pp,
 avg(over_6_rate) OVER(ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_rate
FROM analytics.diagnostics_national_month ORDER BY month;
