"""Synthetic RTT fixture: no synthetic data enter the warehouse or reports."""
import pandas as pd
import pytest
from src.transformation import parsers


def fixture():
    bands=[f'Gt {i:02} To {i+1:02} Weeks SUM 1' for i in range(104)]+['Gt 104 Weeks SUM 1']
    records=[]
    for specialty in ['C_100','C_999']:
        row={c:None for c in bands}
        row.update({'Period':'RTT-September-2024','Provider Org Code':'R1H','Provider Org Name':'SYNTHETIC TEST PROVIDER','Provider Parent Org Code':'QXX','Provider Parent Name':'SYNTHETIC TEST ICB','Commissioner Org Code':'01A','RTT Part Type':'Part_2','Treatment Function Code':specialty,'Treatment Function Name':'Total' if specialty=='C_999' else 'SYNTHETIC TEST SPECIALTY','Total':None,'Patients with unknown clock start date':None,'Total All':'3',bands[0]:'2',bands[52]:'1'})
        records.append(row)
    return pd.DataFrame(records,dtype='string')


def source():
    return {'dataset':'rtt','reporting_month':'2024-09-01','sha256':'a'*64}


def test_proven_blank_zeros_and_long_waits(monkeypatch):
    monkeypatch.setattr(parsers,'read_source',lambda _:fixture())
    frame,_,issues=parsers.parse(source())
    assert len(frame)==1
    assert frame.iloc[0].waiting_count==3 and frame.iloc[0].within_18==2 and frame.iloc[0].over_52==1
    assert pd.isna(frame.iloc[0].unknown_start)
    assert issues[0]['issue']=='structural_blank_bands_proven_zero'


def test_changed_schema_rejected(monkeypatch):
    f=fixture().drop(columns=['Gt 104 Weeks SUM 1'])
    monkeypatch.setattr(parsers,'read_source',lambda _:f)
    with pytest.raises(ValueError,match='schema'):
        parsers.parse(source())


def test_wrong_embedded_period_rejected(monkeypatch):
    f=fixture()
    f['Period']='RTT-October-2024'
    monkeypatch.setattr(parsers,'read_source',lambda _:f)
    with pytest.raises(ValueError,match='month mismatch'):
        parsers.parse(source())


def test_ae_total_case_and_empty_trailing_columns(monkeypatch):
    """Synthetic regression for the observed September 2024 CSV convention."""
    fields=['A&E attendances Type 1','A&E attendances Type 2','A&E attendances Other A&E Department','A&E attendances Booked Appointments Type 1','A&E attendances Booked Appointments Type 2','A&E attendances Booked Appointments Other Department','Attendances over 4hrs Type 1','Attendances over 4hrs Type 2','Attendances over 4hrs Other Department','Attendances over 4hrs Booked Appointments Type 1','Attendances over 4hrs Booked Appointments Type 2','Attendances over 4hrs Booked Appointments Other Department','Patients who have waited 4-12 hs from DTA to admission','Patients who have waited 12+ hrs from DTA to admission','Emergency admissions via A&E - Type 1','Emergency admissions via A&E - Type 2','Emergency admissions via A&E - Other A&E department','Other emergency admissions']
    row={'Period':'MSitAE-SEPTEMBER-2024','Org Code':'R1H','Parent Org':'SYNTHETIC REGION','Org name':'SYNTHETIC TEST PROVIDER',**{c:'0' for c in fields},'Unnamed: 22':None}
    row[fields[0]]='100'
    row[fields[3]]='10'
    row[fields[6]]='20'
    row[fields[9]]='5'
    total={**row,'Period':'Total','Org Code':'Total','Org name':'Total'}
    frame=pd.DataFrame([row,total],dtype='string')
    monkeypatch.setattr(parsers,'read_source',lambda _:frame)
    out,_,issues=parsers.parse({'dataset':'ae','reporting_month':'2024-09-01','sha256':'b'*64})
    assert len(out)==1 and out.iloc[0].attendances==110 and out.iloc[0].within_4==85
    assert issues[0]['issue']=='empty_trailing_csv_columns'
