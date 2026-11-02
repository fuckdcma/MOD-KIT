#!/usr/bin/env python3
"""Mod Studio AI - offline evidence builder and ground-truth evaluator (Python 3.10+).

Input A: Unity Editor text_provenance.jsonl (collector).
Input B: REA inspect-managed-members JSON (same build assembly).
Optional evaluation: ground_truth_v01.csv. Evaluation remains separate and NEVER
appears in model-facing evidence files. No file from the original game is modified.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


def read_jsonl(path):
    records = []
    with path.open(encoding="utf-8-sig") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as exc:
                    raise ValueError(f"{path}:{n}: invalid JSON: {exc}") from exc
    return records


def sha(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def write_jsonl(path, records):
    with path.open("w", encoding="utf-8", newline="\n") as out:
        for record in records:
            out.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def parse_managed(members_path):
    with members_path.open(encoding="utf-8-sig") as f:
        source = json.load(f)
    data = source.get("normalized_result", source)
    source_hash = data.get("artifact", {}).get("sha256", "")
    literals = {x["token"]: x["value"] for x in data.get("user_strings", {}).get("literals", [])}
    calls = {}
    for edge in data.get("call_edges", []):
        calls.setdefault(edge.get("caller_token"), []).append({
            "target": edge.get("target_declaring_type", "") + "." + edge.get("target_name", ""),
            "target_token": edge.get("target_token", "")
        })
    records = []
    for method in data.get("methods", []):
        token = method.get("token", "")
        edges = calls.get(token, [])
        touches_tmp_setter = any(e["target"] == "TMPro.TMP_Text.set_text" for e in edges)
        # Store method-level traces; no unjustified claim that each string is displayed.
        strings = []
        for anchor in method.get("body", {}).get("anchors", []):
            if anchor.get("opcode") == "ldstr" and anchor.get("operand") in literals:
                strings.append({"literal": literals[anchor["operand"]],
                                "literal_token": anchor["operand"],
                                "il_offset": anchor.get("il_offset")})
        if not strings and not touches_tmp_setter:
            continue
        records.append({
            "evidence_kind": "rea_managed_static",
            "verification": "static_evidence_not_runtime_proof",
            "assembly_sha256": source_hash,
            "method": method.get("declaring_type", "") + "." + method.get("name", ""),
            "method_token": token,
            "method_il_sha256": method.get("body", {}).get("il_sha256", ""),
            "touches_tmp_setter": touches_tmp_setter,
            "strings_loaded_by_method": strings,
            "call_targets": edges
        })
    return records, source_hash


def validate_records(records):
    required = {"record_id", "source_kind", "asset_path", "text", "verification"}
    missing = [(i + 1, sorted(required - set(r))) for i, r in enumerate(records) if not required <= set(r)]
    if missing:
        raise ValueError(f"Collector record missing fields: {missing[:5]}")


def matches_template(template, display):
    # Only a review heuristic. Handles integer {0} in the starter's Health template.
    pattern = re.escape(template).replace(re.escape("{0}"), r"\d+")
    return bool(re.fullmatch(pattern, display))


def evaluate(collector, managed, groundtruth):
    # NEVER place this output in a prompt used for a blind benchmark.
    wanted = {
        "serialized_prefab": "prefab_tmp_serialized",
        "scriptable_object": "scriptable_object_kv",
        "external_json": "resources_json_message"
    }
    rows = []
    with groundtruth.open(encoding="utf-8-sig", newline="") as f:
        for gt in csv.DictReader(f):
            kind = gt["source_category"]
            text = gt["displayed_text"]
            expected_kind = wanted.get(kind)
            found = []
            if expected_kind:
                for rec in collector:
                    if rec["source_kind"] == expected_kind and rec.get("text") == text:
                        found.append(rec["source_kind"] + ":" + rec.get("asset_path", "") + "#" + rec.get("source_key", rec.get("object_path", "")))
            elif kind in {"hardcoded_managed", "runtime_generated"}:
                for method in managed:
                    for lit in method["strings_loaded_by_method"]:
                        if lit["literal"] == text or matches_template(lit["literal"], text):
                            found.append("rea:" + method["method"] + "@" + lit["literal_token"])
            rows.append({
                "case_id": gt["case_id"],
                "expected_source_type": kind,
                "expected_text": text,
                "evidence_match": "found_candidate" if found else "not_found",
                "candidate_evidence": " | ".join(found),
                "review_status": "HUMAN_REVIEW_REQUIRED"
            })
    return rows


def main():
    parser = argparse.ArgumentParser(description="Join independent Unity editor and REA evidence; optional ground-truth review.")
    parser.add_argument("--collector", type=Path, required=True, help="Unity text_provenance.jsonl")
    parser.add_argument("--members", type=Path, required=True, help="REA members.json")
    parser.add_argument("--ground-truth", type=Path, help="GROUND TRUTH ONLY for separate evaluator output")
    parser.add_argument("--assembly", type=Path, help="Optional REA assembly_identity.json: validate analyzed SHA-256")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    collector = read_jsonl(args.collector)
    validate_records(collector)
    managed, assembly_hash = parse_managed(args.members)
    if args.assembly:
        identity_data = json.loads(args.assembly.read_text(encoding="utf-8-sig"))
        identity = identity_data.get("normalized_result", identity_data)
        identity_hash = identity.get("artifact", {}).get("sha256", "")
        if not identity_hash or identity_hash != assembly_hash:
            raise ValueError("REA identity SHA-256 and member evidence SHA-256 do not match")

    # Editor evidence is privileged reference data during build-only blind evaluation.
    write_jsonl(args.out / "REFERENCE_editor_evidence_DO_NOT_USE_IN_BLIND_TEST.jsonl", collector)
    write_jsonl(args.out / "model_input_rea_evidence.jsonl", managed)
    manifest = {
        "schema": "modstudio.evidence.v0.1",
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "editor_record_count": len(collector),
        "rea_method_evidence_count": len(managed),
        "editor_kinds": dict(Counter(r["source_kind"] for r in collector)),
        "rea_assembly_sha256": assembly_hash,
        "notes": ["Editor evidence comes from source project; it is REFERENCE ONLY and prohibited as model input in build-only blind tests.",
                  "REA evidence is static and does not prove runtime display.",
                  "This script does not train an AI model."]
    }
    (args.out / "evidence_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.ground_truth:
        rows = evaluate(collector, managed, args.ground_truth)
        with (args.out / "PRIVATE_ground_truth_review.csv").open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["case_id"])
            writer.writeheader()
            writer.writerows(rows)
        print("Ground truth review (PRIVATE - DO NOT USE FOR MODEL INPUT):")
        for r in rows:
            print(f"  {r['case_id']}: {r['evidence_match']} - {r['candidate_evidence']}")
    print(f"Editor records={len(collector)}, REA method traces={len(managed)}")
    print(f"Results written to {args.out}")


if __name__ == "__main__":
    main()