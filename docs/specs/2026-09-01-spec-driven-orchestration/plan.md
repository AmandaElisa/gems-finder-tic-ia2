# Spec-Driven Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a self-contained, versioned orchestration layer that encodes the spec-kit cycle for Gems Finder, plus the first real test suite for the recommendation core.

**Architecture:** Nine tasks in two halves. Tasks 1–4 build the test suite for `src/recomendacao.py`, bottom-up (numeric core → threshold helpers → DataFrame functions → string helpers); they come first because constitution principle 5 is decorative without them and because they are the safety net the later English rename depends on. Tasks 5–9 build the orchestration itself, in dependency order: the constitution states the principles, the templates give the artifacts their shape, the commands drive the cycle, `CLAUDE.md` points at all three, and the last task moves the pre-existing spec into the new home and fixes the README tree.

**Tech Stack:** Python 3.12, pytest 8.x, pandas, Streamlit (imported by `src/dados.py` but never exercised in tests), Claude Code native slash commands (Markdown with YAML frontmatter).

**Spec:** [`docs/specs/2026-09-01-spec-driven-orchestration/spec.md`](./spec.md)

## Global Constraints

Every task's requirements implicitly include these.

- **Branch:** all work lands on `feat/spec-driven-orchestration`, already created from `main`.
- **Language — engineering:** English for identifiers, docstrings, comments, commit subjects, test names, and every file created by this plan.
- **Language — product:** Portuguese for anything a user reads. Test *assertions* therefore compare against Portuguese strings (`"Joia bruta"`, `"Bem underground"`) — that is correct, not a violation.
- **Do not rename existing Python identifiers.** `carregar_catalogo`, `dancabilidade`, `garimpar` and friends stay exactly as they are; the rename is a separate Structural-track job.
- **Do not touch `src/`, `app.py`, or `.streamlit/`.** This plan adds tests and documentation only. If a test fails because the code is wrong, stop and report — do not fix the code under cover of this plan.
- **`pytest` goes in `requirements-dev.txt`, never `requirements.txt`.** Streamlit Community Cloud installs `requirements.txt` on deploy.
- **Never call `carregar_catalogo()` or `carregar_artistas()` in tests.** Both are `@st.cache_data`-wrapped (`src/dados.py:182`, `:193`) and want a script context. Tests build small DataFrames by hand.
- **Commit trailer:** every commit ends with
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`
- **Commit style:** Conventional Commits, English subject. Scopes: `test`, `docs`, `orchestration`.

## File Structure

| File | Responsibility |
|---|---|
| `pytest.ini` (create) | Puts the repo root on `sys.path` so `from src.dados import ...` resolves; points pytest at `tests/` |
| `requirements-dev.txt` (create) | Test-only dependencies, kept out of the deploy |
| `tests/test_recomendacao.py` (create) | The whole suite for `src/recomendacao.py`, one class per function under test |
| `docs/constitution.md` (create) | The five principles, each with its referent in the code |
| `docs/templates/spec.md` (create) | Shape of a spec: what and why, no technical how |
| `docs/templates/plan.md` (create) | Shape of a plan: file map, interfaces, ordering |
| `docs/templates/tasks.md` (create) | Shape of a task list: numbered, each with an acceptance check |
| `.claude/commands/specify.md` … `verify.md` (create, 6 files) | One command per cycle phase |
| `CLAUDE.md` (create) | Entry point: project context, the three tracks, conventions, file map |
| `docs/specs/2026-08-30-real-model-integration/spec.md` (move) | The pre-existing spec, relocated via `git mv` |
| `README.md` (modify) | Repository tree updated for the new `docs/` layout and `tests/` |

One test file, not four: the tests all target one module, they share the `NEUTRAL`/`track()` helpers, and splitting them would duplicate that scaffolding. Tasks 1–4 each append one class to it.

---

### Task 1: Test harness + the numeric core

**Files:**
- Create: `pytest.ini`
- Create: `requirements-dev.txt`
- Create: `tests/test_recomendacao.py`

**Interfaces:**
- Consumes: `src.recomendacao.round_js`, `src.recomendacao.match`, `src.dados.ATRIBUTOS` (all existing).
- Produces: module-level `NEUTRAL: dict[str, float]` (the five audio attributes, all `.5`) and `track(popularidade: int = 30, **atributos: float) -> dict[str, float]`. Tasks 2–4 import nothing new; they reuse both helpers from the same file.

Background an implementer needs: `round_js` is `math.floor(valor + 0.5)`, matching JavaScript's `Math.round` — half rounds *up*, which for negatives means toward zero. `match` computes a weighted absolute distance over `ATRIBUTOS` (`energia` .25, `valencia` .25, `dancabilidade` .20, `instrumentalidade` .15, `acustica` .15), then `bruto = 100 - distancia * 135 + (30 - popularidade) * 0.15`, clamped to 31…99.

- [ ] **Step 1: Write `pytest.ini`**

```ini
[pytest]
pythonpath = .
testpaths = tests
```

`pythonpath` requires pytest >= 7. Without it, pytest's default `prepend` import mode puts `tests/` on `sys.path` but not the repo root, and `from src.dados import ...` fails with `ModuleNotFoundError: No module named 'src'`.

- [ ] **Step 2: Write `requirements-dev.txt`**

```text
# Test-only dependencies. Deliberately NOT in requirements.txt, which
# Streamlit Community Cloud installs on deploy.
-r requirements.txt
pytest>=7.0
```

- [ ] **Step 3: Write the failing test file**

Create `tests/test_recomendacao.py`:

```python
"""Tests for src/recomendacao.py — the logic that decides which gem a user sees.

Only pure functions are covered. The Streamlit UI is verified by running the
app (see CLAUDE.md), not by mocking widgets. Fixtures build small DataFrames by
hand rather than calling carregar_catalogo(), which is @st.cache_data-wrapped
and expects a script context.

Assertions compare against Portuguese strings on purpose: those are UI copy,
and UI copy stays Portuguese.
"""

from __future__ import annotations

from src.dados import ATRIBUTOS
from src.recomendacao import match, round_js

import pytest

# The five audio attributes at dead centre, so a test can move one at a time.
NEUTRAL: dict[str, float] = {atributo: .5 for atributo in ATRIBUTOS}


def track(popularidade: int = 30, **atributos: float) -> dict[str, float]:
    """A track with neutral audio attributes, overridable one by one.

    Popularity defaults to 30, the value at which match()'s obscurity bonus is
    exactly zero — so a test that does not care about popularity gets no bonus
    silently skewing its expected score.
    """
    return {**NEUTRAL, **atributos, "popularidade": popularidade}


class TestRoundJs:
    @pytest.mark.parametrize("valor, esperado", [
        (2.4, 2),
        (2.5, 3),      # half rounds up, not to even
        (-2.5, -2),    # ...which for negatives means toward zero
        (-2.6, -3),
        (0.0, 0),
    ])
    def test_matches_javascript_math_round(self, valor: float, esperado: int) -> None:
        assert round_js(valor) == esperado


class TestMatch:
    def test_clamps_at_99_for_a_perfect_fit(self) -> None:
        # Identical attributes and popularity 30 give a raw score of 100.
        assert match(track(), NEUTRAL) == 99

    def test_clamps_at_31_for_the_worst_possible_fit(self) -> None:
        # Every attribute maximally far: distance 1.0, raw score -35.
        longe = {atributo: 1.0 for atributo in ATRIBUTOS}
        alvo = {atributo: 0.0 for atributo in ATRIBUTOS}
        assert match({**longe, "popularidade": 30}, alvo) == 31

    def test_lower_popularity_earns_the_obscurity_bonus(self) -> None:
        # 0.2 away on the 0.25-weight axis: distance 0.05, raw score 93.25
        # before the bonus, plus (30 - popularidade) * 0.15.
        alvo = {**NEUTRAL, "energia": .7}
        assert match(track(popularidade=30), alvo) == 93
        assert match(track(popularidade=10), alvo) == 96
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `pytest tests/test_recomendacao.py -v`

Expected: 8 passed (5 parametrized `round_js` cases + 3 `match` cases). These test existing, working code, so they pass on the first run — that is the point.

You will also see two harmless warnings, because importing `src.dados` reaches the `@st.cache_data` decorators outside a Streamlit runtime:

```
WARNING streamlit.runtime.caching.cache_data_api: No runtime found, using MemoryCacheStorageManager
```

Leave them. They are the decorators registering, not the loaders running — the tests never call `carregar_catalogo()`. Do not add a warning filter to silence them; a filter would also hide a real caching problem later. A failure here means either the harness is wrong (`ModuleNotFoundError: No module named 'src'` → `pytest.ini` missing or misplaced) or a hand-computed expected value is wrong; recompute from the formula above before changing any assertion, and never edit `src/recomendacao.py` to make a test pass.

- [ ] **Step 5: Commit**

```bash
git add pytest.ini requirements-dev.txt tests/test_recomendacao.py
git commit -m "test: pin the numeric core of the recommendation logic

round_js half-up parity with JavaScript Math.round, and match()'s two
clamps plus the obscurity bonus. First tests in the repo; pytest lives in
requirements-dev.txt so it stays out of the Streamlit Cloud deploy.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Threshold helpers

**Files:**
- Modify: `tests/test_recomendacao.py` (append two classes and extend the imports)

**Interfaces:**
- Consumes: `NEUTRAL` and `track()` from Task 1; `src.recomendacao.rar`, `rotulo_profundidade`, `humor_da_faixa`; `src.tema.LIMA`, `PERI`, `ROSA`.
- Produces: nothing new.

Background: `rar(popularidade)` returns `("Joia bruta", LIMA)` at `<= 8`, `("Rara", ROSA)` at `<= 17`, else `("Pouco ouvida", PERI)`. `rotulo_profundidade(teto)` steps at `<= 10`, `<= 20`, `<= 30`, else. `humor_da_faixa` tests in strict order: `valencia < .3` → `"triste"`, then `energia > .75` → `"treino"`, then `instrumentalidade > .7` → `"foco"`, else `"chill"` — so the order itself is behaviour worth pinning. Note every comparison is strict: the boundary value falls through to the next branch.

- [ ] **Step 1: Extend the imports**

Replace the two import lines from `src.recomendacao` and add `src.tema`:

```python
from src.dados import ATRIBUTOS
from src.recomendacao import (
    humor_da_faixa,
    match,
    rar,
    rotulo_profundidade,
    round_js,
)
from src.tema import LIMA, PERI, ROSA
```

- [ ] **Step 2: Append the failing tests**

Append to `tests/test_recomendacao.py`:

```python
class TestRar:
    @pytest.mark.parametrize("popularidade, selo, cor", [
        (0, "Joia bruta", LIMA),
        (8, "Joia bruta", LIMA),        # boundary: <= 8 is still raw
        (9, "Rara", ROSA),
        (17, "Rara", ROSA),             # boundary: <= 17 is still rare
        (18, "Pouco ouvida", PERI),
    ])
    def test_boundaries(self, popularidade: int, selo: str, cor: str) -> None:
        assert rar(popularidade) == (selo, cor)


class TestRotuloProfundidade:
    @pytest.mark.parametrize("teto, esperado", [
        (5, "Praticamente invisível"),
        (10, "Praticamente invisível"),  # boundary
        (11, "Bem underground"),
        (20, "Bem underground"),         # boundary
        (21, "Conhecida em nicho"),
        (30, "Conhecida em nicho"),       # boundary
        (31, "Começando a aparecer"),
    ])
    def test_boundaries(self, teto: int, esperado: str) -> None:
        assert rotulo_profundidade(teto) == esperado


class TestHumorDaFaixa:
    def test_sadness_wins_over_high_energy(self) -> None:
        assert humor_da_faixa(track(valencia=.2, energia=.9)) == "triste"

    def test_high_energy_wins_over_instrumental(self) -> None:
        assert humor_da_faixa(track(energia=.8, instrumentalidade=.9)) == "treino"

    def test_instrumental_when_calm(self) -> None:
        assert humor_da_faixa(track(instrumentalidade=.8)) == "foco"

    def test_chill_is_the_default(self) -> None:
        assert humor_da_faixa(track()) == "chill"

    def test_every_boundary_value_falls_through(self) -> None:
        # All three comparisons are strict, so the exact threshold is NOT a hit.
        limite = track(valencia=.3, energia=.75, instrumentalidade=.7)
        assert humor_da_faixa(limite) == "chill"
```

- [ ] **Step 3: Run the tests and confirm they pass**

Run: `pytest tests/test_recomendacao.py -v`

Expected: 25 passed (8 from Task 1 + 5 `rar` + 7 `rotulo_profundidade` + 5 `humor_da_faixa`). If `test_every_boundary_value_falls_through` fails, a comparison in `src/recomendacao.py` is `>=`/`<=` where this test assumes strict — report it, do not edit either side until asked.

- [ ] **Step 4: Commit**

```bash
git add tests/test_recomendacao.py
git commit -m "test: pin the threshold helpers and mood precedence

rar at 8/17, rotulo_profundidade at 10/20/30, and the strict-comparison
fall-through in humor_da_faixa, whose branch order is itself behaviour.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: The DataFrame core

**Files:**
- Modify: `tests/test_recomendacao.py` (append a helper and two classes, extend the imports)

**Interfaces:**
- Consumes: `NEUTRAL`, `track()`; `src.recomendacao.garimpar`, `cobertura`.
- Produces: module-level `catalog(*linhas: dict) -> pd.DataFrame`, available to later tasks (none currently need it).

Background: `garimpar(base, alvo, teto, limite=8)` keeps rows with `popularidade <= teto`; on an empty result it returns the empty frame with a `match` column of dtype `int64` (so callers can read `["match"]` without a KeyError); otherwise it scores every row, sorts by `match` descending with `kind="stable"` — which preserves catalog order on ties, matching the prototype's JavaScript `sort` — then takes `head(limite)` and resets the index. `cobertura(base, teto)` returns 0 for an empty base instead of dividing by zero.

- [ ] **Step 1: Extend the imports**

Add `pandas` and the two functions:

```python
import pandas as pd
import pytest

from src.dados import ATRIBUTOS
from src.recomendacao import (
    cobertura,
    garimpar,
    humor_da_faixa,
    match,
    rar,
    rotulo_profundidade,
    round_js,
)
from src.tema import LIMA, PERI, ROSA
```

- [ ] **Step 2: Append the `catalog` helper**

Put it directly below `track()`:

```python
def catalog(*linhas: dict) -> pd.DataFrame:
    """A catalogue DataFrame from hand-written rows, in the given order."""
    return pd.DataFrame(list(linhas))
```

- [ ] **Step 3: Append the failing tests**

```python
class TestGarimpar:
    def test_drops_tracks_above_the_ceiling(self) -> None:
        base = catalog(
            {**track(popularidade=5), "faixa": "A"},
            {**track(popularidade=50), "faixa": "B"},
        )
        assert list(garimpar(base, NEUTRAL, teto=20)["faixa"]) == ["A"]

    def test_empty_result_still_has_an_int64_match_column(self) -> None:
        # Callers read result["match"] unconditionally; a missing column or an
        # object dtype would break them.
        base = catalog({**track(popularidade=90), "faixa": "A"})
        resultado = garimpar(base, NEUTRAL, teto=20)
        assert resultado.empty
        assert resultado["match"].dtype == "int64"

    def test_ties_keep_catalog_order(self) -> None:
        # Identical attributes and popularity give an identical score, so only
        # the stable sort decides the order.
        base = catalog(
            {**track(popularidade=5), "faixa": "first"},
            {**track(popularidade=5), "faixa": "second"},
        )
        assert list(garimpar(base, NEUTRAL, teto=20)["faixa"]) == ["first", "second"]

    def test_ranks_the_closest_match_first(self) -> None:
        alvo = {**NEUTRAL, "energia": 1.0}
        base = catalog(
            {**track(popularidade=5, energia=.1), "faixa": "far"},
            {**track(popularidade=5, energia=.9), "faixa": "near"},
        )
        assert list(garimpar(base, alvo, teto=20)["faixa"]) == ["near", "far"]

    def test_respects_the_limit(self) -> None:
        base = catalog(*[
            {**track(popularidade=5), "faixa": f"t{i}"} for i in range(12)
        ])
        assert len(garimpar(base, NEUTRAL, teto=20)) == 8          # default
        assert len(garimpar(base, NEUTRAL, teto=20, limite=3)) == 3

    def test_resets_the_index(self) -> None:
        base = catalog(
            {**track(popularidade=50), "faixa": "dropped"},
            {**track(popularidade=5), "faixa": "kept"},
        )
        assert list(garimpar(base, NEUTRAL, teto=20).index) == [0]


class TestCobertura:
    def test_percentage_of_the_eligible_universe(self) -> None:
        base = catalog(*[
            {**track(popularidade=p), "faixa": str(p)} for p in (5, 10, 50, 60)
        ])
        assert cobertura(base, 20) == 50

    def test_empty_base_returns_zero_instead_of_dividing_by_zero(self) -> None:
        assert cobertura(pd.DataFrame(), 20) == 0
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `pytest tests/test_recomendacao.py -v`

Expected: 33 passed (25 from Tasks 1–2 + 6 `garimpar` + 2 `cobertura`).

- [ ] **Step 5: Commit**

```bash
git add tests/test_recomendacao.py
git commit -m "test: pin garimpar's filter, stable tie order and empty-frame shape

Also cobertura's zero-length guard. The int64 match column on an empty
result matters: callers read result[\"match\"] unconditionally.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: String helpers

**Files:**
- Modify: `tests/test_recomendacao.py` (append two classes, extend the imports)

**Interfaces:**
- Consumes: `src.recomendacao.email_valido`, `nome_do_email`.
- Produces: nothing new.

Background: `email_valido` strips, then matches `^[^\s@]+@[^\s@]+\.[^\s@]+$` — the prototype's regex, so a domain with no dot is invalid. `nome_do_email` takes the part before `@`, replaces each of `.`, `_`, `-` with a space, then uppercases the first character of every word.

- [ ] **Step 1: Extend the imports**

```python
from src.recomendacao import (
    cobertura,
    email_valido,
    garimpar,
    humor_da_faixa,
    match,
    nome_do_email,
    rar,
    rotulo_profundidade,
    round_js,
)
```

- [ ] **Step 2: Append the failing tests**

```python
class TestEmailValido:
    @pytest.mark.parametrize("email", [
        "amanda@unb.br",
        "  amanda@unb.br  ",              # stripped before matching
        "a.b-c_d@aluno.unb.br",
    ])
    def test_accepts(self, email: str) -> None:
        assert email_valido(email)

    @pytest.mark.parametrize("email", [
        "amanda@unb",                     # no dot in the domain
        "amanda unb@x.br",                # inner space
        "@unb.br",
        "amanda@",
        "amanda@@unb.br",
        "",
    ])
    def test_rejects(self, email: str) -> None:
        assert not email_valido(email)


class TestNomeDoEmail:
    @pytest.mark.parametrize("email, esperado", [
        ("amanda.elisa@aluno.unb.br", "Amanda Elisa"),
        ("maria-carolina@x.br", "Maria Carolina"),
        ("wingrid_costa@x.br", "Wingrid Costa"),
        ("arthur@x.br", "Arthur"),
    ])
    def test_derives_a_presentable_name(self, email: str, esperado: str) -> None:
        assert nome_do_email(email) == esperado
```

- [ ] **Step 3: Run the whole suite and confirm it passes**

Run: `pytest -v`

Expected: 46 passed (33 from Tasks 1–3 + 9 `email_valido` + 4 `nome_do_email`). Running bare `pytest` also confirms `pytest.ini`'s `testpaths` discovers `tests/` with no path argument.

- [ ] **Step 4: Commit**

```bash
git add tests/test_recomendacao.py
git commit -m "test: pin email validation and name derivation

Prototype regex parity, including the domain-needs-a-dot rule, and the
._- separator handling in nome_do_email.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: The constitution

**Files:**
- Create: `docs/constitution.md`

**Interfaces:**
- Consumes: nothing.
- Produces: `docs/constitution.md`, referenced by `CLAUDE.md` (Task 8) and by `.claude/commands/specify.md` and `verify.md` (Task 7).

- [ ] **Step 1: Write the file**

```markdown
# Constitution — Gems Finder

Five principles. Each is derived from something this repository already does,
not imported from a framework: every principle names its referent in the code.
A principle without a referent is a slogan — if one ever loses its referent,
either fix the code or delete the principle.

To amend: open a Structural-track spec (see `CLAUDE.md`) saying which
principle changes and why.

## 1. English in engineering, Portuguese in the product

Identifiers, docstrings, comments, commit subjects, test names, specs and
commands are English. Everything the user reads is Portuguese — UI copy,
labels, error messages, the mascot's voice.
`docs/gems-finder-prototipo.html` is the authority on user-facing wording.

*Referent:* the audio-attribute columns arrive from the dataset in English and
are translated to Portuguese on load; §6 of
`docs/specs/2026-08-30-real-model-integration/spec.md` has to maintain that
mapping table. Standardising on English deletes the mapping layer.

*Known transitional state:* the existing Python is still Portuguese
(`carregar_catalogo`, `dancabilidade`). The rename is a Structural-track job
that waits for the tests which make it safe. Do not rename opportunistically.

## 2. Be honest about what is simulated

A placeholder metric never reaches the UI without a visible marker saying it is
a placeholder. Neither does simulated data presented as real.

*Referent:* the `AVISOS` block in `app.py`, the `TODO` on `PRECISAO_8` at
`src/dados.py:134`, and the deliberate contrast in that docstring — "a métrica
Precisão @8 é PLACEHOLDER" against "a Cobertura é calculada de fato".

## 3. The HTML prototype is the visual spec

`docs/gems-finder-prototipo.html` is the approved authority on flow, copy and
palette. Divergence from it is either a bug or a decision recorded in a spec —
never a silent drift.

*Referent:* `src/tema.py` mirrors the prototype's `:root`;
`src/recomendacao.py` documents itself as a faithful translation of the
prototype's `match()`, `media()`, `centro()` and `rar()`; `garimpar` uses
`kind="stable"` specifically to reproduce the JavaScript `sort`.

## 4. Stable interfaces, small modules

Each module has one responsibility and an interface its callers can rely on.
`carregar_catalogo()` must swap from simulated data to the real dataset
without the rest of the app noticing.

*Referent:* §6 of the real-model spec already promises exactly that swap.
`src/ui/estilo.py` at 318 lines is the largest file in the repo — treat it as
the ceiling, not the target.

## 5. The logic that picks results is tested

`src/recomendacao.py` decides which gem a user sees, so it carries tests. Run
them with `pytest`. Streamlit UI is verified by running the app (the
`debugging-streamlit` skill), not by mocking widgets.

*Referent:* `tests/test_recomendacao.py`, which pins the exact thresholds —
`rar` at 8 and 17, `rotulo_profundidade` at 10/20/30, `match`'s 31…99 clamp,
and `garimpar`'s stable tie order.
```

- [ ] **Step 2: Verify every principle names a real referent**

Run: `grep -n "src/dados.py:134\|estilo.py\|kind=\"stable\"" src/dados.py src/ui/estilo.py src/recomendacao.py | head`

Expected: `src/dados.py:134` is the `TODO` on `PRECISAO_8`, and `kind="stable"` appears in `src/recomendacao.py`. Confirm `wc -l src/ui/estilo.py` reports 318. If any referent has moved, update the constitution to match reality — the file is worthless the moment a citation is wrong.

- [ ] **Step 3: Commit**

```bash
git add docs/constitution.md
git commit -m "docs(orchestration): add the project constitution

Five principles, each citing the line of code it was derived from. A
principle without a referent is a slogan, so the citations are the point.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: The three templates

**Files:**
- Create: `docs/templates/spec.md`
- Create: `docs/templates/plan.md`
- Create: `docs/templates/tasks.md`

**Interfaces:**
- Consumes: nothing.
- Produces: three templates, read by `.claude/commands/specify.md`, `plan.md` and `tasks.md` (Task 7) by exact path.

The spec template's shape is lifted from `docs/spec-integracao-modelo-real.md`, whose "Onde estamos hoje / Em produção" table, motivating-constraint section and checkbox open-questions list are the parts worth keeping.

- [ ] **Step 1: Write `docs/templates/spec.md`**

```markdown
# Spec — <topic>

> One or two sentences: what this changes and for whom. If you cannot write
> this without naming a library or a file, you are writing a plan, not a spec.

**Status:** draft · **Date:** <YYYY-MM-DD> · **Author:** <name>

---

## 1. Problem

What is wrong or missing today, in terms a group member who has not read the
code can follow. No solution here.

## 2. Goal and non-goals

**Goal.** One sentence.

**Non-goals** — what this deliberately does not do, and why. Every row here is
a scope argument you will not have to repeat later.

| Out of scope | Why |
|---|---|
|  |  |

## 3. Where we are today

| Piece | Today | Target |
|---|---|---|
|  |  |  |

## 4. Constraints that shape the design

External limits you did not choose — API deprecations, deploy environment,
dataset columns, the approved prototype. State each one and what it forces.

## 5. Decisions

| Decision | Rationale |
|---|---|
|  |  |

## 6. Verification

This is done when… — a numbered list of checks someone else could run without
asking you what you meant.

## 7. Open questions

- [ ] Question, with your recommendation and its reasoning.

<!-- Rename this section to "Resolved questions", tick the boxes and record the
     decision when they are answered. Never delete the question. -->
```

- [ ] **Step 2: Write `docs/templates/plan.md`**

```markdown
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
```

- [ ] **Step 3: Write `docs/templates/tasks.md`**

```markdown
# <topic> Tasks

**Spec:** [`./spec.md`](./spec.md) · **Plan:** [`./plan.md`](./plan.md)

Tick each box as it lands. One task per commit.

- [ ] **1. <name>**
      Files: `path/one.py`, `tests/test_one.py`
      Accept: the exact command to run and the exact expected result.
- [ ] **2. <name>**
      Files:
      Accept:

## Deferred

Work that came up and was deliberately not done, with the reason. This section
is why the next person does not re-litigate a decision you already made.
```

- [ ] **Step 4: Verify the templates are internally consistent**

Run: `ls docs/templates/ && grep -c "^##" docs/templates/spec.md`

Expected: three files listed; the spec template reports 7 numbered sections. Confirm the plan and tasks templates both link to `./spec.md` with that exact relative path — Task 7's commands depend on all three artifacts living in the same folder.

- [ ] **Step 5: Commit**

```bash
git add docs/templates/
git commit -m "docs(orchestration): add spec, plan and tasks templates

Shape taken from docs/spec-integracao-modelo-real.md rather than from
spec-kit's own templates: the today/target table, the motivating-constraint
section and the checkbox open questions were already the right form.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: The six cycle commands

**Files:**
- Create: `.claude/commands/specify.md`
- Create: `.claude/commands/clarify.md`
- Create: `.claude/commands/plan.md`
- Create: `.claude/commands/tasks.md`
- Create: `.claude/commands/implement.md`
- Create: `.claude/commands/verify.md`

**Interfaces:**
- Consumes: `docs/constitution.md` (Task 5) and the three templates in `docs/templates/` (Task 6), both by exact path.
- Produces: six slash commands, listed in `CLAUDE.md` (Task 8). Each command writes into `docs/specs/<YYYY-MM-DD>-<slug>/`.

Claude Code reads any `.md` file in `.claude/commands/` as a slash command named after the file. YAML frontmatter sets `description` (shown in the `/` menu) and `argument-hint`. `$ARGUMENTS` in the body is replaced with whatever the user typed after the command.

- [ ] **Step 1: Write `.claude/commands/specify.md`**

```markdown
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
```

- [ ] **Step 2: Write `.claude/commands/clarify.md`**

```markdown
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
```

- [ ] **Step 3: Write `.claude/commands/plan.md`**

```markdown
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

Then check your plan against the spec: can you point at a task for every
requirement? Fix gaps inline.

Report the path. Do not write code and do not create `tasks.md` — `/tasks`
does that.
```

- [ ] **Step 4: Write `.claude/commands/tasks.md`**

```markdown
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
```

- [ ] **Step 5: Write `.claude/commands/implement.md`**

```markdown
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
```

- [ ] **Step 6: Write `.claude/commands/verify.md`**

```markdown
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
   another in Task 7 is a bug, not a typo.
4. **Constitution violations.** Each of the five principles, checked against
   what actually landed. Quote the offending line.

End with the `pytest` result, quoted, and one sentence: ready, or not ready and
why. Report what you found, not what you hope — say plainly if something you
could not check remains unchecked.

Do not fix anything. This command reports.
```

- [ ] **Step 7: Verify the commands are well-formed and discoverable**

Run: `ls .claude/commands/ && head -4 .claude/commands/specify.md`

Expected: six files (`clarify.md`, `implement.md`, `plan.md`, `specify.md`, `tasks.md`, `verify.md`); `specify.md` opens with a `---` frontmatter block containing `description:` and `argument-hint:`. Then confirm every path the commands cite actually exists:

Run: `grep -oh "docs/[a-z/.-]*\.md" .claude/commands/*.md | sort -u | xargs ls`

Expected: every listed path resolves — `docs/constitution.md`, `docs/templates/spec.md`, `docs/templates/plan.md`, `docs/templates/tasks.md`. A command citing a path that does not exist is the most likely failure in this task.

- [ ] **Step 8: Commit**

```bash
git add .claude/commands/
git commit -m "feat(orchestration): add the six cycle commands

specify, clarify, plan, tasks, implement, verify — spec-kit's cycle minus
converge, with analyze and checklist folded into verify. Native slash
commands, versioned, so the whole group gets them with nothing to install.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

**Interfaces:**
- Consumes: `docs/constitution.md` (Task 5), `docs/templates/` (Task 6), `.claude/commands/` (Task 7) — all cited by path, so this task runs last of the four.
- Produces: the entry point. Nothing consumes it programmatically; Claude Code loads it automatically at session start.

It must stay short enough to be read in full — it points at the constitution rather than repeating it.

- [ ] **Step 1: Write the file**

```markdown
# Gems Finder — orchestration

Read this first. It carries the project context, how work moves from idea to
code, and the conventions. The principles behind it live in
`docs/constitution.md`; this file points at them rather than repeating them.

## The project

Gems Finder surfaces underrated, underground tracks from the Spotify catalogue
by matching the audio profiles (*moods*) of mainstream hits against
low-popularity tracks. Academic work: Residência em IA · UnB, Turma 2, Grupo 9
(Nano-Challenge: Spotify Data), five members.

Streamlit app on Python 3.12:

    pip install -r requirements.txt
    streamlit run app.py

Tests: `pip install -r requirements-dev.txt && pytest`

## Read this before touching data or metrics

The catalogue is **simulated** — 32 fictional tracks in `src/dados.py`. No
external CSV, no credentials.

Spotify OAuth, `/me/top/tracks` and playlist creation are real. Audio
attributes never are: Spotify deprecated `/v1/audio-features` on 2024-11-27,
so attributes always come from our dataset, never from the API. `PRECISAO_8`
in `src/dados.py` is a placeholder; `cobertura` is computed for real. The
route from simulated to real data is specified in
`docs/specs/2026-08-30-real-model-integration/spec.md`.

## The three tracks

Classify every request out loud before starting, so the classification can be
challenged.

| Track | Trigger | Flow |
|---|---|---|
| **Polish** | One file; CSS, copy, or an obvious bug | Straight to code, descriptive commit |
| **Feature** | New page, search mode, or metric | `/specify` → `/plan` → `/tasks` → `/implement` |
| **Structural** | Changes a data source, or an interface other modules consume | constitution check → `/specify` → `/clarify` → `/plan` → `/tasks` → `/verify` → `/implement` |

**The ratchet turns one way.** Complexity discovered mid-task raises the track
and never lowers it, and whoever raises it says so out loud. Reaching for a
lighter track to skip work is itself the signal to take the heavier one.

Artifacts live in `docs/specs/<YYYY-MM-DD>-<topic>/`, one folder per job:
`spec.md` (what and why), `plan.md` (how), `tasks.md` (the tickable list).
Templates in `docs/templates/`. Adapted from
[github/spec-kit](https://github.com/github/spec-kit) — six of its nine
commands, sized for a 1,900-line repo.

## Conventions

**Language.** English for engineering: identifiers, docstrings, comments,
commit subjects, test names, specs. Portuguese for everything the user reads —
UI copy, labels, error messages, the mascot's voice.
`docs/gems-finder-prototipo.html` is the authority on user-facing wording.

The existing Python is still Portuguese (`carregar_catalogo`,
`dancabilidade`). That is a known transitional state: the rename is a
Structural-track job waiting on the tests that make it safe. Do not rename
opportunistically.

**Commits.** Conventional Commits, English subject:
`feat(ui): thin scrollbar on tabs for mouse users`. Scopes in use: `ui`,
`data`, `model`, `docs`, `test`, `orchestration`.

**Modules.** One responsibility, stable interfaces. `src/ui/estilo.py` at 318
lines is the ceiling, not the target.

**Tests.** `src/recomendacao.py` carries tests — it decides which gem a user
sees. Streamlit UI is verified by running the app (`debugging-streamlit`
skill), not by mocking widgets.

## Where things are

    app.py                   routing between Descobrir and Minha conta
    src/tema.py              palette, mirrors the prototype's :root
    src/dados.py             simulated catalogue and product constants
    src/recomendacao.py      match, garimpo, metrics — the tested core
    src/spotify.py           real OAuth and Web API calls
    src/ui/                  visual layer: estilo, mascote, componentes,
                             estado, sidebar, resultados, descobrir, conta
    tests/                   pytest suite
    docs/constitution.md     the five principles
    docs/templates/          spec, plan and tasks templates
    docs/specs/              one folder per Feature/Structural job
    docs/gems-finder-prototipo.html   approved visual spec
    .claude/commands/        the six cycle commands
    .claude/skills/          installed skills (see skills-lock.json)
```

- [ ] **Step 2: Verify every path cited in CLAUDE.md exists**

Run: `grep -oE "(docs|src|tests|\.claude)/[A-Za-z0-9_./-]*" CLAUDE.md | sed 's/[.,]$//' | sort -u | xargs ls -d`

Expected: every path resolves. `docs/specs/2026-08-30-real-model-integration/` will fail until Task 9 moves it — that is expected, and Task 9 closes it. Any other failure is a broken citation to fix now.

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "feat(orchestration): add CLAUDE.md as the entry point

Project context, the three tracks with the one-way ratchet, the
English-engineering / Portuguese-product rule, and a file map. Points at
docs/constitution.md rather than repeating it, so it stays readable in full.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Relocate the existing spec and fix the README tree

**Files:**
- Move: `docs/spec-integracao-modelo-real.md` → `docs/specs/2026-08-30-real-model-integration/spec.md`
- Modify: `README.md` (the `## 🗂️ Estrutura do Repositório` tree)

**Interfaces:**
- Consumes: the `docs/specs/` convention from Task 6 and the citation in `CLAUDE.md` from Task 8.
- Produces: closes the one expected failure from Task 8's Step 2.

The moved file keeps its Portuguese content untouched. It predates the English convention, and retranslating good content buys nothing — the constitution's principle 1 records this as a transitional state, not a violation. Verified during design: no file in the repo references it by path, so the move breaks nothing.

- [ ] **Step 1: Confirm nothing references the file by path**

Run: `grep -rn "spec-integracao-modelo-real" . --include="*.md" --include="*.py" --include="*.html" --include="*.toml" --include="*.json" | grep -v "docs/specs/2026-09-01"`

Expected: no output. If anything appears, update that reference in this task.

- [ ] **Step 2: Move the file with history**

```bash
mkdir -p docs/specs/2026-08-30-real-model-integration
git mv docs/spec-integracao-modelo-real.md docs/specs/2026-08-30-real-model-integration/spec.md
```

`git mv`, not `mv` — the file's history is the record of how the real-model design was reached.

- [ ] **Step 3: Update the README tree**

In `README.md`, inside the ```text block under `## 🗂️ Estrutura do Repositório`, replace the `docs/` entry and add the new directories. The tree is in Portuguese and stays that way — it is documentation a reader reads, and the surrounding README is Portuguese throughout.

Replace:

```text
├── docs/
│   └── gems-finder-prototipo.html # Protótipo HTML aprovado (especificação visual e funcional)
```

with:

```text
├── CLAUDE.md                 # Orquestração: contexto, ciclo de trabalho e convenções
├── docs/
│   ├── gems-finder-prototipo.html # Protótipo HTML aprovado (especificação visual e funcional)
│   ├── constitution.md       # Princípios do projeto
│   ├── templates/            # Modelos de spec, plano e tarefas
│   └── specs/                # Uma pasta por trabalho (spec, plano, tarefas)
├── tests/                    # Suíte pytest da lógica de recomendação
```

Keep the existing `#` comment alignment of the surrounding lines.

- [ ] **Step 4: Verify the move and the tree**

Run: `ls docs/specs/*/ && git status --short && pytest -q`

Expected: both spec folders listed with their `spec.md`; `git status` shows the rename staged as `R  docs/spec-integracao-modelo-real.md -> docs/specs/2026-08-30-real-model-integration/spec.md` plus the modified `README.md`; `46 passed`.

Then re-run Task 8's path check, which must now pass completely:

Run: `grep -oE "(docs|src|tests|\.claude)/[A-Za-z0-9_./-]*" CLAUDE.md | sed 's/[.,]$//' | sort -u | xargs ls -d`

Expected: every path resolves, with no failures.

- [ ] **Step 5: Commit**

```bash
git add README.md docs/
git commit -m "docs: move the real-model spec into docs/specs/ and fix the README tree

One home for specs; two is the first thing to rot. Content stays in
Portuguese — it predates the English convention and retranslating it buys
nothing. README tree now shows CLAUDE.md, docs/templates and tests.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

## Self-Review

**Spec coverage.** Every spec section maps to a task: §4 command mapping → Task 7; §5 tracks → Tasks 7 (`specify.md`) and 8 (`CLAUDE.md`); §6 layout → Tasks 5–9; §7 principles → Task 5; §8 testing scope → Tasks 1–4, one row of the §8 table per test class, with `novo_id_playlist`, `media`, `centro`, `montar_resultado` and `montar_resultado_conta` excluded exactly as §8 states; §9 verification criteria 1 and 2 → `CLAUDE.md` and the commands, criterion 3 → Tasks 1–4, criterion 4 → Task 5's referent check; §10 resolved questions → Task 9 (move) and Tasks 1–4 (tests ship together). No gaps.

**Test count arithmetic.** Task 1: 5 + 3 = 8. Task 2: +5 +7 +5 = 25. Task 3: +6 +2 = 33. Task 4: +9 +4 = 46. The counts in each task's expected output are consistent, and Task 9's final `pytest -q` expects the same 46.

**Name consistency.** `NEUTRAL` and `track()` are defined in Task 1 and used unchanged in Tasks 2–4; `catalog()` is defined in Task 3 and used only there. The import block grows monotonically across Tasks 1→4, each task showing the full replacement block rather than a diff. Command filenames in Task 7 match the flows in Task 8's table and the spec's §4 exactly: `specify`, `clarify`, `plan`, `tasks`, `implement`, `verify`.

**Known cross-task dependency.** Task 8's path check has one expected failure (`docs/specs/2026-08-30-real-model-integration/`) which Task 9 closes. This is stated in both tasks so an implementer reading either one out of order is not misled.
