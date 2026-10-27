from pathlib import Path
import json
import zipfile
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

root = Path(__file__).resolve().parents[1]
ref = root / "data/reference"
d = json.loads((ref / "publication_discovery.json").read_text(encoding="utf-8"))
base = d["diagnostics"]["page_url"]
for yr in ("2026-27", "2025-26", "2024-25"):
    url = base + f"monthly-diagnostics-data-{yr}/"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    (ref / f"diagnostics_{yr}.html").write_bytes(r.content)
    soup = BeautifulSoup(r.content, "html.parser")
    d[f"diagnostics_{yr}"] = {"page_url": url, "links": [{"text": a.get_text(" ", strip=True), "url": urljoin(url, a["href"])} for a in soup.find_all("a", href=True)], "text": soup.get_text(" ", strip=True)}
    print(yr, json.dumps([a for a in d[f"diagnostics_{yr}"]["links"] if any(e in a["url"].lower() for e in (".xls", ".csv", ".zip"))][:8], indent=2))
(ref / "publication_discovery.json").write_text(json.dumps(d, indent=2), encoding="utf-8")
samples = {
    "rtt": next(x for x in d["rtt_2026-27"]["links"] if "Full CSV" in x["text"]),
    "ae": next(x for x in d["ae_2026-27"]["links"] if "Monthly A&E" in x["text"] and ".csv" in x["url"]),
    "mapping": next(x for x in d["ae_2026-27"]["links"] if "System Mapping" in x["text"]),
}
for k, link in samples.items():
    r = requests.get(link["url"], timeout=120)
    r.raise_for_status()
    p = root / "data/raw/samples" / (k + Path(link["url"]).suffix)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(r.content)
    if p.suffix == ".zip":
        with zipfile.ZipFile(p) as z:
            print("ZIP", [(i.filename, i.file_size) for i in z.infolist()])
            for n in z.namelist()[:2]:
                print(n, z.read(n)[:4000].decode("cp1252", errors="replace"))
    elif p.suffix == ".csv":
        print(k, r.content[:5000].decode("cp1252", errors="replace"))
