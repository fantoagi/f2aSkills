# fanto-article-generator v2 references

This directory contains the v2 editorial contract while the original reference files remain available for v1/legacy compatibility.

- `editorial-brief.md`: reader, promise, evidence, limitation, and action contract.
- `claims-ledger.md`: facts, quotes, attribution, and verification fields.
- `mode-matrix.md`: A/B/C/D/R compatibility and v2 subtypes.
- `quality-gates.md`: blocker versus warning policy.
- `reader-value-rubric.md`: 0-2 scoring rubric and workflow thresholds.
- `stance-gate.md`: C4 author-position routing, independent stance generation, and delivery blockers.
- `editor-technical-gate.md`: v2 G2/G3/G5 mapping for reference logic, mechanism precision, terminology, and rendering.
- `revision-gate.md`: R1-R4 scope, upgrade, regression, and audit contract.

The mechanical checks are:

- `scripts/claims_lint.py`: claim, quote, number, URL, and verification traceability.
- `scripts/reader_value_check.py`: Brief completeness, nine reader-value dimensions, H visibility, and workflow thresholds.
- `scripts/stance_lint.py`: C4 routing, Stance Seed completeness, and article integration.
- `scripts/technical_gate_lint.py`: technical audit completeness and obvious rendering/mechanism-risk prechecks.

The v2 quality-gate namespace is G1-G5. The separate de-AI style reference uses H2-H5 only to avoid collision; scan-16 findings remain warnings and must not be treated as G2 fact blockers.

These scripts are prechecks, not substitutes for source verification or human editorial judgment.

The published article remains `output/<topic>/index.md`; internal artifacts belong in `runlog/<topic>/`.
