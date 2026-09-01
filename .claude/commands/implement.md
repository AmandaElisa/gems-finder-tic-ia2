---
description: Execute an approved task list in order, test-first, one commit per task
argument-hint: [path to spec folder, or blank for the most recent]
---

Target: $ARGUMENTS — if blank, use the most recently modified folder under
`docs/specs/`.

Read its `tasks.md`, `plan.md` and `docs/constitution.md`. Then work the tasks
in order. For each one:

1. Write the failing test first. Run it. Confirm it fails, and that it fails
   for the reason you expect.
2. Write the minimal code that passes it. Run it. Confirm it passes.
3. Run the whole suite (`pytest`) — not just the new test — before committing.
4. Commit, with the trailer from the plan's Global Constraints.
5. Tick the box in `tasks.md`.

Rules:

- Do not start the next task until the current one's tests pass and are
  committed.
- Never edit a test to make it pass. If a test and the code disagree, work out
  which one is wrong and say so.
- Never claim something passes without having run it and read the output.
- If the work turns out bigger than the task says, stop and say so. Record it
  in `tasks.md`'s "Deferred" section rather than quietly widening scope.
- If you find a real problem in the plan, say it in a sentence or two and keep
  going under a stated assumption; do not silently improvise a different design.

When every box is ticked, report what landed and what was deferred.
