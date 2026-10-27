"""Discover official links, preserve revisions and capture SHA-256 provenance."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import re
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://www.england.nhs.uk/statistics/statistical-work-areas/"
LOGGER = logging.getLogger(__name__)
MONTHS = {name.lower(): i for i, name in enumerate(("", "January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December")) if name}


def session() -> requests.Session:
    s = requests.Session()
    retry = Retry(total=4, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.headers["User-Agent"] = "NHS-Operations-Portfolio/1.0 public-aggregate-data-research"
    return s


def infer_month(text: str, domain: str) -> str:
    """Use filename for DM01: publication has a confirmed erroneous link label."""
    if domain == "rtt":
        match = re.search(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{2})\b", text, re.I)
        if not match:
            raise ValueError(f"No reporting month in {text}")
        month = next(i for n, i in MONTHS.items() if n.startswith(match[1].lower()))
        year = 2000 + int(match[2])
    else:
        match = re.search(r"(" + "|".join(MONTHS) + r")[\s_-]+(20\d{2})", text, re.I)
        if not match:
            raise ValueError(f"No reporting month in {text}")
        month, year = MONTHS[match[1].lower()], int(match[2])
    return f"{year:04d}-{month:02d}-01"


def revision_date_from_notice(text: str, month: str) -> str | None:
    pattern = r"data for (\w+ \d{4}) to (\w+ \d{4}) was revised on (\d{1,2})(?:st|nd|rd|th)?\s+(\w+)\s+(\d{4})"
    for match in re.finditer(pattern,text,re.I):
        start,end = infer_month(match[1],"diagnostics"),infer_month(match[2],"diagnostics")
        if start<=month<=end and match[4].lower() in MONTHS:
            return f"{int(match[5]):04d}-{MONTHS[match[4].lower()]:02d}-{int(match[3]):02d}"
    return None


def discover(refresh: bool = True) -> list[dict]:
    config = json.loads((ROOT / "config/settings.json").read_text())
    ref = ROOT / "data/reference"
    ref.mkdir(parents=True, exist_ok=True)
    prior_file = ref / "publication_discovery.json"
    previous = json.loads(prior_file.read_text(encoding="utf-8")) if prior_file.exists() else {}
    catalog = []
    for domain in ("rtt", "ae", "diagnostics"):
        for year in config["source_years"]:
            key = f"{domain}_{year}"
            path = {"rtt": f"rtt-waiting-times/rtt-data-{year}/", "ae": f"ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-{year}/", "diagnostics": f"diagnostics-waiting-times-and-activity/monthly-diagnostics-waiting-times-and-activity/monthly-diagnostics-data-{year}/"}[domain]
            page = BASE + path
            if refresh or key not in previous:
                response = session().get(page, timeout=120)
                response.raise_for_status()
                if "verify that you're not a robot" in response.text:
                    raise RuntimeError(f"Official publication blocked by verification page: {page}")
                (ref / f"{key}.html").write_bytes(response.content)
                soup = BeautifulSoup(response.content, "html.parser")
                links = [{"text": a.get_text(" ", strip=True), "url": urljoin(page, a["href"])} for a in soup.find_all("a", href=True)]
                previous[key] = {"page_url": page, "links": links, "text": soup.get_text(" ", strip=True)}
            for link in previous[key]["links"]:
                text, url = link["text"], link["url"]
                selected = ((domain == "rtt" and "Full CSV data file" in text and url.endswith(".zip")) or (domain == "ae" and "Monthly A&E" in text and url.endswith(".csv")) or (domain == "diagnostics" and "CSV Extract" in text and "CDC" not in text and url.endswith(".zip")))
                if not selected:
                    continue
                month = infer_month(Path(urlparse(url).path).name if domain == "diagnostics" else text, domain)
                if month < config["analysis_start"]:
                    continue
                # An upload directory is not an exact publication date. Keep it separately.
                upload = re.search(r"/uploads/sites/2/(\d{4})/(\d{2})/", url)
                pub_date = None
                if domain == "rtt":
                    pub_date = revision_date_from_notice(previous[key]["text"],month)
                revision = re.search(r"[Rr]evised\s+(\d{2})\.(\d{2})\.(\d{2,4})", text)
                if revision:
                    y = int(revision[3]) + (2000 if len(revision[3]) == 2 else 0)
                    pub_date = f"{y:04d}-{revision[2]}-{revision[1]}"
                if month in ("2026-08-01", "2026-09-01") and year == "2026-27":
                    if domain != "ae" or month == "2026-09-01":
                        pub_date = "2026-10-08"
                catalog.append({"dataset": domain, "reporting_month": month, "url": url, "page_url": page, "label": text, "publication_date": pub_date, "publication_date_basis": "explicit publication/revision date" if pub_date else "unverified; consult release archive", "upload_month": "-".join(upload.groups()) if upload else None, "publisher_revision_label": "revis" in text.lower()})
    prior_file.write_text(json.dumps(previous, indent=2), encoding="utf-8")
    # Duplicate links occur in both the latest block and the month block.
    unique = {(x["dataset"], x["reporting_month"]): x for x in catalog}
    selected = []
    for domain in ("rtt", "ae", "diagnostics"):
        entries = sorted((x for x in unique.values() if x["dataset"] == domain), key=lambda x: x["reporting_month"])
        # Keep a shared start; preserve the newer A&E release too.
        selected.extend(entries)
    (ROOT / "config/source_catalog.json").write_text(json.dumps(selected, indent=2), encoding="utf-8")
    return selected


def download_one(source: dict, old: dict | None = None, check_remote: bool = True) -> dict:
    if old and not check_remote:
        p = ROOT / old["local_path"]
        if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == old["sha256"]:
            merged = {**old, **source, "download_status": "verified_local"}
            if old.get("publication_date") and not source.get("publication_date"):
                merged.update({k:v for k,v in old.items() if k.startswith("publication_date") or k.startswith("release_evidence")})
            return merged
        raise ValueError(f"Missing/corrupt retained file: {p}")
    if urlparse(source["url"]).hostname != "www.england.nhs.uk":
        raise ValueError("Download host is outside the configured official NHS publisher")
    headers = {}
    if old and old["url"] == source["url"]:
        if old.get("etag"):
            headers["If-None-Match"] = old["etag"]
        elif old.get("last_modified"):
            headers["If-Modified-Since"] = old["last_modified"]
    response = session().get(source["url"], timeout=120, headers=headers)
    if response.status_code == 304 and old:
        p = ROOT / old["local_path"]
        if p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == old["sha256"]:
            return {**old, **source, "download_status": "not_modified"}
        return download_one(source, None, True)
    response.raise_for_status()
    content = response.content
    suffix = Path(urlparse(source["url"]).path).suffix
    if not content or (suffix == ".zip" and not content.startswith(b"PK")) or b"<html" in content[:300].lower():
        raise ValueError(f"Invalid publication payload: {source['url']}")
    digest = hashlib.sha256(content).hexdigest()
    p = ROOT / "data/raw" / source["dataset"] / source["reporting_month"] / f"{digest}{suffix}"
    p.parent.mkdir(parents=True, exist_ok=True)
    if not p.exists():
        temp = p.with_suffix(p.suffix + ".tmp")
        temp.write_bytes(content)
        temp.replace(p)
    changed = bool(old and old["sha256"] != digest)
    LOGGER.info("source_acquired", extra={"dataset": source["dataset"], "month": source["reporting_month"], "revised": changed})
    return {**source, "sha256": digest, "bytes": len(content), "local_path": p.relative_to(ROOT).as_posix(), "retrieved_at": datetime.now(timezone.utc).isoformat(), "etag": response.headers.get("ETag"), "last_modified": response.headers.get("Last-Modified"), "download_status": "revised" if changed else ("unchanged" if old else "new"), "supersedes_sha256": old["sha256"] if changed else None}


def acquire(refresh: bool = False) -> list[dict]:
    manifest_path = ROOT / "data/reference/source_manifest.json"
    old_list = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    old = {(x["dataset"], x["reporting_month"]): x for x in old_list}
    sources = discover(refresh=refresh)
    def work(source):
        return download_one(source, old.get((source["dataset"], source["reporting_month"])), refresh or not old)
    with ThreadPoolExecutor(max_workers=4) as pool:
        manifest = list(pool.map(work, sources))
    history = ROOT / "data/reference/manifest_history"
    history.mkdir(exist_ok=True)
    if old_list != manifest:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
        (history / f"{stamp}.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    manifest = acquire(refresh=False)
    print(json.dumps({"files": len(manifest), "bytes": sum(x["bytes"] for x in manifest), "coverage": {d: [min(x["reporting_month"] for x in manifest if x["dataset"] == d), max(x["reporting_month"] for x in manifest if x["dataset"] == d)] for d in ("rtt", "ae", "diagnostics")}}, indent=2))
