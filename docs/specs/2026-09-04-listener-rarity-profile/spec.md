# Spec — how off the beaten path someone already listens

> The "Minha conta" tab describes *what* someone listens to — energetic, sung,
> electric. It says nothing about *how known* that music is, which is the axis
> this whole product is built on. This adds it, as a measured number with a
> label, and is careful not to turn eight tracks into a personality verdict.

**Status:** draft · **Date:** 2026-09-04 · **Author:** Grupo 9 · **Track:** Feature

---

## 1. Problem

The profile card reports five audio attributes and a phrase derived from them
("cantada e elétrica"). All five describe timbre and mood. None describes
obscurity — even though the product exists to find obscure music, and the
listener's own relationship to obscurity is the most interesting thing we can
tell them about themselves.

The data is already there and unused: every matched track carries
`popularidade`, and the catalogue gives the distribution to compare against.

## 2. Goal and non-goals

**Goal.** Tell someone where their own listening sits on the popularity axis,
with the number that produced the claim visible next to it.

**Non-goals**

| Out of scope | Why |
|---|---|
| A personality verdict about the person | We see 8 of 50 tracks, filtered by what our catalogue happens to contain. That describes a sample, not a taste. The label names the *matched tracks*, and the sample size sits beside it |
| Using it to change recommendations | It is a reading, not an input. Mixing it into the ranking would need its own spec and its own evidence |
| A number for the simulated profile | Without a real login there are no matched tracks. The example profile shows no label rather than a fabricated one — principle 2 |
| Comparing users to each other | We have one user at a time and no stored history |

## 3. Where we are today

| Piece | Today | Target |
|---|---|---|
| Profile phrase | `descrever_perfil` — two strongest audio attributes | unchanged |
| Popularity of what they listen to | computed nowhere | median of matched tracks, as a catalogue percentile |
| Label | none | one of four, derived from the percentile |

## 4. Constraints that shape the design

- **The sample is small and biased.** A track only matches if it is among the
  89.740, which is ~1000 tracks per genre selected by Spotify — not a sample
  of world listening. Measured on the real tester: 8 of 50 tracks matched.
  Whatever is shown has to carry that caveat where it is read, not in a
  footnote.
- **`popularidade == 0` means "not captured", not "nobody plays it"** —
  9.347 tracks in the catalogue. Decided in the notebook (the `[0, 0, 44]`
  pattern), and the same decision applies here: a zero among someone's most
  played tracks is a gap in our data, and including it would fake obscurity.
- **Fewer than `MINIMO_DE_FAIXAS_CRUZADAS` matches already means no real
  profile.** The label follows the same rule as the rest of the card: it
  appears only on the path that computed a profile from actual tracks.
- **The prototype has no element for this**, so the copy is new and must sound
  like the mascot rather than like a dashboard.

## 5. Decisions

| Decision | Rationale |
|---|---|
| **Median, not mean** | Eight values, and one mainstream outlier should not move the reading. The catalogue itself is summarised by its median (33) everywhere else |
| **Report a percentile of the catalogue, not the raw popularity** | "Popularity 57" means nothing to a reader. "Above 85% of our catalogue" is a comparison they can hold |
| **Four labels, from the percentile** | Enough to be a real reading, few enough that each boundary can be justified. Quartiles, so the boundaries are the catalogue's own shape rather than round numbers someone liked |
| **Skip tracks at popularity 0** | Same reason the notebook aggregates with `max`: zero is missing data. Counting it would hand someone a "garimpeiro" badge earned by our own gaps |
| **The label names the tracks, not the person** | "Suas faixas são mais escondidas que 78% do catálogo" is measured. "Você é um garimpeiro nato" is a horoscope |
| **No label under the minimum, and none on the example profile** | The card already distinguishes a real profile from an example; this follows it instead of inventing a parallel rule |

## 6. Verification

This is done when:

1. `pytest` covers: the median calculation, the exclusion of popularity 0,
   each of the four label boundaries, and the absence of a label when there
   are too few matched tracks or no real login.
2. Run against the real tester's account: the label matches the percentile
   printed beside it, and the sample size shown equals the number of matched
   tracks the card already reports.
3. The example (non-connected) profile shows no label at all.
4. The app is verified running.

## 7. Open questions

- [ ] **The four label names.** Suggested, and the group renames freely since
      every other user-facing name in this project was its call:
      *Garimpeiro de raridade* (bottom quartile) · *Fora do óbvio* ·
      *Um pé no mainstream* · *Fã de hits* (top quartile).
- [ ] **Should the label appear in the Descobrir tab too?** Recommendation:
      no. It is derived from a connected account, and Descobrir has no
      account.
