# Spec — Hidden-gems recommender methodology

> The methodology behind Gems Finder: content-based filtering over audio
> attributes, a popularity-bias filter, and the evaluation that has to back
> the numbers we publish. Written from the Grupo 9 report so the design stops
> living only in a slide deck.

**Status:** draft · **Date:** 2026-09-01 · **Author:** Grupo 9 (Residência em IA · UnB, Turma 2)

---

## 1. Problem

**The market pain.** Streaming recommendation falls into algorithmic bubbles
that surface the same well-known artists. Mood-based playlists (focus, workout,
chill) repeat the same obvious tracks, ignoring thousands of talented artists
hidden in the catalogue. Independent artists stay invisible because low
popularity excludes them from discovery in the first place — a feedback loop:
few plays means no playlist placement, which means few plays.

**The business objective.** Build an analytical engine that maps the
multidimensional mood space and filters tracks with high technical and
emotional potential but low popularity — *hidden gems* — enabling
hyper-personalised discovery that serves listeners and independent artists at
once.

**The documentation problem this spec fixes.** The methodology exists as a
report, not as anything in this repository. Three different versions of "the
model" are currently in play and none of them references the others (§3). A new
group member reading the code would build the wrong thing, and the report's
own claims cannot be checked against anything.

## 2. Goal and non-goals

**Goal.** Record the recommender's methodology, the state of each piece, and
the decisions already made — so implementation work can be planned against one
written source instead of three divergent ones.

**Non-goals** — explicitly out of scope for this document:

| Out of scope | Why |
|---|---|
| Implementing k-NN, cosine similarity or the attribute graph | This is a spec. Implementation gets its own plan and tasks |
| Choosing the final feature set | It must be decided empirically by the tests in §6.2, not by argument in a document |
| Replacing `src/recomendacao.py` | The app's current model works and ships. Swapping it is a separate Structural job that needs the evaluation numbers first |
| Collaborative filtering | Impossible with this dataset — it carries no listener metadata (§5.1). Not a preference; a constraint |
| The FastAPI + Docker deployment | Planned architecture (§7), unstarted. Needs its own spec once the model is settled |

## 3. Where we are today

The single most important table in this document. "The model" currently means
three different things:

| Piece | The app (`src/`) | The notebooks (`notebook/`) | The report |
|---|---|---|---|
| Catalogue | 32 fictional tracks in `src/dados.py` | Full dataset via Google Drive | 114.001 tracks |
| Similarity | Weighted absolute distance, hand-set weights in `PESOS` | none | k-NN + cosine similarity |
| Structure | Flat DataFrame scan | none | Attribute/artist graph (tracks, artists, genres) |
| Feature selection | 5 attributes chosen by hand | none | Variance Threshold, Pearson, Information Gain, Fisher's Score |
| Underground cut | `popularidade <= teto` from a UI slider | none | Statistical threshold on `popularity` (e.g. percentile 20) |
| Artist status | not modelled | none | `is_consolidated == 'Independente'`, derived by catalogue aggregation |
| Moods | 4 hand-tuned target vectors in `VIBES` | none | Clusters over valence, energy, acousticness, speechiness |
| Precision @8 | `PRECISAO_8` placeholder constant | none | To be measured |
| Runs where | Locally and Streamlit Cloud | **Colab only** — imports `google.colab.drive` | FastAPI + Docker (planned) |

Notebook reality, measured: `dadosLimpos.ipynb` has 17 cells and **no markdown
headings at all**; `gems_finder_eda.ipynb` has 15 cells and two headings
("Import dos Dados e Bibliotecas", "Análise Descritiva"). Neither imports
scikit-learn. Everything in the report's methodology — feature selection,
k-NN, cosine similarity, the graph, the independent-artist filter — is
**unimplemented**.

The app and the report also disagree about *how* similarity works: weighted
absolute distance with fixed weights is not cosine similarity over a k-NN
neighbourhood, and the two will rank the same catalogue differently. Whether
the app adopts the report's model is an open question (§8).

## 4. Who this serves

Two personas, and they are the two sides of one marketplace — the same query
serves both. Full artefact: [`assets/personas.jpeg`](../../../assets/personas.jpeg).

**Marina, 24, data analyst / student — the listener.** Knows her taste well and
wants to escape the mainstream. Her pains: recommendations always bring
well-known artists; popular playlists repeat the same names; genre is too
coarse a handle, since the same genre spans completely different energies and
emotions; she has to dig hard to find anything genuinely good. What she needs:
recommendations that read deep preferences (mood, energy, audio character),
low-popularity tracks aligned to her taste, and exploration that does not cost
her an evening.

> "Não quero ouvir o que todo mundo está ouvindo. Quero descobrir músicas que
> parecem ter sido feitas exatamente para mim."

**Lucas, 27, independent musician — the artist.** Produces good work that does
not reach the right people. His pains: competing with consolidated artists;
algorithms favouring whoever already has engagement; low popularity producing
low exposure; too few plays to enter playlists; marketing he cannot afford.
What he needs: to reach listeners with high musical and emotional
compatibility, and to be judged on potential rather than on current
popularity.

> "Eu não preciso que minha música apareça para milhões de pessoas. Preciso que
> ela chegue às pessoas que têm maior chance de se conectar com ela."

**Design consequence.** Marina is served by mood and similarity matching;
Lucas is served by the independent-artist filter (§5.4). They are not two
features — they are one ranked query with a filter, which is why the product
tagline holds: *conectamos quem quer descobrir com quem quer ser descoberto.*

## 5. Constraints that shape the design

### 5.1 The dataset has no listener metadata

One of the guiding questions asks what information about end listeners is
available: age, demographics, location, browsing history. **The answer is
none.** The dataset carries track attributes and popularity only.

This is not a gap to fill — it decides the architecture. With no user-item
interaction history there is nothing for collaborative filtering to learn
from, so **content-based filtering is forced, not chosen.** Everything the
system knows about a listener has to be inferred from audio attributes.

### 5.2 Spotify killed the audio-attributes endpoint

For apps created after 2024-11-27, Spotify deprecated `/v1/audio-features`,
`/v1/audio-analysis`, `/v1/recommendations`, related artists and preview URLs.

Still working, and already used by the app: OAuth, `/v1/me`,
`/v1/me/top/tracks`, `/v1/me/top/artists`, playlist creation and track
addition.

**Consequence:** audio attributes always come from our dataset, never from the
API. A user's real profile can only be built by matching their top tracks
against the dataset by `track_id` — which makes profile coverage a metric we
have to show honestly, not hide. Detail in
[`docs/specs/2026-08-30-real-model-integration/spec.md`](../2026-08-30-real-model-integration/spec.md).

### 5.3 The notebooks are Colab-bound

`gems_finder_eda.ipynb` imports `from google.colab import drive`. It cannot run
on a teammate's machine, in CI, or anywhere the model would be serialised for
the FastAPI service. Any path from notebook to production crosses this first.

### 5.4 The approved prototype governs the product surface

`docs/gems-finder-prototipo.html` is the authority on flow, copy and palette
(constitution principle 3). A methodology change that alters what the user sees
is a prototype change, not a silent model swap.

## 6. Methodology

### 6.1 Content-based filtering

Items and the listening profile are both described by known metadata and
structured audio attributes. Forced by §5.1.

**Search strategy.** The project evolved from isolated parameters to
simultaneous multifaceted search: the user crosses **moods + genres + artists**
rather than picking one excluding axis. This directly answers Marina's pain
that genre alone is too coarse.

### 6.2 Feature engineering and selection

Numeric Spotify attributes define each track's technical DNA: `danceability`,
`energy`, `valence`, `acousticness`, `instrumentalness`.

Feature choice is **empirical, not fixed**. Seven filter techniques were
considered. Each was tested against the actual dataset before being adopted,
and **five do not apply** — recording why is worth more than running all seven
badly.

| Technique | Applies? | Evidence, measured on `data/raw/dataset_spotify_raw.csv` |
|---|---|---|
| Dispersion ratio | **No — 0 of 9 columns** | The geometric mean needs strictly positive values. `loudness` has 113.910 negative values of 114.000; `instrumentalness` has 38.763 zeros. Every attribute fails |
| Variance Threshold | **Not useful** | It measures unit, not information: `tempo` var = 898,7 · `loudness` var = 25,3 · every other attribute < 0,12. A 0,01 threshold cuts nothing; any threshold that cuts something cuts by scale, keeping only tempo and loudness |
| Mean Absolute Difference | **Not useful** | Same scale problem |
| Chi-square | **No** | Requires non-negative features and a categorical target. `loudness` is negative in 113.910 rows; binning to fix it destroys the continuous space the model works in |
| Pearson's correlation | **Yes** | Applies directly to continuous attributes — and produces the actionable finding below |
| Information Gain | **Yes, but the target decides the answer** | Target = `track_genre`: `acousticness` MI = 0,515, `energy` 0,438, `loudness` 0,373. Target = hidden (`popularity <= 10`): everything falls to 0,02–0,06. The rankings *invert* — `danceability` is 4th by genre (0,370) and **last** by hidden (0,020) |
| Fisher's Score | **Yes, same caveat** | Needs class labels; inherits the same target-choice problem |

**Two findings that change decisions.**

**1. The current model double-counts one axis.** `energy` × `acousticness` have
|r| = **0,734**, and both are among the app's five attributes, weighted 0,25
and 0,15 in `src/dados.py::PESOS`. So **40% of the total weight sits on two
attributes that are 73% redundant**, and the distance counts that sonic axis
twice. (`energy` × `loudness` is higher still at 0,762, but `loudness` is not
in the model.) Either drop one or reduce their combined weight — and either way,
say so in the model's documentation.

**2. Audio does not predict popularity, so do not select on it.** The strongest
correlation between any attribute and `popularity` is |r| = **0,095**
(`instrumentalness`, negative). Selecting features by relevance to popularity
would be selecting on noise. It would also be the wrong criterion: the engine
is unsupervised cosine similarity, not popularity prediction. What matters is
which attributes define the perceptual space the listener navigates — which is
what Information Gain against `track_genre` measures, genre being the only real
label the dataset carries.

This second finding **supports the project's premise** rather than threatening
it: if popularity is not explained by audio characteristics, then genuinely
good low-popularity tracks exist to be found. That is the whole business case,
and it now has a number behind it.

**Adopted:** Pearson (for multicollinearity among attributes) and Information
Gain against `track_genre` (for perceptual relevance). The other five are
rejected on the evidence above. The final feature set is whatever these two
support, decided in the notebook and committed there — this spec deliberately
does not name it (§2).

### 6.3 Graph and vector similarity

To structure catalogue relationships without external user history, an
attribute-and-artist graph (content graph) is built directly on the internal
dataset. Nodes: tracks (`track_id`), artists, genres, and neighbouring tracks
connected by structural proximity. It supports reasoning of the form: *this
independent track connects to genre X and sits structurally close to artist Y.*

The engine over that space is **k-NN with cosine similarity**, measuring the
distance between the desired sonic profile and the rest of the catalogue.

### 6.4 The popularity-bias filter — the business differentiator

Artist status (Consolidated vs Independent) is derived dynamically by
aggregating catalogue metrics. Before results are returned, a strict business
filter applies: `is_consolidated == 'Independente'`.

The effect is the product's whole point: recommended tracks have high sonic
similarity to major hits **and** genuinely belong to underground artists. This
is the mechanism that serves Lucas, and it is a filter rather than a ranking
penalty — a consolidated artist's track is not down-weighted, it is excluded.

### 6.5 Hidden Potential Score

A metric that surfaces underrated tracks — low popularity, audio attributes
close to the platform's big hits — so that discovery is *fair* rather than
merely random. The concrete formula is unspecified here; deriving it is
implementation work, and it must be evaluated (§7) rather than asserted.

## 7. Guiding questions — answered and open

### Answered by the data

| Question | Answer |
|---|---|
| What listener metadata is available? | None. Track attributes and popularity only — see §5.1 and its architectural consequence |
| Do we need more data for the analysis? | Not for content-based filtering. Collaborative filtering would need interaction data we do not have and cannot get from the API (§5.2) |

### Answered by measuring the dataset

Measured on `data/raw/dataset_spotify_raw.csv`, which is present in the repo
(20 MB) — the notebooks read a Colab Drive copy instead (§5.3).

| Question | Measured answer |
|---|---|
| Volumetry | **114.000 rows**, 21 columns. Note: the README and the real-model spec both say 114.001 — off by one, and worth correcting at the source |
| Nulls or corrupted fields? | **Exactly one row**, null in `artists`, `album_name` and `track_name`. Imputation is not the question; dropping one row is |
| Duplicate `track_id`? | **24.259 (21%)** |
| Same (`track_name`, `artists`) under different IDs? | **32.658 (29%)** |
| Genres | **114** distinct `track_genre` values |
| Underground threshold, percentile 20 | `popularity <= 10` |
| Coverage of the app's current cut | `popularity <= 40` covers **67.326 tracks (59,1%)** of the catalogue |

**Two of these change design decisions.**

**The duplicates are structural, not dirt.** This dataset repeats a track once
per genre it belongs to, which is how genre membership is expressed. For
per-genre centroids that is correct. For anything scanning the catalogue
globally it is double-counting — and it makes the real-model spec's §3
instruction ("cruzar por `track_id` com o dataset; merge direto, sem fuzzy
match") actively unsafe: a direct merge on a column with 21% duplicates
multiplies rows and skews the user's mean profile. Deduplicate before merging,
and decide explicitly which genre a deduplicated track keeps.

**The app's underground filter barely filters.** At the slider's maximum, 59,1%
of the catalogue counts as "underground" — the majority. The report's
percentile-20 rule means `popularity <= 10`. These are not two settings of one
knob; they are two different products, and §9 has to settle which one the
premise rests on.

### Still requiring work in the notebooks

| Question | Where it gets answered |
|---|---|
| Outliers that should be treated as noise? | EDA, with the decision recorded — dropping a real outlier can delete exactly the unusual track a discovery engine exists to find |
| Which attributes correlate most with popularity? | Correlation analysis (§6.2) |
| Which low-popularity genres resemble high-popularity ones in audio? | Genre centroid comparison — the core "niche discovery" question |
| Does the model over-prioritise consolidated artists? | Measured after §6.4 is implemented, by checking the independent share of returned results |

## 8. Verification

This methodology is validated when:

1. Every claim in §3's "report" column has either an implementation or a
   recorded decision not to implement it.
2. The feature set is justified by output from the §6.2 techniques, committed
   in a notebook — not by assertion.
3. `PRECISAO_8` in `src/dados.py` is replaced by numbers from a written
   offline evaluation protocol, with the protocol itself in the repo. Until
   then it stays visibly marked as a placeholder (constitution principle 2).
4. The independent share of returned results is measured, confirming §6.4
   actually corrects the bias it targets.
5. A teammate can run the notebooks without a Google account.

## 9. Open questions

- [ ] **Does the app adopt k-NN + cosine, or keep its weighted distance?**
      Recommendation: decide with numbers, not taste — implement both in a
      notebook, evaluate on the same protocol, and let §8.3 settle it. The
      current model is not obviously worse; it is merely un-evaluated.
- [ ] **What is the underground threshold?** The report suggests percentile 20;
      the app currently exposes a 1–40 slider (`src/ui/descobrir.py:129`).
      These are different products:
      a fixed statistical cut versus a user-controlled depth. Recommendation:
      keep the slider for the user and use a fixed percentile for offline
      evaluation, so the metric is stable while the experience stays
      explorable.
- [ ] **How do 114 `track_genre` values map to the prototype's 12 genres?**
      Needed before the real catalogue can back the genre mode.
- [ ] **Minimum matches for a real user profile?** Suggested: 5, with the
      cascade fallback already specified in the real-model spec §3.
- [ ] **What is the offline evaluation protocol for Precision @8?** Without an
      agreed protocol, item 3 of §8 cannot be closed and the metric stays a
      placeholder.
- [ ] **How is `is_consolidated` computed?** "Aggregation of catalogue metrics"
      needs an exact rule — a popularity threshold on the artist's mean, a
      track-count floor, or both.
- [ ] **Do the notebooks get de-Colab'd now or later?** It blocks §8.5 and any
      model serialisation for FastAPI, so it is upstream of more than it looks.
