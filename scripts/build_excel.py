"""Native Excel COM authoring, calculation, PivotTable and PDF verification.

User approved this fallback after the spreadsheet runtime failed to start.
Requires installed Microsoft Excel; creates its own invisible instance only.
"""
from __future__ import annotations
import json
import pythoncom
import win32com.client
from src.ingestion.acquire import ROOT

NAVY, TEAL, WHITE, GREY = 0x473012, 0x867F00, 0xFFFFFF, 0xF5F3F0


def build():
    payload = json.loads((ROOT/'excel/report_payload.json').read_text(encoding='utf-8'))
    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx('Excel.Application')
    app.Visible = False
    app.DisplayAlerts = False
    app.ScreenUpdating = False
    app.AutomationSecurity = 3
    workbook = app.Workbooks.Add()
    names = ['Executive Summary','RTT Performance','A&E Performance','Diagnostics Performance','Provider Comparisons','Monthly Trends','Operational Priorities','KPI Definitions','Data Quality Summary','Scenario Analysis','Source Data']
    while workbook.Worksheets.Count < len(names):
        workbook.Worksheets.Add(After=workbook.Worksheets(workbook.Worksheets.Count))
    for i,name in enumerate(names,1):
        workbook.Worksheets(i).Name=name
    sheets={name:workbook.Worksheets(name) for name in names}
    checks={}
    try:
        for name,sheet in sheets.items():
            sheet.Cells.Font.Name='Aptos'
            sheet.Cells.Font.Size=11
            sheet.Columns('A:A').ColumnWidth=3
            sheet.Columns('B:B').ColumnWidth=25
            sheet.Columns('C:F').ColumnWidth=17
            sheet.Columns('G:G').ColumnWidth=3
            sheet.Columns('H:N').ColumnWidth=13
            title=sheet.Range('B2:N3')
            title.Merge()
            title.Value=f'NHS OPERATIONS  |  {name.upper()}'
            title.Interior.Color=NAVY
            title.Font.Color=WHITE
            title.Font.Size=18
            title.Font.Bold=True
            sheet.Range('B5:N5').Merge()
            sheet.Range('B5').Value='Published aggregate observations · independent portfolio analysis · source-specific reporting months'
            sheet.Range('B5').Font.Color=0x706050
            sheet.PageSetup.Orientation=2
            sheet.PageSetup.PaperSize=9
            sheet.PageSetup.Zoom=False
            sheet.PageSetup.FitToPagesWide=1
            sheet.PageSetup.FitToPagesTall=1
            sheet.PageSetup.LeftMargin=app.InchesToPoints(.3)
            sheet.PageSetup.RightMargin=app.InchesToPoints(.3)
            sheet.PageSetup.CenterFooter='NHS England public aggregate data | Independent analysis | &P of &N'
            sheet.Activate()
            app.ActiveWindow.DisplayGridlines=False
            sheet.Range('C9').Select()
            app.ActiveWindow.FreezePanes=True

        def table(sheet_name,headers,rows,name,startrow=8):
            sh=sheets[sheet_name]
            matrix=[headers]+rows
            rowcount=len(matrix)
            colcount=len(headers)
            rg=sh.Range(sh.Cells(startrow,2),sh.Cells(startrow+rowcount-1,colcount+1))
            rg.Value=tuple(tuple('' if v is None else v for v in row) for row in matrix)
            tab=sh.ListObjects.Add(1,rg,None,1)
            tab.Name=name
            tab.TableStyle='TableStyleMedium2'
            rg.Rows(1).RowHeight=32
            rg.Rows(1).WrapText=True
            rg.NumberFormat='#,##0;[Red](#,##0);–'
            sh.Range(sh.Cells(startrow,2),sh.Cells(startrow+rowcount-1,2)).NumberFormat='@'
            sh.PageSetup.PrintArea=sh.Range('B2:N36').Address
            return tab, startrow+1, startrow+rowcount-1

        # Create every raw/input table before cross-sheet formulas.
        raw=payload['national']
        headers=['Month','RTT waiting','RTT within18','RTT over52','AE attendances','AE within4','Emergency admissions','DTA12plus','Diagnostic waiting','Diagnostic over6','Diagnostic activity']
        # Numerators are source-validated counts; rates remain native formulas.
        by_r={str(x['month'])[:7]:x for x in payload['rtt']}
        by_a={str(x['month'])[:7]:x for x in payload['ae']}
        by_g={str(x['month'])[:7]:x for x in payload['diagnostics']}
        model=[]
        for row in raw:
            m=str(row['month'])[:7]
            r,a,g=by_r.get(m,{}),by_a.get(m,{}),by_g.get(m,{})
            model.append([m,r.get('waiting_count'),r.get('within_18'),r.get('over_52'),a.get('attendances'),a.get('within_4'),a.get('emergency_admissions'),a.get('dta_12_plus'),g.get('waiting_count'),g.get('over_6'),g.get('total_activity')])
        table('Source Data',headers,model,'NationalData')
        sheets['Source Data'].Columns('B:L').ColumnWidth=16
        sheets['Source Data'].PageSetup.PrintArea='B2:L34'

        for name,domain,fields,labels,rate in [
            ('RTT Performance','rtt',['waiting_count','within_18','over_52'],['Incomplete pathways','Within18','Over52'],'Within18 rate'),
            ('A&E Performance','ae',['attendances','within_4','emergency_admissions','dta_12_plus'],['Attendances','Within4','Emergency admissions','DTA12plus'],'Within4 rate'),
            ('Diagnostics Performance','diagnostics',['waiting_count','over_6','total_activity'],['Waiting list','Six weeks or more','Activity'],'Six-week rate')]:
            rows=[[str(x['month'])[:7]]+[x[f] for f in fields]+[None] for x in payload[domain]]
            tab,first,last=table(name,['Month']+labels+[rate],rows,domain.title()+'Report')
            ratecol=2+len(fields)+1
            sh=sheets[name]
            sh.Range(sh.Cells(first,ratecol),sh.Cells(last,ratecol)).FormulaR1C1='=IFERROR(RC4/RC3,"")'
            sh.Range(sh.Cells(first,ratecol),sh.Cells(last,ratecol)).NumberFormat='0.0%'
            sh.Range(sh.Cells(first,ratecol),sh.Cells(last,ratecol)).FormatConditions.AddColorScale(3)
            chart=sh.ChartObjects().Add(sh.Range('H8').Left,sh.Range('H8').Top,570,330).Chart
            chart.ChartType=4
            chart.SetSourceData(sh.Range(sh.Cells(8,2),sh.Cells(last,3)))
            chart.HasTitle=True
            chart.ChartTitle.Text=f'{labels[0]} by reporting month'
            chart.HasLegend=False
            chart.SeriesCollection(1).Format.Line.ForeColor.RGB=TEAL
            chart.Axes(1).TickLabelSpacing=4
            chart.Axes(2).TickLabels.NumberFormat='#,##0'

        prov=payload['providers']
        rows=[[x['provider_code'],x['provider_name'],x['waiting_count'],x['within_18'],x['over_52'],x['priority_reason'],None] for x in prov]
        tab,first,last=table('Provider Comparisons',['Provider code','Provider name','RTT pathways','Within18','Over52','Review signal','Within18 rate'],rows,'Providers')
        sh=sheets['Provider Comparisons']
        sh.Columns('C:C').ColumnWidth=40
        sh.Columns('G:G').ColumnWidth=30
        sh.Range(f'H{first}:H{last}').FormulaR1C1='=IFERROR(RC5/RC4,"")'
        sh.Range(f'H{first}:H{last}').NumberFormat='0.0%'
        # Genuine PivotTable with grouped operational signals.
        cache=workbook.PivotCaches().Create(SourceType=1,SourceData=f"'Provider Comparisons'!{tab.Range.Address}")
        pivot=cache.CreatePivotTable(TableDestination=sh.Range('J8'),TableName='OperationalSignalPivot')
        pivot.PivotFields('Review signal').Orientation=1
        pivot.AddDataField(pivot.PivotFields('RTT pathways'),'Pathways by signal',-4157)
        pivot.AddDataField(pivot.PivotFields('Over52'),'Over52 by signal',-4157)
        pivot.TableStyle2='PivotStyleMedium9'
        sh.PageSetup.PrintArea='B2:M23'

        trendrows=[[x[0],None,None,None] for x in model]
        _,first,last=table('Monthly Trends',['Month','RTT within18 rate','AE within4 rate','Diagnostics six-week rate'],trendrows,'MonthlyRates')
        sh=sheets['Monthly Trends']
        for row in range(first,last+1):
            # No source row for September RTT/DM01: blank denominator stays blank.
            sh.Cells(row,3).Formula=f'=IFERROR(SUMIFS(NationalData[RTT within18],NationalData[Month],B{row})/SUMIFS(NationalData[RTT waiting],NationalData[Month],B{row}),"")'
            sh.Cells(row,4).Formula=f'=IFERROR(SUMIFS(NationalData[AE within4],NationalData[Month],B{row})/SUMIFS(NationalData[AE attendances],NationalData[Month],B{row}),"")'
            sh.Cells(row,5).Formula=f'=IFERROR(SUMIFS(NationalData[Diagnostic over6],NationalData[Month],B{row})/SUMIFS(NationalData[Diagnostic waiting],NationalData[Month],B{row}),"")'
        sh.Range(f'C{first}:E{last}').NumberFormat='0.0%'
        helper=sheets['Source Data']
        helper.Range('P8:R8').Value=(('Month','RTT rate chart','AE rate chart'),)
        for row in range(first,last+1):
            helper.Cells(row,16).Formula=f"='Monthly Trends'!B{row}"
            helper.Cells(row,17).Formula=f'=IF(ISNUMBER(\'Monthly Trends\'!C{row}),\'Monthly Trends\'!C{row},NA())'
            helper.Cells(row,18).Formula=f'=IF(ISNUMBER(\'Monthly Trends\'!D{row}),\'Monthly Trends\'!D{row},NA())'
        helper.Columns('P:R').Hidden=True
        chart=sh.ChartObjects().Add(sh.Range('H8').Left,sh.Range('H8').Top,570,330).Chart
        chart.ChartType=4
        chart.PlotVisibleOnly=False
        chart.PlotVisibleOnly=False
        while chart.SeriesCollection().Count:
            chart.SeriesCollection(1).Delete()
        for col,helper_col,color in [(3,17,TEAL),(4,18,NAVY)]:
            series=chart.SeriesCollection().NewSeries()
            series.Name=sh.Cells(8,col).Value
            series.XValues=sh.Range(f'B{first}:B{last}')
            series.Values=helper.Range(helper.Cells(first,helper_col),helper.Cells(last,helper_col))
            series.Formula=f"=SERIES('Monthly Trends'!${'C' if col==3 else 'D'}$8,'Monthly Trends'!$B${first}:$B${last},'Source Data'!${'Q' if col==3 else 'R'}${first}:${'Q' if col==3 else 'R'}${last},{1 if col==3 else 2})"
            series.Format.Line.ForeColor.RGB=color
        chart.HasTitle=True
        chart.ChartTitle.Text='Published RTT and A&E performance'
        chart.Axes(2).TickLabels.NumberFormat='0%'
        chart.Axes(1).TickLabelSpacing=4
        for index in [1,2]:
            chart.SeriesCollection(index).XValues=tuple(x[0] for x in model)

        top=prov[:15]
        table('Operational Priorities',['Code','Provider','Over52','Review signal'],[[x['provider_code'],x['provider_name'],x['over_52'],x['priority_reason']] for x in top],'PrioritiesTable')
        sheets['Operational Priorities'].Columns('C:C').ColumnWidth=55
        sheets['Operational Priorities'].Columns('E:E').ColumnWidth=40
        sheets['Operational Priorities'].Range('B26:N28').Merge()
        sheets['Operational Priorities'].Range('B26').Value='Signals identify areas for investigation. Account for provider size, specialty mix, code changes and data validation before taking action.'
        sheets['Operational Priorities'].Range('B26').WrapText=True
        defs=payload['definitions']
        table('KPI Definitions',['KPI','Meaning','Numerator','Denominator','Caveat'],[[x['name'],x['meaning'],x['numerator'],x['denominator'],x['data_caveats']] for x in defs],'KPIDefinitions')
        sh=sheets['KPI Definitions']
        sh.Columns('B:F').ColumnWidth=35
        sh.Range(f'B9:F{8+len(defs)}').WrapText=True
        sh.Range(f'B9:F{8+len(defs)}').RowHeight=65
        sh.PageSetup.PrintArea='B2:F15'
        quality=payload['quality']
        table('Data Quality Summary',['Control','Actual evidence','Status'],[[x['check'],x.get('months',x.get('rows','')),x['status']] for x in quality['checks']],'QualityControls')
        sh=sheets['Data Quality Summary']
        sh.Columns('B:B').ColumnWidth=38
        sh.Columns('C:C').ColumnWidth=25
        sh.Range('B18:N20').Merge()
        sh.Range('B18').Value='RTT structural blanks resolve to zero only when observed nonnegative bands exhaust an explicit source total. Suppression remains missing. Historical publication dates that are not verified remain blank.'
        sh.Range('B18').WrapText=True
        table('Data Quality Summary',['Dataset','Reporting month','Publication date','Source URL'],[[x['dataset'],str(x['month'])[:7],str(x.get('publication_date') or '')[:10],x['url']] for x in payload['sources']],'SourceProvenance',startrow=23)
        sh.Columns('E:E').ColumnWidth=42
        for index,source in enumerate(payload['sources'],24):
            sh.Hyperlinks.Add(Anchor=sh.Cells(index,5),Address=source['url'],TextToDisplay='NHS England · '+source['dataset']+' · '+str(source['month'])[:7])
        sh.PageSetup.PrintArea='B2:N33'

        sh=sheets['Scenario Analysis']
        sh.Range('B8:E8').Value=(('Scenario input','Value','Units','Meaning'),)
        sh.Range('B9:E11').Value=(('Current over52',int(payload['rtt'][-1]['over_52']),'pathways','Validated submitted count'),('Hypothetical reduction',.10,'percent','Editable planning assumption'),('Illustrative residual',None,'pathways','Arithmetic scenario, not a forecast or delivered benefit'))
        sh.Range('C10').Interior.Color=0xCCF2FF
        sh.Range('C10').NumberFormat='0%'
        sh.Range('C10').Validation.Add(2,1,1,0,1)
        sh.Range('C11').Formula='=C9*(1-C10)'
        sh.Range('C9:C11').NumberFormat='#,##0'
        sh.Range('C10').NumberFormat='0%'
        sh.Columns('B:B').ColumnWidth=32
        sh.Columns('E:E').ColumnWidth=62
        sh.Range('B15:N17').Merge()
        sh.Range('B15').Value='This scenario shows the arithmetic effect of a hypothetical reduction. It does not model capacity, causality, savings or future patient outcomes.'
        sh.Range('B15').WrapText=True

        sh=sheets['Executive Summary']
        sh.Range('B7:N7').Merge()
        sh.Range('B7').Value='LATEST VALIDATED PUBLICATIONS'
        sh.Range('B7').Font.Bold=True
        sh.Range('B9:E9').Value=(('Domain / unit','Reporting month','Headline volume','Performance'),)
        for row,domain,source,volume,numerator,denominator in [
            (10,'RTT · pathways',payload['rtt'],'RTT waiting','RTT within18','RTT waiting'),
            (11,'A&E · attendances',payload['ae'],'AE attendances','AE within4','AE attendances'),
            (12,'Diagnostics · waits',payload['diagnostics'],'Diagnostic waiting','Diagnostic over6','Diagnostic waiting')]:
            sh.Cells(row,2).Value=domain
            sh.Cells(row,3).Value=str(source[-1]['month'])[:7]
            sh.Cells(row,4).Formula=f'=SUMIFS(NationalData[{volume}],NationalData[Month],C{row})'
            sh.Cells(row,5).Formula=f'=IFERROR(SUMIFS(NationalData[{numerator}],NationalData[Month],C{row})/SUMIFS(NationalData[{denominator}],NationalData[Month],C{row}),"")'
        sh.Range('D10:D12').NumberFormat='[$-en-GB]#,##0'
        sh.Range('E10:E12').NumberFormat='0.0%'
        sh.Columns('D:E').ColumnWidth=23
        sh.Range('D10:E12').Font.Size=20
        sh.Range('D10:E12').Font.Bold=True
        sh.Range('D10:E12').Font.Color=NAVY
        sh.Range('B10:E12').RowHeight=38
        sh.Range('B9:E9').Interior.Color=TEAL
        sh.Range('B9:E9').Font.Color=WHITE
        sh.Range('B14:N15').Merge()
        sh.Range('B14').Value='RTT/A&E: higher performance is better. Diagnostics: lower six-week-or-more rate is better. Different populations and reporting dates; never sum headline volumes.'
        sh.Range('B14').WrapText=True
        sh.Range('B18').Value='Provider investigation'
        sh.Range('C18').Value=prov[0]['provider_code']
        sh.Range('B19').Value='Selected provider'
        sh.Range('C19:F19').Merge()
        sh.Range('C19').Formula2='=XLOOKUP(C18,Providers[Provider code],Providers[Provider name],"Not in comparable cohort")'
        sh.Range('B21').Value='Review signals'
        sh.Range('C21').Formula='=COUNTIFS(Providers[Review signal],"Review sustained deterioration")'
        sh.Range('D21:F21').Merge()
        sh.Range('D21').Value='Providers with sustained deterioration'
        sh.Range('B23:F25').Merge()
        sh.Range('B23').Value='Management action: review long-wait concentration, diagnostic test bottlenecks and admission flow with local operational evidence. Signals are proposed investigations, not clinical-quality rankings.'
        sh.Range('B23').WrapText=True
        sh.Range('B28:F30').Merge()
        sh.Range('B28').Value='Source: NHS England RTT, monthly A&E and DM01. Official URLs, release evidence and checksum lineage are available on Data Quality Summary and in the repository manifest.'
        sh.Range('B28').WrapText=True
        executive_chart=sh.ChartObjects().Add(sh.Range('H18').Left,sh.Range('H18').Top,500,230).Chart
        executive_chart.ChartType=4
        executive_chart.PlotVisibleOnly=False
        while executive_chart.SeriesCollection().Count:
            executive_chart.SeriesCollection(1).Delete()
        for col,helper_col,color in [(3,17,TEAL),(4,18,NAVY)]:
            series=executive_chart.SeriesCollection().NewSeries()
            series.Name=sheets['Monthly Trends'].Cells(8,col).Value
            series.XValues=sheets['Monthly Trends'].Range(f'B9:B{8+len(model)}')
            series.Values=helper.Range(helper.Cells(9,helper_col),helper.Cells(8+len(model),helper_col))
            series.Formula=f"=SERIES('Monthly Trends'!${'C' if col==3 else 'D'}$8,'Monthly Trends'!$B$9:$B${8+len(model)},'Source Data'!${'Q' if col==3 else 'R'}$9:${'Q' if col==3 else 'R'}${8+len(model)},{1 if col==3 else 2})"
            series.Format.Line.ForeColor.RGB=color
        executive_chart.HasTitle=True
        executive_chart.ChartTitle.Text='Published waiting-time performance'
        executive_chart.Axes(2).TickLabels.NumberFormat='0%'
        executive_chart.Axes(1).TickLabelSpacing=4
        for index in [1,2]:
            executive_chart.SeriesCollection(index).XValues=tuple(x[0] for x in model)

        # A real stored Power Query asset; existing imported data remain the audited snapshot.
        csv_path=str(ROOT/'powerbi/data/National.csv').replace('"','""')
        m=f'let Source = Csv.Document(File.Contents("{csv_path}"),[Delimiter=",",Encoding=65001,QuoteStyle=QuoteStyle.Csv]), Headers = Table.PromoteHeaders(Source,[PromoteAllScalars=true]) in Headers'
        workbook.Queries.Add('NHS_National_Publication_Import',m)
        app.CalculateFullRebuild()
        checks['headline_volume_reconciliation']={
            'rtt':sh.Range('D10').Value==payload['rtt'][-1]['waiting_count'],
            'ae':sh.Range('D11').Value==payload['ae'][-1]['attendances'],
            'diagnostics':sh.Range('D12').Value==payload['diagnostics'][-1]['waiting_count']}
        checks['headline_rate_reconciliation']={
            'rtt':abs(sh.Range('E10').Value-payload['rtt'][-1]['within_18_rate'])<1e-10,
            'ae':abs(sh.Range('E11').Value-payload['ae'][-1]['within_4_rate'])<1e-10,
            'diagnostics':abs(sh.Range('E12').Value-payload['diagnostics'][-1]['over_6_rate'])<1e-10}
        checks['formula_errors']=[]
        checks['intentional_chart_gaps']=[]
        for name,sheet in sheets.items():
            try:
                errs=sheet.UsedRange.SpecialCells(-4123,16)
                for cell in errs.Cells:
                    if name=='Source Data' and cell.Column in (17,18) and 9<=cell.Row<=8+len(model) and sheet.Evaluate('ISNA('+cell.Address+')'):
                        checks['intentional_chart_gaps'].append({'sheet':name,'cell':cell.Address,'handling':'Intentional NA in hidden chart helper prevents a missing publication month from plotting as zero'})
                    else:
                        checks['formula_errors'].append({'sheet':name,'cell':cell.Address,'error':cell.Text})
            except Exception:
                pass
        checks['sheets']=names
        checks['native_charts']=sum(sheet.ChartObjects().Count for sheet in sheets.values())
        checks['pivot_tables']=sum(sheet.PivotTables().Count for sheet in sheets.values())
        checks['power_queries']=workbook.Queries.Count
        checks['power_query_refresh']='Stored M query validated for existence; not refreshed through an external connection'
        checks['excel_version']=app.Version
        checks['headline_display']=[sh.Range(f'D{row}').Text for row in [10,11,12]]
        checks['status']='PASS' if all(checks['headline_volume_reconciliation'].values()) and all(checks['headline_rate_reconciliation'].values()) and not checks['formula_errors'] else 'FAIL'
        sheets['Executive Summary'].Activate()
        sheets['Executive Summary'].Range('B2').Select()
        destination=ROOT/'excel/NHS_Healthcare_Executive_Analysis.xlsx'
        workbook.SaveAs(str(destination),51)
        previews=ROOT/'excel/previews'
        previews.mkdir(exist_ok=True)
        for i,(name,sheet) in enumerate(sheets.items(),1):
            sheet.ExportAsFixedFormat(0,str(previews/f'{i:02}_{name.replace("&","and").replace(" ","_")}.pdf'))
        (ROOT/'reports/validation/excel_validation.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
        print(json.dumps(checks,indent=2))
        if checks['status']!='PASS':
            raise ValueError('Native Excel validation failed')
    finally:
        workbook.Close(False)
        app.Quit()
        pythoncom.CoUninitialize()


if __name__=='__main__':
    build()
