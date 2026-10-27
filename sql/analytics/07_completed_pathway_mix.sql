SELECT month,sum(waiting_count) FILTER(WHERE pathway_type='Part_1A') AS admitted_completed,
 sum(waiting_count) FILTER(WHERE pathway_type='Part_1B') AS nonadmitted_completed,
 sum(total_all-waiting_count) FILTER(WHERE pathway_type IN ('Part_1A','Part_1B')) AS unknown_start
FROM analytics.fact_rtt GROUP BY month ORDER BY month;
