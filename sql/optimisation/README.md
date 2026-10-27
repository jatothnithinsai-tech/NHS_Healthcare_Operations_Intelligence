# Measured query-plan inspection

`src.analytics.run_sql.optimisation` executes the same selected-provider RTT long-wait aggregation five times with the default planner and five times with index/bitmap scans disabled. The partial provider/month index covers incomplete-pathway waiting and long-wait counts. PostgreSQL statistics are refreshed after loading.

Actual `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` output, buffers and per-execution timings are recorded in `reports/validation/explain_analyze.json`. The executive report records the resulting median times. Cache state, run order and this local dataset limit generalisation; an index is not assumed to improve every national aggregation.
