SELECT dataset,max(month) AS latest_reporting_month,max(publication_date) AS latest_verified_publication_date,
 count(*) FILTER(WHERE publication_date IS NULL) AS unverified_publication_dates,count(*) AS retained_versions
FROM raw.source_file GROUP BY dataset;
