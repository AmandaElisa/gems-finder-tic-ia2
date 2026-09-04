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

The catalogue is **real**: 89.740 deduplicated tracks in `data/processed/`,
exported by `notebook/Grupo_9_Sound_Hunters.ipynb`. The app never trains —
it loads artifacts and reads parameters, so scikit-learn is not a runtime
dependency. `src/dados.py` keeps product constants, not data; the only
fiction left there is the staged login of a visitor who never connects, and
the screen labels that case as an example.

**Every number on screen is measured, or it is not shown.** `Precisão @8` was
removed rather than relabelled: it displayed 91% under a caption claiming
user tests that never happened. It returns when an evaluation protocol
exists. `cobertura`, the match and the rarity badge are all computed.

Two platform walls shape the product, both documented in the README with
sources. Spotify deprecated `/v1/audio-features` on 2024-11-27, so audio
attributes NEVER come from the API — a connected user's profile is built by
crossing their most-played tracks against our catalogue by `track_id`. And
apps in Development Mode may read but not write, so playlist creation returns
403; it stays implemented on purpose, with the restriction explained on
screen.

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

**Modules.** One responsibility, stable interfaces. `src/ui/estilo.py` is the
largest file in the UI layer at ~300 lines. Roughly 300 is the ceiling, not the
target.

**Tests.** `src/recomendacao.py` carries tests — it decides which gem a user
sees. Streamlit UI is verified by running the app (`debugging-streamlit`
skill), not by mocking widgets.

## Where things are

    app.py                   routing between Descobrir and Minha conta
    src/tema.py              palette, mirrors the prototype's :root
    src/dados.py             product constants (the catalogue lives in data/processed/)
    src/recomendacao.py      match, garimpo, metrics — the tested core
    src/artefatos.py         the boundary: loads the notebook's artifacts
    src/generos.py           genre families, read from the model
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
