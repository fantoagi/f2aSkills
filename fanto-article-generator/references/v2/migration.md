# v1 → v2 migration notes

## Default

New invocations use v2. The public modes A/B/C/D/R and the existing Markdown frontmatter remain compatible.

## Explicit legacy route

Use `v1`, `legacy`, “按旧版流程”, “不要走新流程”, or “保持原来的完整阶段输出” in a request to use `legacy/SKILL.v1.md` and the original mode references.

## Historical output

Existing files under `output/` are not rewritten. They can be scanned with the new tools for diagnosis, but they are not required to satisfy v2 runlog or reader-value artifacts.

## v2 artifacts

- Lite: `runlog/<topic>/stage-01-brief.md`, `stage-06-audit.md`
- Standard: intake, brief, source inventory, optional C4 stance (`stage-03-stance.md`), claims ledger (`claims.md` plus optional `stage-03-claims.md` snapshot), outline, title, audit; Standard/High-risk also complete the v2 Editor Technical Gate in `stage-06-audit.md`
- High-risk: Standard plus verification, quote audit (`stage-03-quotes.md`), and translation audit files; C4 and H are separate checks, and H is explicitly exempted only when the Brief records a justified information-type/source-hook policy

## Tool behavior

`c2_scan.py` defaults to v2: style findings are warnings, while semantic, terminology, and rendering findings can block. Pass `--legacy` to restore the original core-scan exit behavior. The companion checks are `claims_lint.py`, `reader_value_check.py`, `stance_lint.py`, and `technical_gate_lint.py`; their findings must be aggregated into G1-G5 rather than read as isolated scores.
