---
description: Resolve underspecified areas in a spec before planning
argument-hint: [path to spec folder, or blank for the most recent]
---

Target: $ARGUMENTS — if blank, use the most recently modified folder under
`docs/specs/`.

Read its `spec.md` and `docs/constitution.md`. Then hunt for what is
underspecified, specifically:

- Requirements that could be read two different ways.
- Numbers with no stated source (thresholds, limits, page sizes).
- Behaviour on the empty, missing or malformed case.
- Anything the constitution's five principles have an opinion about, where the
  spec is silent.
- Work the spec implies but never states.

Ask about them ONE per message, most consequential first, preferring multiple
choice with your recommendation first. Do not batch them.

As each is answered, write the decision AND its reasoning into the spec's §7,
renaming the section to "Resolved questions" and ticking the box. Never delete
a question — a resolved question is the record of why.

When nothing consequential is left, say so plainly and stop. Do not drift into
planning.
