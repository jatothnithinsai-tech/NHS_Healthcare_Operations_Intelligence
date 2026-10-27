from __future__ import annotations
import hashlib
import re
import zipfile
import pandas as pd
from src.cleaning.numeric import numeric, strict_sum
from src.ingestion.acquire import ROOT, infer_month
from src.profiling.profile import profile


def read_source(source: dict) -> pd.DataFrame:
    p = ROOT / source["local_path"]
    if hashlib.sha256(p.read_bytes()).hexdigest() != source["sha256"]:
        raise ValueError(f"Checksum mismatch: {p.name}")
    if p.suffix == ".zip":
        with zipfile.ZipFile(p) as z:
            members = [i for i in z.infolist() if i.filename.lower().endswith(".csv")]
            if len(members) != 1 or members[0].file_size > 600_000_000:
                raise ValueError("Unexpected archive layout or size")
            with z.open(members[0]) as f:
                frame = pd.read_csv(f, dtype="string", encoding="cp1252")
    else:
        frame = pd.read_csv(p, dtype="string", encoding="cp1252")
    frame.columns = frame.columns.str.strip()
    return frame


def aggregate(frame: pd.DataFrame, keys: list[str], counts: list[str]) -> pd.DataFrame:
    # A suppressed component makes the aggregate unknown, not a partial total.
    grouped = frame.groupby(keys, dropna=False, sort=False)
    result = grouped[counts].sum(min_count=1)
    result = result.mask(grouped[counts].count().lt(grouped.size(), axis=0))
    return result.reset_index()


def validate_period(frame: pd.DataFrame, source: dict) -> None:
    values = [x for x in frame["Period"].dropna().unique() if x.strip().upper() != "TOTAL"]
    months = {infer_month(x, "diagnostics" if source["dataset"] == "rtt" else source["dataset"]) for x in values}
    if months != {source["reporting_month"]}:
        raise ValueError(f"Publication month mismatch: {months} vs {source['reporting_month']}")


def parse(source: dict) -> tuple[pd.DataFrame, dict, list[dict]]:
    raw = read_source(source)
    validate_period(raw, source)
    prof = profile(raw, source)
    issues = []
    domain = source["dataset"]
    if domain == "rtt":
        frame = raw[raw["RTT Part Type"].isin(["Part_1A", "Part_1B", "Part_2"]) & raw["Commissioner Org Code"].ne("NONC").fillna(True)].copy()
        bands = [c for c in frame if re.match(r"Gt \d+", c)]
        if len(bands) != 105:
            raise ValueError(f"RTT schema change: {len(bands)} waiting bands")
        counts = bands + ["Total", "Patients with unknown clock start date", "Total All"]
        originally_blank = frame[bands].isna()
        frame[counts] = numeric(frame[counts])
        incomplete = frame["RTT Part Type"].eq("Part_2")
        source_total = frame["Total"].where(~incomplete, frame["Total All"])
        # For nonnegative counts, a blank is provably zero only when every
        # observed band already sums to the published total. Suppression tokens
        # and inconsistent/incomplete rows are never filled by this rule.
        recoverable = (frame[bands].sum(axis=1) == source_total) & ~(frame[bands].isna() & ~originally_blank).any(axis=1)
        recovered_cells = int((originally_blank.loc[recoverable]).sum().sum())
        frame.loc[recoverable, bands] = frame.loc[recoverable, bands].fillna(0)
        if recovered_cells:
            issues.append({"dataset": domain, "month": source["reporting_month"], "issue": "structural_blank_bands_proven_zero", "cells": recovered_cells, "handling": "Only blank cells whose nonnegative observed row counts already equal the official total are resolved to zero; explicit suppression tokens remain NULL."})
        frame["band_sum"] = strict_sum(frame, bands)
        # Total and unknown-start fields apply to completed pathways only.
        # Incomplete pathways report Total All; their denominator is the band sum.
        frame["waiting_count"] = frame["Total"].where(~incomplete, frame["band_sum"])
        frame["unknown_start"] = (frame["Total All"] - frame["Total"]).where(~incomplete)
        frame["total_all"] = frame["Total All"]
        for threshold in (18, 52, 65, 78, 104):
            frame[f"over_{threshold}"] = strict_sum(frame, bands[threshold:])
        frame["within_18"] = strict_sum(frame, bands[:18])
        bad = (frame["band_sum"] != frame["waiting_count"]) | ((frame["waiting_count"] + frame["unknown_start"] != frame["total_all"]) & ~incomplete) | ((frame["band_sum"] != frame["total_all"]) & incomplete)
        if bad.fillna(False).any():
            raise ValueError("RTT waiting band/total reconciliation failure")
        # C_999 duplicates all specialties; keep as a separate control only.
        control = frame.loc[frame["Treatment Function Code"] == "C_999", "waiting_count"].sum()
        frame = frame[frame["Treatment Function Code"] != "C_999"].copy()
        if frame["waiting_count"].sum() != control:
            raise ValueError("RTT detailed specialties disagree with source C_999 controls")
        frame = frame.rename(columns={"Provider Org Code": "provider_code", "Provider Org Name": "provider_name", "Provider Parent Org Code": "parent_code", "Provider Parent Name": "parent_name", "Treatment Function Code": "specialty_code", "Treatment Function Name": "specialty_name", "RTT Part Type": "pathway_type"})
        keys = ["provider_code", "provider_name", "parent_code", "parent_name", "specialty_code", "specialty_name", "pathway_type"]
        measures = ["waiting_count", "total_all", "unknown_start", "within_18", "over_18", "over_52", "over_65", "over_78", "over_104"]
        output = aggregate(frame, keys, measures)
    elif domain == "diagnostics":
        bands = [c for c in raw if re.match(r"\d\d < \d\d Week|13\+ Weeks", c)]
        if len(bands) != 14:
            raise ValueError("Diagnostic waiting-band schema changed")
        counts = bands + ["Total WL", "Waiting List Activity", "Planned Activity", "Unscheduled Activity", "Total Activity"]
        frame = raw.copy()
        frame[counts] = numeric(frame[counts])
        frame["waiting_count"] = frame["Total WL"]
        frame["over_6"] = strict_sum(frame, bands[6:])
        frame["over_13"] = frame["13+ Weeks"]
        frame["total_activity"] = frame["Total Activity"]
        frame["waiting_activity"] = frame["Waiting List Activity"]
        frame["planned_activity"] = frame["Planned Activity"]
        frame["unscheduled_activity"] = frame["Unscheduled Activity"]
        if (strict_sum(frame, bands) != frame["waiting_count"]).fillna(False).any():
            raise ValueError("Diagnostic waiting bands do not reconcile")
        if (strict_sum(frame, ["Waiting List Activity", "Planned Activity", "Unscheduled Activity"]) != frame["total_activity"]).fillna(False).any():
            raise ValueError("Diagnostic activity components do not reconcile")
        control = frame.loc[frame["Diagnostic Tests"] == "TOTAL", "waiting_count"].sum()
        frame = frame[frame["Diagnostic Tests"] != "TOTAL"].copy()
        if frame["waiting_count"].sum() != control:
            raise ValueError("Diagnostic test categories disagree with TOTAL controls")
        frame = frame.rename(columns={"Provider Org Code": "provider_code", "Provider Org Name": "provider_name", "Provider Parent Org Code": "parent_code", "Provider Parent Name": "parent_name", "Diagnostic Tests Sort Order": "test_code", "Diagnostic Tests": "test_name"})
        keys = ["provider_code", "provider_name", "parent_code", "parent_name", "test_code", "test_name"]
        measures = ["waiting_count", "over_6", "over_13", "total_activity", "waiting_activity", "planned_activity", "unscheduled_activity"]
        output = aggregate(frame, keys, measures)
    else:
        frame = raw[raw["Org Code"].str.strip().str.upper() != "TOTAL"].copy()
        counts = [c for c in raw if c.startswith(("A&E attendances", "Attendances over 4hrs", "Emergency admissions via A&E")) or c in ["Patients who have waited 4-12 hs from DTA to admission", "Patients who have waited 12+ hrs from DTA to admission", "Other emergency admissions"]]
        extra = [c for c in raw.columns[4:] if c not in counts]
        if any(raw[c].notna().any() for c in extra):
            raise ValueError(f"Unrecognised nonempty A&E source columns: {extra}")
        if extra:
            issues.append({"dataset":domain,"month":source["reporting_month"],"issue":"empty_trailing_csv_columns","columns":extra,"handling":"Profiled and ignored only after proving every cell is empty; named measure columns remain strict."})
        frame[counts] = numeric(frame[counts])
        attendance = [c for c in counts if c.startswith("A&E attendances")]
        breaches = [c for c in counts if c.startswith("Attendances over 4hrs")]
        admissions = [c for c in counts if c.startswith("Emergency admissions via A&E")]
        if len(attendance) != 6 or len(breaches) != 6 or len(admissions) != 3:
            raise ValueError("A&E schema changed")
        frame["attendances"] = strict_sum(frame, attendance)
        frame["over_4"] = strict_sum(frame, breaches)
        frame["within_4"] = frame["attendances"] - frame["over_4"]
        frame["type1_attendances"] = strict_sum(frame, [c for c in attendance if c.endswith("Type 1")])
        frame["type1_over_4"] = strict_sum(frame, [c for c in breaches if c.endswith("Type 1")])
        frame["admissions_via_ae"] = strict_sum(frame, admissions)
        frame["other_admissions"] = frame["Other emergency admissions"]
        frame["emergency_admissions"] = frame["admissions_via_ae"] + frame["other_admissions"]
        frame["dta_4_12"] = frame["Patients who have waited 4-12 hs from DTA to admission"]
        frame["dta_12_plus"] = frame["Patients who have waited 12+ hrs from DTA to admission"]
        control = numeric(raw.loc[raw["Org Code"].str.strip().str.upper() == "TOTAL", counts])
        for c in counts:
            if len(control) != 1 or frame[c].sum(min_count=len(frame)) != control.iloc[0][c]:
                raise ValueError(f"A&E national control does not reconcile: {c}")
        frame = frame.rename(columns={"Org Code": "provider_code", "Org name": "provider_name", "Parent Org": "region_name"})
        frame["region_name"] = frame["region_name"].str.strip()
        keys = ["provider_code", "provider_name", "region_name"]
        measures = ["attendances", "over_4", "within_4", "type1_attendances", "type1_over_4", "admissions_via_ae", "other_admissions", "emergency_admissions", "dta_4_12", "dta_12_plus"]
        output = frame[keys + measures].copy()
    output.insert(0, "month", source["reporting_month"])
    output["source_sha256"] = source["sha256"]
    applicable = [x for x in measures if not (domain == "rtt" and x == "unknown_start")]
    missing = output[applicable].isna().sum().sum()
    if missing:
        issues.append({"dataset": domain, "month": source["reporting_month"], "issue": "missing_or_suppressed_counts", "cells": int(missing), "handling": "retained NULL; completeness required for aggregation"})
    missing_names = output["provider_name"].isna().sum()
    if missing_names:
        issues.append({"dataset": domain, "month": source["reporting_month"], "issue": "missing_provider_names", "rows": int(missing_names), "handling": "retain code; do not invent organisation identity"})
    prof.update({"transformed_rows": len(output), "source_control_waiting_or_activity": int(output["attendances" if domain == "ae" else "waiting_count"].sum()), "numeric_missing_cells": int(missing), "transformed_numeric_ranges": {c:{"min":int(output[c].min()),"max":int(output[c].max())} for c in measures if output[c].notna().any()}, "schema_sha256": hashlib.sha256("|".join(raw.columns).encode()).hexdigest(), "service_codes": sorted(output["specialty_code" if domain=="rtt" else "test_code"].dropna().unique().tolist()) if domain!='ae' else []})
    return output, prof, issues
