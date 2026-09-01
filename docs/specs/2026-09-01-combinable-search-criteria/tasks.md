# combinable search criteria Tasks

**Spec:** [`./spec.md`](./spec.md) · **Plan:** [`./plan.md`](./plan.md)

All eight landed. Every command below ran from the worktree root; `python` means
the primary checkout's venv interpreter,
`C:/Users/Amanda/gems-finder-tic-ia2/.venv/Scripts/python.exe`, since the
worktree has no `.venv` of its own. Every number here was measured, not
predicted — where the plan's arithmetic was off, the measured value replaced it
and the difference is noted.

Baseline before Task 1: `python -m pytest -q` → `46 passed`.
Final: `python -m pytest -q` → `82 passed`.

- [x] **1. Mean of vectors, and the search universe** — 4066ce2
      Files: `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q` → `52 passed`;
      `python -m pytest -q -k "MediaDeVetores or Universo"` → `6 passed`.
      (The plan predicted 9 for the targeted run; it is 3 + 3 = 6.)

- [x] **2. The Precisão @8 placeholder rises with each combined criterion** — b2f7e97
      Files: `src/dados.py`, `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q -k PrecisaoCombinada` → `5 passed`;
      `python -c "from src.recomendacao import precisao_combinada as p; print(p(1), p(2), p(3))"`
      → `87 90 91`; `grep -c TODO src/dados.py` → `1`, still at line 134, so the
      constitution's citation of it holds.
      The plan expected the full suite to break here because `montar_resultado()`
      still read the deleted `PRECISAO_8["vibe_foco"]`. It did not: no test in
      the suite called `montar_resultado()` before Task 5. Full suite stayed
      green at `57 passed`.

- [x] **3. One criterion per active group** — 4ea65af
      Files: `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q -k CriteriosAtivos` → `7 passed`;
      full suite → `64 passed`.

- [x] **4. The status sentence lists every active criterion** — ad3374c
      Files: `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q -k TextoStatus` → `7 passed`;
      full suite → `71 passed`.

- [x] **5. `montar_resultado()` takes the three criterion lists** — ed2ab7a
      Files: `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q -k MontarResultado` → `11 passed`;
      full suite → `82 passed`. (The plan said 12 / 83:
      `test_precision_follows_the_number_of_active_groups` is one test with
      three asserts, not three tests.)

- [x] **6. Three selection lists replace mode, vibe and genre** — a8949a5
      Files: `app.py`, `src/dados.py`, `src/ui/estado.py`
      Accept: `python -m pytest -q` → `82 passed` (unchanged; no test touches
      session state); `grep -rn "MODOS" --include=*.py app.py src tests` → only
      `src/ui/descobrir.py`, closed by Task 7. The plan's "no output" was too
      strict for this task's boundary. As planned, the app does not import
      between Tasks 6 and 7.

- [x] **7. Step 1 becomes three optional, combinable groups** — ead4a84
      Files: `src/ui/descobrir.py`, `src/ui/estilo.py`
      Accept: `python -m pytest -q` → `82 passed`;
      `python -c "import app, src.ui.descobrir"` → imports ok;
      `grep -rn "stButtonGroup\|segmented_control\|_texto_alvo\|seletor_modo\|MODOS" --include=*.py src app.py`
      → no output; `grep -c "gf-metrics{grid-template-columns:1fr;}" src/ui/estilo.py`
      → `1`; `wc -l src/ui/estilo.py` → `276`, down from 318 and back under the
      ~300 ceiling.

- [x] **8. Verify in the running app, then commit the prototype**
      Files: `docs/gems-finder-prototipo.html` and
      `docs/specs/2026-09-01-combinable-search-criteria/` (committed early, in
      a10ba2d, on request), `docs/constitution.md`
      Accept: `python -m pytest -q` → `82 passed`. All nine §6 checks verified
      against the real app script through Streamlit's `AppTest` harness — which
      runs `app.py` itself rather than mocking widgets — plus the app served at
      `http://localhost:8502` for hands-on review. Measured: nothing selected on
      first load and the dig button disabled; the status line asking for a
      criterion; three optional group labels present and zero button groups (no
      mode selector); a vibe toggling on then off; `['chill', 'treino']` and
      `['Ambiente', 'Slowcore']` selected together with results drawn from both
      genres; the combined status line exactly as §6 requires; Precisão @8 `91`
      with three groups; title `Joias — Chill · MPB · parecido com Dora Lima`;
      results `[('Varanda Aberta', 99), ('Manhã de Terça', 96)]`; the empty
      state and its two-way hint at ceiling 1.

## Deferred

- **Renaming the branch to `feat/combinable-search-criteria`.** The harness
  created `worktree-feat+combinable-search-criteria`; renaming mid-job would
  desync its worktree bookkeeping. Done at push time, which is also when the PR
  is opened — neither happens until the listener has tested locally.
- **An artist search field in Step 1.** The prototype has one and the Streamlit
  app never did. A pre-existing divergence, out of scope per spec §2, and cheap
  to add later: 10 reference artists fit on screen without it.
- **Splitting `src/ui/estilo.py`.** It was 318 lines on `main`, past the ~300
  ceiling in constitution principle 4. Task 7 dropped it to 276 by deleting the
  dead segmented-control CSS, so this job does not need the split — but it is a
  couple of CSS commits from the ceiling again, and splitting it is a Structural
  job whenever it crosses back.
- **The constitution's `estilo.py` referent was already stale** before this job:
  it cited 280 lines on `main`, while `main` measures 318 (the CSS branch it
  called "the direction of travel" has since merged). Task 8 corrected the
  citation to the measured numbers rather than leaving a wrong one standing.
- **The three open questions in spec §7.** All three carry a recommendation and
  none blocks implementation; the Precisão @8 cap question dies with the
  placeholder.
- **A UI regression test for Step 1.** The `AppTest` script that verified §6
  lives in the scratchpad, not the repo, because CLAUDE.md keeps Streamlit UI
  out of `pytest`. If that convention is ever revisited, that script is the
  starting point — it drives the real app script and needed no widget mocking.
