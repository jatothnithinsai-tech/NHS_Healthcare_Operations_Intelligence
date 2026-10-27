SELECT month,sum(within_18) AS within_18,sum(over_18-over_52) AS over_18_to_52,
 sum(over_52-over_65) AS over_52_to_65,sum(over_65-over_78) AS over_65_to_78,
 sum(over_78-over_104) AS over_78_to_104,sum(over_104) AS over_104
FROM analytics.fact_rtt WHERE pathway_type='Part_2' GROUP BY month ORDER BY month;
