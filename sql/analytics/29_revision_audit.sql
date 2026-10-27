SELECT s.dataset,s.month,count(*) AS retained_versions,max(s.retrieved_at) AS last_retrieved,
bool_or(coalesce((metadata->>'publisher_revision_label')::boolean,false)) AS publisher_revised
FROM raw.source_file s GROUP BY s.dataset,s.month ORDER BY s.dataset,s.month;
