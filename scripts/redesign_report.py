"""Apply the portfolio presentation to the existing report; data models and queries stay intact."""

from pathlib import Path
import json

BG = "#F6F8FC"
INK = "#263445"
MUTED = "#56687A"
WHITE = "#FFFFFF"
LINE = "#DEE5EE"
BLUE = "#2563A6"
TEAL = "#087F75"
CORAL = "#C9513E"
AMBER = "#A56C16"
PURPLE = "#7664BF"


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def write(p, d):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def lit(v):
    s = (
        str(v).lower()
        if isinstance(v, bool)
        else str(v) + "D"
        if isinstance(v, (float, int))
        else "'" + str(v).replace("'", "''") + "'"
    )
    return {"expr": {"Literal": {"Value": s}}}


def color(v):
    return {"solid": {"color": lit(v)}}


def obj(d, k, props):
    d.setdefault(k, [{"properties": {}}])[0].setdefault("properties", {}).update(props)


def rect(v, x, y, w, h):
    v["position"].update(x=x, y=y, width=w, height=h)


def title(v, text):
    obj(v["visual"].setdefault("visualContainerObjects", {}), "title", {"text": lit(text)})


def text(v, content, size=18, c=INK, bold=False):
    obj(
        v["visual"].setdefault("objects", {}),
        "general",
        {
            "paragraphs": [
                {
                    "textRuns": [
                        {
                            "value": content,
                            "textStyle": {
                                "fontFamily": "Segoe UI",
                                "fontSize": f"{size}px",
                                "color": c,
                                "fontWeight": "bold" if bold else "normal",
                            },
                        }
                    ]
                }
            ]
        },
    )


def props(v):
    return v["visual"].setdefault("objects", {})


def style(v, accent=BLUE, tint=None):
    cfg = v["visual"]
    typ = cfg["visualType"]
    vc = cfg.setdefault("visualContainerObjects", {})
    o = cfg.setdefault("objects", {})
    obj(
        vc,
        "title",
        {"fontColor": color(INK), "fontSize": lit(14), "fontFamily": lit("Segoe UI Semibold"), "bold": lit(True)},
    )
    obj(vc, "subTitle", {"fontColor": color(MUTED), "fontSize": lit(10)}) if "subTitle" in vc else None
    obj(vc, "background", {"show": lit(typ != "textbox"), "color": color(tint or WHITE), "transparency": lit(0)})
    obj(vc, "border", {"show": lit(typ != "textbox"), "color": color(LINE), "radius": lit(10)})

    # Replace previous dark-mode literal colours throughout visual formatting, without touching query bindings.
    def walk(x):
        if isinstance(x, dict):
            for k, val in x.items():
                if k == "Value" and isinstance(val, str):
                    swap = {
                        "'#F1F6FC'": f"'{INK}'",
                        "'#AFC0D5'": f"'{MUTED}'",
                        "'#112239'": f"'{WHITE}'",
                        "'#263D57'": f"'{LINE}'",
                    }
                    if val in swap:
                        x[k] = swap[val]
                elif isinstance(val, (dict, list)):
                    walk(val)
        elif isinstance(x, list):
            for val in x:
                walk(val)

    walk(o)
    if typ == "card":
        obj(
            o,
            "labels",
            {
                "color": color(accent),
                "fontSize": lit(30),
                "fontFamily": lit("Segoe UI Semibold"),
                "labelDisplayUnits": lit(1),
            },
        )
        obj(o, "categoryLabels", {"show": lit(False)})
    elif typ == "slicer":
        obj(o, "data", {"mode": lit("Dropdown")})
        obj(o, "items", {"fontColor": color(INK), "background": color(WHITE), "textSize": lit(12)})
        obj(o, "header", {"show": lit(False)})
    elif typ in ["lineChart", "barChart", "clusteredBarChart", "clusteredColumnChart"]:
        obj(o, "dataPoint", {"defaultColor": color(accent)})
        if len(cfg.get("query", {}).get("queryState", {}).get("Y", {}).get("projections", [])) > 1:
            o["dataPoint"][0]["properties"].pop("defaultColor", None)
        obj(o, "categoryAxis", {"labelColor": color(MUTED), "fontSize": lit(11), "showAxisTitle": lit(False)})
        obj(
            o,
            "valueAxis",
            {
                "labelColor": color(MUTED),
                "fontSize": lit(10),
                "showAxisTitle": lit(False),
                "gridlineColor": color(LINE),
                "gridlineTransparency": lit(30),
            },
        )
        obj(o, "legend", {"labelColor": color(MUTED), "fontSize": lit(11)})
        if "labels" in o:
            obj(o, "labels", {"color": color(INK), "fontSize": lit(11)})
    elif typ in ["tableEx", "pivotTable"]:
        obj(
            o,
            "columnHeaders",
            {
                "fontColor": color(WHITE),
                "backColor": color(accent),
                "fontSize": lit(11),
                "bold": lit(True),
                "autoSizeColumnWidth": lit(True),
                "columnAdjustment": lit("growToFit"),
            },
        )
        obj(
            o,
            "values",
            {
                "fontColorPrimary": color(INK),
                "backColorPrimary": color(WHITE),
                "fontColorSecondary": color(INK),
                "backColorSecondary": color("#F0F4FA"),
                "fontSize": lit(12),
            },
        )
        obj(
            o,
            "grid",
            {
                "gridVertical": lit(False),
                "gridHorizontal": lit(True),
                "gridHorizontalColor": color(LINE),
                "rowPadding": lit(5),
            },
        )


def theme(report, name, palette):
    f = report / "definition/report.json"
    d = read(f)
    d["$schema"] = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json"
    d.setdefault("settings", {})["locale"] = "en-GB"
    d.setdefault("themeCollection", {})["customTheme"] = {
        "name": name,
        "type": "RegisteredResources",
        "reportVersionAtImport": {"visual": "2.1.0", "report": "3.0.0", "page": "2.0.0"},
    }
    pkgs = d.setdefault("resourcePackages", [])
    pkg = next((p for p in pkgs if p["name"] == "RegisteredResources"), None)
    if pkg is None:
        pkg = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        pkgs.append(pkg)
    pkg["items"] = [i for i in pkg["items"] if i.get("type") != "CustomTheme"] + [
        {"name": name, "path": name + ".json", "type": "CustomTheme"}
    ]
    write(
        report / "StaticResources/RegisteredResources" / f"{name}.json",
        {
            "name": name,
            "dataColors": palette,
            "background": BG,
            "foreground": INK,
            "tableAccent": palette[0],
            "good": TEAL,
            "neutral": "#C48B25",
            "bad": CORAL,
            "textClasses": {
                "title": {"fontFace": "Segoe UI Semibold", "color": INK},
                "label": {"fontFace": "Segoe UI", "color": MUTED},
                "callout": {"fontFace": "Segoe UI Semibold", "color": INK},
            },
        },
    )
    write(f, d)


def report_pages(report):
    return sorted((report / "definition/pages").glob("*/page.json"))


def load_page(f):
    pg = read(f)
    vs = {x.parent.name: read(x) for x in sorted((f.parent / "visuals").glob("*/visual.json"))}
    return pg, vs


def save_page(f, pg, vs):
    write(f, pg)
    for k, v in vs.items():
        write(f.parent / "visuals" / k / "visual.json", v)


def page_bg(pg, w, h):
    pg.update(width=w, height=h, displayOption="FitToPage")
    obj(pg.setdefault("objects", {}), "background", {"color": color(BG), "transparency": lit(0)})


def textbox(ref, name, content, box, size=18, c=MUTED, bold=False):
    v = {
        "$schema": ref,
        "name": name,
        "position": dict(zip(["x", "y", "width", "height"], box)) | {"z": 90, "tabOrder": 90},
        "visual": {
            "visualType": "textbox",
            "visualContainerObjects": {"title": [{"properties": {"show": lit(False)}}]},
        },
    }
    style(v)
    text(v, content, size, c, bold)
    return v


def redesign(base):
    target = Path(base)
    report = next(target.glob("*.Report"))
    for f in report_pages(report):
        pg, vs = load_page(f)
        page_bg(pg, 1600, 900)
        key = pg["name"]
        for k, v in vs.items():
            style(v, BLUE)
        headings = {
            "Executive": "Healthcare performance",
            "RTT": "Waiting list intelligence",
            "UrgentDiagnostics": "Urgent care & diagnostics",
            "Monitoring": "Data quality & operational monitoring",
        }
        text(vs["page_title"], headings[key], 32, INK, True)
        rect(vs["page_title"], 32, 18, 1536, 62)
        rect(vs["date_filter"], 32, 88, 298, 66)
        rect(vs["provider_filter"], 350, 88, 420, 66)
        rect(vs["context_note"], 794, 88, 774, 66)
        # Keep source/publication caveats verbatim; only make them readable.
        for para in props(vs["context_note"])["general"][0]["properties"]["paragraphs"]:
            for run in para["textRuns"]:
                run["textStyle"].update(fontSize="16px", color=MUTED)
        for i in range(4):
            v = vs[f"kpi_{i}"]
            rect(v, 32 + i * 388, 182, 372, 112)
            style(v, [BLUE, TEAL, CORAL, PURPLE][i], ["#EDF3FC", "#EAF6F2", "#FCF0EB", "#F2F0FA"][i])
        maps = {
            "Executive": {
                "rtt_trend": (32, 324, 758, 302),
                "ae_trend": (810, 324, 758, 302),
                "provider_summary": (32, 650, 1536, 218),
            },
            "RTT": {
                "specialty": (32, 324, 758, 302),
                "long_wait_trend": (810, 324, 758, 302),
                "provider_detail": (32, 650, 1536, 218),
            },
            "UrgentDiagnostics": {
                "ae_activity": (32, 324, 758, 302),
                "diagnostic_test": (810, 324, 758, 302),
                "selected_provider": (32, 650, 1536, 218),
            },
            "Monitoring": {
                "monitor_0": (32, 314, 372, 92),
                "monitor_1": (420, 314, 372, 92),
                "monitor_2": (808, 314, 372, 92),
                "monitor_3": (1196, 314, 372, 92),
                "source_dates": (32, 430, 936, 174),
                "coverage_checks": (988, 430, 580, 174),
                "pipeline_runs": (32, 626, 1536, 162),
                "quality_note": (32, 810, 1536, 58),
            },
        }
        for k, box in maps[key].items():
            rect(vs[k], *box)
        labels = {
            "rtt_trend": "Waiting pathways by reporting month",
            "ae_trend": "A&E attendances within four hours",
            "provider_summary": "Provider overview | latest month in the selected period",
            "specialty": "Pathways waiting over 52 weeks by specialty",
            "long_wait_trend": "Long waits over time | thresholds overlap",
            "provider_detail": "Provider investigation | drillthrough target",
            "ae_activity": "A&E attendances & emergency admissions",
            "diagnostic_test": "Diagnostic waits of six weeks or more | latest selected month",
            "selected_provider": "Provider comparisons | separate metric populations",
            "source_dates": "Source reporting periods & publication dates",
            "coverage_checks": "Coverage & validation checks",
            "pipeline_runs": "Pipeline execution history | full timestamps",
        }
        for k, v in vs.items():
            if k in labels:
                title(v, labels[k])
        # Order comparisons by their displayed measure; show recent monitoring records first.
        sorts = {
            "specialty": ("RTT Over52 Latest", "Measure"),
            "diagnostic_test": ("Diagnostic Over6 Latest", "Measure"),
            "provider_summary": ("RTT Over52 Latest", "Measure"),
            "provider_detail": ("RTT Over52 Latest", "Measure"),
            "pipeline_runs": ("started_at", "Column"),
            "source_dates": ("month", "Column"),
        }
        for k, (prop, kind) in sorts.items():
            if k not in vs:
                continue
            query = vs[k]["visual"]["query"]
            fields = [p["field"] for role in query["queryState"].values() for p in role.get("projections", [])]
            field = next(f for f in fields if kind in f and f[kind]["Property"] == prop)
            query["sortDefinition"] = {"sort": [{"field": field, "direction": "Descending"}], "isDefaultSort": False}
        for k in ["ae_trend", "long_wait_trend", "diagnostic_test"]:
            if k in vs:
                style(vs[k], CORAL if k != "ae_trend" else TEAL)
        if key == "Monitoring":
            for i in range(4):
                style(vs[f"monitor_{i}"], [BLUE, TEAL, AMBER, TEAL][i])
                obj(props(vs["monitor_3"]), "labels", {"fontSize": lit(26)})
            obj(props(vs["kpi_3"]), "labels", {"fontSize": lit(21)})
        save_page(f, pg, vs)
    theme(report, "NHS_Operations", [BLUE, TEAL, CORAL, PURPLE, "#C48B25"])
    return target


if __name__ == "__main__":
    redesign(Path(__file__).resolve().parents[1] / "powerbi")
