"""Review actual publication candidates and record concrete public-data controls."""
from __future__ import annotations
import json
import re
import subprocess
import zipfile
from src.ingestion.acquire import ROOT


def review():
    result=subprocess.run(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True,capture_output=True,check=True)
    candidates=sorted(set(result.stdout.splitlines()))
    findings=[]
    secret_patterns=[r'gh[pousr]_[A-Za-z0-9]{30,}',r'github_pat_[A-Za-z0-9_]{30,}',r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',r'AKIA[0-9A-Z]{16}']
    sensitive_columns=['nhs_number','patient_name','patient_id','date_of_birth','home_address']
    total=0
    for rel in candidates:
        path=ROOT/rel
        if not path.is_file():
            continue
        total+=path.stat().st_size
        if path.stat().st_size>=95*1024*1024:
            findings.append({'path':rel,'issue':'Near or beyond GitHub individual-file limit'})
        if rel=='.env' or rel.startswith(('.venv/','.local/','data/raw/','logs/')):
            findings.append({'path':rel,'issue':'Excluded local/private artifact included in candidate set'})
        if path.suffix.lower() in ['.py','.ps1','.md','.json','.sql','.toml','.yml','.csv','.tmdl','.pbip','.pbir','.pbism']:
            text=path.read_text(encoding='utf-8-sig',errors='replace')
            for pattern in secret_patterns:
                if re.search(pattern,text):
                    findings.append({'path':rel,'issue':'Potential credential/private key pattern'})
            if path.suffix.lower()=='.csv':
                header=text.splitlines()[0].lower() if text else ''
                for name in sensitive_columns:
                    if name in header:
                        findings.append({'path':rel,'issue':'Patient-level identifier column'})
        if path.suffix.lower()=='.xlsx':
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    if name.endswith('.xml'):
                        text=archive.read(name).decode('utf-8',errors='replace')
                        if any(re.search(pattern,text) for pattern in secret_patterns):
                            findings.append({'path':rel,'issue':'Potential embedded credential'})
    evidence={'status':'PASS' if not findings else 'FAIL','candidate_files':len(candidates),'candidate_bytes':total,'findings':findings,'scope':'Git candidates; token/private-key patterns, ignored artifact leakage, patient identifier columns, workbook XML, file sizes','data_classification':'Published NHS provider/commissioner/specialty/test aggregates only; no patient records','attribution':'Official NHS terms verified as Open Government Licence reuse with exclusions; see docs/DATA_ATTRIBUTION.md','limitations':'Pattern scans are not a formal security certification; manually reviewed source definitions and publication scope remain necessary'}
    (ROOT/'reports/validation/security_review.json').write_text(json.dumps(evidence,indent=2))
    print(json.dumps(evidence,indent=2))
    if findings:
        raise ValueError('Publication candidates failed security review')


if __name__=='__main__':
    review()
