#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, re
from collections import defaultdict
from typing import Any, Dict, List, Tuple

FEATURES: Dict[str, List[str]] = {
    "QuickSnap_Instants": [
        "ig_ios_quick_snap", "ig_ios_quicksnap", "ig_ios_instants",
        "ig_quick_snap_show_peek_in_view_did_appear", "ig_instants_hide",
        "isQuicksnapEnabled:", "isQuicksnapEnabledInInbox:", "isQuicksnapEnabledAsPeek:",
        "isQPEnabled:", "_isEligibleForQuicksnapCornerStackTransitionDialog",
        "IGQuickSnapExperimentationHelper", "IGNotesTrayController",
    ],
    "FriendMap_Maps": [
        "ig_test_sessioned_mc_ig_notes_friend_map_enabled", "ig_friend_map_location_update",
        "ig_ios_friend_map", "ig_ios_friendmap", "ig_ios_friends_map", "ig_ios_friend_lane",
        "IGDirectNotesExperimentHelper", "DirectNotesExperimentHelper",
    ],
    "Icebreaker": [
        "ig_ios_notes_icebreakers", "ctd_in_thread_icebreakers_ios_mc",
        "biig_icebreaker_completeness_upsell_mc", "igd_ios_default_icebreakers_in_faq_settings",
        "ig_default_icebreaker_appointment", "IGDirectMutualInterestFeatureGatingService",
        "Icebreaker", "icebreaker",
    ],
    "Story_Tray": [
        "ig_ios_stories_tray", "ig_ios_story_tray", "ig_story_tray",
        "ig_ios_stories_in_view_nav_tray", "ig_empty_story_tray_su_redesign",
        "story_tray", "stories_tray", "isStoriesFetchHandledIndependently",
        "isDynamicTabStoryGridEnabled", "isVerticalStoriesTray",
    ],
    "DM_Inline_Like": ["dm_inline_like", "direct_inline_like", "inline_like"],
}

MC_PREFIXES = (
    "_ig_", "_ctd_", "_biig_", "_igd_", "_mwb_", "_mwa_", "_msgc_", "_mci_",
)


def load_json(path: str, fallback: Any) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return fallback


def first8_to_u64(first8: str | None) -> int | None:
    if not first8:
        return None
    clean = first8.replace(" ", "").replace("0x", "")
    if len(clean) < 16:
        return None
    try:
        return int.from_bytes(bytes.fromhex(clean[:16]), "little")
    except Exception:
        return None


def is_mc_param(rec: Dict[str, Any]) -> bool:
    text = str(rec.get("text") or rec.get("name") or "")
    section = str(rec.get("section") or "")
    return text.startswith(MC_PREFIXES) and "__const" in section


def rel_binary_name(report_root: str, path: str) -> str:
    d = os.path.dirname(path)
    rel = os.path.relpath(d, report_root)
    if rel == ".":
        return "root"
    return rel


def collect_report(report_root: str) -> Tuple[List[Dict[str, Any]], Dict[str, List[Dict[str, Any]]]]:
    records: List[Dict[str, Any]] = []
    by_binary: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for root, _dirs, files in os.walk(report_root):
        if "target_matches.json" not in files:
            continue
        path = os.path.join(root, "target_matches.json")
        binary_key = rel_binary_name(report_root, path)
        arr = load_json(path, [])
        if not isinstance(arr, list):
            continue
        for rec in arr:
            if not isinstance(rec, dict):
                continue
            r = dict(rec)
            r["binary_report"] = binary_key
            text = str(r.get("text") or r.get("name") or "")
            r["normalized_text"] = text
            if is_mc_param(r):
                stable = first8_to_u64(r.get("first_8_bytes") or r.get("first8"))
                if stable is not None:
                    r["mc_stable_id_hex"] = f"0x{stable:016x}"
                    r["mc_stable_id_normalized_hex"] = f"0x{(stable & 0x00ffffffffffffff):014x}"
            records.append(r)
            by_binary[binary_key].append(r)
    return records, by_binary


def feature_for_record(rec: Dict[str, Any]) -> Tuple[str, str] | None:
    text = str(rec.get("normalized_text") or "")
    pattern = str(rec.get("pattern") or "")
    hay = f"{text}\n{pattern}"
    for group, pats in FEATURES.items():
        for p in pats:
            if p and p in hay:
                return group, p
    return None


def summarize(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    grouped: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    for rec in records:
        fp = feature_for_record(rec)
        if not fp:
            continue
        group, pat = fp
        grouped[group][pat].append(rec)

    for group, pats in FEATURES.items():
        g: Dict[str, Any] = {
            "requested_patterns": len(pats),
            "patterns_present_anywhere": 0,
            "patterns_present_in_main": 0,
            "patterns_present_in_frameworks": 0,
            "mc_params": [],
            "objc_or_swift_methods": [],
            "patterns": {},
        }
        for pat in pats:
            recs = grouped[group].get(pat, [])
            binaries = sorted({r.get("binary_report", "") for r in recs})
            present_main = any(str(b).startswith("main") for b in binaries)
            present_fw = any(str(b).startswith("frameworks") for b in binaries)
            if recs:
                g["patterns_present_anywhere"] += 1
            if present_main:
                g["patterns_present_in_main"] += 1
            if present_fw:
                g["patterns_present_in_frameworks"] += 1
            mc = [r for r in recs if "mc_stable_id_hex" in r]
            meth = [r for r in recs if r.get("kind") in ("objc_selector_string", "objc_selref") or "TtC" in str(r.get("text")) or str(r.get("text", "")).startswith("_OBJC_CLASS_$_")]
            for r in mc:
                item = {k: r.get(k) for k in ("text", "binary_report", "vmaddr", "fileoff", "section", "first_8_bytes", "mc_stable_id_hex", "mc_stable_id_normalized_hex")}
                if item not in g["mc_params"]:
                    g["mc_params"].append(item)
            for r in meth:
                item = {k: r.get(k) for k in ("text", "kind", "binary_report", "vmaddr", "fileoff", "section")}
                if item not in g["objc_or_swift_methods"]:
                    g["objc_or_swift_methods"].append(item)
            g["patterns"][pat] = {
                "matches": len(recs),
                "binaries": binaries,
                "present_in_main": present_main,
                "present_in_frameworks": present_fw,
                "sample": [{k: r.get(k) for k in ("text", "kind", "binary_report", "vmaddr", "fileoff", "section", "mc_stable_id_hex")} for r in recs[:8]],
            }
        if g["patterns_present_anywhere"] == 0:
            verdict = "not_found_in_scanned_binaries"
        elif g["patterns_present_in_main"] and g["patterns_present_in_frameworks"]:
            verdict = "split_between_main_and_frameworks"
        elif g["patterns_present_in_main"]:
            verdict = "main_executable_required"
        elif g["patterns_present_in_frameworks"]:
            verdict = "framework_evidence_only_need_main_for_callers"
        else:
            verdict = "present_without_role_classification"
        g["verdict"] = verdict
        out[group] = g
    return out


def write_md(path: str, summary: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("# Cross-Binary Feature Gap Report\n\n")
        f.write("This report prevents false negatives caused by analyzing only one framework. A feature can have MobileConfig param symbols in `FBSharedFramework` while helper classes/selectors live in the main Instagram executable.\n\n")
        f.write("| Feature | Verdict | Present anywhere | Present in main | Present in frameworks | MC params decoded | ObjC/Swift anchors |\n")
        f.write("|---|---|---:|---:|---:|---:|---:|\n")
        for group, g in summary.items():
            f.write(f"| `{group}` | `{g['verdict']}` | {g['patterns_present_anywhere']} | {g['patterns_present_in_main']} | {g['patterns_present_in_frameworks']} | {len(g['mc_params'])} | {len(g['objc_or_swift_methods'])} |\n")
        for group, g in summary.items():
            f.write(f"\n## {group}\n\n")
            f.write(f"Verdict: `{g['verdict']}`\n\n")
            if g["mc_params"]:
                f.write("### Decoded MC params\n\n")
                f.write("| Name | Binary | Fileoff | VMAddr | Stable ID | Normalized |\n|---|---|---:|---:|---:|---:|\n")
                for r in g["mc_params"][:80]:
                    f.write(f"| `{r.get('text','')}` | `{r.get('binary_report','')}` | `{r.get('fileoff','')}` | `{r.get('vmaddr','')}` | `{r.get('mc_stable_id_hex','')}` | `{r.get('mc_stable_id_normalized_hex','')}` |\n")
            if g["objc_or_swift_methods"]:
                f.write("\n### ObjC/Swift anchors\n\n")
                f.write("| Text | Kind | Binary | Fileoff | VMAddr |\n|---|---|---|---:|---:|\n")
                for r in g["objc_or_swift_methods"][:80]:
                    f.write(f"| `{r.get('text','')}` | `{r.get('kind','')}` | `{r.get('binary_report','')}` | `{r.get('fileoff','')}` | `{r.get('vmaddr','')}` |\n")
            f.write("\n### Pattern matrix\n\n")
            f.write("| Pattern | Matches | Binaries |\n|---|---:|---|\n")
            for pat, p in g["patterns"].items():
                bins = ", ".join(f"`{b}`" for b in p["binaries"][:10])
                f.write(f"| `{pat}` | {p['matches']} | {bins} |\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-root", required=True)
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    args = ap.parse_args()
    records, _by_binary = collect_report(args.report_root)
    summary = summarize(records)
    out_json = args.out_json or os.path.join(args.report_root, "90_cross_binary_feature_gaps.json")
    out_md = args.out_md or os.path.join(args.report_root, "90_cross_binary_feature_gaps.md")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    write_md(out_md, summary)
    print(f"[radan] cross-binary feature report: {out_md}")

if __name__ == "__main__":
    main()
