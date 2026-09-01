# Spec — Spec-driven orchestration for Gems Finder

> Adapts the spec-driven development cycle from [github/spec-kit](https://github.com/github/spec-kit)
> into an orchestration layer that lives in this repo and works for all five
> members of Grupo 9 with nothing to install.

**Status:** design approved, pending spec review · **Date:** 2026-09-01 · **Author:** Amanda Elisa

---

## 1. Problem

There is no orchestration layer in this repository. `.claude/` holds three
installed skills (`debugging-streamlit`, `developing-with-streamlit`,
`python-testing-patterns`, tracked in `skills-lock.json`) and nothing else. No
`CLAUDE.md` exists — not in the working tree, and not anywhere in git history.

Consequences today:

- Project context (Streamlit, simulated data, the approved HTML prototype as
  visual spec, the Spotify API deprecation that shaped the design) has to be
  re-explained to an agent in every new session.
- How work moves from idea to code lives in one person's head. The other four
  members have no written process to follow.
- `docs/spec-integracao-modelo-real.md` proves the appetite for spec-driven
  work — it is a genuine spec, with a today/target table, the API constraint
  that motivated the design, a deploy checklist and open questions. It is a
  one-off, with no process around it and no second example.

## 2. Goal and non-goals

**Goal.** A self-contained, versioned orchestration layer that encodes the
spec-kit cycle, adapted to this project's size and vocabulary.

**Non-goals** — explicitly out of scope for this work:

| Out of scope | Why |
|---|---|
| Installing the `specify` CLI, `.specify/`, presets, extensions | Requires uv + Python 3.11+; dumps generated English scaffolding into a 1,894-line academic repo |
| `/speckit.converge` | Built for large codebases drifting from their spec; this one fits in one head |
| Migrating Python identifiers to English | Real work, touches all 16 files — becomes the first structural-track job, with its own spec |
| Rewriting UI copy | Stays in Portuguese, permanently (see principle 1) |

## 3. Decisions

| Decision | Rationale |
|---|---|
| Adapt the methodology; do not install the framework | No new dependency, our vocabulary, and no generated files nobody owns |
| Classify work by size, three tracks | The five most recent commits are all UI polish. A ritual applied to a CSS tweak costs more than the tweak, and the process gets abandoned by week two |
| English for the engineering layer | Matches global code convention, and removes the pt-BR column translation layer that `spec-integracao-modelo-real.md` §6 has to maintain when the real dataset lands |
| Portuguese for UI copy, permanently | The app is for a Brazilian user; `docs/gems-finder-prototipo.html` is the approved visual spec |
| Python code stays Portuguese for now | Renaming 16 files with zero tests in the repo has no safety net. Tests come first (§8), then the rename |
| Templates derived from our own existing spec | `spec-integracao-modelo-real.md` already has the right shape and the group's language; better than an imported template |
| Tests are a required principle, not an aspiration | An unenforced testing principle discredits the whole constitution |

## 4. Command mapping

Six of spec-kit's nine commands earn their place. `/analyze` and `/checklist`
collapse into one `/verify`; `/converge` is dropped (§2).

| spec-kit | ours | produces |
|---|---|---|
| `/speckit.constitution` | `docs/constitution.md` | Written once; revised when a principle breaks |
| `/speckit.specify` | `/specify` | `spec.md` — what and why, no technical choices |
| `/speckit.clarify` | `/clarify` | Resolved ambiguities appended to `spec.md` |
| `/speckit.plan` | `/plan` | `plan.md` — files, interfaces, order |
| `/speckit.tasks` | `/tasks` | `tasks.md` — numbered, each with an acceptance check |
| `/speckit.implement` | `/implement` | Code, executing `tasks.md` in order |
| `/analyze` + `/checklist` | `/verify` | Consistency report: spec × plan × tasks × code |

## 5. Track classification

The entry gate. Every request gets classified out loud before work starts, so
the classification can be challenged.

| Track | Trigger | Flow |
|---|---|---|
| **Polish** | One file; CSS, copy, or an obvious bug | Straight to code, descriptive commit |
| **Feature** | New page, search mode, or metric | `/specify` → `/plan` → `/tasks` → `/implement` |
| **Structural** | Changes a data source, or an interface other modules consume | constitution check → `/specify` → `/clarify` → `/plan` → `/tasks` → `/verify` → `/implement` |

**The ratchet turns one way.** Complexity discovered mid-task raises the
track and never lowers it, and whoever raises it says so out loud. Reaching
for a lighter track to skip work is itself the signal to take the heavier one.

Calibration against real history: the five most recent commits on
`feat/link-github-sidebar` (scrollable mobile tabs, thin scrollbar, GitHub
link) are all Polish — unchanged by this proposal. Replacing simulated data
with the real model is Structural.

## 6. File layout

```
CLAUDE.md                          entry point: context, conventions, the three tracks
docs/
  constitution.md                  the principles (§7)
  templates/
    spec.md  plan.md  tasks.md     derived from spec-integracao-modelo-real.md
  specs/
    2026-09-01-spec-driven-orchestration/   this document
    <date>-<topic>/                one folder per Feature/Structural job
.claude/commands/
  specify.md  clarify.md  plan.md
  tasks.md    implement.md  verify.md       versioned, native, zero install
tests/
  test_recomendacao.py             the first real tests (§8)
```

`CLAUDE.md` stays short enough to be read in full. It carries project context,
the conventions, the three tracks, and a pointer to the constitution — not a
copy of it.

## 7. Constitution principles

Derived from what this repo already does, not invented.

1. **English in engineering, Portuguese in the product.** Identifiers,
   docstrings, comments, commits, specs and commands are English. Everything
   the user reads is Portuguese. `docs/gems-finder-prototipo.html` is the
   authority on user-facing wording.
2. **Be honest about what is simulated.** The `AVISOS` block in `app.py`, the
   `TODO` on `PRECISAO_8` in `src/dados.py:134`, and "Cobertura é calculada de
   fato" set the standard. As a rule: a placeholder metric never reaches the UI
   without a visible marker saying so.
3. **The HTML prototype is the visual spec.** Divergence from
   `docs/gems-finder-prototipo.html` is either a bug or a decision recorded in
   a spec. Never a silent drift.
4. **Stable interfaces, small modules.** `carregar_catalogo()` must swap from
   simulated data to the real dataset without the rest of the app noticing —
   §6 of the real-model spec already promises this. `src/ui/estilo.py` is the
   largest file in the repo — 280 lines on `main`, 318 on
   `feat/link-github-sidebar`. Roughly 300 lines is the ceiling, not the target.
5. **The logic that picks results is tested.** `src/recomendacao.py` decides
   which gem a user sees; it carries tests. Streamlit UI is verified by running
   the app (`debugging-streamlit` skill), not by mocking widgets.

## 8. Testing scope

The repo has zero tests: no `test_*.py`, no `conftest.py`, no `pyproject.toml`,
and `pytest` is absent from `requirements.txt` — while the
`python-testing-patterns` skill sits installed and unused.

This work adds `pytest` to a new `requirements-dev.txt` — not to
`requirements.txt`, which Streamlit Community Cloud installs on deploy (§5 of
the real-model spec); a test dependency has no business in production — plus a
`pytest.ini` and `tests/test_recomendacao.py`.
`src/recomendacao.py` is a good target: fourteen functions, no Streamlit
import, and every one of them deterministic except `novo_id_playlist` (which
draws from `random`). Several carry exact thresholds worth locking down.

The table below is the full scope. Deliberately excluded: `novo_id_playlist`
(random; a test would only restate the format), and `media`, `centro`,
`montar_resultado`, `montar_resultado_conta` (thin composition over the
functions already covered — they get exercised through `garimpar`).

| Function | What the test pins |
|---|---|
| `round_js` | Half-up rounding, matching JavaScript `Math.round` (`.5` → up, negatives included) |
| `match` | Clamp at 31 and 99; the obscurity bonus raises a low-popularity track |
| `rar` | Boundaries at 8 and 17 — the exact values, not just either side |
| `garimpar` | Empty result keeps an `int64` `match` column; `kind="stable"` preserves catalog order on ties; respects `limite` |
| `cobertura` | Empty base returns 0 instead of dividing by zero |
| `rotulo_profundidade` | Boundaries at 10, 20, 30 |
| `humor_da_faixa` | Precedence order: sad beats high-energy beats instrumental |
| `email_valido`, `nome_do_email` | Prototype regex parity; separator handling (`._-`) and capitalization |

These tests are also the safety net the English rename needs. That ordering is
deliberate: tests, then rename.

## 9. Verification

This work is done when:

1. A new session with no context can read `CLAUDE.md` and correctly classify a
   request into one of the three tracks.
2. `/specify` through `/verify` each run and produce their artifact in
   `docs/specs/<date>-<topic>/`.
3. `pytest` passes, and each function in the §8 table has at least one test
   pinning a stated boundary.
4. Every constitution principle traces to something the repo already does or
   has explicitly decided — no principle without a referent.

## 10. Resolved questions

- [x] **`docs/spec-integracao-modelo-real.md` moves** to
      `docs/specs/2026-08-30-real-model-integration/spec.md`, via `git mv` so
      history follows. Two homes for specs is the first thing to rot. Its
      Portuguese content stays as written — it predates the English
      convention, and retranslating good content buys nothing. Verified: no
      file in the repo references it by path, so the move breaks nothing. The
      repository tree in `README.md` does need updating for the new `docs/`
      layout — it currently lists only `gems-finder-prototipo.html`.
- [x] **The §8 tests ship with this work.** Principle 5 is decorative without
      them, and they are the safety net the English rename depends on.

No open questions remain.
