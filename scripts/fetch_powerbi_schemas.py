"""Retain authoritative Microsoft JSON schemas for offline PBIR validation."""
import json
import requests
from urllib.parse import urljoin
from src.ingestion.acquire import ROOT

base = 'https://developer.microsoft.com/json-schemas/fabric/'
schemas = {
    'pbip': 'pbip/pbipProperties/1.0.0/schema.json',
    'pbir': 'item/report/definitionProperties/2.0.0/schema.json',
    'version': 'item/report/definition/versionMetadata/1.0.0/schema.json',
    'report': 'item/report/definition/report/3.0.0/schema.json',
    'pages': 'item/report/definition/pagesMetadata/1.0.0/schema.json',
    'page': 'item/report/definition/page/2.0.0/schema.json',
    'visual': 'item/report/definition/visualContainer/2.1.0/schema.json',
    'pbism': 'item/semanticModel/definitionProperties/1.0.0/schema.json',
}
out = ROOT / 'powerbi/schemas'
out.mkdir(parents=True, exist_ok=True)
queue = [base + p for p in schemas.values()]
for path in (ROOT/'powerbi/NHS_Healthcare.Report/definition').rglob('*.json'):
    value=json.loads(path.read_text(encoding='utf-8-sig'))
    schema_url=value.get('$schema')
    if schema_url and schema_url.startswith('https://developer.microsoft.com/json-schemas/fabric/'):
        queue.append(schema_url)
registry = {}
unavailable = []
while queue:
    url = queue.pop(0)
    if url in registry:
        continue
    r = requests.get(url, timeout=60)
    if r.status_code == 404:
        unavailable.append(url)
        registry[url] = None
        continue
    r.raise_for_status()
    data = r.json()
    registry[url] = data
    def refs(obj):
        if isinstance(obj, dict):
            for k,v in obj.items():
                if k == '$ref' and not v.startswith('#'):
                    queue.append(urljoin(url, v).split('#')[0])
                else:
                    refs(v)
        elif isinstance(obj,list):
            for x in obj:
                refs(x)
    refs(data)
(out / 'registry.json').write_text(json.dumps({k:v for k,v in registry.items() if v is not None}, indent=2), encoding='utf-8')
(out / 'unavailable_urls.json').write_text(json.dumps(unavailable,indent=2))
(out / 'urls.json').write_text(json.dumps({k:base+v for k,v in schemas.items()}, indent=2))
print('Downloaded',len(registry),'Microsoft JSON schemas')
