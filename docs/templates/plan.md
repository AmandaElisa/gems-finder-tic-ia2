# <topic> Implementation Plan

**Goal:** One sentence.

**Architecture:** Two or three sentences on the approach and the task ordering,
including why that order and not another.

**Tech Stack:** What this touches.

**Spec:** [`./spec.md`](./spec.md)

## Global Constraints

Project-wide requirements, one line each, values copied verbatim from the spec.
Every task implicitly includes this section. Always state: the branch, the
language rule, what must NOT be touched, and the commit trailer.

## File Structure

| File | Responsibility |
|---|---|
|  |  |

One responsibility per file. If two files always change together, ask whether
they are one file.

---

### Task N: <name>

**Files:**
- Create / Modify / Test: exact paths, with line numbers when modifying.

**Interfaces:**
- Consumes: exact signatures this task uses from earlier tasks.
- Produces: exact names and types later tasks rely on. An implementer sees
  only their own task — this block is how they learn the neighbouring names.

Background the implementer needs: existing behaviour, formulas, gotchas.

- [ ] **Step 1: Write the failing test** — with the actual test code.
- [ ] **Step 2: Run it and confirm it fails** — with the command and the
      expected failure message.
- [ ] **Step 3: Implement** — with the actual code.
- [ ] **Step 4: Run it and confirm it passes** — with the command and the
      expected count.
- [ ] **Step 5: Commit** — with the actual commit command.

No "TBD", no "add error handling", no "similar to Task N". If a step does not
contain what the implementer needs to type, it is not finished.
