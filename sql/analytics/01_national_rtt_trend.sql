-- Submitted incomplete pathways; never includes estimates for missing trusts.
SELECT *, waiting_count-lag(waiting_count) OVER(ORDER BY month) AS mom_change,
 100.0*(within_18_rate-lag(within_18_rate) OVER(ORDER BY month)) AS mom_percentage_points
FROM analytics.rtt_national_month ORDER BY month;
