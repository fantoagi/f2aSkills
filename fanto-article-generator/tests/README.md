## fanto-article-generator v2 regression tests

Run from the skill directory:

```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

The fixtures cover:

- valid and invalid Editorial Brief / claims ledger inputs;
- style warnings that do not block v2;
- legacy C2 compatibility;
- number and backtick integrity blockers;
- unverified high-risk claims, including non-time-sensitive fact claims;
- synthetic direct quotes and quote-ledger completeness;
- C4 stance routing, forbidden author stance in faithful mode, and D-reading anti-fabrication checks;
- H information-mode policy and reader-value scoring;
- v2 skill/reference contracts and the 21-article historical output baseline.

The current suite contains 19 tests. These tests do not rewrite anything under `output/`.
