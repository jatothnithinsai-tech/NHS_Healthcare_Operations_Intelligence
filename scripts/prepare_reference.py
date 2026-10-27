import hashlib
import json
import pandas as pd
from src.ingestion.acquire import ROOT

path=ROOT/'data/raw/samples/mapping.xls'
frame=pd.read_excel(path,header=7,usecols=[1,2,3,4,5],dtype=str)
frame.columns=['provider_code','provider_name','icb_code','icb_name','region_name']
frame=frame[frame.provider_code.str.fullmatch(r'[A-Z0-9]{3,6}',na=False)].copy()
frame=frame.drop_duplicates()
ambiguous=frame.loc[frame.duplicated('provider_code',keep=False),'provider_code'].unique().tolist()
frame.to_csv(ROOT/'data/reference/current_ae_provider_mapping.csv',index=False)
meta={'source_url':'https://www.england.nhs.uk/statistics/wp-content/uploads/sites/2/2026/06/System-Mapping-Apr-26.xls','sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'rows':len(frame),'unique_provider_codes':int(frame.provider_code.nunique()),'source_last_updated':'2026-05-14','use':'Current A&E provider-to-ICB reference only; not backdated onto historical RTT or DM01','validation':'Unique official provider keys; no forced hospital/trust/site equivalence'}
meta['ambiguous_provider_codes']=ambiguous
meta['validation']='Exact duplicate reference rows removed. Ambiguous provider-to-ICB mappings retained explicitly and prohibited from one-to-one enrichment; the file is reference-only.'
(ROOT/'data/reference/provider_mapping_metadata.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta,indent=2))
