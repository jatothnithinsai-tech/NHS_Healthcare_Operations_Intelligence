SELECT *,100.0*(within_4_rate-lag(within_4_rate) OVER(ORDER BY month)) AS mom_pp,
 attendances-lag(attendances) OVER(ORDER BY month) AS attendance_change FROM analytics.ae_national_month ORDER BY month;
