import json
from src.ingestion.acquire import ROOT
from src.database.warehouse import query_frame
from src.pipeline import run


def fingerprints():
    result={}
    for table,keys in [('fact_rtt','month,provider_code,specialty_code,pathway_type'),('fact_ae','month,provider_code'),('fact_diagnostics','month,provider_code,test_code')]:
        row=query_frame(f"SELECT count(*) AS rows,md5(string_agg(md5(row_to_json(f)::text),'' ORDER BY {keys})) AS fingerprint FROM analytics.{table} f").iloc[0]
        result[table]={'rows':int(row.rows),'fingerprint':row.fingerprint}
    return result


before=fingerprints()
summary=run(refresh=False,reports=False)
after=fingerprints()
evidence={'status':'PASS' if before==after and summary['loaded']==0 and summary['skipped']==73 else 'FAIL','before':before,'after':after,'loaded':summary['loaded'],'skipped':summary['skipped'],'run_id':summary['run_id']}
(ROOT/'reports/validation/idempotency.json').write_text(json.dumps(evidence,indent=2))
print(json.dumps(evidence,indent=2))
if evidence['status']!='PASS':
    raise ValueError('Idempotency reconciliation failed')
