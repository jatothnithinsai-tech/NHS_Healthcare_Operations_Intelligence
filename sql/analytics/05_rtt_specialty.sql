SELECT f.specialty_code,s.specialty_name,sum(waiting_count) AS waiting,sum(over_52) AS over_52,
 sum(within_18)::numeric/nullif(sum(waiting_count),0) AS within_18_rate
FROM analytics.fact_rtt f JOIN analytics.dim_specialty s USING(specialty_code)
WHERE pathway_type='Part_2' AND month=(SELECT max(month) FROM analytics.fact_rtt)
GROUP BY f.specialty_code,s.specialty_name ORDER BY over_52 DESC;
