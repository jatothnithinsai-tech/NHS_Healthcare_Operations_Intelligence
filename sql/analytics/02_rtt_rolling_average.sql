SELECT month,waiting_count,avg(waiting_count) OVER(ORDER BY month ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS rolling_three_months
FROM analytics.rtt_national_month ORDER BY month;
