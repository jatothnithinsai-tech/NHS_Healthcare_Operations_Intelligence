SELECT month,sum(waiting_activity) AS waiting_list_activity,sum(planned_activity) AS planned_activity,
 sum(unscheduled_activity) AS unscheduled_activity,sum(total_activity) AS total_activity FROM analytics.fact_diagnostics GROUP BY month ORDER BY month;
