# Spec — combinable search criteria

Step 1 of Descobrir stops being a three-way choice and becomes three optional,
independently combinable criteria, so a listener can ask for "Chill, in MPB,
like Dora Lima" in one dig instead of three separate ones.

**Status:** draft · **Date:** 2026-09-01 · **Author:** Amanda Elisa

---

## 1. Problem

Today Step 1 makes the listener pick exactly one of three starting points: a
vibe, a genre, or a favourite artist. The three are mutually exclusive, and
each accepts a single value — except favourite artist, which already accepts up
to three.

That exclusivity is a lie about how people describe taste. Someone who wants
calm acoustic MPB has to choose between the *feeling* and the *genre*, run one
dig, look at results from the wrong half of their request, then go back and run
the other. Worse, the two digs cannot be reconciled: the app never scores a
track against both ideas at once, so the answer to the combined question simply
does not exist in the product.

The exclusivity also wastes the one search intent that is genuinely a filter. A
genre is a statement about *which tracks are even candidates*; a vibe and an
artist are statements about *what the ideal track sounds like*. Collapsing all
three into "pick one mode" hides that distinction, and with it the most useful
thing a listener can do: narrow the universe and aim inside it.

## 2. Goal and non-goals

**Goal.** Let a listener combine any number of vibes, genres and favourite
artists in a single dig, where genres narrow the search universe and vibes and
artists together form the audio target.

**Non-goals**

| Out of scope | Why |
|---|---|
| Per-criterion weighting (e.g. "vibe counts double") | The approved prototype averages the criteria unweighted. Weighting is a modelling decision that needs real evaluation data to justify, not a UI knob invented here. |
| Letting vibes or artists narrow the universe | Only genre is a categorical property of a track. A vibe is a point in audio space and an artist is a reference profile; neither names a subset of the catalogue. |
| An artist search field in the app | The prototype has one and the Streamlit app never did — a pre-existing divergence, unrelated to combinability, with only 10 reference artists to scroll. Recorded here so the next person does not read its absence as a regression from this job. |
| Replacing the Precisão @8 placeholder with a real number | Still blocked on the offline evaluation (see `2026-08-30-real-model-integration`). This job only changes how the placeholder responds to the new inputs, and keeps its `TODO`. |
| Any change to Minha conta | The connected-tester flow builds its target from the listener's own top tracks and has no Step 1. Untouched. |
| Raising the three-artist cap | Unchanged behaviour; the cap is in the approved prototype. |

## 3. Where we are today

| Piece | Today | Target |
|---|---|---|
| Step 1 shape | A segmented control picks one of three modes; only the chosen mode's selector is visible | Three always-visible, separately labelled groups, each marked optional |
| Vibe | Exactly one of four, always one selected | Zero or more of four, none selected at first |
| Genre | Exactly one of twelve, always one selected | Zero or more of twelve, none selected at first |
| Favourite artist | Zero to three; already a toggle | Unchanged — zero to three, toggle |
| Search universe | The whole catalogue, except in genre mode, where it is that one genre | The whole catalogue, narrowed to the selected genres when any are selected |
| Audio target | The chosen mode's vector: the vibe's target, the genre's centroid, or the mean of the chosen artists | The mean of one vector per active criterion group: the mean of the selected vibes' targets, the mean of the selected genres' centroids, and the mean of the selected artists' profiles |
| Status line | Names the single active mode and the popularity ceiling | Lists every active criterion in order, then the ceiling |
| Nothing selected | Impossible for vibe and genre; in artist mode the dig warns and does nothing | The dig button is unavailable and says why, before the listener clicks |
| Precisão @8 | One placeholder per mode | A placeholder that rises with each combined criterion group, still marked as a placeholder |
| Result heading | Names the single mode | Names every active criterion |

## 4. Constraints that shape the design

**The approved prototype is the authority, and it has already been updated.**
`docs/gems-finder-prototipo.html` now carries this exact design: the three
labelled optional groups, multi-select toggles on vibe and genre, genres
filtering the universe, the averaged target, the combined status line, the
blocked dig, and the rising Precisão @8. Per constitution principle 3 the app
mirrors it, and every piece of Portuguese copy in this change is copied from it
rather than invented. Where this spec and the prototype disagree, the prototype
wins and the disagreement is a bug in this spec.

**The Precisão @8 metric is a placeholder and must stay visibly one.**
Constitution principle 2 forbids a placeholder metric reaching the UI without a
marker. Making the number *move* in response to the listener's choices makes it
look more like a measurement than the fixed per-mode constants did, so the
`TODO` marking it as unmeasured has to survive this change and name the new
formula.

**The catalogue is simulated and small** — 32 tracks across 12 genres, some
genres holding as few as two. Combining several narrow genres with a low
popularity ceiling can legitimately empty the result set, so the empty state is
a normal outcome of this feature, not an error path.

**Averaging is what makes combination coherent.** The scoring function compares
one track against one target vector, and that is the piece the constitution's
referents pin as a faithful translation of the prototype. So combination has to
happen *before* scoring, by reducing the active criteria to a single vector —
not by scoring several times and merging rankings.

**Existing selection state cannot survive the change.** The stored choices are
single-valued and one of them is "which mode"; the new shape is three lists and
no mode. A returning listener starts from nothing selected.

## 5. Decisions

| Decision | Rationale |
|---|---|
| Genres filter the universe; vibes and artists only form the target | The one distinction the old mode-picker hid, and the reason combining is useful rather than merely permissive. A genre names a subset of the catalogue; the other two name a point in audio space. |
| The target is the unweighted mean of one vector per *group*, not per selection | Two vibes and one artist give a target halfway between "the vibes" and "the artist", not two-thirds vibe. Each idea the listener expressed counts once, however many chips it took to express it. Copied from the prototype. |
| Selected genres contribute to the target as well as filtering | A listener who picks only a genre still needs a target to rank against, and that genre's own average sound is the only honest one. Keeps genre-only digs working exactly as they do today. |
| Nothing selected disables the dig button, with the reason visible next to it | The old flow let the listener click and then told them off. With three optional groups, "nothing selected" is now reachable from the initial state, so the block has to be visible before the click, not after. |
| Nothing is selected on first load | With three combinable groups there is no honest default: pre-selecting a vibe would silently bias every first dig toward it. The status line and the disabled button say what to do instead. |
| Precisão @8 rises by 3 points per active group over a base of 84, capped at +7 | Copied verbatim from the prototype, whose comment gives the reasoning: more criteria pin the target more precisely. It stays a placeholder — the numbers are invented, and the `TODO` says so. |
| The result heading and the per-track "why" sentence list every active criterion | A listener who combined three ideas needs to see all three reflected back, or the results look like they answered a narrower question. |
| The mode concept is deleted, not kept as a fourth "combined" mode | Keeping it would leave dead selection state and a constant listing modes that no longer exist. There is one flow now. |
| The result heading's mascot keeps a vibe's colour only when exactly one vibe is selected | The app currently tints it with the chosen vibe's colour, which the prototype does not do. With several vibes there is no single source for the tint, so it falls back to the prototype's lime. Recorded rather than silently kept, per principle 3. |

## 6. Verification

This is done when someone else can run these checks:

1. `pytest` passes, and the suite covers: the mean of several criterion
   vectors, the universe narrowing to the selected genres, a genre-only dig
   still ranking against that genre's average sound, the Precisão @8 value for
   one, two and three active groups, and the status line's wording for every
   combination of active groups including none.
2. Running the app (`streamlit run app.py`), Step 1 shows three labelled groups
   at once — Vibe, Gênero, Artista favorito — each marked optional, with no
   mode selector anywhere on the page.
3. On first load nothing is selected, the dig button is unavailable, and the
   text beside it tells the listener to choose at least one criterion.
4. Clicking a vibe selects it and clicking it again clears it; the same holds
   for a genre. Several of each can be selected at once. The artist group still
   caps at three and still says how many are chosen.
5. With vibe Chill, genre MPB and artist Dora Lima all selected and a ceiling of
   18, the status line reads `Buscando por vibe Chill, gênero MPB, parecido com
   Dora Lima, com popularidade até 18.`
6. With one genre selected, every returned track is in that genre. With two
   genres selected, every returned track is in one of the two. With no genre
   selected, tracks from any genre can appear.
7. Selecting a second and then a third criterion group raises the displayed
   Precisão @8, and the `TODO` in the code still marks it as a placeholder,
   naming the new formula.
8. A combination that matches nothing at the chosen ceiling shows the empty
   state, whose hint points at both the ceiling and the Step 1 criteria.
9. Every string added to the UI appears in
   `docs/gems-finder-prototipo.html`, and no engineering identifier added by
   this change is Portuguese.

## 7. Open questions

- [ ] Should a listener who selects a genre *and* an artist from a different
      genre be warned that the combination may be self-defeating (the artist
      pulls the target away from every candidate track)?
      *Recommendation:* no. It is a legitimate request — "MPB that sounds like
      MC Vitrine" is a real, if narrow, taste — and the empty state already
      covers the case where it finds nothing. A warning here would be the app
      second-guessing a choice it cannot evaluate without real data.
- [ ] Should the selected criteria persist across a page switch to Minha conta
      and back, as the dig *results* already do?
      *Recommendation:* yes, and it comes for free from how selection state is
      stored — no extra work. Flagged only so the next person knows it was
      considered rather than accidental.
- [ ] Does the cap on the Precisão @8 bonus (+7) still make sense once the real
      evaluation lands?
      *Recommendation:* the question dies with the placeholder. Whatever
      replaces it will be measured per configuration, not computed from a
      criterion count, so the cap is not a decision this job hands forward.
