"""Execute read-only DAX against this project's actual Desktop analysis engine."""
from __future__ import annotations
import json
from pathlib import Path
import re
import psutil
import win32com.client
from src.ingestion.acquire import ROOT
from src.database.warehouse import query_frame


def records(connection,query):
    result=connection.Execute(query)
    rs=result[0] if isinstance(result,tuple) else result
    names=[rs.Fields.Item(i).Name for i in range(rs.Fields.Count)]
    rows=[]
    while not rs.EOF:
        rows.append({name:rs.Fields.Item(i).Value for i,name in enumerate(names)})
        rs.MoveNext()
    rs.Close()
    return rows


def main():
    state=json.loads((ROOT/'.local/powerbi_desktop.json').read_text())
    engine=next((p for p in psutil.Process(state['pid']).children(recursive=True) if p.name().lower()=='msmdsrv.exe'),None)
    if engine is None:
        raise RuntimeError('This project has no running Power BI analysis engine')
    command=engine.cmdline()
    data=Path(command[command.index('-s')+1])
    port_bytes=(data/'msmdsrv.port.txt').read_bytes().replace(b'\x00',b'')
    port=int(re.search(rb'\d+',port_bytes)[0])
    connection=win32com.client.Dispatch('ADODB.Connection')
    connection.ConnectionTimeout=30
    connection.CommandTimeout=90
    connection.Open(f'Provider=MSOLAP;Data Source=localhost:{port};')
    catalogs=records(connection,'SELECT [CATALOG_NAME] FROM $SYSTEM.DBSCHEMA_CATALOGS')
    catalog=catalogs[0]['CATALOG_NAME']
    connection.Close()
    connection.Open(f'Provider=MSOLAP;Data Source=localhost:{port};Initial Catalog={catalog};')
    pairs=[('RTT waiting','RTT Pathways Latest','SELECT waiting_count FROM analytics.rtt_national_month ORDER BY month DESC LIMIT 1'),('RTT within18 rate','RTT Within18 Rate Latest','SELECT within_18_rate FROM analytics.rtt_national_month ORDER BY month DESC LIMIT 1'),('RTT over52','RTT Over52 Latest','SELECT over_52 FROM analytics.rtt_national_month ORDER BY month DESC LIMIT 1'),('A&E attendances','AE Attendances Latest','SELECT attendances FROM analytics.ae_national_month ORDER BY month DESC LIMIT 1'),('A&E four-hour rate','AE Within4 Rate Latest','SELECT within_4_rate FROM analytics.ae_national_month ORDER BY month DESC LIMIT 1'),('Diagnostic waiting','Diagnostic Waiting Latest','SELECT waiting_count FROM analytics.diagnostics_national_month ORDER BY month DESC LIMIT 1'),('Diagnostic six-week rate','Diagnostic SixWeek Rate Latest','SELECT over_6_rate FROM analytics.diagnostics_national_month ORDER BY month DESC LIMIT 1'),('Diagnostic activity','Diagnostic Activity Latest','SELECT total_activity FROM analytics.diagnostics_national_month ORDER BY month DESC LIMIT 1')]
    checks=[]
    for label,measure,sql in pairs:
        actual=records(connection,f'EVALUATE ROW("Value",[{measure}])')[0]['[Value]']
        expected=query_frame(sql).iloc[0,0]
        error=abs(float(actual)-float(expected)) if actual is not None else None
        checks.append({'check':label,'dax':actual,'sql':float(expected),'absolute_error':error,'status':'PASS' if error is not None and error<1e-8 else 'FAIL'})
    # Verify actual filter propagation through Provider and Date dimensions.
    provider=query_frame('SELECT provider_code FROM analytics.rtt_provider_month ORDER BY month DESC,over_52 DESC LIMIT 1').iloc[0,0]
    month=str(query_frame('SELECT max(month) FROM analytics.fact_rtt').iloc[0,0])[:10]
    year,mon,day=month.split('-')
    actual=records(connection,f'EVALUATE CALCULATETABLE(ROW("Value",[RTT Pathways]),TREATAS({{"{provider}"}},Provider[provider_code]),TREATAS({{DATE({year},{int(mon)},{int(day)})}},\'Date\'[month]))')[0]['[Value]']
    expected=query_frame(f"SELECT waiting_count FROM analytics.rtt_provider_month WHERE provider_code='{provider}' AND month='{month}'").iloc[0,0]
    checks.append({'check':'Provider/date dimension filter context','provider_code':provider,'month':month,'dax':actual,'sql':int(expected),'status':'PASS' if actual is not None and abs(float(actual)-float(expected))<1e-8 else 'FAIL'})
    monthly=records(connection,'EVALUATE SUMMARIZECOLUMNS(\'Date\'[month],"RTTWaiting",[RTT Pathways],"AEAttendances",[AE Attendances],"DiagnosticWaiting",[Diagnostic Waiting]) ORDER BY \'Date\'[month]')
    expected_months=query_frame('SELECT month,rtt_waiting,attendances,diagnostic_waiting FROM analytics.executive_month ORDER BY month')
    matches=0
    for row in monthly:
        month=str(row['Date[month]'])[:10]
        exp=expected_months[expected_months.month.astype(str)==month]
        if exp.empty:
            continue
        e=exp.iloc[0]
        valid=True
        for dax_key,sql_key in [('[RTTWaiting]','rtt_waiting'),('[AEAttendances]','attendances'),('[DiagnosticWaiting]','diagnostic_waiting')]:
            expected=e[sql_key]
            actual=row[dax_key]
            if expected is None:
                valid &= actual is None
            else:
                valid &= actual is not None and abs(float(actual)-float(expected))<1e-8
        matches+=int(valid)
    checks.append({'check':'All monthly domain totals','matched_months':matches,'expected_months':len(expected_months),'status':'PASS' if matches==len(expected_months) else 'FAIL'})
    errors=records(connection,'SELECT [MEASURE_NAME],[EXPRESSION] FROM $SYSTEM.MDSCHEMA_MEASURES')
    connection.Close()
    evidence={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','connection':'Actual local Power BI Desktop engine; endpoint retained only in ignored local state','catalog':catalog,'checks':checks,'visible_measures':len(errors),'monthly_dax':[{k:str(v) if hasattr(v,'year') else v for k,v in r.items()} for r in monthly]}
    (ROOT/'reports/validation/dax_reconciliation.json').write_text(json.dumps(evidence,indent=2,default=str))
    print(json.dumps({k:v for k,v in evidence.items() if k!='monthly_dax'},indent=2,default=str))
    if evidence['status']!='PASS':
        raise ValueError('DAX/SQL reconciliation failed')


if __name__=='__main__':
    main()
