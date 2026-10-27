"""Augment early-version profiles from genuine processed records, not guesses."""
import hashlib
import json
import pandas as pd
from src.ingestion.acquire import ROOT

version=json.loads((ROOT/'config/settings.json').read_text())['parser_version']
manifest=json.loads((ROOT/'data/reference/source_manifest.json').read_text())
profiles=[]
for source in manifest:
    path=ROOT/'data/processed'/source['dataset']/f"{source['sha256']}-{version}.parquet"
    detail=json.loads(path.with_suffix('.profile.json').read_text())
    frame=pd.read_parquet(path)
    profile=detail['profile']
    profile['transformed_numeric_ranges']={c:{'min':int(frame[c].min()),'max':int(frame[c].max()),'missing':int(frame[c].isna().sum())} for c in frame.select_dtypes('number') if frame[c].notna().any()}
    profile['schema_sha256']=hashlib.sha256('|'.join(profile['columns']).encode()).hexdigest()
    path.with_suffix('.profile.json').write_text(json.dumps(detail,indent=2))
    profiles.append(profile)
(ROOT/'reports/validation/source_profiles.json').write_text(json.dumps(profiles,indent=2))
print('Completed transformed numeric-range and missing-count profiling for',len(profiles),'authentic files')
