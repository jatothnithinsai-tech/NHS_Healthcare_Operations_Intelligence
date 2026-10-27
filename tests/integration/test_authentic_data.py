"""Only retained genuine NHS data are used by these integration tests."""
import hashlib
import json
import os
import pandas as pd
import pytest
from src.database.warehouse import query_frame, load_frame
from src.ingestion.acquire import ROOT

pytestmark=[pytest.mark.integration,pytest.mark.skipif(os.getenv('NHS_INTEGRATION')!='1',reason='Set NHS_INTEGRATION=1 after authentic ingestion and PostgreSQL startup')]


@pytest.mark.parametrize('domain,months',[('rtt',24),('ae',25),('diagnostics',24)])
def test_genuine_coverage_and_checksums(domain,months):
    manifest=json.loads((ROOT/'data/reference/source_manifest.json').read_text())
    selected=[x for x in manifest if x['dataset']==domain]
    assert len(selected)>=months
    for x in selected:
        p=ROOT/x['local_path']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==x['sha256']
    periods=pd.to_datetime([x['reporting_month'] for x in selected])
    assert len(periods)==len(pd.date_range(periods.min(),periods.max(),freq='MS'))


@pytest.mark.parametrize('domain,keys',[('rtt','month,provider_code,specialty_code,pathway_type'),('ae','month,provider_code'),('diagnostics','month,provider_code,test_code')])
def test_fact_grains_and_foreign_keys(domain,keys):
    assert query_frame(f'SELECT {keys},count(*) FROM analytics.fact_{domain} GROUP BY {keys} HAVING count(*)>1').empty
    assert query_frame(f'SELECT f.provider_code FROM analytics.fact_{domain} f LEFT JOIN analytics.dim_provider p USING(provider_code) WHERE p.provider_code IS NULL').empty


def test_sql_reconciliation():
    r=query_frame("SELECT sum(waiting_count) AS n,sum(within_18) AS w FROM analytics.fact_rtt WHERE pathway_type='Part_2'").iloc[0]
    v=query_frame('SELECT sum(waiting_count) AS n,sum(within_18) AS w FROM analytics.rtt_national_month').iloc[0]
    assert tuple(r)==tuple(v)
    a=query_frame('SELECT sum(attendances) AS n,sum(within_4) AS w FROM analytics.fact_ae').iloc[0]
    b=query_frame('SELECT sum(attendances) AS n,sum(within_4) AS w FROM analytics.ae_national_month').iloc[0]
    assert tuple(a)==tuple(b)


def test_sql_execution_evidence():
    evidence=json.loads((ROOT/'reports/validation/sql_execution.json').read_text())
    assert evidence['passed']>=25 and evidence['failed']==0


def test_real_load_is_idempotent():
    manifest=json.loads((ROOT/'data/reference/source_manifest.json').read_text())
    source=next(x for x in manifest if x['dataset']=='ae')
    version=json.loads((ROOT/'config/settings.json').read_text())['parser_version']
    frame=pd.read_parquet(ROOT/'data/processed/ae'/f'{source["sha256"]}-{version}.parquet')
    before=query_frame('SELECT count(*) AS n,sum(attendances) AS total FROM analytics.fact_ae').iloc[0].tolist()
    assert load_frame(frame,source,version) is False
    assert before==query_frame('SELECT count(*) AS n,sum(attendances) AS total FROM analytics.fact_ae').iloc[0].tolist()


def test_no_redundant_totals():
    assert query_frame("SELECT count(*) AS n FROM analytics.fact_rtt WHERE specialty_code='C_999'").iloc[0,0]==0
    assert query_frame("SELECT count(*) AS n FROM analytics.fact_diagnostics d JOIN analytics.dim_service s USING(test_code) WHERE test_name='TOTAL'").iloc[0,0]==0


def test_workbook_kpi_evidence():
    result=json.loads((ROOT/'reports/validation/excel_validation.json').read_text())
    assert result['status']=='PASS' and result['pivot_tables']>=1 and result['native_charts']>=1
    assert len(result.get('intentional_chart_gaps',[]))==1


def test_powerbi_schema_evidence():
    result=json.loads((ROOT/'reports/validation/powerbi_metadata.json').read_text())
    assert result['failed']==0


def test_actual_powerbi_dax_matches_postgresql():
    result=json.loads((ROOT/'reports/validation/dax_reconciliation.json').read_text())
    assert result['status']=='PASS'
    assert all(x['status']=='PASS' for x in result['checks'])


def test_source_profile_counts_reconcile():
    profiles=json.loads((ROOT/'reports/validation/source_profiles.json').read_text())
    assert sum(x['transformed_rows'] for x in profiles)==query_frame('SELECT sum(rows_loaded) FROM audit.loaded_source').iloc[0,0]
