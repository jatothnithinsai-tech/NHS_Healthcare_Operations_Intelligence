"""Inspect official publication links before designing source-specific parsers."""
from pathlib import Path
import json
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "reference"
OUT.mkdir(parents=True, exist_ok=True)
pages = {}
for year in ("2026-27", "2025-26", "2024-25", "2023-24"):
    pages[f"rtt_{year}"] = f"https://www.england.nhs.uk/statistics/statistical-work-areas/rtt-waiting-times/rtt-data-{year}/"
    pages[f"ae_{year}"] = f"https://www.england.nhs.uk/statistics/statistical-work-areas/ae-waiting-times-and-activity/ae-attendances-and-emergency-admissions-{year}/"
pages["diagnostics"] = "https://www.england.nhs.uk/statistics/statistical-work-areas/diagnostics-waiting-times-and-activity/monthly-diagnostics-waiting-times-and-activity/"
result = {}
for key, url in pages.items():
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    (OUT / f"{key}.html").write_bytes(response.content)
    soup = BeautifulSoup(response.content, "html.parser")
    main = soup.find("main") or soup
    links = [{"text": a.get_text(" ", strip=True), "url": urljoin(url, a["href"])} for a in main.find_all("a", href=True)]
    result[key] = {"page_url": url, "links": links, "text": main.get_text(" ", strip=True)}
    chosen = [x for x in links if any(t in x["url"].lower() for t in (".csv", ".zip", ".xlsx", ".xls"))]
    print(key, "bytes", len(response.content), "data_links", len(chosen))
    print(json.dumps(chosen[:8], indent=2))
(OUT / "publication_discovery.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
