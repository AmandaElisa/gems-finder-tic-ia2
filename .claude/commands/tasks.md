---
description: Extract the tickable task list from an approved plan
argument-hint: [path to spec folder, or blank for the most recent]
---

Target: $ARGUMENTS — if blank, use the most recently modified folder under
`docs/specs/`.

Read its `plan.md`. Write `tasks.md` beside it, from
`docs/templates/tasks.md`.

One entry per plan task, in the plan's order. Each entry carries:

- the number and name, matching the plan exactly, so the two can be diffed;
- the files it touches;
- **Accept:** the exact command to run and the exact expected result. "Tests
  pass" is not an acceptance check; `pytest -v` → `46 passed` is.

Any task whose acceptance check you cannot state concretely is a task the plan
under-specified. Say which one and why, rather than inventing a vague check.

Keep the "Deferred" section, even if empty — it is where work that comes up
mid-implementation gets recorded instead of silently expanding scope.
