# Spec — recommendation quality: from one centroid to per-track neighbourhoods

> The app recommends by averaging everything the user likes into a single
> five-number target, then picking the eight rarest tracks near it. Both halves
> are broken: the average describes no music anyone listens to, and "near it"
> covers hundreds of unrelated tracks, so rarity — not similarity — decides
> what is shown. This replaces the centroid with neighbourhoods around each
> seed, and takes rarity out of the ranking.

**Status:** draft · **Date:** 2026-09-03 · **Author:** Grupo 9

---

## 1. Problem

A real user logged in with Spotify. Her most-played tracks are indie, emo,
folk and pop-punk: Forrest Nolan, Angels & Airwaves, Ben Howard, blink-182.
The app recommended `j-dance`, `kids`, `breakbeat`, `club`, `detroit-techno`,
`iranian` and `j-idol` — at 93–96% "afinidade". The first result was *70's
Party Dance Medley (YMCA)*.

Nothing failed. Every step did exactly what it was written to do. Three
measured causes compound.

**The match score saturates instead of ranking.** It is a weighted absolute
distance over five audio attributes, mapped to 31–99. Measured over the
21.594 eligible tracks at popularity ≤ 30:

| target | tracks ≥ 95% | ≥ 90% | ≥ 80% |
|---|---|---|---|
| vibe Heavy | 47 | 888 | 5.564 |
| vibe Gingado | 63 | 782 | 5.351 |
| the real user profile above | 19 | 610 | 5.734 |

The screen shows eight. With 610 tracks tied at ≥ 90%, the match score does
not choose them — it only decides who is admitted to the tie. Within three
percentage points of the top sit `j-idol`, `goth`, `power-pop`, `afrobeat`
and `heavy-metal` simultaneously. Five audio attributes cannot separate
genres, and the number the card shows as *afinidade* is the ceiling of a
ruler that is not measuring.

**Rarity is the actual ranking function.** `pontuacao_de_garimpo` adds 0,15
per popularity point below 30 — up to 4,5 points, which is larger than the
entire spread of the top 71 matches. So among hundreds of near-ties, the
obscurity bonus picks the winners. That is how a 94% *70's Party Dance
Medley* at popularity 8 beat a 96% track at popularity 23. The product
promises "these sound like what you love, and nobody knows them"; it delivers
"these are the most obscure things in a very wide neighbourhood".

**The average of a taste is not a taste.** The user's eight matched tracks
fall in four different moods (4 Gingado, 3 Heavy, 2 Aconchego, 1 Foco). Their
mean is a point that belongs to none of them — Ben Howard's *Promise* sits at
distance 2,01 from the very centroid it helped form. Averaging an eclectic
listener produces the middle of the audio space, which is where the tracks
that resemble nothing in particular live.

The same three causes explain the gospel/indie-rock case already recorded in
`2026-09-03-real-model-in-the-app`. That was not an isolated bug.

## 2. Goal and non-goals

**Goal.** Recommend tracks that a listener recognises as belonging to what
they already like, and show a similarity number that actually varies.

**Non-goals**

| Out of scope | Why |
|---|---|
| Retraining the clustering or changing K | The clusters are validated. The defect is in how the app queries them, not in how they were formed |
| Adding audio features beyond the five | The seven filter techniques already rejected the others in the correct order. Adding `speechiness` back would not separate `j-idol` from `punk-rock` either — genre is not an audio attribute |
| Collaborative filtering | We have no interaction data. One user's Spotify history is not a matrix |
| Changing the Descobrir tab's criteria model | Vibe, genre and artist selection stay as they are. Only the ranking underneath changes |

## 3. Where we are today

| Piece | Today | Target |
|---|---|---|
| Target vector | One centroid, the mean of everything selected | One neighbourhood per seed, merged |
| Ranking | `match + (30 − popularidade) × 0,15` | `match` alone; popularity stays a filter |
| Genre | Ignored in similarity entirely | Constrains the candidate pool per seed |
| Displayed match | 93–96% for almost everything | Varies (measured 66–96% on the same user) |

## 4. Constraints that shape the design

- **`/v1/audio-features` is deprecated.** Attributes for the user's tracks can
  only come from our catalogue, matched by `track_id`. A user whose taste we
  cannot match keeps needing the fallback cascade.
- **`/v1/artists/{id}` returns no `genres` or `followers` for this app.** The
  artist object carries only `external_urls, href, id, images, name, type,
  uri`. Genre affinity must therefore come from the genres of the *matched
  tracks* in our catalogue, not from the API.
- **Genre families are too coarse to use as the constraint.** Restricting to
  the four families covering the user's taste still left 9.246 candidates and
  still returned bluegrass and *Country Roads* — because "Eletrônica" holds
  both her dubstep and trance, and "Folk, jazz e country" holds both Ben
  Howard and bluegrass. The constraint has to be the raw `track_genre`.
- **The prototype is the authority on wording**, so any copy change must be
  justified against `docs/gems-finder-prototipo.html`.

## 5. Decisions

| Decision | Rationale |
|---|---|
| **Recommend per seed, not per centroid** | Measured on the real user: seeding each of her tracks and searching its own genres returned Foals for Forrest Nolan, Dirt Monkey for the ILLENIUM dubstep, Electrelane for Ben Howard. The centroid returned none of these. An eclectic listener gets each of their tastes served, instead of the midpoint of all of them |
| **Rank by `match` only; drop the obscurity bonus from ordering** | It is currently the de-facto ranking function among hundreds of ties, and it selects for the catalogue's junk — mislabelled and novelty tracks cluster at the bottom of popularity. Obscurity is already guaranteed by two filters that cannot be gamed: `elegivel` (independent artist, real music) and the popularity ceiling. It does not need to also win ties |
| **Constrain each seed's candidates to its own `track_genre` values** | The raw genre, not the family. It is the only signal in the dataset that separates `punk-rock` from `j-idol` when their audio vectors are three points apart |
| **Keep the displayed number as pure `match`** | Already decided in the previous spec, and now it means something: on the real user it ranged 66–96% instead of 93–96% |
| **Interleave, do not concatenate** | Take the best from each seed in turn, so eight results cover the listener's range rather than eight variations of their single most-representative track |

## 6. Verification

This is done when:

1. `pytest` passes, with new tests covering: per-seed merge order, the
   genre constraint, and that `garimpar` no longer applies the bonus.
2. Re-running the real user's profile (the eight matched `track_id`s recorded
   in this folder) returns at least five tracks whose genres intersect her
   seeds' genres. Today it returns zero.
3. The displayed match values across those eight results span more than 10
   percentage points. Today they span 3.
4. No result is a track from `GENEROS_FORA_DA_REFERENCIA` (`kids`,
   `children`, `comedy`, `sleep`, `white-noise`, `show-tunes`) — the *YMCA
   medley* case.
5. The Descobrir tab still returns eight gems for every vibe and every artist
   in the selector. Four families — Gospel, MPB, Forró and Sertanejo — return
   fewer at the default ceiling of 30, because their lowest eligible
   popularity is 37, 23, 36 and 43. That is the dataset, not a regression:
   it predates this change and the empty state already names the number to
   raise the slider to. Verified as *unchanged*, not as fixed.
6. The app is verified running, not only unit-tested.

## 7. Resolved questions

- [x] **What happens when a seed's genres have no eligible obscure tracks?**
      **Decided: genre → family → the whole universe.** The group chose that
      the screen never returns fewer than eight gems for lack of an obscure
      tail. This was against the recommendation, which was to drop the seed
      instead: the third level is exactly the wide search that produced
      `j-idol` and the YMCA medley. The trade is accepted knowingly, and the
      exposure is bounded — the level is reached only when a seed's genre
      *and* its family both come up short, and the card names the seed, so a
      distant result is legible rather than mysterious.
      Also decided, on the same call: `kids`, `comedy`, `sleep` and
      `white-noise` are **not** excluded from that last level. They are
      excluded from the artist selector, and that stays as it is.
      Implementation note: the cascade widens when a level has fewer
      candidates than the number of gems requested, not merely when it is
      empty. Stopping at a non-empty level with three tracks left three
      artists in the selector returning three gems instead of eight.
- [x] **Should the Descobrir tab (vibe/genre/artist) also use per-seed?**
      **Decided: yes for artist, no for vibe.** Each chosen artist is a seed
      searching its own genres. A vibe *is* a centroid by definition — the
      measured mean of a cluster — so it is the one place where an average
      describes something that exists. Genre keeps constraining the universe.
      With no artist selected, the search behaves exactly as before, minus
      the obscurity bonus.
- [x] **Does the card need to say which of the user's tracks a gem came from?**
      **Decided: yes.** "Entrou por causa de *Only Love*". The seed is already
      known, so it costs nothing, and it lets the listener judge the path
      instead of accepting a number.

## 8. Result, measured

Re-run against the eight matched tracks of the real user from §1:

| check | before | after |
|---|---|---|
| gems whose genre intersects her seeds' | 0 / 8 | **8 / 8** |
| spread of the displayed match | 3 points (93–96%) | **51 points (42–93%)** |
| tracks from `kids`/`comedy`/`sleep` | 1 (the YMCA medley, ranked first) | 0 |

What she now gets: Foals for *Summer Vibe*, Veer for the ILLENIUM remix,
Electrelane and Ralph McTell for Ben Howard, Fleetwood Mac for blink-182.

One result comes back at 42% — a dub track from the second round of a seed
whose genre is thin. It is kept rather than hidden: the card shows 42%, and a
weak match the listener can see is honest in a way that a fabricated 96% was
not. That number being low is the system working, not failing.

## 9. Why the widely-copied Kaggle approach would not have helped

The reference implementation everyone starts from
([*Music Recommendation System using Spotify
Dataset*](https://www.kaggle.com/code/vatsalmavani/music-recommendation-system-using-spotify-dataset))
does exactly what §1 describes as the defect: `get_mean_vector` returns
`np.mean(song_matrix, axis=0)`, then ranks the whole catalogue by cosine
distance to that one point. It looks convincing in its own demo because the
seed list is five Nirvana songs — a homogeneous taste, where the mean is a
fair summary. It degrades the same way ours did on a listener who likes more
than one thing.

Three concrete differences, recorded because the group will be asked about
this comparison.

**Its data path no longer exists.** `sp.audio_features(track_id)` was
deprecated for new apps on 2024-11-27. That notebook cannot run today with
new credentials, which is also why our attributes come from the catalogue by
`track_id` rather than from the API.

**It puts `popularity` inside the distance metric.** For a general
recommender that is reasonable. For this product it is self-defeating: if
popularity is one of the axes, an obscure track can never be close to a hit —
and finding the obscure neighbours of hits is the entire premise.

**Its 15 features would make our saturation worse, not better.** The obvious
reading of §1 is that five attributes are too few. Measured on the eligible
pool, adding `speechiness`, `loudness`, `bpm` and `duration_ms`:

| | 5 attributes | 9 attributes |
|---|---|---|
| tracks ≥ 90% of the top | 1.112 | **1.653** |
| standard deviation of the distance | 0,129 | **0,079** |

The extra columns are near-constant across this catalogue — normalised
variance 0,0009 for `duration_ms`, 0,0087 for `speechiness`, 0,0110 for
`loudness`. Averaging over more axes that barely move dilutes the distance
instead of spreading it, and `loudness` correlates +0,77 with `energy`, the
redundancy the feature selection already rejected.

So the five-feature choice holds, and the conclusion is stronger than "we
picked a better metric": no audio-only metric was going to separate
`punk-rock` from `j-idol`. The signal had to come from genre.
