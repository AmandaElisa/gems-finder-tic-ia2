# Spec — Wiring the real model into the app

> Connects the artifacts the clustering notebook exports to the Streamlit app,
> replacing the 32 simulated tracks with the 89.740 real ones and the four
> hand-written vibes with the five measured moods.

**Status:** draft · **Date:** 2026-09-03 · **Author:** Grupo 9

---

## 1. Problem

The notebook and the app are two disconnected halves.

`notebook/Grupo_9_Sound_Hunters.ipynb` now produces validated artifacts in
`data/processed/`: a catalogue of 89.740 deduplicated tracks with a mood per
track, the fitted `StandardScaler` and `KMeans`, and artist-level status. The
app reads none of it — `src/dados.py` still serves 32 fictional tracks and four
vibes whose target vectors were invented for the prototype.

So the work that was validated is invisible, and the app shows numbers nobody
measured.

## 2. Goal and non-goals

**Goal.** The app loads the real artifacts through the interface it already
uses, so the UI keeps working while the data underneath becomes real.

**Non-goals** — out of scope here:

| Out of scope | Why |
|---|---|
| Changing the recommendation logic in `src/recomendacao.py` | It works and is tested. This job changes the *data source*, not the ranking. Whether the app adopts cosine k-NN is a separate decision, still open in the methodology spec §9 |
| Re-training or re-clustering | The notebook owns that. The app consumes artifacts; it never fits |
| FastAPI and Docker | See §7 — an open question, not a settled requirement |
| Real Spotify audio attributes | Impossible: the endpoint is deprecated (§4.1) |

## 3. Where we are today

| Piece | App today | After this work |
|---|---|---|
| Catalogue | 32 fictional tracks in `src/dados.py` | 89.740 tracks from `catalogo.parquet` |
| Audio attributes | 5, hand-set per track | 5, measured — the selected feature set |
| Moods | 4 vibes, target vectors written by hand | 5 moods from `KMeans`, one per track |
| Genres | 12 invented | 114 real, as a list per track |
| Artist status | not modelled | `status_artista` from `artistas.parquet` |
| Scaler | none | the exported one, reused — never re-fitted |
| `ano`, `cidade` on the card | shown | **removed** — the dataset has neither |
| Precision @8 | `PRECISAO_8` placeholder | still placeholder (§7) |

## 4. Constraints that shape the design

### 4.1 Audio attributes can never come from the API

Spotify deprecated `/v1/audio-features` on 2024-11-27 for apps created after
that date. OAuth, `/me/top/tracks` and playlist creation still work. So
attributes always come from our dataset, and a user's profile is built by
matching their top tracks against the catalogue by `track_id`.

**And that merge is now a known trap:** the raw dataset repeats a track once per
genre, so a direct merge multiplies rows. The exported catalogue is already
deduplicated — one row per `track_id` — which is precisely what makes the merge
safe. Use the parquet, never the raw CSV.

### 4.2 The scaler must be the exported one

User tracks have to be transformed with the same `StandardScaler` that produced
the cluster space. Fitting a new one would compare vectors in different scales
and silently return wrong neighbours.

### 4.3 The interface stays put

Constitution principle 4: `carregar_catalogo()` must swap data sources without
the rest of the app noticing. It keeps its name, its signature, and its
Portuguese column names — eight UI modules consume them.

### 4.4 Streamlit Community Cloud hosts one app

`requirements.txt` is installed at deploy; the notebook is never executed there.
The artifacts must therefore be committed, which they now are.

## 5. Decisions

| Decision | Rationale |
|---|---|
| `carregar_catalogo()` keeps its interface and translates columns on load | Principle 4. `track_name→faixa`, `artists→artista`, `danceability→dancabilidade`, `energy→energia`, `valence→valencia`, `acousticness→acustica`, `instrumentalness→instrumentalidade`, `popularity→popularidade`, `tempo→bpm`, and `track_id` is kept |
| `ano` and `cidade` leave the card | The dataset has neither, and inventing them would violate principle 2. Decided by the group |
| `VIBES` is derived from the model, not hand-written | Five moods, from `modelo.joblib`'s cluster profiles. The measured centroid becomes each vibe's target vector, so the app and the notebook agree by construction |
| Mascot expressions are reassigned, none drawn | No new asset needed. `Foco`→`foco`, `Aconchego`→`chill`, `Gingado`→`feliz`, **`Treino`→ the old `triste` expression** (flat neutral mouth, which suits hypnotic steady techno better than exertion), **`Heavy`→ the old `treino` expression** (the open "O" mouth reads as a shout, which is metal with vocals). Decided by the group |
| The artist picker shows **consolidated** artists | It exists to give the user a reference point — the Netflix pattern: pick something you recognise, get something you do not. The reference is famous; the *results* are independent. Today's prototype shows fictional indie names, which is backwards |
| `humor_da_faixa()` reads the `mood` column | The track already carries its cluster. Recomputing an expression from thresholds would let the mascot disagree with the mood label shown beside it |
| The app never fits a model | It loads `modelo.joblib` and calls `transform`. Any `fit` in `src/` is a bug |

## 6. Verification

Done when:

1. `streamlit run app.py` serves the app with 89.740 tracks and five moods, and
   no UI module was changed except the two the mood count and the card require.
2. `carregar_catalogo()` returns the same column names it returns today, so no
   UI module needs to learn a new schema.
3. **The vibe tests are updated, not left passing by accident.** Sixteen
   references in `tests/test_recomendacao.py` use the keys `chill`, `treino`
   and `foco` and assert on the hand-written target vectors — for instance that
   averaging Chill and Treino gives `energia` 0,635, a number derived from two
   invented targets. `treino` and `foco` survive into the measured set;
   `chill` becomes `aconchego` and the targets all change. Those tests must be
   rewritten against the measured moods. A test that still asserts 0,635 after
   this change is pinning a fiction.
4. No `ano` or `cidade` appears in the rendered card.
5. Five mood chips render, each with a mascot expression that matches its mood.
6. Nothing in `src/` calls `fit` or `fit_transform`.
7. A track picked in the UI returns neighbours whose `status_artista` is
   `Independente`, confirming the artifact's filter reached the surface.


## 6.1 Quality findings the artifacts surfaced

Measured while checking that the artist picker would work. None of these blocks
the loader; all three would embarrass the product if shipped unnoticed.

**1. The top of `Foco` is white noise.** Its most popular artists are
"White Noise for Babies" and "White Noise Baby Sleep". The `sleep` genre landed
in this cluster, which is correct by audio attributes — quiet, instrumental,
acoustic — but nobody picks white noise as a taste reference. The artist picker
needs a filter beyond popularity, or `Foco` needs the `sleep` genre excluded
from its reference list.

**2. The mood names are narrower than the clusters they label.** `Heavy` was
named after its dominant genres (metalcore, heavy-metal, grunge), but its
best-known artists are Kim Petras, David Guetta and OneRepublic — high-energy
electric pop with vocals. The name is defensible by genre and misleading by
artist. Worth revisiting once real users see it.

**3. `funk` in this dataset is US funk/soul, not funk brasileiro.** Querying the
Brazilian-adjacent genres returned Coolio, Dr. Dre, Snoop Dogg, Earth Wind &
Fire and Marvin Gaye; Anitta was the only recognisable Brazilian artist. Any UI
copy or genre grouping that assumes `funk` means Brazilian funk will mislabel
the catalogue.

## 7. Open questions

- [ ] **Do we need FastAPI and Docker?** Technically, no: Streamlit is Python
      and loads the artifacts in-process; cosine similarity over 89.740 rows is
      milliseconds in memory, and Streamlit Community Cloud hosts one service,
      not two. An API would add a second deployable for no functional gain.
      What changes the answer is the Residência's evaluation criteria — if
      demonstrating API exposure and containerisation is part of the
      deliverable, they earn their place as academic artifacts rather than as
      architecture. Either way the loader in this spec is the shared piece: the
      API would only wrap it. **Decision belongs to the group and the
      instructor.**
- [ ] **A new mascot expression for `Heavy`.** Needs drawing — the current five
      are `feliz`, `foco`, `treino`, `chill`, `triste`, and none reads as
      intense-and-dark.
- [ ] **What replaces the 12-genre list?** The catalogue carries 114 genres as a
      list per track. Showing 114 chips is not a UI; grouping them is a product
      decision.
- [ ] **Does the popularity slider stay at 1–40?** With real data, that range
      admits most of the catalogue. The notebook's underground rule is
      `2 < popularity < percentile 20`. Reconciling the user-facing slider with
      the measured cut is a product call.
- [ ] **Precision @8 stays a placeholder** until an offline evaluation protocol
      exists. Constitution principle 2 keeps the visible marker until then.

## 8. Relationship to the earlier spec

`docs/specs/2026-08-30-real-model-integration/spec.md` planned this integration
before the model existed. It remains the reference for the Spotify API
constraints (§2), the user-profile cascade (§3), playlist creation (§4) and the
deploy checklist (§5), all still valid.

Two of its sections are **superseded** by what the notebook measured:

- its §3 instruction to merge user top tracks by `track_id` "sem fuzzy match"
  is unsafe against the raw CSV, and safe only against the deduplicated parquet
  (§4.1 here);
- its §6 column mapping assumed the app's five hand-picked attributes; the
  selected feature set and the mood clusters replace that plan.
