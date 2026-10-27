"""Publish only the explicitly authorised repository; never print credentials."""
from __future__ import annotations
import argparse
import json
import os
import subprocess
import requests
from src.ingestion.acquire import ROOT

ACCOUNT = 'jatothnithinsai-tech'
REPO = 'NHS_Healthcare_Operations_Intelligence'
URL = f'https://github.com/{ACCOUNT}/{REPO}'


def git(*args, check=True):
    return subprocess.run(['git', *args],cwd=ROOT,text=True,capture_output=True,check=check)


def authenticate():
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0', GCM_INTERACTIVE='Never')
    result = subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\n\n',env=env,text=True,capture_output=True)
    if result.returncode:
        raise RuntimeError('GitHub sign-in required through Git Credential Manager; no credential found')
    fields = dict(line.split('=',1) for line in result.stdout.splitlines() if '=' in line)
    token = fields.get('password')
    if not token:
        raise RuntimeError('No GitHub credential available')
    s = requests.Session()
    s.headers.update({'Authorization':f'Bearer {token}','Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28'})
    user = s.get('https://api.github.com/user',timeout=30)
    user.raise_for_status()
    login = user.json()['login']
    if login.lower()!=ACCOUNT.lower():
        raise RuntimeError(f'Authenticated account {login} is not the authorised {ACCOUNT}; no changes made')
    return s,user.json()


def main(publish=False):
    s,user = authenticate()
    r = s.get(f'https://api.github.com/repos/{ACCOUNT}/{REPO}',timeout=30)
    if r.status_code not in (200,404):
        r.raise_for_status()
    exists = r.status_code==200
    status = {'authenticated_account':user['login'],'repository_exists':exists,'url':URL}
    if exists:
        status.update({'visibility':r.json()['visibility'],'default_branch':r.json()['default_branch'],'size_kb':r.json()['size']})
    print(json.dumps(status,indent=2))
    if not publish:
        return
    # Publication is permitted only after the explicit security gate exists and passes.
    audit = json.loads((ROOT/'reports/validation/security_review.json').read_text())
    if audit['status']!='PASS':
        raise RuntimeError('Security review is not passing')
    if not (ROOT/'.git').exists():
        git('init','-b','main')
    git('config','user.name',ACCOUNT)
    git('config','user.email',f'{user["id"]}+{ACCOUNT}@users.noreply.github.com')
    remote = f'{URL}.git'
    remotes = git('remote').stdout.split()
    if 'origin' in remotes and git('remote','get-url','origin').stdout.strip().rstrip('/')!=remote:
        raise RuntimeError('Existing origin differs; no remote changed')
    if exists:
        refs = git('ls-remote',remote).stdout.strip()
        if refs:
            # Never overwrite a populated remote without inspecting its history/content.
            raise RuntimeError('Remote already contains commits; inspect and integrate before publication')
    else:
        create=s.post('https://api.github.com/user/repos',json={'name':REPO,'description':'Reproducible NHS England operational analytics: Python, PostgreSQL, Excel and Power BI','private':False,'auto_init':False},timeout=30)
        create.raise_for_status()
    if 'origin' not in remotes:
        git('remote','add','origin',remote)
    git('add','.')
    git('commit','-m','Build validated NHS operations analytics and reporting portfolio')
    git('push','-u','origin','main')
    local=git('rev-parse','HEAD').stdout.strip()
    remote_sha=git('ls-remote','origin','refs/heads/main').stdout.split()[0]
    repo=s.get(f'https://api.github.com/repos/{ACCOUNT}/{REPO}',timeout=30)
    repo.raise_for_status()
    readme=requests.get(f'https://raw.githubusercontent.com/{ACCOUNT}/{REPO}/main/README.md',timeout=30)
    result={'url':URL,'local_commit':local,'remote_commit':remote_sha,'sha_match':local==remote_sha,'public':not repo.json()['private'],'readme_http_status':readme.status_code}
    tree=s.get(f'https://api.github.com/repos/{ACCOUNT}/{REPO}/git/trees/main?recursive=1',timeout=60)
    tree.raise_for_status()
    paths={x['path'] for x in tree.json()['tree']}
    required=['README.md','docs/architecture/ARCHITECTURE.md','docs/testing/FINAL_INDUSTRY_AUDIT.md','excel/NHS_Healthcare_Executive_Analysis.xlsx','powerbi/NHS_Healthcare_Operations_Intelligence.pbip','screenshots/01_executive.png','screenshots/02_rtt.png','screenshots/03_ae_diagnostics.png','screenshots/04_monitoring.png']
    result['required_public_artifacts']={p:p in paths for p in required}
    result['source_code_present']=any(p.startswith('src/') and p.endswith('.py') for p in paths)
    result['sql_analyses_present']=len([p for p in paths if p.startswith('sql/analytics/') and p.endswith('.sql')])
    if not result['sha_match'] or not result['public'] or readme.status_code!=200 or not all(result['required_public_artifacts'].values()):
        raise RuntimeError('Post-push public repository verification failed')
    (ROOT/'reports/validation/github_publication.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish',action='store_true')
    main(parser.parse_args().publish)
