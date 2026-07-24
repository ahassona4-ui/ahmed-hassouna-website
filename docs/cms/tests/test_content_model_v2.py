from pathlib import Path
from copy import deepcopy
import importlib.util
import json
import unittest

import yaml
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[3]
TOOLS = ROOT / "docs/cms/tools"
FIX = Path(__file__).resolve().parent / "fixtures"

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

migrator = load_module("migrator", TOOLS / "migrate_content_model_v1_to_v2.py")
serializer = load_module("serializer", TOOLS / "simulate_pages_serializer.py")
content_validator = load_module("content_validator", TOOLS / "validate_content_model_v2.py")

CONFIG = yaml.safe_load((ROOT / ".pages.yml").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "docs/cms/schemas/content-model.schema.json").read_text(encoding="utf-8"))
CLASSIFICATION = json.loads((ROOT / "docs/cms/state-classification-v2.json").read_text(encoding="utf-8"))
SCHEMA_VALIDATOR = Draft202012Validator(SCHEMA, format_checker=FormatChecker())

def fm(path):
    text = path.read_text(encoding="utf-8")
    end = text.find("\n---", 4)
    return yaml.safe_load(text[4:end]) or {}

def schema_errors(record):
    return list(SCHEMA_VALIDATOR.iter_errors(record))

def semantic_errors(record):
    content_id = record.get("article_id") or record.get("project_id")
    return content_validator.validate_record_semantics(record, content_id, CLASSIFICATION)

def all_errors(record):
    return schema_errors(record) + semantic_errors(record)

class ContentModelV2Candidate003Tests(unittest.TestCase):
    def test_article_fixture_mapping(self):
        self.assertEqual(
            migrator.migrate(fm(FIX / "v1-legacy-article.md"), CLASSIFICATION),
            fm(FIX / "v2-legacy-article.md"),
        )

    def test_ah_art_002_fixture_mapping(self):
        self.assertEqual(
            migrator.migrate(fm(FIX / "v1-ah-art-002.md"), CLASSIFICATION),
            fm(FIX / "v2-ah-art-002.md"),
        )

    def test_project_fixture_mapping(self):
        self.assertEqual(
            migrator.migrate(fm(FIX / "v1-decorative-project.md"), CLASSIFICATION),
            fm(FIX / "v2-decorative-project.md"),
        )

    def test_second_pass_idempotence(self):
        for folder in ("_articles", "_projects"):
            for path in (ROOT / folder).glob("*.md"):
                record = fm(path)
                self.assertEqual(record, migrator.migrate(record, CLASSIFICATION), str(path))

    def test_hosted_serializer_idempotence(self):
        for folder, name in (("_articles", "articles"), ("_projects", "projects")):
            schema = serializer.schema_for(CONFIG, name)
            for path in (ROOT / folder).glob("*.md"):
                record = fm(path)
                self.assertEqual(record, serializer.hosted_update(record, schema, CONFIG), str(path))

    def test_false_is_preserved(self):
        value = {"featured": False, "zero": 0}
        self.assertEqual(value, serializer.sanitize_object(value))

    def test_non_runtime_samples_validate(self):
        samples = yaml.safe_load((ROOT / "docs/cms/samples/non-runtime-samples.yml").read_text(encoding="utf-8"))
        for name, record in samples.items():
            self.assertEqual([], all_errors(record), name)

    def test_hosted_serializer_sample_creation(self):
        samples = yaml.safe_load((ROOT / "docs/cms/samples/non-runtime-samples.yml").read_text(encoding="utf-8"))
        for name, record in samples.items():
            collection = "articles" if record.get("content_type") == "article" else "projects"
            self.assertEqual(
                record,
                serializer.hosted_create(record, serializer.schema_for(CONFIG, collection), CONFIG),
                name,
            )

    def test_state_payload_guards(self):
        record = fm(FIX / "v2-legacy-article.md")
        changed = deepcopy(record)
        changed["publication_date_state"] = "recorded"
        self.assertTrue(schema_errors(changed))
        changed = deepcopy(record)
        changed["media_state"] = "ready"
        self.assertTrue(schema_errors(changed))
        changed = deepcopy(record)
        changed["claims_state"] = "structured"
        self.assertTrue(schema_errors(changed))

    def test_meaningful_and_decorative_media_rules(self):
        record = fm(FIX / "v2-decorative-project.md")
        changed = deepcopy(record)
        changed["media"]["decorative"] = False
        self.assertTrue(schema_errors(changed))
        changed = deepcopy(record)
        changed["media"]["alt"] = {"ar": "وصف", "en": "Description"}
        self.assertTrue(schema_errors(changed))

    def test_governance_decision_001_classification(self):
        records = CLASSIFICATION["records"]
        for article_id in ("AH-ART-001", "AH-ART-002", "AH-ART-003"):
            self.assertEqual("none", records[article_id]["claims_state"])
        for project_id in ("AH-PRJ-001", "AH-PRJ-002", "AH-PRJ-003", "AH-PRJ-004", "AH-PRJ-005"):
            self.assertEqual("legacy_embedded", records[project_id]["claims_state"])

    def test_article_legacy_embedded_is_rejected(self):
        record = fm(FIX / "v2-ah-art-002.md")
        record["claims_state"] = "legacy_embedded"
        self.assertTrue(schema_errors(record))

    def test_pages_uses_only_publication_date_state(self):
        pages = (ROOT / ".pages.yml").read_text(encoding="utf-8")
        self.assertNotIn("legacy_date_pending", pages)
        self.assertIn("publication_date_state", pages)

    def test_current_records_do_not_require_main_js_change(self):
        for path in (ROOT / "_articles").glob("*.md"):
            record = fm(path)
            self.assertEqual("none", record["media_state"])
            self.assertNotIn("media", record)
        for path in (ROOT / "_projects").glob("*.md"):
            record = fm(path)
            self.assertEqual("ready", record["media_state"])
            self.assertTrue(record["media"]["decorative"])
            self.assertNotIn("alt", record["media"])

    def test_no_legacy_date_field(self):
        for path in (ROOT / "_articles").glob("*.md"):
            record = fm(path)
            self.assertNotIn("legacy_date_pending", record)
            self.assertNotIn("published_at", record)

    def test_review_and_claim_lifecycle_cases(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        for name, case in cases.items():
            errors = all_errors(case["record"])
            if case["expected_valid"]:
                self.assertEqual([], errors, name)
            else:
                self.assertTrue(errors, name)

    def test_pending_review_without_reviewer_and_notes_passes(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertEqual([], all_errors(cases["pending_review_without_reviewer_notes_pass"]["record"]))

    def test_recorded_review_missing_required_metadata_fails(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        for name in (
            "recorded_review_without_reviewer_fail",
            "recorded_review_without_timestamp_fail",
            "recorded_review_without_timezone_fail",
        ):
            self.assertTrue(all_errors(cases[name]["record"]), name)

    def test_not_recorded_cannot_complete_review(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["approved_future_review_with_not_recorded_fail"]["record"]))
        self.assertTrue(all_errors(cases["rejected_future_review_with_not_recorded_fail"]["record"]))

    def test_legacy_unrecorded_is_migration_only(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["legacy_unrecorded_outside_migrated_allowlist_fail"]["record"]))

    def test_approved_claim_requires_timezone_aware_approval(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["approved_structured_claim_without_approved_at_fail"]["record"]))
        self.assertTrue(all_errors(cases["approved_structured_claim_without_timezone_fail"]["record"]))

    def test_quantitative_and_status_claims_require_boundary(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["quantitative_claim_without_boundary_fail"]["record"]))
        self.assertTrue(all_errors(cases["status_claim_without_boundary_fail"]["record"]))

    def test_valid_quantitative_and_status_claims_pass(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertEqual([], all_errors(cases["valid_quantitative_claim_pass"]["record"]))
        self.assertEqual([], all_errors(cases["valid_status_claim_pass"]["record"]))

    def test_credential_requires_evidence(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["credential_claim_without_evidence_fail"]["record"]))

    def test_baseline_approved_is_migration_governed(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["baseline_approved_outside_migrated_allowlist_fail"]["record"]))

    def test_publication_date_lifecycle_cycle_003(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["archived_article_unassigned_fail"]["record"]))

    def test_published_article_media_gate_cycle_003(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["published_article_planned_fail"]["record"]))
        self.assertEqual([], all_errors(cases["published_article_none_pass"]["record"]))
        self.assertEqual([], all_errors(cases["published_article_ready_valid_media_pass"]["record"]))

    def test_published_project_media_gate_cycle_003(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["published_project_none_fail"]["record"]))
        self.assertTrue(all_errors(cases["published_project_planned_fail"]["record"]))
        self.assertEqual([], all_errors(cases["published_project_ready_valid_media_pass"]["record"]))

    def test_review_decision_lifecycle_cycle_003(self):
        cases = yaml.safe_load((FIX / "review-claim-lifecycle-cases.yml").read_text(encoding="utf-8"))
        self.assertTrue(all_errors(cases["pending_review_recorded_fail"]["record"]))
        self.assertEqual([], all_errors(cases["approved_recorded_review_pass"]["record"]))
        self.assertEqual([], all_errors(cases["rejected_recorded_review_pass"]["record"]))
        self.assertEqual([], all_errors(cases["under_review_pending_not_recorded_pass"]["record"]))

if __name__ == "__main__":
    unittest.main()
