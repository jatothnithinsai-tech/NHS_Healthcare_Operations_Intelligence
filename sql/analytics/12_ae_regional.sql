SELECT month,region_name,sum(attendances) AS attendances,sum(within_4)::numeric/nullif(sum(attendances),0) AS within_4_rate
FROM analytics.fact_ae GROUP BY month,region_name ORDER BY month,region_name;
