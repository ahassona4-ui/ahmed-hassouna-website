#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import re
import subprocess
import sys
import unicodedata
import xml.etree.ElementTree as ET

import yaml
from PIL import Image

ZERO = "0" * 40

def run(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()

def blob(repo: Path, revision: str, path: str) -> bytes:
    return subprocess.check_output(["git", "-C", str(repo), "show", f"{revision}:{path}"])

def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def frontmatter_bytes(raw: bytes) -> dict:
    text = raw.decode("utf-8")
    if not text.startswith("---\n"):
        raise ValueError("missing YAML frontmatter start")
    end = text.find("\n---", 4)
    if end < 0:
        raise ValueError("missing YAML frontmatter end")
    value = yaml.safe_load(text[4:end])
    if not isinstance(value, dict):
        raise ValueError("frontmatter must be an object")
    return value

def diff_rows(repo: Path, base: str, head: str):
    raw = run(repo, "diff", "--name-status", "--find-renames", base, head)
    rows = []
    for line in raw.splitlines():
        if not line:
            continue
        cols = line.split("\t")
        status = cols[0]
        if status.startswith(("R", "C")):
            rows.append((status, cols[1], cols[2]))
        else:
            rows.append((status, cols[1], None))
    return rows

def changed_commits(repo: Path, base: str, head: str):
    raw = run(repo, "rev-list", "--reverse", f"{base}..{head}")
    return [line for line in raw.splitlines() if line]

def normalized_scalar(value):
    if isinstance(value, str):
        return " ".join(unicodedata.normalize("NFKC", value).split())
    return value

def semantic_diff(before, after, prefix="$"):
    added, removed, changed = set(), set(), set()
    if isinstance(before, dict) and isinstance(after, dict):
        for key in before.keys() - after.keys():
            removed.add(f"{prefix}.{key}")
        for key in after.keys() - before.keys():
            added.add(f"{prefix}.{key}")
        for key in before.keys() & after.keys():
            a, r, c = semantic_diff(before[key], after[key], f"{prefix}.{key}")
            added |= a; removed |= r; changed |= c
    elif isinstance(before, list) and isinstance(after, list):
        if before != after:
            changed.add(prefix)
    elif normalized_scalar(before) != normalized_scalar(after):
        changed.add(prefix)
    return added, removed, changed

def get_path(data, dotted, default=None):
    current = data
    for part in dotted.split("."):
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current

def has_path(data, dotted):
    sentinel = object()
    return get_path(data, dotted, sentinel) is not sentinel

def starts(path, dotted):
    target = "$." + dotted
    return path == target or path.startswith(target + ".") or path.startswith(target + "[")

def allowed_routine_path(path: str, policy: dict):
    pp = PurePosixPath(path)
    if path in policy["routine"]["prohibited_exact_paths"]:
        return None
    if any(path.startswith(prefix) for prefix in policy["routine"]["prohibited_prefixes"]):
        return None
    if any(pp.match(pattern) for pattern in policy["routine"]["allowed_content_globs"]):
        return "content"
    if any(pp.match(pattern) for pattern in policy["routine"]["allowed_media_globs"]):
        return "media"
    return None

def expected_record_id(path: str):
    name = PurePosixPath(path).stem.lower()
    if path.startswith("_articles/") and re.fullmatch(r"ah-art-\d{3}", name):
        return name.upper()
    if path.startswith("_projects/") and re.fullmatch(r"ah-prj-\d{3}", name):
        return name.upper()
    return None

def review_is_reopened(after: dict, policy: dict):
    expected = policy["review_reopen_contract"]
    review = after.get("review") or {}
    return (
        after.get("status") == expected["status"]
        and review.get("content_review_state") == expected["content_review_state"]
        and review.get("claim_review_state") == expected["claim_review_state"]
        and review.get("timestamp_state") == expected["timestamp_state"]
        and all(field not in review for field in expected["prohibited_fields"])
    )

def changed_under(paths, dotted):
    return any(starts(path, dotted) for path in paths)

def validate_review_transition(before, after, all_paths, policy):
    errors = []
    old = (before.get("review") or {}).get("timestamp_state")
    new = (after.get("review") or {}).get("timestamp_state")
    allowed = policy["state_transitions"]["review_timestamp_state"].get(old, [])
    if new not in allowed:
        errors.append(f"review.timestamp_state transition prohibited: {old} -> {new}")
        return errors
    before_review = before.get("review") or {}
    after_review = after.get("review") or {}
    if new == "not_recorded":
        if old != "not_recorded" and not review_is_reopened(after, policy):
            errors.append("review transition to not_recorded requires a complete review reopen")
    if old == "not_recorded" and new == "recorded":
        if after_review.get("content_review_state") not in {"approved", "rejected"}:
            errors.append("recorded review requires completed content review")
        if after_review.get("claim_review_state") not in {"approved", "rejected"}:
            errors.append("recorded review requires completed claim review")
        if not after_review.get("reviewed_by") or not after_review.get("reviewed_at"):
            errors.append("recorded review requires reviewed_by and reviewed_at")
    if old == "legacy_unrecorded" and new == "recorded":
        errors.append("legacy_unrecorded must be reopened through not_recorded before a new recorded review")
    if old == "recorded" and new == "recorded":
        if before_review.get("reviewed_at") != after_review.get("reviewed_at"):
            errors.append("recorded timestamp cannot be silently rewritten; reopen review first")
    return errors

def validate_publication_transition(before, after, policy):
    errors = []
    if after.get("content_type") != "article":
        return errors
    old = before.get("publication_date_state")
    new = after.get("publication_date_state")
    allowed = policy["state_transitions"]["publication_date_state"].get(old, [])
    if new not in allowed:
        errors.append(f"publication_date_state transition prohibited in routine mode: {old} -> {new}")
    if before.get("published_at") != after.get("published_at"):
        errors.append("published_at addition, removal or rewrite requires a separately authorized controlled operation")
    if old == "recorded" and new != "recorded":
        errors.append("recorded publication state cannot be downgraded")
    return errors

def validate_media_transition(before, after, all_paths, policy):
    errors = []
    old = before.get("media_state")
    new = after.get("media_state")
    allowed = policy["state_transitions"]["media_state"].get(old, [])
    if new not in allowed:
        errors.append(f"media_state transition prohibited: {old} -> {new}")
        return errors
    media_changed = changed_under(all_paths, "media")
    state_changed = old != new
    if old == "ready" and new != "ready":
        if "media" in after:
            errors.append("non-ready media state must remove the media payload")
        if not review_is_reopened(after, policy):
            errors.append("ready media removal requires status under_review and complete review reset")
    elif old != "ready" and new == "ready":
        if "media" not in after:
            errors.append("ready media state requires a media payload")
        if before.get("status") == "published" or (before.get("review") or {}).get("content_review_state") == "approved":
            if not review_is_reopened(after, policy):
                errors.append("introducing media to an approved/published record requires review reopen")
    elif old == "ready" and new == "ready" and media_changed:
        if not review_is_reopened(after, policy):
            errors.append("material media payload change requires review reopen")
    elif old != "ready" and "media" in after:
        errors.append("orphan media payload is prohibited when media_state is not ready")
    if changed_under(all_paths, "seo.og_image") and not review_is_reopened(after, policy):
        errors.append("SEO sharing-image change requires review reopen")
    return errors

def claim_conversion_complete(after, policy):
    errors = []
    review = after.get("review") or {}
    claims = after.get("claims")
    contract = policy["structured_conversion_contract"]
    if after.get("claims_state") != contract["claims_state"]:
        errors.append("conversion must set claims_state to structured")
    if after.get("status") != contract["status"]:
        errors.append("conversion must reopen record status to under_review")
    if review.get("content_review_state") != contract["review_content_state"]:
        errors.append("conversion must reset content_review_state to pending")
    if review.get("claim_review_state") != contract["review_claim_state"]:
        errors.append("conversion must reset claim_review_state to pending")
    if review.get("timestamp_state") != contract["review_timestamp_state"]:
        errors.append("conversion must reset review.timestamp_state to not_recorded")
    if "reviewed_by" in review or "reviewed_at" in review:
        errors.append("conversion must remove historical reviewer/timestamp payload during reopen")
    if not isinstance(claims, list) or not claims:
        errors.append("conversion requires a nonempty claims payload")
        return errors
    for index, claim in enumerate(claims):
        ctype = claim.get("claim_type")
        if claim.get("approval_state") != contract["claim_approval_state"]:
            errors.append(f"claim[{index}] approval_state must reset to pending")
        if "approved_by" in claim or "approved_at" in claim:
            errors.append(f"claim[{index}] approval metadata must be removed during conversion")
        if ctype in contract["evidence_required_for"] and not claim.get("evidence_refs"):
            errors.append(f"claim[{index}] {ctype} requires evidence_refs")
        if ctype in contract["boundary_required_for"]:
            boundary = claim.get("boundary") or {}
            if not boundary.get("ar") or not boundary.get("en"):
                errors.append(f"claim[{index}] {ctype} requires bilingual boundary")
    return errors

def validate_claim_transition(before, after, all_paths, policy):
    errors = []
    old = before.get("claims_state")
    new = after.get("claims_state")
    allowed = policy["state_transitions"]["claims_state"].get(old, [])
    if new not in allowed:
        errors.append(f"claims_state transition prohibited: {old} -> {new}")
        return errors
    record_id = after.get("project_id") or after.get("article_id")
    current_projects = set(policy["runtime_record_ids"]["projects"])
    if record_id in current_projects and new == "none":
        errors.append("current governed projects cannot use claims_state none")
    claim_payload_changed = changed_under(all_paths, "claims")
    claim_bearing_changed = any(changed_under(all_paths, dotted) for dotted in policy["legacy_claim_bearing_paths"])
    if old == "legacy_embedded":
        if new == "legacy_embedded" and claim_bearing_changed:
            errors.append("material legacy-embedded claim-bearing edit requires complete structured conversion")
        if new == "structured":
            errors.extend(claim_conversion_complete(after, policy))
        elif new != "legacy_embedded":
            errors.append("legacy_embedded can transition only to structured")
    elif old == "structured":
        if new != "structured":
            if "claims" in after:
                errors.append("non-structured claims state must remove claims payload")
            if not review_is_reopened(after, policy):
                errors.append("structured-claims removal requires review reopen")
        elif claim_payload_changed:
            if not review_is_reopened(after, policy):
                errors.append("structured claims edit requires review reopen")
            for index, claim in enumerate(after.get("claims") or []):
                if claim.get("approval_state") != "pending":
                    errors.append(f"claim[{index}] must reset approval_state to pending after material edit")
                if "approved_by" in claim or "approved_at" in claim:
                    errors.append(f"claim[{index}] must remove approval metadata after material edit")
    elif new == "structured":
        errors.extend(claim_conversion_complete(after, policy))
    elif "claims" in after:
        errors.append("claims payload is prohibited unless claims_state is structured")
    return errors

def validate_generic_removals(removed, before, after, policy):
    errors = []
    old_media = before.get("media_state")
    new_media = after.get("media_state")
    old_claims = before.get("claims_state")
    new_claims = after.get("claims_state")
    review_old = (before.get("review") or {}).get("timestamp_state")
    review_new = (after.get("review") or {}).get("timestamp_state")
    reopened = review_is_reopened(after, policy)
    for path in sorted(removed):
        allowed = False
        if starts(path, "media") and old_media == "ready" and new_media != "ready":
            allowed = True
        elif starts(path, "claims") and old_claims == "structured" and new_claims != "structured":
            allowed = True
        elif path in {"$.review.reviewed_at", "$.review.reviewed_by"} and review_new == "not_recorded" and reopened:
            allowed = True
        elif path in {"$.review.notes", "$.seo.og_image", "$.quote"} and reopened:
            allowed = True
        elif starts(path, "media.alt") and get_path(before, "media.decorative") is False and get_path(after, "media.decorative") is True and reopened:
            allowed = True
        elif (path.startswith("$.media.") or path.startswith("$.media[")) and reopened and new_media == "ready":
            allowed = True
        if not allowed:
            errors.append(f"unexpected semantic key removal: {path}")
    return errors

def validate_status_and_review(before, after, all_paths, policy):
    errors = []
    old_status = before.get("status")
    new_status = after.get("status")
    if new_status not in policy["allowed_status_transitions"].get(old_status, []):
        errors.append(f"status transition prohibited: {old_status} -> {new_status}")
    substantive = {
        p for p in all_paths
        if not starts(p, "status")
        and not starts(p, "review")
        and not starts(p, "updated_at")
        and not any(starts(p, dotted) for dotted in policy.get("non_review_editorial_paths", []))
    }
    if old_status == "published" and substantive:
        if new_status != "under_review":
            errors.append("semantic change to published content requires status under_review")
        if not review_is_reopened(after, policy):
            errors.append("semantic change to published content requires complete review reset")
    elif (before.get("review") or {}).get("content_review_state") == "approved" and substantive:
        if not review_is_reopened(after, policy):
            errors.append("semantic change to approved content requires complete review reset")
    if old_status == "published" and new_status == "archived":
        non_archive = {p for p in all_paths if p not in {"$.status", "$.featured"}}
        if non_archive:
            errors.append("published to archived transition may change only status and project featured flag")
        if after.get("content_type") == "project" and after.get("featured") is not False:
            errors.append("archived project must set featured to false")
    return errors

def validate_content_transition(before, after, path, policy):
    errors, notes = [], []
    added, removed, changed = semantic_diff(before, after)
    all_paths = added | removed | changed
    if not all_paths:
        notes.append(f"{path}: formatting-only YAML change")
        return errors, notes
    record_id = after.get("article_id") or after.get("project_id")
    expected_id = expected_record_id(path)
    if expected_id and record_id != expected_id:
        errors.append(f"{path}: record ID does not match filename")
    for field in policy["protected_fields"]["common"]:
        if before.get(field) != after.get(field):
            errors.append(f"{path}: protected field changed: {field}")
    extra = "article" if after.get("content_type") == "article" else "project"
    for field in policy["protected_fields"][extra]:
        if before.get(field) != after.get(field):
            errors.append(f"{path}: protected field changed: {field}")
    errors.extend(validate_status_and_review(before, after, all_paths, policy))
    errors.extend(validate_review_transition(before, after, all_paths, policy))
    errors.extend(validate_publication_transition(before, after, policy))
    errors.extend(validate_media_transition(before, after, all_paths, policy))
    errors.extend(validate_claim_transition(before, after, all_paths, policy))
    errors.extend(validate_generic_removals(removed, before, after, policy))
    notes.append(f"{path}: semantic change paths={sorted(all_paths)}")
    return errors, notes

def svg_security(path: Path):
    errors = []
    try:
        root = ET.parse(path).getroot()
    except Exception as exc:
        return [f"invalid SVG XML: {exc}"]
    for element in root.iter():
        tag = element.tag.lower()
        if tag.endswith("script") or tag.endswith("foreignobject"):
            errors.append(f"prohibited SVG element: {element.tag}")
        for key, value in element.attrib.items():
            low = key.lower()
            val = str(value).strip().lower()
            if low.startswith("on"):
                errors.append(f"prohibited SVG event attribute: {key}")
            if low.endswith("href") and value and not str(value).startswith("#"):
                errors.append("external SVG href prohibited")
            if "javascript:" in val or "data:" in val:
                errors.append("active/data SVG reference prohibited")
    return errors

def validate_media_file(path: Path, policy: dict, upload=True):
    errors = []
    ext = path.suffix.lower()
    data = path.read_bytes()
    media = policy["media"]
    if upload and ext not in media["allowed_upload_extensions"]:
        errors.append(f"unsupported upload extension: {ext}")
    if len(data) > media["max_bytes"]:
        errors.append("media file exceeds maximum bytes")
    if upload and not re.fullmatch(media["safe_filename_regex"], path.name):
        errors.append("media filename must be lowercase kebab-case")
    if ext == ".svg":
        if upload and media["prohibit_upload_svg"]:
            errors.append("SVG uploads are prohibited")
        errors.extend(svg_security(path))
    elif ext in {".png", ".jpg", ".jpeg", ".webp"}:
        expected = {".png": "PNG", ".jpg": "JPEG", ".jpeg": "JPEG", ".webp": "WEBP"}[ext]
        try:
            with Image.open(path) as image:
                fmt = image.format
                width, height = image.size
                image.verify()
            if fmt != expected:
                errors.append(f"MIME/signature mismatch: expected {expected}, got {fmt}")
            if max(width, height) > media["max_dimension"]:
                errors.append("media dimensions exceed policy")
        except Exception as exc:
            errors.append(f"invalid raster image: {exc}")
    else:
        errors.append(f"unsupported media extension: {ext}")
    return errors

def verify_schema_and_classification(repo: Path, head: str, policy: dict):
    errors = []
    schema_bytes = blob(repo, head, policy["canonical_schema"]["path"])
    actual = hashlib.sha256(schema_bytes).hexdigest()
    if actual != policy["canonical_schema"]["sha256"]:
        errors.append(f"canonical schema SHA mismatch: {actual}")
    classification = json.loads(blob(repo, head, policy["classification_path"]))
    records = classification.get("records") or {}
    for rid in policy["runtime_record_ids"]["articles"]:
        if records.get(rid, {}).get("claims_state") != "none":
            errors.append(f"{rid}: conflicting claims_state classification")
    for rid in policy["runtime_record_ids"]["projects"]:
        if records.get(rid, {}).get("claims_state") != "legacy_embedded":
            errors.append(f"{rid}: conflicting claims_state classification")
    return errors

def validate_routine_commit(repo: Path, commit: str, policy: dict):
    parent = run(repo, "rev-parse", f"{commit}^")
    rows = diff_rows(repo, parent, commit)
    errors, notes = [], []
    if len(rows) != policy["routine"]["paths_per_commit"]:
        return [f"{commit}: routine commit must change exactly one path; got {len(rows)}"], notes
    status, path, new_path = rows[0]
    if new_path:
        return [f"{commit}: rename/copy prohibited: {path} -> {new_path}"], notes
    kind = allowed_routine_path(path, policy)
    if not kind:
        return [f"{commit}: prohibited routine path: {path}"], notes
    if kind == "content":
        if status != "M":
            errors.append(f"{commit}: content operation must be modify, got {status}")
        else:
            before = frontmatter_bytes(blob(repo, parent, path))
            after = frontmatter_bytes(blob(repo, commit, path))
            more, info = validate_content_transition(before, after, path, policy)
            errors.extend(more); notes.extend(info)
    else:
        if status != "A":
            errors.append(f"{commit}: media operation must be add, got {status}")
        else:
            target = repo / path
            errors.extend(f"{commit}:{path}: {item}" for item in validate_media_file(target, policy, upload=True))
    return errors, notes

def collect_media_references(repo: Path, revision: str):
    refs = set()
    for folder in ("_articles", "_projects"):
        paths = run(repo, "ls-tree", "-r", "--name-only", revision, folder)
        for path in paths.splitlines():
            if not path.endswith(".md"):
                continue
            data = frontmatter_bytes(blob(repo, revision, path))
            def walk(value):
                if isinstance(value, dict):
                    for key, child in value.items():
                        if key in {"src", "og_image"} and isinstance(child, str):
                            refs.add(child.lstrip("/"))
                        walk(child)
                elif isinstance(value, list):
                    for child in value:
                        walk(child)
            walk(data)
    return refs

def validate_promotion(repo: Path, base: str, head: str, policy: dict):
    errors, notes = [], []
    commits = changed_commits(repo, base, head)
    if not commits:
        errors.append("promotion contains no commits")
    for commit in commits:
        more, info = validate_routine_commit(repo, commit, policy)
        errors.extend(more); notes.extend(info)
    added_media = []
    for status, path, new_path in diff_rows(repo, base, head):
        if new_path:
            errors.append(f"promotion rename/copy prohibited: {path} -> {new_path}")
            continue
        kind = allowed_routine_path(path, policy)
        if kind == "media" and status == "A":
            added_media.append(path)
        if kind == "media" and status != "A":
            errors.append(f"media deletion/modification prohibited at promotion: {path}")
        if kind is None:
            errors.append(f"promotion contains prohibited path: {path}")
    refs = collect_media_references(repo, head)
    for path in added_media:
        if path not in refs:
            errors.append(f"new media remains orphaned at promotion: {path}")
    return errors, notes

def validate_bootstrap(repo: Path, base: str, head: str, policy: dict, manifest: dict):
    errors, notes = [], []
    if base != policy["bootstrap"]["exact_base"]:
        errors.append(f"bootstrap base must equal {policy['bootstrap']['exact_base']}")
    commits = changed_commits(repo, base, head)
    if len(commits) != 1:
        errors.append(f"bootstrap must be one coordinated commit; got {len(commits)}")
    if commits:
        parents = run(repo, "rev-list", "--parents", "-n", "1", head).split()
        if len(parents) != 2:
            errors.append("bootstrap head must be a non-merge commit")
    actual_rows = diff_rows(repo, base, head)
    actual = {}
    for status, path, new_path in actual_rows:
        if new_path:
            errors.append(f"bootstrap rename/copy prohibited: {path} -> {new_path}")
        else:
            actual[path] = status[0]
    expected = {item["path"]: item["operation_code"] for item in manifest["operations"]}
    if actual != expected:
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        wrong = sorted(path for path in set(expected) & set(actual) if expected[path] != actual[path])
        errors.append(f"bootstrap operation mismatch; missing={missing}; extra={extra}; wrong={wrong}")
    for item in manifest["operations"]:
        path = item["path"]
        code = item["operation_code"]
        if path == "assets/main.js":
            errors.append("assets/main.js is explicitly excluded")
        if code in {"A", "M"} and item.get("after_sha256") not in {None, "SELF"}:
            target = repo / path
            if not target.is_file():
                errors.append(f"{path}: expected output missing")
            elif file_sha256(target) != item["after_sha256"]:
                errors.append(f"{path}: after SHA mismatch")
        if code == "M" and item.get("before_sha256"):
            actual_before = hashlib.sha256(blob(repo, base, path)).hexdigest()
            if actual_before != item["before_sha256"]:
                errors.append(f"{path}: before SHA mismatch")
        if code == "D" and path != policy["deleted_workflow"]:
            errors.append(f"unapproved bootstrap deletion: {path}")
    notes.append(f"bootstrap exact operation count: {len(actual_rows)}")
    return errors, notes

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=".")
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--mode", choices=["bootstrap", "routine", "promotion"], required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--report-json")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    policy = json.loads(Path(args.policy).read_text(encoding="utf-8"))
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    errors, notes = [], []

    expected_branch = policy["development_branch"]
    if args.mode in {"bootstrap", "routine"} and args.branch != expected_branch:
        errors.append(f"wrong branch: expected {expected_branch}, got {args.branch}")
    if args.mode == "promotion" and args.branch != f"{expected_branch}->{policy['protected_branch']}":
        errors.append("promotion branch context must be cms-development-rc4.4->main")

    errors.extend(verify_schema_and_classification(repo, args.head, policy))
    if args.mode == "bootstrap":
        more, info = validate_bootstrap(repo, args.base, args.head, policy, manifest)
    elif args.mode == "routine":
        commits = changed_commits(repo, args.base, args.head)
        if not commits:
            more, info = ["routine range contains no commits"], []
        else:
            more, info = [], []
            for commit in commits:
                e, n = validate_routine_commit(repo, commit, policy)
                more.extend(e); info.extend(n)
    else:
        more, info = validate_promotion(repo, args.base, args.head, policy)
    errors.extend(more); notes.extend(info)

    report = {
        "status": "failed" if errors else "passed",
        "mode": args.mode,
        "branch": args.branch,
        "base": args.base,
        "head": args.head,
        "errors": errors,
        "notes": notes,
    }
    if args.report_json:
        destination = Path(args.report_json)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for note in notes:
        print("INFO:", note)
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print(f"PASS: platform policy ({args.mode})")
    return 0

if __name__ == "__main__":
    sys.exit(main())
