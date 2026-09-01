---
description: Cross-check spec, plan, tasks and code for gaps and drift
argument-hint: [path to spec folder, or blank for the most recent]
---

Target: $ARGUMENTS — if blank, use the most recently modified folder under
`docs/specs/`.

Read `spec.md`, `plan.md`, `tasks.md`, `docs/constitution.md`, and the code the
plan says it touched. Run `pytest`. Then report, as four short lists:

1. **Spec requirements with no task.** Walk the spec's §6 Verification list and
   §2 Goal; point at the task covering each, or name the gap.
2. **Tasks with no spec requirement.** Work that appeared without being asked
   for — scope creep, or a spec that was never updated.
3. **Drift.** Names, signatures, thresholds or paths that differ between spec,
   plan, tasks and the actual code. A function called one thing in Task 3 and
   another in Task 7 is a bug, not a typo. Check cited numbers and file paths
   by running the commands, not by reading — and check them on the branch you
   are on, since a citation measured elsewhere can be silently wrong here.
4. **Constitution violations.** Each of the five principles, checked against
   what actually landed. Quote the offending line.

End with the `pytest` result, quoted, and one sentence: ready, or not ready and
why. Report what you found, not what you hope — say plainly if something you
could not check remains unchecked.

Do not fix anything. This command reports.
