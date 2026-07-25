#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import argparse
import datetime as dt
import json
import re
import sys
import xml.etree.ElementTree as ET

import yaml
from jsonschema import Draft202012Validator, FormatChecker
from PIL import Image

MAX_UPLOAD_BYTES = 5 * 1024 * 1024
MAX_DIMENSION = 4096

def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    if not text.startswith("---\n") or end < 0:
        raise ValueError("invalid frontmatter")
    return yaml.safe_load(text[4:end]) or {}

def walk_empty(value, path="$") -> list[str]:
    errors = []
    if value is None or value == "" or value == [] or value == {}:
        errors.append(path)
    elif isinstance(value, dict):
        for key, child in value.items():
            errors.extend(walk_empty(child, f"{path}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            errors.extend(walk_empty(child, f"{path}[{index}]"))
    return errors

def timezone_aware(value: object) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None

def validate_review(review: dict, content_id: str, legacy_allowlist: set[str]) -> list[str]:
    errors = []
    state = review.get("timestamp_state")
    content_state = review.get("content_review_state")
    claim_state = review.get("claim_review_state")
    reviewed_by = review.get("reviewed_by")
    reviewed_at = review.get("reviewed_at")

    if state == "recorded":
        if content_state == "pending" or claim_state == "pending":
            errors.append("review.recorded requires completed non-pending review decisions")
        if content_state not in {"approved", "rejected"} or claim_state not in {"approved", "rejected"}:
            errors.append("review.recorded permits only approved or rejected review states")
        if not reviewed_by:
            errors.append("review.recorded requires reviewed_by")
        if not timezone_aware(reviewed_at):
            errors.append("review.recorded requires timezone-aware reviewed_at")
    elif state == "legacy_unrecorded":
        if content_id not in legacy_allowlist:
            errors.append("review.legacy_unrecorded is migration-only for approved migrated records")
        if not reviewed_by:
            errors.append("review.legacy_unrecorded requires reviewed_by")
        if "reviewed_at" in review:
            errors.append("review.legacy_unrecorded prohibits reviewed_at")
        if content_state != "approved" or claim_state != "approved":
            errors.append("review.legacy_unrecorded requires approved content and claim review states")
    elif state == "not_recorded":
        if "reviewed_at" in review:
            errors.append("review.not_recorded prohibits reviewed_at")
        if content_state != "pending" or claim_state != "pending":
            errors.append("review.not_recorded is valid only while both review states are pending")
    else:
        errors.append("review.timestamp_state is invalid")

    if "notes" in review and not review.get("notes"):
        errors.append("review.notes must be omitted when empty")
    return errors

def validate_claim(claim: dict, content_id: str, baseline_allowlist: set[str]) -> list[str]:
    errors = []
    claim_id = claim.get("claim_id", "<unknown>")
    claim_type = claim.get("claim_type")
    evidence = claim.get("evidence_refs")
    boundary = claim.get("boundary")
    approval_state = claim.get("approval_state")

    if claim_type in {"quantitative", "status"}:
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"claim {claim_id}: {claim_type} requires evidence_refs")
        if not isinstance(boundary, dict) or not boundary.get("ar") or not boundary.get("en"):
            errors.append(f"claim {claim_id}: {claim_type} requires bilingual boundary")
    elif claim_type == "credential":
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"claim {claim_id}: credential requires evidence_refs")

    if approval_state == "approved":
        if not claim.get("approved_by"):
            errors.append(f"claim {claim_id}: approved requires approved_by")
        if not timezone_aware(claim.get("approved_at")):
            errors.append(f"claim {claim_id}: approved requires timezone-aware approved_at")
    elif approval_state == "baseline_approved":
        if content_id not in baseline_allowlist:
            errors.append(f"claim {claim_id}: baseline_approved is not allowed for this record")
        if not claim.get("approved_by"):
            errors.append(f"claim {claim_id}: baseline_approved requires approved_by")
        if "approved_at" in claim:
            errors.append(f"claim {claim_id}: baseline_approved prohibits approved_at")

    return errors

def media_paths(data: dict):
    result = []
    def add_asset(asset, label):
        if isinstance(asset, dict) and asset.get("src"):
            result.append((label, asset["src"], asset))
    media = data.get("media") or {}
    if data.get("content_type") == "project" and media.get("src"):
        result.append(("media.src", media["src"], media))
    add_asset(media.get("thumbnail"), "media.thumbnail")
    add_asset(media.get("cover"), "media.cover")
    for index, item in enumerate(media.get("gallery") or []):
        add_asset(item, f"media.gallery[{index}]")
    if (data.get("seo") or {}).get("og_image"):
        result.append(("seo.og_image", data["seo"]["og_image"], None))
    return result

def check_svg(path: Path):
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        return f"invalid SVG XML: {exc}"
    for element in root.iter():
        if element.tag.lower().endswith("script"):
            return "SVG script element is prohibited"
        for key, value in element.attrib.items():
            low = key.lower()
            if low.startswith("on"):
                return f"SVG event attribute {key} is prohibited"
            if low.endswith("href") and value and not value.startswith("#"):
                return "external SVG href is prohibited"
    return None

def validate_media(root: Path, path_value: str, label: str) -> list[str]:
    errors = []
    if not isinstance(path_value, str) or not path_value.startswith("/assets/"):
        return [f"{label}: media path must be repository-local under /assets/"]
    if "://" in path_value or path_value.startswith(("data:", "javascript:")):
        return [f"{label}: external/data/script path prohibited"]
    target = (root / path_value.lstrip("/")).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        return [f"{label}: path escapes repository"]
    if not target.is_file():
        return [f"{label}: missing file {path_value}"]
    ext = target.suffix.lower()
    if target.stat().st_size > MAX_UPLOAD_BYTES:
        errors.append(f"{label}: file exceeds 5 MiB")
    upload = "/assets/uploads/" in path_value
    if upload and ext == ".svg":
        errors.append(f"{label}: SVG uploads are prohibited")
    if ext == ".svg":
        issue = check_svg(target)
        if issue:
            errors.append(f"{label}: {issue}")
    elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
        try:
            with Image.open(target) as image:
                image.verify()
            with Image.open(target) as image:
                if image.width > MAX_DIMENSION or image.height > MAX_DIMENSION:
                    errors.append(f"{label}: dimensions exceed {MAX_DIMENSION}px")
        except Exception as exc:
            errors.append(f"{label}: invalid raster image: {exc}")
    else:
        errors.append(f"{label}: unsupported extension {ext}")
    return errors

def validate_record_semantics(data: dict, content_id: str, classification: dict) -> list[str]:
    errors = []
    legacy_allowlist = set(classification.get("review_migration_allowlist", []))
    baseline_allowlist = set(classification.get("baseline_approved_claim_allowlist", []))
    errors.extend(validate_review(data.get("review") or {}, content_id, legacy_allowlist))
    for claim in data.get("claims") or []:
        errors.extend(validate_claim(claim, content_id, baseline_allowlist))
    if data.get("claims_state") == "legacy_embedded":
        if content_id not in {f"AH-PRJ-{index:03d}" for index in range(1, 6)}:
            errors.append("legacy_embedded is permitted only for the five approved migrated projects")
        if (data.get("review") or {}).get("claim_review_state") != "approved":
            errors.append("legacy_embedded requires approved claim review")
    if data.get("claims_state") == "structured" and not data.get("claims"):
        errors.append("structured claims_state requires a nonempty claims collection")

    content_type = data.get("content_type")
    status = data.get("status")
    media_state = data.get("media_state")
    if content_type == "article":
        publication_state = data.get("publication_date_state")
        if publication_state == "unassigned" and status not in {"draft", "under_review"}:
            errors.append("article publication_date_state unassigned is limited to draft or under_review")
        if status == "published" and media_state not in {"none", "ready"}:
            errors.append("published article media_state must be none or ready")
    elif content_type == "project":
        if status == "published" and media_state != "ready":
            errors.append("published project media_state must be ready")
    return errors

def validate_samples(root: Path, validator, classification: dict) -> list[str]:
    errors = []
    sample_path = root / "docs/cms/samples/non-runtime-samples.yml"
    samples = yaml.safe_load(sample_path.read_text(encoding="utf-8")) or {}
    for name, data in samples.items():
        for issue in validator.iter_errors(data):
            location = ".".join(map(str, issue.path)) or "$"
            errors.append(f"{sample_path.relative_to(root)}::{name}:{location}: {issue.message}")
        for empty_path in walk_empty(data):
            errors.append(f"{sample_path.relative_to(root)}::{name}:{empty_path}: noncanonical empty")
        content_id = data.get("article_id") or data.get("project_id") or name
        for issue in validate_record_semantics(data, content_id, classification):
            errors.append(f"{sample_path.relative_to(root)}::{name}: {issue}")
    return errors

def main() -> int:
    parser = argparse.ArgumentParser(description="Validate AH Website Unified Content Model v2.0 Corrected Engineering Candidate #003.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--schema", required=True)
    parser.add_argument("--classification", required=True)
    parser.add_argument("--report-json")
    parser.add_argument("--skip-samples", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    schema = json.loads(Path(args.schema).read_text(encoding="utf-8"))
    classification = json.loads(Path(args.classification).read_text(encoding="utf-8"))
    expected_records = classification["records"]
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = []
    warnings = []
    rows = []
    records = []

    for folder in ("_projects", "_articles"):
        for path in sorted((root / folder).glob("*.md")):
            try:
                data = frontmatter(path)
            except Exception as exc:
                errors.append(f"{path.relative_to(root)}: {exc}")
                continue

            records.append((path, data))
            relative = str(path.relative_to(root))
            content_id = data.get("article_id") or data.get("project_id")
            record_errors = []

            for issue in validator.iter_errors(data):
                location = ".".join(map(str, issue.path)) or "$"
                record_errors.append(f"{location}: {issue.message}")
            for empty_path in walk_empty(data):
                record_errors.append(f"{empty_path}: noncanonical empty value/container")

            expected = expected_records.get(content_id)
            if not expected:
                record_errors.append("missing approved state classification")
            else:
                for key in ("media_state", "claims_state"):
                    if data.get(key) != expected[key]:
                        record_errors.append(f"{key} differs from approved classification")
                if data.get("content_type") == "article" and data.get("publication_date_state") != expected["publication_date_state"]:
                    record_errors.append("publication_date_state differs from approved classification")
                if (data.get("review") or {}).get("timestamp_state") != expected["review_timestamp_state"]:
                    record_errors.append("review.timestamp_state differs from approved classification")

            if data.get("schema_version") != "2.0":
                record_errors.append("schema_version must be 2.0")
            if "legacy_date_pending" in data:
                record_errors.append("legacy_date_pending is prohibited in v2 runtime records")
            if data.get("publication_date_state") == "legacy_pending" and "published_at" in data:
                record_errors.append("legacy_pending must omit published_at")

            record_errors.extend(validate_record_semantics(data, content_id, classification))

            for label, path_value, asset in media_paths(data):
                record_errors.extend(validate_media(root, path_value, label))
                if asset:
                    if asset.get("decorative") is True and "alt" in asset:
                        record_errors.append(f"{label}: decorative asset must omit stored alt")
                    if asset.get("decorative") is False:
                        alt = asset.get("alt") or {}
                        if not alt.get("ar") or not alt.get("en"):
                            record_errors.append(f"{label}: meaningful asset requires Arabic and English alt")

            if data.get("content_type") == "project" and data.get("claims_state") == "legacy_embedded":
                evidence = data.get("evidence") or {}
                if not evidence.get("documented_impact") or not evidence.get("claim_boundaries"):
                    record_errors.append("legacy project claims require impact and boundary narrative")

            errors.extend(f"{relative}: {message}" for message in record_errors)
            rows.append({"path": relative, "id": content_id, "errors": record_errors})

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
        key=lambda item: item[1]["order"],
    )
    for index, (path, data) in enumerate(projects):
        previous = projects[(index - 1) % len(projects)][1]
        following = projects[(index + 1) % len(projects)][1]
        navigation = data.get("navigation") or {}
        if navigation.get("previous") != {"path": previous["permalink"], "project_id": previous["project_id"]}:
            errors.append(f"{path.relative_to(root)}: wrong circular previous")
        if navigation.get("next") != {"path": following["permalink"], "project_id": following["project_id"]}:
            errors.append(f"{path.relative_to(root)}: wrong circular next")

    if not args.skip_samples:
        errors.extend(validate_samples(root, validator, classification))

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
                errors.append(f"{relative}: missing required state-aware token {token}")
        if re.search(r"page\.(date|last_modified_at)|site\.time|file\.mtime|git", text, re.I):
            errors.append(f"{relative}: prohibited date/build inference token")

    active_legacy_surfaces = [
        ".pages.yml",
        "docs/cms/schemas/content-model.schema.json",
        "docs/cms/state-classification-v2.json",
        "docs/cms/STATE_CLASSIFICATION_V2.md",
        "docs/cms/CONTENT_MODEL_SPECIFICATION.md",
        "docs/cms/CONTENT_MODEL_ADDENDUM.md",
        "docs/cms/MIGRATION_MAP.md",
    ]
    for relative in active_legacy_surfaces:
        text = (root / relative).read_text(encoding="utf-8")
        if "legacy_date_pending" in text:
            errors.append(f"{relative}: active v2 surface contains legacy_date_pending")

    report = {
        "status": "passed" if not errors else "failed",
        "record_count": len(records),
        "records": rows,
        "errors": errors,
        "warnings": warnings,
    }
    if args.report_json:
        report_path = Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if errors:
        print("\n".join(f"FAIL: {error}" for error in errors))
        return 1
    print(f"PASS: {len(records)} runtime records, samples, review lifecycle, claims, media, navigation and templates satisfy v2.0 Corrected Engineering Candidate #003")
    return 0

if __name__ == "__main__":
    sys.exit(main())
