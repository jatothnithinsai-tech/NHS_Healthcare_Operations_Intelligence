import json
from src.ingestion.acquire import ROOT
from src.transformation.parsers import parse

manifest = json.loads((ROOT / 'data/reference/source_manifest.json').read_text())
for domain in ('rtt', 'ae', 'diagnostics'):
    source = [x for x in manifest if x['dataset'] == domain][-1]
    frame, prof, issues = parse(source)
    print(domain, frame.shape, prof['source_control_waiting_or_activity'], issues[:3])
    print(frame.head(2).to_string(index=False))
