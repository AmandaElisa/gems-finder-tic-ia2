# Spec — a learned item representation, so genre stops living in an `if`

> Genre affinity is currently enforced by hand-written rules: a family map, a
> curated list of tags that are not genres, and a cascade of `if`s deciding
> which pool a seed may search. This replaces the *ranking* half of that with
> a learned representation — genre folded into the item vector — while leaving
> the family names, which are the interface, exactly as they are.

**Status:** draft · **Date:** 2026-09-04 · **Author:** Grupo 9

---

## 1. Problem

The recommender works, and it works for a reason nobody can point at in the
model. Every improvement of the last cycle was a rule:

- `NAO_SAO_GENEROS` — twelve tag names typed by hand, because `chill` and
  `piano` leaked across families (19% of the Indie universe, 50% of Clássica).
- `_pool_da_semente` — a three-level `if` cascade choosing where a seed may
  look.
- `_genero_visivel` — a preference order for which genre a card should show.

Each is defensible in isolation. Together they mean the system's core
competence — *knowing that punk-rock is near emo and far from j-idol* — lives
in curated lists rather than in anything measured. A reviewer asking "where is
the machine learning in the recommendation?" would be right to press.

The underlying cause is recorded in
`2026-09-03-recommendation-quality`: five audio attributes cannot separate
genres. For one real user profile, 610 eligible tracks tie at ≥ 90% match, and
`j-idol`, `goth`, `power-pop`, `afrobeat` and `heavy-metal` sit within three
points of each other. The rules exist to compensate for a representation that
does not carry genre at all.

## 2. Goal and non-goals

**Goal.** Put genre inside the item vector, so that similarity respects it by
construction and the hand-written rules stop deciding what is recommended.

**Non-goals**

| Out of scope | Why |
|---|---|
| **Renaming or regrouping the 15 families** | They are the interface. Rock, Indie, Forró, MPB, Índia e Oriente and the rest are the group's curated, intuitive vocabulary, and people click them. The learned dimensions are latent, unnamed and never shown |
| Removing the family filter | It stays as the *universe* filter. Intuitive names choose **where** to search; the learned vectors decide **what** comes back from there |
| Re-clustering, or changing K or the moods | The five moods are validated and are product vocabulary |
| Bringing scikit-learn into production | It was removed deliberately when the deploy broke. Training stays in the notebook; the app receives finished vectors |
| The Brazilian canon misclassification | Measured and deferred by the group on evidence: those 26 artists appear in 4 of 120 recommendations (3%). Recorded in §6 as a known limitation |

## 3. Where we are today

| Piece | Today | Target |
|---|---|---|
| Item representation | 5 audio attributes | 5 audio attributes + 24 latent genre dimensions |
| Similarity | Weighted absolute distance, hand-tuned `PESOS` | Cosine on the combined normalised vector |
| Genre in ranking | A cascade of `if`s over raw genre names | Inside the vector |
| `NAO_SAO_GENEROS` in search | Filters family membership | No longer needed for ranking; kept for artist labelling |
| Family names | 15 curated names | **Unchanged** |

## 4. Constraints that shape the design

- **No scikit-learn in production.** `requirements.txt` is streamlit, pandas,
  numpy, requests, pyarrow. The notebook fits the transforms; the app loads a
  matrix and takes dot products. Cosine on unit-normalised vectors *is* a dot
  product, so numpy suffices.
- **The artifact contract grows.** A new file under `data/processed/`, aligned
  row-for-row with `catalogo.parquet`. At 89.740 × 29 in float32 that is
  ~10 MB, which the repo can carry.
- **Model versioning must keep working.** The content hash in `modelo.json`
  has to cover the new transform parameters, or the app could load embeddings
  from one training run against a catalogue from another.
- **The prototype remains the authority on wording.** No user-visible copy
  changes here.

## 5. Decisions

| Decision | Rationale |
|---|---|
| **Multi-hot the 114 genres, reduce with TruncatedSVD to 24 dimensions** | The genre matrix is sparse and binary; SVD is the standard reduction for it and needs no tuning beyond the rank. 24 is a starting point to be validated, not a result |
| **Normalise the audio block and the genre block separately, then weight** | Otherwise the block with more dimensions dominates by accident rather than by choice. The weight becomes one explicit, calibratable parameter instead of an emergent one |
| **Cosine, not the current weighted absolute distance** | It is the standard metric for this kind of vector, and it is what the k-NN literature and the Kaggle reference both use. It also removes the hand-tuned `PESOS` from the ranking path |
| **Keep the family filter as the universe** | The names are the interface and they are good. This is the one place where a curated list is the right answer, because it encodes what people call music, not what the data can measure |
| **Export vectors, not the fitted objects** | Same reasoning as `modelo.json` over `modelo.joblib`: pickled sklearn is fragile across versions, and the app never calls `fit` or `predict` |

## 6. Verification

This is done when:

1. `pytest` passes, with tests covering the new similarity and the fallback
   when embeddings are absent.
2. The notebook executes clean end to end and exports vectors aligned
   row-for-row with `catalogo.parquet` — asserted in the notebook, not
   assumed.
3. **Measured against the current implementation, on the same queries**, and
   reported honestly whether it wins or loses:
   - the real user profile from the previous spec (8 seeds),
   - the Indie + Cigarettes After Sex + Joji query,
   - one query per family.
   Reported: share of results inside the seed's genre, spread of the displayed
   match, and variety (distinct genres among the eight).
4. The 15 family names are byte-identical to today's in `modelo.json`.
5. `requirements.txt` is unchanged.
6. The app is verified running.

**Known limitation, carried forward.** 26 consolidated Brazilian artists —
Tim Maia, Gilberto Gil, Chico Buarque, Marisa Monte, Djavan and others — are
classified `Independente` because their popularity in this dataset (43–49)
sits below the consolidation threshold. Popularity cannot separate them: they
are at percentile 12–65 of Brazilian artists, and 511 of 557 non-canonical
artists have a higher ceiling. Catalogue depth can — `n ≥ 15 tracks` selects
exactly those 26 with no false positives — and the group deferred applying it
after measuring the impact: they appear in **4 of 120** recommendations (3%),
and the dataset does not contain their hits anyway (Gilberto Gil's 20 tracks
span popularity 28–43).

## 7. What the measurement changed

The spec above proposed replacing the ranking wholesale. **Measurement says
that would be worse**, and the plan changed because of it.

Swept 5 SVD ranks × 4 block weights, evaluated on six real seeds, against the
current implementation:

| configuration | coherence | variety |
|---|---|---|
| **current implementation** | **100%** | **3,2** |
| embeddings K=48, weight 0,4 | 92% | 2,7 |
| embeddings K=24, weight 0,6 | 92% | 2,2 |
| embeddings K=64, weight 0,7 | 100% | 1,7 |

No configuration dominates. Where coherence ties, variety collapses. One
caveat against our own result: coherence is measured as *shares a raw genre
with the seed*, which is precisely what the hard filter optimises by
construction, so that column is biased toward the baseline. Variety is not,
and the embeddings lose there in every configuration.

**But the filter has a case with no answer at all**, and there the result
inverts. Seeding *Manchete dos Jornais* (Calcinha Preta — `forro`, `pagode`,
`sertanejo`) at ceiling 20, where the genre has **zero** eligible tracks:

| | returns |
|---|---|
| current — the cascade falls to the whole catalogue | j-idol, j-idol, grunge, honky-tonk, j-dance |
| embeddings | honky-tonk × 5 |

The embedding discovered that **forró neighbours honky-tonk** — Brazilian and
American country dance music. No rule in this repository encodes that; it came
out of genre co-occurrence.

**So the decision is a hybrid, not a replacement.** The family filter and the
per-seed pools keep levels 1 and 2, which they win. The learned representation
replaces level 3 — the fall-through to the whole catalogue — which is the only
place the rules produce noise. Smaller change, measured benefit, and nothing
that works today gets worse.

## 8. Open questions

- [ ] **What weight between the audio block and the genre block?** To be
      calibrated, not assumed. The prototype used 0,6 for genre and produced
      strongly coherent but *narrow* results — five tracks of the same genre
      per seed. Recommendation: sweep it and choose on measured variety and
      genre coherence together, reporting the trade-off rather than hiding it.
- [ ] **How many SVD components?** 24 explained only 30,7% of variance in the
      prototype. Recommendation: sweep the rank, and report the variance
      curve — a low number is expected for sparse tag data and is not by
      itself a defect, but the group should be able to answer for it.
- [ ] **Does this replace `garimpar_por_sementes` or feed it?** Recommendation:
      feed it. The per-seed round robin solved a different problem — an
      eclectic listener whose average belongs to nobody — and that problem
      does not go away with a better metric.
