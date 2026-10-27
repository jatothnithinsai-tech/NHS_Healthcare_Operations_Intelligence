"""Generate a genuine PBIP/PBIR/TMDL project backed by validated CSV exports."""
from __future__ import annotations
import json
import uuid
from jsonschema import Draft7Validator
from referencing import Registry, Resource
from src.ingestion.acquire import ROOT

BASE=ROOT/'powerbi'
REPORT=BASE/'NHS_Healthcare.Report'
MODEL=BASE/'NHS_Healthcare.SemanticModel'
URLS=json.loads((BASE/'schemas/urls.json').read_text()) if (BASE/'schemas/urls.json').exists() else {}


def save(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False),encoding='utf-8')


def literal(value):
    if isinstance(value,bool):
        expr='true' if value else 'false'
    elif isinstance(value,(int,float)):
        expr=f'{value}D'
    else:
        expr="'"+str(value).replace("'","''")+"'"
    return {'expr':{'Literal':{'Value':expr}}}


def column(table,name):
    return {'Column':{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}


def measure(name,table='RTT'):
    return {'Measure':{'Expression':{'SourceRef':{'Entity':table}},'Property':name}}


def projection(field,label):
    content=next(iter(field.values()))
    return {'field':field,'queryRef':content['Expression']['SourceRef']['Entity']+'.'+content['Property'],'displayName':label,'nativeQueryRef':label}


def visual(page,name,kind,x,y,w,h,title,roles=None,text=None):
    cfg={'visualType':kind,'drillFilterOtherVisuals':True,'visualContainerObjects':{
        'title':[{'properties':{'show':literal(True),'text':literal(title),'fontColor':{'solid':{'color':literal('#123047')}},'fontSize':literal(12),'bold':literal(True)}}],
        'background':[{'properties':{'show':literal(True),'color':{'solid':{'color':literal('#FFFFFF')}},'transparency':literal(0)}}],
        'border':[{'properties':{'show':literal(True),'color':{'solid':{'color':literal('#DAE3E8')}},'radius':literal(8)}}]
    }}
    if roles:
        cfg['query']={'queryState':{role:{'projections':[projection(field,label) for field,label in fields]} for role,fields in roles.items()}}
    if text:
        cfg['objects']={'general':[{'properties':{'paragraphs':[{'textRuns':[{'value':text,'textStyle':{'fontFamily':'Segoe UI','fontSize':'16px','color':'#123047'}}]}]}}]}
        cfg['visualContainerObjects']['title'][0]['properties']['show']=literal(False)
    obj={'$schema':URLS['visual'],'name':name,'position':{'x':x,'y':y,'z':len(list((page/'visuals').glob('*'))) if (page/'visuals').exists() else 0,'height':h,'width':w},'visual':cfg}
    save(page/'visuals'/name/'visual.json',obj)


def semantic_model():
    definition=MODEL/'definition'
    (definition/'tables').mkdir(parents=True,exist_ok=True)
    save(MODEL/'definition.pbism',{'$schema':URLS['pbism'],'version':'4.0','settings':{}})
    (definition/'database.tmdl').write_text('database NHS_Healthcare\n\tcompatibilityLevel: 1601\n',encoding='utf-8')
    (definition/'model.tmdl').write_text('model Model\n\tculture: en-GB\n\tdefaultPowerBIDataSourceVersion: powerBI_V3\n\tsourceQueryCulture: en-GB\n\tdataAccessOptions\n\t\tlegacyRedirects\n\t\treturnErrorValuesAsNull\n\tannotation __PBI_TimeIntelligenceEnabled = 0\n',encoding='utf-8')
    root=str(BASE/'data').replace('\\','/')
    (definition/'expressions.tmdl').write_text(f'expression DataRoot = "{root}" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]\n',encoding='utf-8')
    specs={
        'Date':{'month':'dateTime','year':'int64','month_number':'int64','month_name':'string','financial_year':'string'},
        'Provider':{'provider_code':'string','provider_name':'string'},
        'Specialty':{'specialty_code':'string','specialty_name':'string'},
        'Service':{'test_code':'string','test_name':'string'},
        'Region':{'region_name':'string'},'Parent':{'parent_code':'string','parent_name':'string'},
        'RTT':{'month':'dateTime','provider_code':'string','parent_code':'string','specialty_code':'string','pathway_type':'string',**{c:'int64' for c in ['waiting_count','total_all','unknown_start','within_18','over_18','over_52','over_65','over_78','over_104']},'source_sha256':'string'},
        'AE':{'month':'dateTime','provider_code':'string','region_name':'string',**{c:'int64' for c in ['attendances','over_4','within_4','type1_attendances','type1_over_4','admissions_via_ae','other_admissions','emergency_admissions','dta_4_12','dta_12_plus']},'source_sha256':'string'},
        'Diagnostics':{'month':'dateTime','provider_code':'string','parent_code':'string','test_code':'string',**{c:'int64' for c in ['waiting_count','over_6','over_13','total_activity','waiting_activity','planned_activity','unscheduled_activity']},'source_sha256':'string'},
        'Sources':{'dataset':'string','month':'dateTime','publication_date':'dateTime','retrieved_at':'dateTime','sha256':'string','bytes':'int64','url':'string','publisher_revision_label':'boolean','download_status':'string'},
        'Pipeline':{'run_id':'string','started_at':'dateTime','finished_at':'dateTime','status':'string','loaded_files':'int64','unchanged_files':'int64'},
        'Quality':{'check_name':'string','status':'string','months':'int64','row_count':'int64'},
    }
    def complete(t,c):
        return f'IF(COUNT({t}[{c}])=COUNTROWS({t}),SUM({t}[{c}]))'
    dax={
        'RTT Pathways':('CALCULATE('+complete('RTT','waiting_count')+',RTT[pathway_type]="Part_2")','#,0'),
        'RTT Within18':('CALCULATE('+complete('RTT','within_18')+',RTT[pathway_type]="Part_2")','#,0'),
        'RTT Within18 Rate':('DIVIDE([RTT Within18],[RTT Pathways])','0.0%'),
        **{f'RTT Over{n}':('CALCULATE('+complete('RTT',f'over_{n}')+',RTT[pathway_type]="Part_2")','#,0') for n in [18,52,65,78,104]},
        'RTT Admitted Completed':('CALCULATE(SUM(RTT[total_all]),RTT[pathway_type]="Part_1A")','#,0'),
        'RTT Nonadmitted Completed':('CALCULATE(SUM(RTT[total_all]),RTT[pathway_type]="Part_1B")','#,0'),
        'AE Attendances':(complete('AE','attendances'),'#,0'),
        'AE Within4 Rate':('DIVIDE('+complete('AE','within_4')+',[AE Attendances])','0.0%'),
        'AE Type1 Within4 Rate':('DIVIDE(SUM(AE[type1_attendances])-SUM(AE[type1_over_4]),SUM(AE[type1_attendances]))','0.0%'),
        'Emergency Admissions':(complete('AE','emergency_admissions'),'#,0'),
        'DTA12 Plus':(complete('AE','dta_12_plus'),'#,0'),
        'Diagnostic Waiting':(complete('Diagnostics','waiting_count'),'#,0'),
        'Diagnostic Over6':(complete('Diagnostics','over_6'),'#,0'),
        'Diagnostic SixWeek Rate':('DIVIDE([Diagnostic Over6],[Diagnostic Waiting])','0.0%'),
        'Diagnostic Activity':(complete('Diagnostics','total_activity'),'#,0'),
        'RTT Latest Month':('MAX(RTT[month])','MMM yyyy'),
        'AE Latest Month':('MAX(AE[month])','MMM yyyy'),
        'Diagnostic Latest Month':('MAX(Diagnostics[month])','MMM yyyy'),
        'RTT Previous Year':('CALCULATE([RTT Pathways],SAMEPERIODLASTYEAR(\'Date\'[month]))','#,0'),
        'RTT YoY Change':('IF(NOT ISBLANK([RTT Previous Year]),[RTT Pathways]-[RTT Previous Year])','#,0'),
        'Providers Over1000 LongWaits':('COUNTROWS(FILTER(VALUES(Provider[provider_code]),[RTT Over52]>=1000))','#,0'),
        'Source Files':('COUNTROWS(Sources)','#,0'),
        'Publisher Revisions':('COUNTROWS(FILTER(Sources,Sources[publisher_revision_label]=TRUE()))','#,0'),
        'Source Retrieval Age Days':('DATEDIFF(MAX(Sources[retrieved_at]),NOW(),DAY)','#,0'),
        'Missing Domains':('3-DISTINCTCOUNT(Sources[dataset])','#,0'),
        'Failed Quality Checks':('COUNTROWS(FILTER(Quality,Quality[status]<>"PASS"))','#,0'),
        'Validation Status':('IF([Failed Quality Checks]=0,"PASS","FAIL")',''),
        'Unverified Publication Dates':('COUNTROWS(FILTER(Sources,ISBLANK(Sources[publication_date])))','#,0'),
        'Latest Pipeline Status':('VAR t=TOPN(1,Pipeline,Pipeline[started_at],DESC) RETURN CONCATENATEX(t,Pipeline[status],",")',''),
        'Latest Source Retrieval':('MAX(Sources[retrieved_at])','dd MMM yyyy HH:mm'),
    }
    latest=[('RTT','RTT Pathways'),('RTT','RTT Within18 Rate'),('RTT','RTT Over52'),('RTT','RTT Over65'),('RTT','RTT Over78'),('RTT','RTT Over104'),('AE','AE Attendances'),('AE','AE Within4 Rate'),('AE','Emergency Admissions'),('AE','DTA12 Plus'),('Diagnostics','Diagnostic Waiting'),('Diagnostics','Diagnostic Over6'),('Diagnostics','Diagnostic SixWeek Rate'),('Diagnostics','Diagnostic Activity')]
    for t,m in latest:
        dax[m+' Latest']=(f"VAR latestMonth=MAX({t}[month]) RETURN CALCULATE([{m}],KEEPFILTERS('Date'[month]=latestMonth))",dax[m][1])
    dax['RTT MoM Latest']=("VAR m=MAX(RTT[month]) VAR currentValue=CALCULATE([RTT Pathways],'Date'[month]=m) VAR previousValue=CALCULATE([RTT Pathways],REMOVEFILTERS('Date'),'Date'[month]=EDATE(m,-1)) RETURN IF(NOT ISBLANK(previousValue),currentValue-previousValue)",'#,0')
    dax['AE MoM pp Latest']=("VAR m=MAX(AE[month]) VAR currentValue=CALCULATE([AE Within4 Rate],'Date'[month]=m) VAR previousValue=CALCULATE([AE Within4 Rate],REMOVEFILTERS('Date'),'Date'[month]=EDATE(m,-1)) RETURN IF(NOT ISBLANK(previousValue),100*(currentValue-previousValue))",'0.00 "pp"')
    for table,columns in specs.items():
        types=[]
        lines=[f"table '{table}'",f'\tlineageTag: {uuid.uuid5(uuid.NAMESPACE_URL,"nhs/"+table)}']
        if table=='Date':
            lines += ['\tdataCategory: Time']
        for name,dtype in columns.items():
            lines += ['',f"\tcolumn '{name}'",f'\t\tdataType: {dtype}',f'\t\tsourceColumn: {name}',f'\t\tsummarizeBy: {"sum" if dtype=="int64" and table not in ("Date",) else "none"}']
            if dtype=='dateTime':
                lines += ['\t\tformatString: '+('dd MMM yyyy HH:mm:ss' if name in ['started_at','finished_at','retrieved_at'] else 'yyyy-MM-dd')]
            if name in ['provider_code','parent_code','specialty_code','test_code','source_sha256'] and table in ['RTT','AE','Diagnostics']:
                lines+=['\t\tisHidden']
            typ='Int64.Type' if dtype=='int64' else ('type datetime' if dtype=='dateTime' else ('type logical' if dtype=='boolean' else 'type text'))
            types.append('{"'+name+'", '+typ+'}')
        if table=='RTT':
            for name,(expr,fmt) in dax.items():
                lines += ['',f"\tmeasure '{name}' = {expr}"]
                if fmt:
                    lines += [f'\t\tformatString: {fmt}']
                lines+=['\t\tdisplayFolder: Operational KPIs']
        m='let\n\t\t\t\tSource = Csv.Document(File.Contents(DataRoot & "/'+table+'.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),\n\t\t\t\tHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),\n\t\t\t\tTyped = Table.TransformColumnTypes(Headers, {'+', '.join(types)+'}, "en-GB")\n\t\t\tin\n\t\t\t\tTyped'
        lines+=['',f"\tpartition '{table}' = m",'\t\tmode: import','\t\tsource =','\t\t\t'+m]
        (definition/'tables'/f'{table}.tmdl').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    relationships=[]
    for fact in ['RTT','AE','Diagnostics']:
        for dim,key in [('Date','month'),('Provider','provider_code')]:
            relationships += [f'relationship {uuid.uuid5(uuid.NAMESPACE_URL,f"nhs/{fact}/{dim}")}',f"\tfromColumn: '{fact}'.'{key}'",f"\ttoColumn: '{dim}'.'{key}'",'\tcrossFilteringBehavior: oneDirection','']
    for fact,dim,key in [('RTT','Specialty','specialty_code'),('RTT','Parent','parent_code'),('Diagnostics','Service','test_code'),('Diagnostics','Parent','parent_code'),('AE','Region','region_name')]:
        relationships += [f'relationship {uuid.uuid5(uuid.NAMESPACE_URL,f"nhs/{fact}/{dim}")}',f"\tfromColumn: '{fact}'.'{key}'",f"\ttoColumn: '{dim}'.'{key}'",'\tcrossFilteringBehavior: oneDirection','']
    (definition/'relationships.tmdl').write_text('\n'.join(relationships),encoding='utf-8')
    save(BASE/'dax_catalogue.json',{name:{'expression':expr,'format':fmt} for name,(expr,fmt) in dax.items()})


def report():
    save(BASE/'NHS_Healthcare_Operations_Intelligence.pbip',{'$schema':URLS['pbip'],'version':'1.0','artifacts':[{'report':{'path':REPORT.name}}],'settings':{'enableAutoRecovery':True}})
    save(REPORT/'definition.pbir',{'$schema':URLS['pbir'],'version':'4.0','datasetReference':{'byPath':{'path':'../'+MODEL.name}}})
    definition=REPORT/'definition'
    save(definition/'version.json',{'$schema':URLS['version'],'version':'2.0.0'})
    theme={'name':'NHS_Operations','dataColors':['#007F86','#123047','#5B8BA3','#78BDB4','#B5C7D3','#C88448'],'background':'#F3F6F8','foreground':'#123047','tableAccent':'#007F86','textClasses':{'title':{'fontFace':'Segoe UI Semibold','color':'#123047'},'label':{'fontFace':'Segoe UI','color':'#526575'}}}
    save(REPORT/'StaticResources/RegisteredResources/NHS_Operations.json',theme)
    versions={'visual':'2.1.0','page':'2.0.0','report':'3.0.0'}
    save(definition/'report.json',{'$schema':URLS['report'],'themeCollection':{'baseTheme':{'name':'CY24SU11','reportVersionAtImport':versions,'type':'SharedResources'},'customTheme':{'name':'NHS_Operations','reportVersionAtImport':versions,'type':'RegisteredResources'}},'resourcePackages':[{'name':'RegisteredResources','type':'RegisteredResources','items':[{'name':'NHS_Operations','path':'NHS_Operations.json','type':'CustomTheme'}]}]})
    pages=[('Executive','Executive Healthcare Performance'),('RTT','RTT Waiting List Intelligence'),('UrgentDiagnostics','A&E and Diagnostics Intelligence'),('Monitoring','Data Quality & Operational Monitoring')]
    save(definition/'pages/pages.json',{'$schema':URLS['pages'],'pageOrder':[x[0] for x in pages],'activePageName':'Executive'})
    for name,title in pages:
        p=definition/'pages'/name
        page={'$schema':URLS['page'],'name':name,'displayName':title,'displayOption':'FitToPage','height':840,'width':1280,'objects':{'background':[{'properties':{'color':{'solid':{'color':literal('#F3F6F8')}},'transparency':literal(0)}}]}}
        if name=='RTT':
            page['pageBinding']={'name':'ProviderInvestigation','type':'Drillthrough','acceptsFilterContext':'Default','parameters':[{'name':'Provider','fieldExpr':column('Provider','provider_code')}]}
        save(p/'page.json',page)
        visual(p,'page_title','textbox',24,16,1230,60,'',text='NHS OPERATIONS  |  '+title.upper())
        visual(p,'date_filter','slicer',24,80,280,90,'Reporting month',{'Values':[(column('Date','month_name'),'Reporting month')]})
        visual(p,'provider_filter','slicer',320,80,440,90,'Provider',{'Values':[(column('Provider','provider_name'),'Provider')]})
        manifest=json.loads((ROOT/'data/reference/source_manifest.json').read_text())
        latest_months={d:max(s['reporting_month'] for s in manifest if s['dataset']==d)[:7] for d in ['rtt','ae','diagnostics']}
        visual(p,'context_note','textbox',780,80,476,90,'',text=f"Latest releases: RTT {latest_months['rtt']}; A&E {latest_months['ae']}; diagnostics {latest_months['diagnostics']}. Monthly aggregates; separate populations.")
        if name=='Executive':
            cards=[('RTT Pathways Latest','Incomplete RTT pathways'),('RTT Within18 Rate Latest','RTT within 18 weeks'),('AE Within4 Rate Latest','A&E within four hours'),('Diagnostic SixWeek Rate Latest','Diagnostics six weeks or more')]
            for i,(m,label) in enumerate(cards):
                visual(p,'kpi_'+str(i),'card',24+i*312,190,296,120,label,{'Values':[(measure(m),label)]})
            visual(p,'rtt_trend','lineChart',24,330,606,270,'RTT incomplete pathways',{'Category':[(column('Date','month'),'Month')],'Y':[(measure('RTT Pathways'),'Pathways')],'Tooltips':[(measure('RTT Over52'),'Over52')]})
            visual(p,'ae_trend','lineChart',650,330,606,270,'A&E four-hour performance',{'Category':[(column('Date','month'),'Month')],'Y':[(measure('AE Within4 Rate'),'Four-hour performance')],'Tooltips':[(measure('AE Attendances'),'Attendances')]})
            visual(p,'provider_summary','tableEx',24,620,1232,190,'Provider overview · latest month in the active date context',{'Values':[(column('Provider','provider_name'),'Provider'),(measure('RTT Pathways Latest'),'RTT pathways'),(measure('RTT Over52 Latest'),'Over52'),(measure('AE Attendances Latest'),'A&E attendances')]})
        elif name=='RTT':
            for i,(m,label) in enumerate([('RTT Pathways Latest','Incomplete pathways'),('RTT Over52 Latest','Over 52 weeks'),('RTT MoM Latest','Monthly list change'),('RTT Latest Month','RTT reporting month')]):
                visual(p,'kpi_'+str(i),'card',24+i*312,190,296,120,label,{'Values':[(measure(m),label)]})
            visual(p,'specialty','barChart',24,330,606,270,'Long waits by specialty',{'Category':[(column('Specialty','specialty_name'),'Specialty')],'Y':[(measure('RTT Over52 Latest'),'Over52')],'Tooltips':[(measure('RTT Pathways Latest'),'Pathways')]})
            visual(p,'long_wait_trend','lineChart',650,330,606,270,'Long-wait thresholds · nested counts',{'Category':[(column('Date','month'),'Month')],'Y':[(measure('RTT Over52'),'Over52'),(measure('RTT Over78'),'Over78'),(measure('RTT Over104'),'Over104')]})
            visual(p,'provider_detail','tableEx',24,620,1232,190,'Provider investigation · drillthrough target',{'Values':[(column('Provider','provider_name'),'Provider'),(measure('RTT Within18 Rate Latest'),'Within18'),(measure('RTT Over52 Latest'),'Over52'),(measure('RTT Over65 Latest'),'Over65')]})
        elif name=='UrgentDiagnostics':
            for i,(m,label) in enumerate([('AE Attendances Latest','A&E attendances'),('DTA12 Plus Latest','12+ hours after decision to admit'),('Diagnostic Waiting Latest','Diagnostic waits'),('Diagnostic Activity Latest','Diagnostic activity')]):
                visual(p,'kpi_'+str(i),'card',24+i*312,190,296,120,label,{'Values':[(measure(m),label)]})
            visual(p,'ae_activity','lineChart',24,330,606,270,'A&E attendances and emergency admissions',{'Category':[(column('Date','month'),'Month')],'Y':[(measure('AE Attendances'),'Attendances'),(measure('Emergency Admissions'),'Emergency admissions')]})
            visual(p,'diagnostic_test','barChart',650,330,606,270,'Six-week-or-more waits by diagnostic test · latest selected month',{'Category':[(column('Service','test_name'),'Diagnostic test')],'Y':[(measure('Diagnostic Over6 Latest'),'Six-week-or-more waits')],'Tooltips':[(measure('Diagnostic SixWeek Rate Latest'),'Six-week rate')]})
            visual(p,'selected_provider','tableEx',24,620,1232,190,'Selected provider comparisons · each metric has its own denominator',{'Values':[(column('Provider','provider_name'),'Provider'),(measure('AE Within4 Rate Latest'),'A&E within4'),(measure('Diagnostic SixWeek Rate Latest'),'Diagnostics six-week rate')]})
        else:
            for i,(m,label) in enumerate([('Source Files','Retained source versions'),('Unverified Publication Dates','Publication dates awaiting verification'),('Latest Pipeline Status','Latest pipeline status'),('Latest Source Retrieval','Latest source retrieval')]):
                visual(p,'kpi_'+str(i),'card',24+i*312,190,296,120,label,{'Values':[(measure(m),label)]})
            for i,(m,label) in enumerate([('Source Retrieval Age Days','Days since retrieval'),('Missing Domains','Missing data domains'),('Publisher Revisions','Publisher-labelled revised files'),('Validation Status','Warehouse validation status')]):
                visual(p,'monitor_'+str(i),'card',24+i*312,325,296,90,label,{'Values':[(measure(m),label)]})
            visual(p,'source_dates','tableEx',24,430,775,145,'Reporting dates and verified publication dates',{'Values':[(column('Sources','dataset'),'Dataset'),(column('Sources','month'),'Reporting month'),(column('Sources','publication_date'),'Publication date')]})
            visual(p,'coverage_checks','tableEx',815,430,441,145,'Coverage and validation',{'Values':[(column('Quality','check_name'),'Check'),(column('Quality','status'),'Status'),(column('Quality','months'),'Months')]})
            visual(p,'pipeline_runs','tableEx',24,590,1232,140,'Actual pipeline execution records · full timestamps',{'Values':[(column('Pipeline','started_at'),'Started'),(column('Pipeline','finished_at'),'Finished'),(column('Pipeline','status'),'Status'),(column('Pipeline','loaded_files'),'Changed files'),(column('Pipeline','unchanged_files'),'Unchanged files')]})
            visual(p,'quality_note','textbox',24,750,1232,60,'',text='Coverage and source totals are enforced before reporting. Historical revisions and interrupted/failed runs remain visible. No live patient feeds.')


def validate():
    schemas=json.loads((BASE/'schemas/registry.json').read_text())
    registry=Registry().with_resources((uri,Resource.from_contents(schema)) for uri,schema in schemas.items())
    results=[]
    paths=[BASE/'NHS_Healthcare_Operations_Intelligence.pbip',MODEL/'definition.pbism',REPORT/'definition.pbir']+list((REPORT/'definition').rglob('*.json'))
    for p in paths:
        value=json.loads(p.read_text(encoding='utf-8'))
        schema=schemas[value['$schema']]
        errors=list(Draft7Validator(schema,registry=registry).iter_errors(value))
        results.append({'file':p.relative_to(BASE).as_posix(),'errors':[e.message for e in errors]})
    failures=[r for r in results if r['errors']]
    status={'json_files':len(results),'failed':len(failures),'results':results,'desktop_open':'not yet verified','tmdl':'requires TOM/Desktop validation','dax':'requires execution against refreshed semantic model'}
    save(ROOT/'reports/validation/powerbi_metadata.json',status)
    if failures:
        print(json.dumps(failures[:5],indent=2))
        raise ValueError(f'{len(failures)} PBIR schema validation failures')
    print(f'{len(results)} Power BI project/report JSON files passed Microsoft schema validation')


def build():
    semantic_model()
    report()
    validate()


if __name__=='__main__':
    build()
