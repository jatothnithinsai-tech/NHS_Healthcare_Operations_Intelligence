from src.database.warehouse import query_frame

for sql in [
    'SELECT dataset,count(*) AS months,sum(rows_loaded) AS rows FROM audit.loaded_source GROUP BY dataset ORDER BY dataset',
    "SELECT month,sum(waiting_count) AS incomplete,sum(within_18)::numeric/nullif(sum(waiting_count),0) AS within18,sum(over_52) AS over52 FROM analytics.fact_rtt WHERE pathway_type='Part_2' GROUP BY month ORDER BY month DESC LIMIT 2",
]:
    print(query_frame(sql).to_string(index=False))
