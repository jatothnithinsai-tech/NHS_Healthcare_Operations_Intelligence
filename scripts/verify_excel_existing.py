"""Recheck the saved native workbook, including intentional hidden chart gaps."""
import json
import argparse
import win32com.client
from src.ingestion.acquire import ROOT

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repair-chart-visibility',action='store_true')
args=parser.parse_args()
app=win32com.client.DispatchEx('Excel.Application')
app.Visible=False
app.DisplayAlerts=False
book=app.Workbooks.Open(str(ROOT/'excel/NHS_Healthcare_Executive_Analysis.xlsx'),UpdateLinks=0,ReadOnly=not args.repair_chart_visibility)
try:
    payload=json.loads((ROOT/'excel/report_payload.json').read_text())
    if args.repair_chart_visibility:
        for name in ['Executive Summary','Monthly Trends']:
            chart=book.Worksheets(name).ChartObjects(1).Chart
            chart.PlotVisibleOnly=False
            for index,field,valuecol in [(1,'C','Q'),(2,'D','R')]:
                chart.SeriesCollection(index).Formula=f"=SERIES('Monthly Trends'!${field}$8,'Monthly Trends'!$B$9:$B$33,'Source Data'!${valuecol}$9:${valuecol}$33,{index})"
            chart.Axes(1).CategoryType=2
            months=tuple(str(x['month'])[:7] for x in payload['national'])
            for index in [1,2]:
                chart.SeriesCollection(index).XValues=months
    app.CalculateFullRebuild()
    previous=json.loads((ROOT/'reports/validation/excel_validation.json').read_text())
    payload=json.loads((ROOT/'excel/report_payload.json').read_text())
    previous['formula_errors']=[]
    previous['intentional_chart_gaps']=[]
    for sheet in book.Worksheets:
        try:
            errors=sheet.UsedRange.SpecialCells(-4123,16)
        except Exception:
            continue
        for cell in errors.Cells:
            if sheet.Name=='Source Data' and cell.Column in (17,18) and 9<=cell.Row<=8+len(payload['national']) and sheet.Evaluate('ISNA('+cell.Address+')'):
                previous['intentional_chart_gaps'].append({'sheet':sheet.Name,'cell':cell.Address,'handling':'Intentional NA in hidden chart helper prevents missing publication data from plotting as zero'})
            else:
                previous['formula_errors'].append({'sheet':sheet.Name,'cell':cell.Address,'formula':cell.Formula})
    summary=book.Worksheets('Executive Summary')
    volumes=[payload['rtt'][-1]['waiting_count'],payload['ae'][-1]['attendances'],payload['diagnostics'][-1]['waiting_count']]
    rates=[payload['rtt'][-1]['within_18_rate'],payload['ae'][-1]['within_4_rate'],payload['diagnostics'][-1]['over_6_rate']]
    previous['headline_volume_reconciliation']={k:summary.Cells(i+10,4).Value==v for i,(k,v) in enumerate(zip(['rtt','ae','diagnostics'],volumes))}
    previous['headline_rate_reconciliation']={k:abs(summary.Cells(i+10,5).Value-v)<1e-10 for i,(k,v) in enumerate(zip(['rtt','ae','diagnostics'],rates))}
    previous['chart_series_counts']={'Executive Summary':summary.ChartObjects(1).Chart.SeriesCollection().Count,'Monthly Trends':book.Worksheets('Monthly Trends').ChartObjects(1).Chart.SeriesCollection().Count}
    previous['status']='PASS' if not previous['formula_errors'] and all(previous['headline_volume_reconciliation'].values()) and all(previous['headline_rate_reconciliation'].values()) and all(v==2 for v in previous['chart_series_counts'].values()) and len(previous['intentional_chart_gaps'])==1 else 'FAIL'
    if args.repair_chart_visibility:
        book.Save()
        for index,name in [(1,'Executive Summary'),(6,'Monthly Trends')]:
            book.Worksheets(name).Activate()
            book.Worksheets(name).Range('B2').Select()
            book.Worksheets(name).ExportAsFixedFormat(0,str(ROOT/'excel/previews'/f'{index:02}_{name.replace(" ","_")}.pdf'))
    (ROOT/'reports/validation/excel_validation.json').write_text(json.dumps(previous,indent=2))
    print(json.dumps(previous,indent=2))
    if previous['status']!='PASS':
        raise ValueError('Saved workbook verification failed')
finally:
    book.Close(False)
    app.Quit()
