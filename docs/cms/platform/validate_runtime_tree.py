#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import importlib.util
import json
import re
import sys

import yaml
from jsonschema import Draft202012Validator, FormatChecker

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def frontmatter(path: Path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing frontmatter")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("missing frontmatter end")
    value = yaml.safe_load(text[4:end])
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be an object")
    return value

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--classification", required=True)
    parser.add_argument("--engineering-validator", required=True)
    parser.add_argument("--report-json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    classification = json.loads(Path(args.classification).read_text(encoding="utf-8"))
    engineering = load_module("engineering_v2_validator", Path(args.engineering_validator))
    schema_validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    records = []
    rows = []

    for folder in ("_articles", "_projects"):
        for path in sorted((root / folder).glob("*.md")):
            relative = str(path.relative_to(root))
            try:
                data = frontmatter(path)
            except Exception as exc:
                errors.append(f"{relative}: {exc}")
                continue
            content_id = data.get("article_id") or data.get("project_id")
            item_errors = []
            for issue in schema_validator.iter_errors(data):
                location = ".".join(map(str, issue.path)) or "$"
                item_errors.append(f"{location}: {issue.message}")
            for empty_path in engineering.walk_empty(data):
                item_errors.append(f"{empty_path}: noncanonical empty value/container")
            item_errors.extend(engineering.validate_record_semantics(data, content_id, classification))
            if data.get("schema_version") != "2.0":
                item_errors.append("schema_version must be 2.0")
            if "legacy_date_pending" in data:
                item_errors.append("legacy_date_pending is prohibited")
            approved_records = classification.get("records") or {}
            legacy_claim_ids = {
                rid for rid, row in approved_records.items()
                if row.get("claims_state") == "legacy_embedded"
            }
            legacy_publication_ids = {
                rid for rid, row in approved_records.items()
                if row.get("publication_date_state") == "legacy_pending"
            }
            if data.get("claims_state") == "legacy_embedded" and content_id not in legacy_claim_ids:
                item_errors.append("legacy_embedded is migration-only")
            if (data.get("review") or {}).get("timestamp_state") == "legacy_unrecorded" and content_id not in classification.get("review_migration_allowlist", []):
                item_errors.append("legacy_unrecorded is migration-only")
            if data.get("publication_date_state") == "legacy_pending" and content_id not in legacy_publication_ids:
                item_errors.append("legacy_pending is migration-only")
            if content_id in {f"AH-PRJ-{index:03d}" for index in range(1, 6)} and data.get("claims_state") == "none":
                item_errors.append("current governed project cannot use claims_state none")
            for label, path_value, asset in engineering.media_paths(data):
                item_errors.extend(engineering.validate_media(root, path_value, label))
                if asset:
                    if asset.get("decorative") is True and "alt" in asset:
                        item_errors.append(f"{label}: decorative asset must omit stored alt")
                    if asset.get("decorative") is False:
                        alt = asset.get("alt") or {}
                        if not alt.get("ar") or not alt.get("en"):
                            item_errors.append(f"{label}: meaningful asset requires bilingual alt")
            records.append((path, data))
            rows.append({"path": relative, "id": content_id, "errors": item_errors})
            errors.extend(f"{relative}: {message}" for message in item_errors)

    for field in ("project_id", "article_id", "slug", "permalink"):
        values = [data[field] for _, data in records if field in data]
        if len(values) != len(set(values)):
            errors.append(f"duplicate {field}")

    for content_type in ("project", "article"):
        values = [
            data["order"] for _, data in records
            if data.get("content_type") == content_type and data.get("status") == "published"
        ]
        if len(values) != len(set(values)):
            errors.append(f"duplicate published {content_type} order")

    projects = sorted(
        [(path, data) for path, data in records if data.get("content_type") == "project"],
        key=lambda pair: pair[1]["order"],
    )
    if projects:
        for index, (path, data) in enumerate(projects):
            previous = projects[(index - 1) % len(projects)][1]
            following = projects[(index + 1) % len(projects)][1]
            navigation = data.get("navigation") or {}
            if navigation.get("previous") != {"path": previous["permalink"], "project_id": previous["project_id"]}:
                errors.append(f"{path.relative_to(root)}: wrong circular previous")
            if navigation.get("next") != {"path": following["permalink"], "project_id": following["project_id"]}:
                errors.append(f"{path.relative_to(root)}: wrong circular next")

    template_checks = {
        "_layouts/article.html": ["publication_date_state", "media_state", "claims_state"],
        "_layouts/project.html": ["media_state", "claims_state", 'alt=""', "data-alt-ar"],
        "_includes/head.html": ["page.seo.og_image"],
        "_includes/article-card.html": ["publication_date_state"],
        "_includes/project-card.html": ["media_state", 'alt=""'],
    }
    for relative, tokens in template_checks.items():
        text = (root / relative).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                errors.append(f"{relative}: missing state-aware token {token}")
        if re.search(r"page\.(date|last_modified_at)|site\.time|file\.mtime|git", text, re.I):
            errors.append(f"{relative}: prohibited date/build inference token")

    report = {
        "status": "failed" if errors else "passed",
        "record_count": len(records),
        "records": rows,
        "errors": errors,
    }
    if args.report_json:
        output = Path(args.report_json)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print(f"PASS: dynamic v2 runtime tree validation ({len(records)} records)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
