from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import importlib.util
import json
import tempfile
import unittest

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[4]
PLATFORM = ROOT / "docs/cms/platform"

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

validator = load_module("platform_validator", PLATFORM / "validate_platform_change.py")
POLICY = json.loads((PLATFORM / "CMS_PLATFORM_POLICY_V2.json").read_text(encoding="utf-8"))

def fm(path):
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    return yaml.safe_load(text[4:end]) or {}

ARTICLE = fm(ROOT / "_articles/ah-art-001.md")
PROJECT = fm(ROOT / "_projects/ah-prj-001.md")

def errors(before, after, path):
    return validator.validate_content_transition(before, after, path, POLICY)[0]

def reopened(record):
    record["status"] = "under_review"
    record["review"] = {
        "content_review_state": "pending",
        "claim_review_state": "pending",
        "timestamp_state": "not_recorded",
    }
    return record

def structured_claim():
    return {
        "claim_id": "AH-PRJ-001-C01",
        "claim_type": "quantitative",
        "text": {"ar": "نتيجة كمية تحت المراجعة", "en": "Quantitative result under review"},
        "evidence_refs": ["EVIDENCE-001"],
        "boundary": {"ar": "لا تعمم النتيجة خارج النطاق.", "en": "The result is not generalized beyond scope."},
        "approval_state": "pending",
    }

class PlatformCycle002Tests(unittest.TestCase):
    def test_formatting_only_semantic_equality_passes(self):
        self.assertEqual([], errors(ARTICLE, deepcopy(ARTICLE), "_articles/ah-art-001.md"))

    def test_protected_identity_change_fails(self):
        changed = deepcopy(ARTICLE)
        changed["owner"] = "Someone Else"
        self.assertTrue(errors(ARTICLE, changed, "_articles/ah-art-001.md"))

    def test_slug_and_permalink_change_fail(self):
        changed = deepcopy(ARTICLE)
        changed["slug"] = "changed"
        changed["permalink"] = "/articles/changed.html"
        result = errors(ARTICLE, changed, "_articles/ah-art-001.md")
        self.assertTrue(any("slug" in item for item in result))
        self.assertTrue(any("permalink" in item for item in result))

    def test_semantic_edit_to_published_record_requires_reopen(self):
        changed = deepcopy(ARTICLE)
        changed["summary"]["en"] += " Changed."
        self.assertTrue(errors(ARTICLE, changed, "_articles/ah-art-001.md"))

    def test_semantic_edit_with_complete_reopen_passes(self):
        changed = reopened(deepcopy(ARTICLE))
        changed["summary"]["en"] += " Changed under review."
        self.assertEqual([], errors(ARTICLE, changed, "_articles/ah-art-001.md"))

    def test_state_aware_media_removal_passes(self):
        before = deepcopy(PROJECT)
        after = reopened(deepcopy(PROJECT))
        after["media_state"] = "planned"
        after.pop("media")
        self.assertEqual([], errors(before, after, "_projects/ah-prj-001.md"))

    def test_media_removal_without_state_transition_fails(self):
        after = reopened(deepcopy(PROJECT))
        after.pop("media")
        result = errors(PROJECT, after, "_projects/ah-prj-001.md")
        self.assertTrue(any("unexpected semantic key removal" in item or "material media" in item for item in result))

    def test_orphan_media_payload_fails(self):
        after = reopened(deepcopy(ARTICLE))
        after["media"] = {"cover": {"src": "/assets/uploads/articles/test.png", "decorative": True}}
        self.assertTrue(errors(ARTICLE, after, "_articles/ah-art-001.md"))

    def test_legacy_embedded_material_edit_fails(self):
        after = reopened(deepcopy(PROJECT))
        after["evidence"]["documented_impact"]["en"] += " Material change."
        result = errors(PROJECT, after, "_projects/ah-prj-001.md")
        self.assertTrue(any("structured conversion" in item for item in result))

    def test_legacy_embedded_unrelated_card_title_edit_passes_without_claim_reclassification(self):
        after = deepcopy(PROJECT)
        after["card_title"] += " — Revised"
        self.assertEqual([], errors(PROJECT, after, "_projects/ah-prj-001.md"))

    def test_complete_structured_conversion_passes(self):
        after = reopened(deepcopy(PROJECT))
        after["claims_state"] = "structured"
        after["claims"] = [structured_claim()]
        after["evidence"]["documented_impact"]["en"] += " Converted for structured review."
        self.assertEqual([], errors(PROJECT, after, "_projects/ah-prj-001.md"))

    def test_conversion_without_claims_fails(self):
        after = reopened(deepcopy(PROJECT))
        after["claims_state"] = "structured"
        after["evidence"]["documented_impact"]["en"] += " Changed."
        self.assertTrue(errors(PROJECT, after, "_projects/ah-prj-001.md"))

    def test_conversion_without_review_reset_fails(self):
        after = deepcopy(PROJECT)
        after["claims_state"] = "structured"
        after["claims"] = [structured_claim()]
        after["evidence"]["documented_impact"]["en"] += " Changed."
        self.assertTrue(errors(PROJECT, after, "_projects/ah-prj-001.md"))

    def test_conversion_claim_requires_evidence_and_boundary(self):
        after = reopened(deepcopy(PROJECT))
        after["claims_state"] = "structured"
        claim = structured_claim()
        claim.pop("evidence_refs")
        claim.pop("boundary")
        after["claims"] = [claim]
        after["evidence"]["documented_impact"]["en"] += " Changed."
        result = errors(PROJECT, after, "_projects/ah-prj-001.md")
        self.assertTrue(any("evidence_refs" in item for item in result))
        self.assertTrue(any("boundary" in item for item in result))

    def test_legacy_project_cannot_downgrade_to_none(self):
        after = reopened(deepcopy(PROJECT))
        after["claims_state"] = "none"
        self.assertTrue(errors(PROJECT, after, "_projects/ah-prj-001.md"))

    def test_reviewed_timestamp_removal_allowed_only_on_reopen(self):
        before = deepcopy(ARTICLE)
        before["status"] = "published"
        before["review"] = {
            "content_review_state": "approved",
            "claim_review_state": "approved",
            "timestamp_state": "recorded",
            "reviewed_by": "Reviewer",
            "reviewed_at": "2026-07-16T12:00:00+03:00",
        }
        after = reopened(deepcopy(before))
        after["summary"]["en"] += " New review."
        self.assertEqual([], errors(before, after, "_articles/ah-art-001.md"))

    def test_recorded_timestamp_silent_rewrite_fails(self):
        before = deepcopy(ARTICLE)
        before["review"] = {
            "content_review_state": "approved",
            "claim_review_state": "approved",
            "timestamp_state": "recorded",
            "reviewed_by": "Reviewer",
            "reviewed_at": "2026-07-16T12:00:00+03:00",
        }
        after = deepcopy(before)
        after["review"]["reviewed_at"] = "2026-07-17T12:00:00+03:00"
        self.assertTrue(errors(before, after, "_articles/ah-art-001.md"))

    def test_publication_date_recording_is_deferred_from_routine(self):
        after = reopened(deepcopy(ARTICLE))
        after["publication_date_state"] = "recorded"
        after["published_at"] = "2026-07-16"
        self.assertTrue(errors(ARTICLE, after, "_articles/ah-art-001.md"))

    def test_expected_paths_and_prohibited_paths(self):
        self.assertEqual("content", validator.allowed_routine_path("_articles/ah-art-001.md", POLICY))
        self.assertEqual("media", validator.allowed_routine_path("assets/uploads/articles/example.png", POLICY))
        self.assertIsNone(validator.allowed_routine_path(".github/workflows/cms-content-integrity.yml", POLICY))
        self.assertIsNone(validator.allowed_routine_path("assets/main.js", POLICY))

    def test_media_signature_and_filename_controls(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            good = root / "safe-image.png"
            Image.new("RGB", (8, 8)).save(good, "PNG")
            self.assertEqual([], validator.validate_media_file(good, POLICY, upload=True))
            bad_name = root / "Unsafe Image.png"
            Image.new("RGB", (8, 8)).save(bad_name, "PNG")
            self.assertTrue(validator.validate_media_file(bad_name, POLICY, upload=True))
            mismatch = root / "wrong.jpg"
            Image.new("RGB", (8, 8)).save(mismatch, "PNG")
            self.assertTrue(validator.validate_media_file(mismatch, POLICY, upload=True))

    def test_svg_active_content_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "unsafe.svg"
            path.write_text('<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>')
            issues = validator.validate_media_file(path, POLICY, upload=True)
            self.assertTrue(issues)

if __name__ == "__main__":
    unittest.main()
