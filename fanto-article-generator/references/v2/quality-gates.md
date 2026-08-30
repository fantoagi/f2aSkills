# Quality Gates v2

## Gate levels

### G1 Source integrity — BLOCKER

- Source body is complete enough for the requested output.
- Required images, links, code blocks, and sections are preserved when the task is translation or source-based adaptation.
- Source locators exist for high-risk claims and direct quotes.

### G2 Facts, quotes, and attribution — BLOCKER

- No untracked high-risk claim.
- No unverified high-risk claim stated as certain fact.
- No synthetic quote in quotation marks.
- Numbers, dates, product names, and causal direction are consistent with the source or verification record.
- Source opinions, author inference, and author judgment are distinguishable.

### G3 Thesis, stance, and structure — BLOCKER

- Brief contains a one-sentence core thesis.
- Article delivers the promise made by the final title.
- Each section advances the thesis or supplies evidence, context, counterpoint, or action.
- The conclusion returns to the reader's question rather than adding a generic uplift.
- When C4 applies, the Stance Seed is visible in the article and is not fused into source attribution.

### G4 Reader value and H tension — BLOCKER in Standard/High-risk, WARNING in Lite

- The target reader is specific.
- A reader can name the new judgment, method, or action after reading.
- The article contains a concrete “so what” for the target role.
- Removing a paragraph removes information, evidence, or a necessary transition.
- A plausible concrete forwarding message exists.
- The article has a source-backed contrast, open question, surprising observation, or concrete tension. In Standard, A-explainer, B-analysis, and C-commentary treat `curiosity_tension` as a required non-zero dimension. B-news, C-faithful, and C-retelling may use an information/source-hook policy instead of inventing drama, but the Brief must explicitly record “无新增悬念，采用信息型标题” (or an equivalent reason).

### G5 Language, technical precision, and rendering — BLOCKER/WARNING

Blockers:

- `references/v2/editor-technical-gate.md` is not completed for Standard/High-risk tasks.
- Broken Markdown, image path, source link, code fence, or required frontmatter.
- Technical mechanism is ambiguous or materially wrong.
- Core terms change meaning across the article.

Warnings:

- Repeated em dashes, triads, bold conclusions, generic transitions, or overuse of quotes.
- AI-flavored phrasing, rhythm uniformity, and “升华” language.
- Warnings require editorial judgment; they are not automatically failures.

## Complexity routing

- Lite may complete G1, G3, and basic G5; G2 is required for any external claim, and C4 still applies to A-explainer when that subtype is selected.
- Standard completes all five gates.
- High-risk completes all five plus source verification and quote audit.

## Delivery result

Use one of:

- `通过` — no blockers.
- `通过但有警告` — no blockers, warnings remain with rationale.
- `未通过` — at least one blocker remains; list the claim, section, or file requiring repair.
