from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
FIXTURES = ROOT / "tests" / "fixtures"


def run_script(script: str, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        capture_output=True,
    )


class V2ScriptsTest(unittest.TestCase):
    def test_good_claims_and_reader_value(self):
        claims = run_script(
            "claims_lint.py",
            str(FIXTURES / "article-good.md"),
            "--ledger",
            str(FIXTURES / "claims-good.md"),
            "--high-risk",
            "--json",
        )
        self.assertEqual(claims.returncode, 0, claims.stdout + claims.stderr)
        claims_data = json.loads(claims.stdout)
        self.assertEqual(claims_data["blockers"], 0)

        reader = run_script(
            "reader_value_check.py",
            str(FIXTURES / "article-good.md"),
            "--brief",
            str(FIXTURES / "brief-good.md"),
            "--workflow",
            "High-risk",
            "--mode",
            "C-commentary",
            "--json",
        )
        self.assertEqual(reader.returncode, 0, reader.stdout + reader.stderr)
        reader_data = json.loads(reader.stdout)
        self.assertGreaterEqual(reader_data["score"], 13)
        self.assertEqual(len(reader_data["dimensions"]), 9)
        self.assertGreaterEqual(reader_data["score"], 15)

    def test_bad_claims_block(self):
        result = run_script(
            "claims_lint.py",
            str(FIXTURES / "article-bad.md"),
            "--ledger",
            str(FIXTURES / "claims-good.md"),
            "--high-risk",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("QUOTE_UNTRACKED", result.stdout)
        self.assertIn("NUMBER_UNTRACKED", result.stdout)

    def test_bad_brief_blocks(self):
        result = run_script(
            "reader_value_check.py",
            str(FIXTURES / "article-bad.md"),
            "--brief",
            str(FIXTURES / "brief-bad.md"),
            "--workflow",
            "Standard",
            "--mode",
            "C-commentary",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("AUDIENCE_UNCLEAR", result.stdout)
        self.assertIn("THESIS_MISSING", result.stdout)

    def test_c2_style_warnings_do_not_block_v2(self):
        result = run_script("c2_scan.py", str(FIXTURES / "style-warning.md"), "--json")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["blockers"], 0)
        self.assertGreaterEqual(data["warnings"], 0)
        self.assertEqual(data["workflow"], "v2")
        scan16 = next(group for group in data["groups"] if group["id"] == 16)
        self.assertIn("H2-H5", scan16["name"])

    def test_c2_legacy_flag_remains_available(self):
        result = run_script("c2_scan.py", str(FIXTURES / "style-warning.md"), "--legacy")
        self.assertIn("工作流：v1/legacy", result.stdout)

    def test_c2_number_and_backtick_integrity_are_blockers(self):
        result = run_script(
            "c2_scan.py",
            str(FIXTURES / "c2-integrity-zh.md"),
            "--original-en",
            str(FIXTURES / "c2-integrity-en.md"),
            "--json",
        )
        data = json.loads(result.stdout)
        severities = {group["id"]: group["severity"] for group in data["groups"]}
        self.assertEqual(severities[8], "BLOCKER")
        self.assertEqual(severities[9], "BLOCKER")

    def test_high_risk_unverified_claim_blocks(self):
        result = run_script(
            "claims_lint.py",
            str(FIXTURES / "article-unverified.md"),
            "--ledger",
            str(FIXTURES / "claims-unverified.md"),
            "--high-risk",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("HIGH_RISK_UNVERIFIED", result.stdout)

    def test_synthetic_quote_blocks(self):
        result = run_script(
            "claims_lint.py",
            str(FIXTURES / "article-synthetic.md"),
            "--ledger",
            str(FIXTURES / "claims-synthetic.md"),
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("QUOTE_SYNTHETIC", result.stdout)

    def test_high_risk_unverified_fact_blocks_even_when_not_time_sensitive(self):
        result = run_script(
            "claims_lint.py",
            str(FIXTURES / "article-unverified.md"),
            "--ledger",
            str(FIXTURES / "claims-unverified-nontime.md"),
            "--high-risk",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("HIGH_RISK_UNVERIFIED", result.stdout)

    def test_required_stance_reaches_article(self):
        result = run_script(
            "stance_lint.py",
            str(FIXTURES / "article-good.md"),
            "--stance",
            str(FIXTURES / "stance-good.md"),
            "--mode",
            "C-commentary",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["blockers"], 0)

    def test_rephrased_stance_is_manual_review_not_false_blocker(self):
        result = run_script(
            "stance_lint.py",
            str(FIXTURES / "article-rephrased-stance.md"),
            "--stance",
            str(FIXTURES / "stance-good.md"),
            "--mode",
            "C-commentary",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["blockers"], 0)
        self.assertIn("STANCE_INTEGRATION_REVIEW", {item["code"] for item in data["findings"]})

    def test_required_stance_missing_blocks(self):
        result = run_script(
            "stance_lint.py",
            str(FIXTURES / "article-good.md"),
            "--mode",
            "C-commentary",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("STANCE_MISSING", result.stdout)

    def test_technical_gate_audit_passes(self):
        result = run_script(
            "technical_gate_lint.py",
            str(FIXTURES / "article-good.md"),
            "--audit",
            str(FIXTURES / "technical-audit-good.md"),
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["blockers"], 0)

    def test_technical_gate_accepts_numbered_human_readable_audit(self):
        result = run_script(
            "technical_gate_lint.py",
            str(FIXTURES / "article-good.md"),
            "--audit",
            str(FIXTURES / "technical-audit-numbered.md"),
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["blockers"], 0)

    def test_missing_h_tension_blocks_high_risk(self):
        result = run_script(
            "reader_value_check.py",
            str(FIXTURES / "article-good.md"),
            "--brief",
            str(FIXTURES / "brief-no-tension.md"),
            "--workflow",
            "High-risk",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("TENSION_MISSING", result.stdout)
        self.assertIn("curiosity_tension", result.stdout)

    def test_information_mode_may_use_explicit_no_h_policy(self):
        result = run_script(
            "reader_value_check.py",
            str(FIXTURES / "article-good.md"),
            "--brief",
            str(FIXTURES / "brief-info.md"),
            "--workflow",
            "High-risk",
            "--mode",
            "B-news",
            "--json",
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["dimensions"]["curiosity_tension"], 2)
        self.assertEqual(data["mode"], "B-news")

    def test_standard_required_h_mode_blocks_missing_tension(self):
        result = run_script(
            "reader_value_check.py",
            str(FIXTURES / "article-good.md"),
            "--brief",
            str(FIXTURES / "brief-no-tension.md"),
            "--workflow",
            "Standard",
            "--mode",
            "B-analysis",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("RUBRIC_ZERO_DIMENSION", result.stdout)
        self.assertIn("curiosity_tension", result.stdout)

    def test_lite_explainer_still_requires_c4(self):
        result = run_script(
            "stance_lint.py",
            str(FIXTURES / "article-good.md"),
            "--mode",
            "A-explainer",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("STANCE_MISSING", result.stdout)

    def test_d_reading_without_observation_cannot_claim_experience(self):
        result = run_script(
            "stance_lint.py",
            str(FIXTURES / "article-fabricated-reading.md"),
            "--mode",
            "D-reading",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("D_READING_UNSUPPORTED_EXPERIENCE", result.stdout)

    def test_faithful_mode_rejects_unrequested_author_stance(self):
        result = run_script(
            "stance_lint.py",
            str(FIXTURES / "article-good.md"),
            "--mode",
            "C-faithful",
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("AUTHOR_STANCE_FORBIDDEN", result.stdout)


class V2ContractTest(unittest.TestCase):
    def test_skill_contract_and_references_exist(self):
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        required_terms = [
            "v2", "v1", "legacy", "Lite", "Standard", "High-risk",
            "Editorial Brief", "BLOCKER", "WARNING", "A", "B-news",
            "B-analysis", "C-faithful", "C-retelling", "C-commentary",
            "D-reading", "D-learning", "D-practice", "R1", "R2", "R3", "R4",
            "output/<topic>/index.md", "runlog/<topic>/", "C4", "stance-gate",
            "curiosity_tension", "editor-technical-gate", "H2-H5",
        ]
        for term in required_terms:
            self.assertIn(term, skill, term)

        deai = (ROOT / "references/ai-humanize-gates.md").read_text(encoding="utf-8")
        self.assertIn("H2-H5", deai)
        self.assertNotIn("### G2 ", deai)

        for rel in [
            "references/ai-humanize-gates.md",
            "references/v2/editorial-brief.md",
            "references/v2/claims-ledger.md",
            "references/v2/mode-matrix.md",
            "references/v2/quality-gates.md",
            "references/v2/reader-value-rubric.md",
            "references/v2/stance-gate.md",
            "references/v2/editor-technical-gate.md",
            "references/v2/revision-gate.md",
            "legacy/SKILL.v1.md",
            "scripts/c2_scan.py",
            "scripts/claims_lint.py",
            "scripts/reader_value_check.py",
            "scripts/stance_lint.py",
            "scripts/technical_gate_lint.py",
        ]:
            self.assertTrue((ROOT / rel).exists(), rel)

    def test_technical_gate_template_uses_lint_field_keys_and_preserves_thread_g4_comment(self):
        technical_gate = (ROOT / "references/v2/editor-technical-gate.md").read_text(encoding="utf-8")
        required_fields = [
            "指代与逻辑",
            "技术机制",
            "渲染等价性",
            "概念与术语",
            "品牌与大小写",
            "正文口语词",
            "聚合结果",
        ]
        for field in required_fields:
            self.assertIn(f"- {field}：", technical_gate, field)

        # The production v2 mapping table must not teach agents the old long labels.
        for legacy_label in [
            "指代与逻辑自洽",
            "技术机制精确性",
            "概念/角色/状态一致性",
            "品牌/标题大小写",
        ]:
            self.assertNotIn(f"| {legacy_label} |", technical_gate, legacy_label)

        mode_a = (ROOT / "legacy/mode-a.v1.md").read_text(encoding="utf-8")
        stance = (ROOT / "references/stance-injection.md").read_text(encoding="utf-8")
        self.assertNotIn("ai-humanize-gates G2", mode_a)
        self.assertNotIn("ai-humanize-gates G2/G4", stance)
        self.assertIn("ai-humanize-gates H2", mode_a)
        self.assertIn("ai-humanize-gates H2/H4", stance)

        # This is a media-counting comment, not a quality-gate namespace.
        thread_script = (ROOT / "scripts/extract_x_thread.py").read_text(encoding="utf-8")
        self.assertIn("G4 fix: separate static + thumbnail counts", thread_script)

    def test_historical_output_count_is_unchanged_baseline(self):
        # Local workspaces may carry the 21 historical articles; the public skill
        # repository intentionally ships the generator, not generated output.
        output_dir = ROOT / "output"
        if not output_dir.exists():
            self.skipTest("historical output is intentionally excluded from the skill repository")
        articles = list(output_dir.glob("*/index.md"))
        if not articles:
            self.skipTest("historical output is intentionally excluded from the skill repository")
        self.assertEqual(len(articles), 21)

if __name__ == "__main__":
    unittest.main()
