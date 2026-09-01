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
`src/ui/estilo.py` is the largest file in the repo — 318 lines on `main` (the
CSS branch that took it there has since merged), and 276 on
`feat/combinable-search-criteria`, which deleted the mode selector and the ~46
lines of segmented-control CSS that only it used. Treat roughly 300 lines as
the ceiling, not the target: a file past it is doing more than one thing. Both
directions of travel are real — a feature can pay the ceiling back by removing
what it made dead.

## 5. The logic that picks results is tested

`src/recomendacao.py` decides which gem a user sees, so it carries tests. Run
them with `pytest`. Streamlit UI is verified by running the app (the
`debugging-streamlit` skill), not by mocking widgets.

*Referent:* `tests/test_recomendacao.py`, which pins the exact thresholds —
`rar` at 8 and 17, `rotulo_profundidade` at 10/20/30, `match`'s 31…99 clamp,
and `garimpar`'s stable tie order.
