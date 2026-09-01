# combinable search criteria Tasks

**Spec:** [`./spec.md`](./spec.md) · **Plan:** [`./plan.md`](./plan.md)

Tick each box as it lands. One task per commit. Every command runs from the
worktree root; `python` means the primary checkout's venv interpreter,
`C:/Users/Amanda/gems-finder-tic-ia2/.venv/Scripts/python.exe`, since the
worktree has no `.venv` of its own.

Baseline before Task 1: `python -m pytest -q` → `46 passed`.

- [x] **1. Mean of vectors, and the search universe**
      Files: `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest tests/test_recomendacao.py -q` → `52 passed`.
      `python -m pytest -q -k "MediaDeVetores or Universo"` → `6 passed`.
      Landed in 4066ce2, both measured.

- [ ] **2. The Precisão @8 placeholder rises with each combined criterion**
      Files: `src/dados.py`, `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q -k PrecisaoCombinada` → `6 passed`, and
      `python -c "from src.recomendacao import precisao_combinada as p; print(p(1), p(2), p(3))"`
      → `87 90 91`. `grep -c TODO src/dados.py` → `1`.
      Full suite is expected to break here — `montar_resultado()` still reads
      the deleted `PRECISAO_8["vibe_foco"]` key and is fixed in Task 5 — so the
      gate for this task is the two commands above plus
      `python -m pytest -q -k "not MontarResultado"` → `56 passed`.

- [ ] **3. One criterion per active group**
      Files: `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q -k CriteriosAtivos` → `7 passed`, and
      `python -m pytest -q -k "not MontarResultado"` → `64 passed`.

- [ ] **4. The status sentence lists every active criterion**
      Files: `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q -k TextoStatus` → `7 passed`, and
      `python -m pytest -q -k "not MontarResultado"` → `71 passed`.

- [ ] **5. `montar_resultado()` takes the three criterion lists**
      Files: `src/recomendacao.py`, `tests/test_recomendacao.py`
      Accept: `python -m pytest -q` → `83 passed` — the whole suite green again,
      including `TestMontarResultado` (12 tests).

- [ ] **6. Three selection lists replace mode, vibe and genre**
      Files: `app.py`, `src/dados.py`, `src/ui/estado.py`
      Accept: `python -m pytest -q` → `83 passed` (unchanged — no test touches
      session state), and
      `grep -rn "MODOS\|session_state\.modo\|session_state\.vibe\b\|session_state\.genero\b" --include=*.py app.py src tests`
      → no output. Do NOT run the app between Tasks 6 and 7: `descobrir.py`
      still calls the old `montar_resultado()` signature and will raise.

- [ ] **7. Step 1 becomes three optional, combinable groups**
      Files: `src/ui/descobrir.py`, `src/ui/estilo.py`
      Accept: `python -m pytest -q` → `83 passed`.
      `grep -rn "stButtonGroup\|segmented_control\|_texto_alvo\|seletor_modo" --include=*.py src app.py`
      → no output. `grep -c "gf-metrics{grid-template-columns:1fr;}" src/ui/estilo.py`
      → `1` (the one rule kept from the deleted media block).
      `wc -l src/ui/estilo.py` → 270–285, i.e. back under the ~300 ceiling from
      318. `python -c "import src.ui.descobrir"` → exits 0, no output.

- [ ] **8. Verify in the running app, then commit the prototype**
      Files: `docs/gems-finder-prototipo.html`,
      `docs/specs/2026-09-01-combinable-search-criteria/`,
      `docs/constitution.md` (only if a referent moved)
      Accept: `python -m pytest -q` → `83 passed`.
      `grep -n "TODO" src/dados.py` → the line number matches the one
      `docs/constitution.md` cites, or the constitution is corrected in this
      commit. `wc -l src/ui/estilo.py` → matches the number the constitution
      quotes for this branch, or the constitution is corrected.
      Then, in the running app (`python -m streamlit run app.py`), all nine
      checks in §6 of the spec, of which these are the falsifiable ones:
      first load has nothing selected and the "Garimpar joias" button disabled;
      clicking a vibe twice leaves it unselected; with Ambiente + Slowcore
      selected the results contain tracks from both genres; with vibe Chill +
      genre MPB + artist Dora Lima at ceiling 18 the status line reads
      `Buscando por vibe Chill, gênero MPB, parecido com Dora Lima, com
      popularidade até 18.`, Precisão @8 shows `91%`, and the two results are
      `Varanda Aberta` (match 99) then `Manhã de Terça` (match 96);
      genre MPB at ceiling 1 shows the empty state.

## Deferred

- **Renaming the branch to `feat/combinable-search-criteria`.** The harness
  created `worktree-feat+combinable-search-criteria`; renaming mid-job would
  desync its worktree bookkeeping. Done at push time, which is also when the PR
  is opened — neither happens until the listener has tested locally.
- **An artist search field in Step 1.** The prototype has one and the Streamlit
  app never did. A pre-existing divergence, out of scope per spec §2, and cheap
  to add later: 10 reference artists fit on screen without it.
- **Splitting `src/ui/estilo.py`.** It was 318 lines, past the ~300 ceiling in
  constitution principle 4. Task 7 drops it back under by deleting the dead
  segmented-control rules, so this job does not need the split — but the file is
  one CSS commit away from the ceiling again, and splitting it is a Structural
  job whenever it crosses back.
- **The three open questions in spec §7.** All three carry a recommendation and
  none blocks implementation; the Precisão @8 cap question dies with the
  placeholder.
