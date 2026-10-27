"""Acquire Microsoft's public TOM validator; keep dependencies local and ignored."""
from io import BytesIO
import hashlib
import json
import zipfile
import requests
from src.ingestion.acquire import ROOT

base='https://api.nuget.org/v3-flatcontainer/microsoft.analysisservices.retail.amd64/'
r=requests.get(base+'index.json',timeout=60)
r.raise_for_status()
versions=[v for v in r.json()['versions'] if '-' not in v]
version=versions[-1]
url=base+version+'/microsoft.analysisservices.retail.amd64.'+version+'.nupkg'
r=requests.get(url,timeout=120)
r.raise_for_status()
out=ROOT/'.local/tom'
out.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(BytesIO(r.content)) as z:
    dlls=[n for n in z.namelist() if n.endswith('.dll') and n.startswith('lib/')]
    frameworks=sorted({n.split('/')[1] for n in dlls})
    preferred=next((x for x in ['net48','net472','net45','net40'] if x in frameworks),frameworks[0])
    for n in dlls:
        if n.split('/')[1]==preferred and len(n.split('/'))==3:
            (out/n.split('/')[-1]).write_bytes(z.read(n))
meta={'publisher':'Microsoft','package':'Microsoft.AnalysisServices.retail.amd64','version':version,'framework':preferred,'url':url,'sha256':hashlib.sha256(r.content).hexdigest(),'installed_libraries':[p.name for p in out.glob('*.dll')]}
(ROOT/'reports/validation/tom_dependency.json').write_text(json.dumps(meta,indent=2))
print(json.dumps(meta,indent=2))
