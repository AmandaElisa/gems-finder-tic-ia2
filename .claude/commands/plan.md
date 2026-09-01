---
description: Turn an approved spec into a file map and an ordered task breakdown
argument-hint: [path to spec folder, or blank for the most recent]
---

Target: $ARGUMENTS — if blank, use the most recently modified folder under
`docs/specs/`.

Read its `spec.md`, `docs/constitution.md`, and enough of the actual code to
plan against reality rather than against your assumptions. Follow the patterns
already in the repo.

Write `plan.md` beside the spec, from `docs/templates/plan.md`:

1. **Global Constraints** — copy the project-wide rules verbatim from the spec.
   Always state the branch, the English-engineering / Portuguese-product rule,
   what must NOT be touched, and the commit trailer.
2. **File Structure** — every file created or modified, and the one
   responsibility each carries. Lock the decomposition here.
3. **Tasks** — each with exact file paths, a Consumes/Produces interface block,
   the background an implementer with no context would need, and bite-sized
   steps: failing test, run it fail, implement, run it pass, commit.

Write the actual test code and the actual commit commands. No "TBD", no "add
error handling", no "similar to Task N" — an implementer may read tasks out of
order and sees only their own.

Any number you write down — a line count, a test count, an expected output —
run the code and check it before writing it, and say which branch you measured
on. A plan citing a number nobody verified is worse than one that omits it.

Then check your plan against the spec: can you point at a task for every
requirement? Fix gaps inline.

Report the path. Do not write code and do not create `tasks.md` — `/tasks`
does that.
