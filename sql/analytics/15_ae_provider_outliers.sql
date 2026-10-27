WITH rates AS (SELECT *,within_4::numeric/nullif(attendances,0) AS rate FROM analytics.fact_ae WHERE month=(SELECT max(month) FROM analytics.fact_ae) AND type1_attendances>=1000),
quartiles AS (SELECT percentile_cont(0.25) WITHIN GROUP(ORDER BY rate) AS q1,percentile_cont(0.75) WITHIN GROUP(ORDER BY rate) AS q3 FROM rates)
SELECT provider_code,attendances,rate,q1,q3 FROM rates CROSS JOIN quartiles WHERE rate<q1-1.5*(q3-q1) ORDER BY rate;
