import json
from src.ingestion.acquire import ROOT


def test_secret_files_ignored():
    text=(ROOT/'.gitignore').read_text()
    assert '.env\n' in text and '.local/' in text and '.venv/' in text and 'data/raw/' in text


def test_kpi_definitions_complete():
    kpis=json.loads((ROOT/'config/kpi_catalogue.json').read_text(encoding='utf-8'))
    required={'name','meaning','numerator','denominator','calculation','source','reporting_grain','time_period','applicable_filters','data_caveats','validation'}
    assert len(kpis)>=20
    assert all(required.issubset(k) and all(k[f] for f in required) for k in kpis)


def test_no_hardcoded_password_in_example():
    assert 'YOUR_LOCAL_PASSWORD' in (ROOT/'.env.example').read_text()
