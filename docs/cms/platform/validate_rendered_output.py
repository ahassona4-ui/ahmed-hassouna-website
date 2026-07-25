#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit
import argparse
import hashlib
import html
import json
import re
import sys
import yaml

def frontmatter(path: Path) -> dict:
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

def output_path(site: Path, permalink: str) -> Path:
    relative = permalink.lstrip("/")
    if relative.endswith("/"):
        return site / relative / "index.html"
    return site / relative

class Collector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
        self.images = []
        self.html_attrs = {}
        self.times = []
        self.meta = []
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "html":
            self.html_attrs = values
        for name, value in attrs:
            if name in {"href", "src"} and value:
                self.refs.append((tag, name, value))
        if tag == "img":
            self.images.append(values)
        if tag == "time":
            self.times.append(values)
        if tag == "meta":
            self.meta.append(values)

def local_target(site: Path, page: Path, raw: str):
    value = html.unescape(raw.strip())
    parsed = urlsplit(value)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data", "javascript"}:
        return None
    if value.startswith("#") or not parsed.path:
        return None
    clean = unquote(parsed.path)
    target = site / clean.lstrip("/") if clean.startswith("/") else page.parent / clean
    target = target.resolve()
    target.relative_to(site.resolve())
    if target.is_dir():
        return target / "index.html"
    return target

def image_by_src(images, expected):
    clean = expected.lstrip("/")
    for attrs in images:
        src = (attrs.get("src") or "").split("?", 1)[0].lstrip("/")
        if src == clean:
            return attrs
    return None

def validate_page(source_path: Path, data: dict, page: Path, site: Path):
    errors = []
    if not page.is_file():
        return [f"{source_path}: generated route missing: {page.relative_to(site)}"], {}
    text = page.read_text(encoding="utf-8")
    parser = Collector()
    parser.feed(text)
    if "<html" not in text.lower() or "</html>" not in text.lower():
        errors.append(f"{source_path}: missing HTML skeleton")
    if "{{" in text or "{%" in text:
        errors.append(f"{source_path}: unresolved Liquid")
    if "Ahmed Hassouna" not in text or "أحمد حسونة" not in text:
        errors.append(f"{source_path}: canonical bilingual identity missing")
    if 'data-ar=' not in text or 'data-en=' not in text:
        errors.append(f"{source_path}: bilingual data attributes missing")
    if data.get("content_type") == "article":
        state = data.get("publication_date_state")
        if state == "recorded":
            if len(parser.times) != 1:
                errors.append(f"{source_path}: recorded article must render one time element")
            elif parser.times[0].get("datetime") != data.get("published_at"):
                errors.append(f"{source_path}: rendered publication date differs from source")
        else:
            if parser.times:
                errors.append(f"{source_path}: non-recorded article must not render a time element")
        if state == "legacy_pending" and 'data-legacy-date-pending="true"' not in text:
            errors.append(f"{source_path}: legacy_pending marker missing")
    media_state = data.get("media_state")
    media = data.get("media") or {}
    expected_assets = []
    if media_state == "ready":
        if data.get("content_type") == "project":
            if media.get("src"):
                expected_assets.append((media["src"], media))
        else:
            if isinstance(media.get("cover"), dict):
                expected_assets.append((media["cover"].get("src"), media["cover"]))
            for item in media.get("gallery") or []:
                expected_assets.append((item.get("src"), item))
    for src, asset in expected_assets:
        attrs = image_by_src(parser.images, src)
        if attrs is None:
            errors.append(f"{source_path}: ready media not rendered: {src}")
            continue
        if asset.get("decorative") is True:
            if attrs.get("alt") != "" or attrs.get("aria-hidden") != "true":
                errors.append(f"{source_path}: decorative media must render alt=\"\" and aria-hidden=\"true\"")
        else:
            alt = asset.get("alt") or {}
            if attrs.get("alt") != alt.get("ar"):
                errors.append(f"{source_path}: meaningful image Arabic alt mismatch")
            if attrs.get("data-alt-ar") != alt.get("ar") or attrs.get("data-alt-en") != alt.get("en"):
                errors.append(f"{source_path}: meaningful image bilingual alt attributes missing")
    if media_state != "ready":
        known_media = []
        def walk(value):
            if isinstance(value, dict):
                for key, child in value.items():
                    if key == "src" and isinstance(child, str):
                        known_media.append(child)
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)
        walk(media)
        for src in known_media:
            if image_by_src(parser.images, src):
                errors.append(f"{source_path}: non-ready media unexpectedly rendered")
    og_images = [m for m in parser.meta if m.get("property") == "og:image" or m.get("name") == "twitter:image"]
    expected_og = (data.get("seo") or {}).get("og_image")
    if expected_og:
        if len(og_images) < 2:
            errors.append(f"{source_path}: real sharing image metadata missing")
        if any(not m.get("content") for m in og_images):
            errors.append(f"{source_path}: empty sharing image metadata")
    elif og_images:
        errors.append(f"{source_path}: sharing image metadata rendered without a source value")
    for tag, name, raw in parser.refs:
        try:
            target = local_target(site, page, raw)
        except ValueError:
            errors.append(f"{source_path}: local reference escapes site: {raw}")
            continue
        if target is not None and not target.exists():
            errors.append(f"{source_path}: broken local reference: {tag}[{name}]={raw}")
    return errors, {
        "source": str(source_path),
        "output": str(page.relative_to(site)),
        "sha256": hashlib.sha256(page.read_bytes()).hexdigest(),
        "references": len(parser.refs),
        "images": len(parser.images),
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--site", required=True)
    parser.add_argument("--report-json")
    args = parser.parse_args()
    source = Path(args.source).resolve()
    site = Path(args.site).resolve()
    errors = []
    rows = []
    records = []
    for folder in ("_articles", "_projects"):
        for path in sorted((source / folder).glob("*.md")):
            try:
                data = frontmatter(path)
            except Exception as exc:
                errors.append(f"{path.relative_to(source)}: {exc}")
                continue
            records.append((path.relative_to(source), data))
    for relative, data in records:
        route = output_path(site, data["permalink"])
        page_errors, row = validate_page(relative, data, route, site)
        errors.extend(page_errors)
        if row:
            rows.append(row)
    index = site / "index.html"
    if not index.is_file():
        errors.append("index.html missing")
    else:
        text = index.read_text(encoding="utf-8")
        if "{{" in text or "{%" in text:
            errors.append("index.html contains unresolved Liquid")
        if 'lang="ar"' not in text or 'dir="rtl"' not in text:
            errors.append("index.html initial Arabic RTL attributes missing")
        if "data-ar=" not in text or "data-en=" not in text:
            errors.append("index.html bilingual content markers missing")
        if "assets/main.js" not in text:
            errors.append("index.html approved language runtime reference missing")
    report = {
        "status": "failed" if errors else "passed",
        "record_count": len(records),
        "generated_pages": rows,
        "errors": errors,
    }
    if args.report_json:
        destination = Path(args.report_json)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for error in errors:
        print("FAIL:", error)
    if errors:
        return 1
    print(f"PASS: {len(records)} CMS routes, links, dates, media, accessibility, bilingual markers and Liquid output")
    return 0

if __name__ == "__main__":
    sys.exit(main())
