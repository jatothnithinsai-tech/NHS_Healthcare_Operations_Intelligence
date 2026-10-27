SELECT month,within_4_rate,type1_within_4_rate,100.0*(within_4_rate-type1_within_4_rate) AS percentage_point_difference
FROM analytics.ae_national_month ORDER BY month;
