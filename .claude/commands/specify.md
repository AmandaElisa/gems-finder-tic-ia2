---
description: Classify the work, then write the spec — what and why, no technical how
argument-hint: [what you want to build]
---

The user wants: $ARGUMENTS

First, read `docs/constitution.md`. Then classify this request out loud, using
the three tracks in `CLAUDE.md`:

- **Polish** — one file; CSS, copy, or an obvious bug. Say so, say no spec is
  needed, and stop. Do not write a spec for a Polish job.
- **Feature** or **Structural** — continue below.

State the classification and let the user challenge it before you write
anything.

Then:

1. Ask the questions that matter, ONE per message, preferring multiple choice.
   You are trying to understand purpose, constraints and success criteria —
   not implementation.
2. Create `docs/specs/<YYYY-MM-DD>-<slug>/spec.md` from
   `docs/templates/spec.md`, where `<slug>` is 2–4 words, lowercase, hyphenated.
3. Fill every section. A section you cannot fill is an open question in §7,
   with your recommendation — never a "TBD".
4. Keep technical choices OUT. No library names, no file paths, no function
   signatures. Those belong in `/plan`. If you cannot describe the change
   without them, you have not understood the problem yet.
5. Re-read what you wrote and check: placeholders, sections that contradict
   each other, requirements that could be read two ways. Fix them inline.
6. Report the path and ask the user to review it before `/plan`.

Do not write code. Do not create the plan. Stop after the spec.
