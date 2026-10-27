SELECT run_id,started_at,finished_at,status,extract(epoch FROM finished_at-started_at) AS elapsed_seconds,
summary->>'loaded' AS loaded_files,summary->>'skipped' AS unchanged_files FROM audit.pipeline_run ORDER BY started_at DESC;
