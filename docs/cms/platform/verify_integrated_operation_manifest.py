#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import sys

def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--report-json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    checked = []

    operations = manifest.get("operations") or []
    if len(operations) != manifest.get("operation_count"):
        errors.append("operation_count does not match operation list")
    paths = [item.get("path") for item in operations]
    if len(paths) != len(set(paths)):
        errors.append("duplicate operation paths")
    if "assets/main.js" in paths:
        errors.append("assets/main.js is explicitly excluded")
    workflow_paths = [
        path for path in paths
        if path and path.startswith(".github/workflows/") and
        next(item for item in operations if item["path"] == path)["operation_code"] != "D"
    ]
    if workflow_paths != [".github/workflows/cms-content-integrity.yml"]:
        errors.append(f"authoritative workflow topology mismatch: {workflow_paths}")

    for item in operations:
        path = item["path"]
        code = item["operation_code"]
        target = root / path
        if code in {"A", "M"}:
            if not target.is_file():
                errors.append(f"{path}: expected candidate file missing")
                continue
            expected = item.get("after_sha256")
            if expected not in {None, "SELF"}:
                actual = sha256(target)
                if actual != expected:
                    errors.append(f"{path}: SHA mismatch {actual}")
                checked.append({"path": path, "sha256": actual})
        elif code == "D":
            if target.exists():
                errors.append(f"{path}: deleted path is present in candidate tree")
        else:
            errors.append(f"{path}: unknown operation code {code}")

    schema = manifest.get("canonical_schema") or {}
    schema_path = root / schema.get("path", "")
    if not schema_path.is_file():
        errors.append("canonical schema file missing")
    elif sha256(schema_path) != schema.get("sha256"):
        errors.append("canonical schema SHA mismatch")

    report = {
        "status": "failed" if errors else "passed",
        "operation_count": len(operations),
        "checked_files": checked,
        "errors": errors,
    }
    if args.report_json:
        out = Path(args.report_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print(f"PASS: exact integrated operation manifest ({len(operations)} operations)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
