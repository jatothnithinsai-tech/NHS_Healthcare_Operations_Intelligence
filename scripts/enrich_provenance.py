"""Retain official release documents; extract only explicit publication dates."""
from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
import hashlib
import json
import re
from bs4 import BeautifulSoup
from pypdf import PdfReader
from src.ingestion.acquire import ROOT, MONTHS, infer_month, session, revision_date_from_notice


def main():
    discovery=json.loads((ROOT/'data/reference/publication_discovery.json').read_text(encoding='utf-8'))
    manifest=json.loads((ROOT/'data/reference/source_manifest.json').read_text())
    pdfs={}
    for key,page in discovery.items():
        domain=key.split('_')[0]
        if domain not in ('rtt','ae','diagnostics'):
            continue
        for link in page['links']:
            label=link['text']
            if not link['url'].lower().endswith('.pdf'):
                continue
            selected=(domain=='rtt' and 'statistical press notice' in label.lower()) or (domain=='ae' and 'statistical commentary' in label.lower() and 'ecds' not in label.lower()) or (domain=='diagnostics' and 'report' in label.lower() and 'pre-release' not in label.lower())
            if not selected:
                continue
            try:
                month=infer_month(label,domain)
            except ValueError:
                continue
            pdfs[(domain,month)]=link
    out=ROOT/'data/reference/release_evidence'
    out.mkdir(parents=True,exist_ok=True)
    def work(source):
        if source.get('publication_date'):
            return source
        if source['dataset']=='rtt':
            page=next((p for p in discovery.values() if p.get('page_url')==source['page_url']),{})
            date=revision_date_from_notice(page.get('text',''),source['reporting_month'])
            if date:
                source['publication_date']=date
                source['publication_date_basis']='Explicit official publication-page revision notice covering this reporting-month range'
                return source
        link=pdfs.get((source['dataset'],source['reporting_month']))
        if not link:
            return source
        response=session().get(link['url'],timeout=90)
        response.raise_for_status()
        if not response.content.startswith(b'%PDF'):
            raise ValueError('Non-PDF release evidence')
        path=out/f"{source['dataset']}_{source['reporting_month']}.pdf"
        path.write_bytes(response.content)
        text='\n'.join(p.extract_text() or '' for p in PdfReader(BytesIO(response.content)).pages[:2])
        dates=[]
        for match in re.finditer(r'\b(\d{1,2})(?:st|nd|rd|th)?\s+('+'|'.join(MONTHS)+r')\s+(20\d{2})\b',text,re.I):
            date=f'{int(match[3]):04d}-{MONTHS[match[2].lower()]:02d}-{int(match[1]):02d}'
            # A date is accepted only with explicit publication/release context.
            context=text[max(0,match.start()-120):match.end()+40]
            if any(w in context.lower() for w in ['published','publication','released','release date']):
                dates.append((date,context.strip()))
        source['release_evidence_url']=link['url']
        source['release_evidence_sha256']=hashlib.sha256(response.content).hexdigest()
        source['release_evidence_path']=path.relative_to(ROOT).as_posix()
        if dates:
            source['publication_date']=dates[0][0]
            source['publication_date_basis']='Explicit date in official release document; original publication, revision edition date may differ'
            source['publication_date_evidence']=dates[0][1]
        return source
    with ThreadPoolExecutor(max_workers=4) as pool:
        manifest=list(pool.map(work,manifest))
    (ROOT/'data/reference/source_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    source_docs={
        'rtt_user_guidance':'https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/rtt-statistics-user-guidance/',
        'nhs_terms':'https://www.england.nhs.uk/contact-us/terms-and-conditions/',
        'diagnostic_definitions':'https://digital.nhs.uk/data-and-information/data-collections-and-data-sets/data-collections/diagnostics-waiting-times-and-activity-dm01',
    }
    for key,url in source_docs.items():
        response=session().get(url,timeout=60)
        response.raise_for_status()
        soup=BeautifulSoup(response.content,'html.parser')
        main=soup.find('main') or soup
        (ROOT/f'data/reference/{key}.txt').write_text(main.get_text(' ',strip=True),encoding='utf-8')
        if key=='nhs_terms':
            text=main.get_text(' ',strip=True)
            idx=text.lower().find('licen')
            print('Licence text:',text[max(0,idx-150):idx+900])
    print(json.dumps({'files':len(manifest),'verified_publication_dates':sum(bool(x.get('publication_date')) for x in manifest),'unverified':[(x['dataset'],x['reporting_month']) for x in manifest if not x.get('publication_date')]},indent=2))


if __name__=='__main__':
    main()
