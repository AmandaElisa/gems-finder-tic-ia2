# combinable search criteria Implementation Plan

**Goal:** Let a listener combine any number of vibes, genres and favourite
artists in a single dig, where genres narrow the search universe and vibes and
artists together form the audio target.

**Architecture:** The pure logic lands first, bottom-up, and the UI last. Every
piece of combination is a separate pure function in `src/recomendacao.py` —
mean of vectors, universe narrowing, active criteria, placeholder precision,
status sentence — so each gets its own failing test before the orchestrator
`montar_resultado()` is rewritten to call them (Tasks 1–5). Only then does the
selection state change shape (Task 6) and the UI stop being a mode picker
(Task 7). That order and not the reverse because the UI is the one layer with
no automated test: it is verified by running the app (Task 8), so everything it
depends on must already be pinned by `pytest` before it moves.

**Tech Stack:** Python 3.12, Streamlit, pandas, numpy, pytest. No new
dependency.

**Spec:** [`./spec.md`](./spec.md)

## Global Constraints

- **Branch:** an isolated worktree at
  `.claude/worktrees/feat+combinable-search-criteria`, on branch
  `worktree-feat+combinable-search-criteria` cut from `origin/main` (005af11).
  The harness named the branch; it is renamed to
  `feat/combinable-search-criteria` when the work is pushed. Never commit on
  `main`.
- **Language:** English for identifiers, docstrings, comments, commit subjects
  and test names. Portuguese for every string a listener reads.
- **Copy comes from the prototype.** Every Portuguese string in this change is
  copied from `docs/gems-finder-prototipo.html`, which already carries this
  design. Do not invent wording; if a string you need is not there, that is a
  spec gap, not licence to write your own.
- **Do NOT touch:** `src/spotify.py`, `src/ui/conta.py`, `src/ui/sidebar.py`,
  `src/tema.py`, `src/ui/mascote.py`, `montar_resultado_conta()` in
  `src/recomendacao.py`, or anything under `notebook/`. The working tree has
  unrelated uncommitted notebook changes — leave them uncommitted and out of
  every commit; stage files by name, never `git add -A`.
- **The Precisão @8 placeholder stays marked as one.** The `TODO` on
  `PRECISAO_8` in `src/dados.py` survives this change and names the new
  formula. Constitution principle 2.
- **Constitution referents must stay true.** `docs/constitution.md` cites the
  `TODO` on `PRECISAO_8` at `src/dados.py:134` and `src/ui/estilo.py`'s line
  count. If either moves, fix the citation in the same commit (Task 8).
- **Commit trailer** on every commit:
  `Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>`
- **Do not push and do not open a PR** until the listener has tested the app
  locally.

Measured on `docs/recommender-methodology-spec` (the branch this plan was
written on, identical in these files to `main`): `pytest` reports **46 passed**;
`src/ui/estilo.py` is **318** lines, `src/recomendacao.py` **168**,
`src/ui/descobrir.py` **164**, `src/dados.py` **210**, `src/ui/estado.py` **46**.

## File Structure

| File | Responsibility |
|---|---|
| `src/dados.py` | Simulated catalogue and product constants. Gains the Precisão @8 placeholder knobs; loses `MODOS`. |
| `src/recomendacao.py` | Match, garimpo, metrics — the tested core. Gains the five combination functions; `montar_resultado()` takes the three criterion lists. |
| `tests/test_recomendacao.py` | Pytest suite for the pure logic. One test class per new function. |
| `src/ui/estado.py` | `st.session_state` defaults. Three selection lists replace mode/vibe/genre. |
| `app.py` | Routing. Only the `iniciar_estado()` call site. |
| `src/ui/descobrir.py` | The Descobrir page. Step 1 becomes three optional groups; the dig button gates on having a criterion. |
| `src/ui/estilo.py` | Stylesheet. Gains the group label; loses the dead segmented-control rules. |
| `docs/gems-finder-prototipo.html` | The approved visual spec. Already updated in the working tree; committed in Task 8. |

---

### Task 1: Mean of vectors, and the search universe

**Files:**
- Modify: `src/recomendacao.py` — add after `centro()` (line 51).
- Test: `tests/test_recomendacao.py` — add two classes after `TestMatch`.

**Interfaces:**
- Consumes: `ATRIBUTOS` from `src.dados`; `media()` and `centro()`, already in
  this module.
- Produces:
  - `media_de_vetores(vetores: Sequence[Mapping[str, float]]) -> dict[str, float]`
  - `universo(catalogo: pd.DataFrame, generos: Sequence[str]) -> pd.DataFrame`

Background: `media()` already averages the attributes of a **DataFrame** of
tracks or artists. What is missing is the average of several loose target
**vectors** (a vibe's target is a plain dict, not a row), which is the
prototype's `media()` applied to an array of objects. `ATRIBUTOS` is the tuple
of the five attribute keys; iterate it rather than the dict's own keys, so a
vector carrying extra keys (a track row carries `popularidade`, `genero`, …)
contributes only its audio attributes. `universo()` narrows the catalogue to
the selected genres, and returns the catalogue untouched when the list is
empty — a listener with no genre selected searches everything.

- [ ] **Step 1: Write the failing test.**

```python
class TestMediaDeVetores:
    def test_averages_each_attribute_independently(self) -> None:
        um = {atributo: .2 for atributo in ATRIBUTOS}
        outro = {**{atributo: .8 for atributo in ATRIBUTOS}, "energia": .6}
        assert media_de_vetores([um, outro]) == pytest.approx(
            {**{atributo: .5 for atributo in ATRIBUTOS}, "energia": .4})

    def test_a_single_vector_is_its_own_mean(self) -> None:
        alvo = {**NEUTRAL, "energia": .9}
        assert media_de_vetores([alvo]) == pytest.approx(alvo)

    def test_ignores_keys_that_are_not_audio_attributes(self) -> None:
        # Track rows carry popularidade, genero and friends; only the five
        # audio attributes may reach the target vector.
        resultado = media_de_vetores([track(popularidade=5), track(popularidade=90)])
        assert set(resultado) == set(ATRIBUTOS)


class TestUniverso:
    def test_no_genre_selected_searches_the_whole_catalogue(self) -> None:
        base = catalog(
            {**track(), "faixa": "A", "genero": "MPB"},
            {**track(), "faixa": "B", "genero": "Punk"},
        )
        assert list(universo(base, [])["faixa"]) == ["A", "B"]

    def test_one_genre_narrows_to_that_genre(self) -> None:
        base = catalog(
            {**track(), "faixa": "A", "genero": "MPB"},
            {**track(), "faixa": "B", "genero": "Punk"},
        )
        assert list(universo(base, ["MPB"])["faixa"]) == ["A"]

    def test_several_genres_keep_every_one_of_them(self) -> None:
        base = catalog(
            {**track(), "faixa": "A", "genero": "MPB"},
            {**track(), "faixa": "B", "genero": "Punk"},
            {**track(), "faixa": "C", "genero": "Techno"},
        )
        assert list(universo(base, ["MPB", "Techno"])["faixa"]) == ["A", "C"]
```

Add `media_de_vetores` and `universo` to the import block at the top of the
test file, and `pytest.approx` needs no import beyond the existing `pytest`.

- [ ] **Step 2: Run it and confirm it fails.**
      `python -m pytest tests/test_recomendacao.py -q`
      Expected: collection fails with
      `ImportError: cannot import name 'media_de_vetores' from 'src.recomendacao'`.

- [ ] **Step 3: Implement.** In `src/recomendacao.py`, extend the typing import
      to `from typing import Any, Mapping, NamedTuple, Sequence` and add after
      `centro()`:

```python
def media_de_vetores(vetores: Sequence[Mapping[str, float]]) -> dict[str, float]:
    """Média elemento a elemento de vários vetores-alvo de atributos de áudio.

    O `media()` acima resume um DataFrame de faixas; este resume vetores soltos
    — o alvo de uma vibe é um dicionário, não uma linha do catálogo.
    """
    return {atributo: sum(float(v[atributo]) for v in vetores) / len(vetores)
            for atributo in ATRIBUTOS}


def universo(catalogo: pd.DataFrame, generos: Sequence[str]) -> pd.DataFrame:
    """Universo de busca: o catálogo todo, ou só as faixas dos gêneros escolhidos."""
    if not generos:
        return catalogo
    return catalogo[catalogo["genero"].isin(list(generos))]
```

- [ ] **Step 4: Run it and confirm it passes.**
      `python -m pytest tests/test_recomendacao.py -q`
      Expected: `52 passed` (46 before, 6 added).

- [ ] **Step 5: Commit.**

```bash
git add src/recomendacao.py tests/test_recomendacao.py
git commit -m "feat(model): average several target vectors and narrow the universe by genre

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: The Precisão @8 placeholder rises with each combined criterion

**Files:**
- Modify: `src/dados.py` — the `TODO` and `PRECISAO_8` block, lines 134–144.
- Modify: `src/recomendacao.py` — add `precisao_combinada()` after `universo()`.
- Test: `tests/test_recomendacao.py` — one class.

**Interfaces:**
- Consumes: `PRECISAO_8` from `src.dados`, reshaped by this task.
- Produces:
  - `PRECISAO_8` with keys `"base"`, `"por_criterio"`, `"bonus_maximo"`, `"conta"`
  - `precisao_combinada(n_criterios: int) -> int`

Background: today `PRECISAO_8` holds one invented number per search mode
(`vibe_foco`, `genero`, `artista`, `conta`). With no modes left, the per-mode
keys die and the public dig computes its number from how many criterion groups
are active, exactly as the prototype does:
`84 + Math.min(7, alvos.length*3)` — so 87 for one group, 90 for two, **91**
for three, because the +7 cap bites before 3×3. Keep the constant *named*
`PRECISAO_8` and keep its `TODO` as the first line of the comment block: both
`app.py`'s AVISOS docstring and `docs/constitution.md` cite that name and that
line. `montar_resultado_conta()` keeps reading `PRECISAO_8["conta"]` and must
not change.

- [ ] **Step 1: Write the failing test.**

```python
class TestPrecisaoCombinada:
    @pytest.mark.parametrize("n_criterios, esperado", [
        (1, 87),
        (2, 90),
        (3, 91),    # the +7 cap bites before 3 * 3 does
    ])
    def test_rises_with_each_combined_criterion(self, n_criterios: int,
                                                esperado: int) -> None:
        assert precisao_combinada(n_criterios) == esperado

    def test_no_criterion_is_the_bare_base(self) -> None:
        # Unreachable from the UI — the dig button is disabled with nothing
        # selected — but the function stays total rather than raising.
        assert precisao_combinada(0) == 84

    def test_the_bonus_never_exceeds_the_cap(self) -> None:
        assert precisao_combinada(99) == precisao_combinada(3)
```

- [ ] **Step 2: Run it and confirm it fails.**
      `python -m pytest tests/test_recomendacao.py -q`
      Expected: `ImportError: cannot import name 'precisao_combinada' from 'src.recomendacao'`.

- [ ] **Step 3: Implement.** Replace lines 134–144 of `src/dados.py` — keeping
      the `TODO` on the first line — with:

```python
# TODO: trocar pelos números reais da avaliação offline do modelo.
# Por enquanto são PLACEHOLDERS herdados do protótipo aprovado. No garimpo
# público a Precisão @8 é `base` + `por_criterio` pontos por critério combinado
# no passo 1, com teto de `bonus_maximo` — 87 com um critério, 90 com dois, 91
# com três. Nenhum desses números foi medido.
PRECISAO_8: dict[str, int] = {
    "base": 84,
    "por_criterio": 3,
    "bonus_maximo": 7,
    "conta": 88,
}
```

Then in `src/recomendacao.py`, after `universo()`:

```python
def precisao_combinada(n_criterios: int) -> int:
    """Precisão @8 PLACEHOLDER: sobe com cada critério combinado no passo 1.

    Não é medida — ver o TODO em `src/dados.py::PRECISAO_8`.
    """
    return PRECISAO_8["base"] + min(PRECISAO_8["bonus_maximo"],
                                    n_criterios * PRECISAO_8["por_criterio"])
```

- [ ] **Step 4: Run it and confirm it passes.**
      `python -m pytest tests/test_recomendacao.py -q`
      Expected: `56 passed`. It will instead error with
      `KeyError: 'vibe_foco'` if `montar_resultado()` was left reading the old
      keys — that is Task 5's job, so at this point run
      `python -m pytest tests/test_recomendacao.py -q -k "not Resultado"` if the
      suite has already grown a `montar_resultado` test.

- [ ] **Step 5: Commit.**

```bash
git add src/dados.py src/recomendacao.py tests/test_recomendacao.py
git commit -m "feat(model): raise the placeholder Precisao @8 per combined criterion

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: One criterion per active group

**Files:**
- Modify: `src/recomendacao.py` — add `Criterio` and `criterios_ativos()` after
  `precisao_combinada()`.
- Test: `tests/test_recomendacao.py` — one class.

**Interfaces:**
- Consumes: `media_de_vetores()`, `media()`, `centro()` (Task 1 and existing);
  `VIBES` from `src.dados`.
- Produces:
  - `class Criterio(NamedTuple)` with fields `alvo: dict[str, float]`,
    `titulo: str`, `ctx: str`
  - `criterios_ativos(catalogo, artistas, vibes, generos, favoritos) -> list[Criterio]`

Background: each of the three groups collapses to **one** `Criterio` however
many chips it holds — two vibes average into a single vibe target, so the final
target is halfway between "the vibes" and "the artist", not two-thirds vibe.
The order is the order the UI shows the groups: vibe, genre, artist. `titulo`
and `ctx` are Portuguese fragments copied from the prototype's `render()`:
titles join with `" + "` (artists too), `ctx` reads `bate com a vibe X + Y`,
`representa o som de G1 + G2`, and `chega perto de A e B` (artists joined with
`" e "` here, deliberately unlike the title). `centro()` averages a genre over
the **whole** catalogue, not the narrowed universe — same as the prototype.

- [ ] **Step 1: Write the failing test.**

```python
class TestCriteriosAtivos:
    ARTISTAS = catalog(
        {**track(), "artista": "Dora Lima", "genero": "MPB", "energia": .42},
        {**track(), "artista": "MC Vitrine", "genero": "Funk BR", "energia": .90},
    )
    CATALOGO = catalog(
        {**track(popularidade=8), "faixa": "A", "genero": "MPB", "energia": .3},
        {**track(popularidade=15), "faixa": "B", "genero": "MPB", "energia": .5},
        {**track(popularidade=9), "faixa": "C", "genero": "Punk", "energia": .9},
    )

    def test_nothing_selected_gives_no_criteria(self) -> None:
        assert criterios_ativos(self.CATALOGO, self.ARTISTAS, [], [], []) == []

    def test_one_group_per_selection_kind_in_ui_order(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS,
                                  ["chill"], ["MPB"], ["Dora Lima"])
        assert [c.titulo for c in ativos] == ["Chill", "MPB", "parecido com Dora Lima"]

    def test_several_vibes_collapse_into_one_averaged_criterion(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS,
                                  ["chill", "treino"], [], [])
        assert len(ativos) == 1
        assert ativos[0].titulo == "Chill + Treino"
        # Chill's energia is .35 and Treino's is .92.
        assert ativos[0].alvo["energia"] == pytest.approx(.635)

    def test_a_genre_criterion_is_that_genre_average_over_the_whole_catalogue(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS, [], ["MPB"], [])
        assert ativos[0].alvo["energia"] == pytest.approx(.4)   # (.3 + .5) / 2
        assert ativos[0].ctx == "representa o som de MPB"

    def test_several_genres_average_their_centroids_not_their_tracks(self) -> None:
        # MPB averages .3 and .5 to .4; Punk is a single .9 track. The mean of
        # the two centroids is .65 — a per-track mean would give .5667.
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS, [], ["MPB", "Punk"], [])
        assert ativos[0].alvo["energia"] == pytest.approx(.65)
        assert ativos[0].titulo == "MPB + Punk"

    def test_artists_join_with_plus_in_the_title_and_with_e_in_the_context(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS, [], [],
                                  ["Dora Lima", "MC Vitrine"])
        assert ativos[0].titulo == "parecido com Dora Lima + MC Vitrine"
        assert ativos[0].ctx == "chega perto de Dora Lima e MC Vitrine"
        assert ativos[0].alvo["energia"] == pytest.approx(.66)  # (.42 + .90) / 2

    def test_the_vibe_context_names_every_selected_vibe(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS, ["chill", "foco"], [], [])
        assert ativos[0].ctx == "bate com a vibe Chill + Foco"
```

- [ ] **Step 2: Run it and confirm it fails.**
      `python -m pytest tests/test_recomendacao.py -q`
      Expected: `ImportError: cannot import name 'criterios_ativos' from 'src.recomendacao'`.

- [ ] **Step 3: Implement.** In `src/recomendacao.py`:

```python
class Criterio(NamedTuple):
    """Um critério ativo do passo 1: seu vetor-alvo e como ele se descreve."""

    alvo: dict[str, float]
    titulo: str
    ctx: str


def criterios_ativos(catalogo: pd.DataFrame, artistas: pd.DataFrame,
                     vibes: Sequence[str], generos: Sequence[str],
                     favoritos: Sequence[str]) -> list[Criterio]:
    """Um Criterio por grupo escolhido no passo 1, na ordem em que a UI os mostra.

    Cada grupo vira UM critério, quantas fichas tenha: duas vibes viram um só
    alvo médio, então o alvo final fica no meio entre "as vibes" e "o artista",
    não a dois terços da vibe.
    """
    ativos: list[Criterio] = []
    if vibes:
        nomes = " + ".join(VIBES[vibe]["nome"] for vibe in vibes)
        ativos.append(Criterio(
            media_de_vetores([VIBES[vibe]["alvo"] for vibe in vibes]),
            nomes, f"bate com a vibe {nomes}"))
    if generos:
        nomes = " + ".join(generos)
        ativos.append(Criterio(
            media_de_vetores([centro(catalogo, genero) for genero in generos]),
            nomes, f"representa o som de {nomes}"))
    if favoritos:
        escolhidos = artistas[artistas["artista"].isin(list(favoritos))]
        ativos.append(Criterio(
            media(escolhidos),
            "parecido com " + " + ".join(favoritos),
            "chega perto de " + " e ".join(favoritos)))
    return ativos
```

- [ ] **Step 4: Run it and confirm it passes.**
      `python -m pytest tests/test_recomendacao.py -q`
      Expected: `64 passed`.

- [ ] **Step 5: Commit.**

```bash
git add src/recomendacao.py tests/test_recomendacao.py
git commit -m "feat(model): build one target criterion per active step-1 group

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: The status sentence lists every active criterion

**Files:**
- Modify: `src/recomendacao.py` — add `texto_status()` after `criterios_ativos()`.
- Test: `tests/test_recomendacao.py` — one class.

**Interfaces:**
- Consumes: `VIBES` from `src.dados`.
- Produces: `texto_status(vibes, generos, favoritos, teto: int) -> str` —
  returns an HTML fragment (with `<b>` tags), without the wrapping `<p>`.

Background: this replaces `_texto_alvo()` in `src/ui/descobrir.py`, which named
the single active mode. It lives in `src/recomendacao.py` and not in the UI
because the spec requires its wording to be covered by `pytest`, and this
module already produces Portuguese copy (`titulo`, `ctx`, `legenda`). Copy the
prototype's `status()` exactly: parts joined with `", "`, vibes and genres
joined internally with `" + "`, artists with `", "`, and the fallback
`<b>escolha ao menos um critério acima</b>` when nothing is selected. The
sentence is `Buscando por …, com popularidade até <b>N</b>.` — note this is the
prototype's wording, which puts the ceiling last; earlier drafts of the request
phrased it `até 18 de popularidade`, and the prototype wins (constitution
principle 3).

- [ ] **Step 1: Write the failing test.**

```python
class TestTextoStatus:
    def test_lists_all_three_groups_in_ui_order(self) -> None:
        assert texto_status(["chill"], ["MPB"], ["Dora Lima"], 18) == (
            "Buscando por vibe <b>Chill</b>, gênero <b>MPB</b>, "
            "parecido com <b>Dora Lima</b>, com popularidade até <b>18</b>.")

    def test_joins_several_vibes_and_genres_with_plus(self) -> None:
        assert texto_status(["chill", "treino"], ["MPB", "Samba"], [], 7) == (
            "Buscando por vibe <b>Chill + Treino</b>, gênero <b>MPB + Samba</b>, "
            "com popularidade até <b>7</b>.")

    def test_joins_several_artists_with_commas(self) -> None:
        assert texto_status([], [], ["Dora Lima", "Nêga Sol"], 30) == (
            "Buscando por parecido com <b>Dora Lima, Nêga Sol</b>, "
            "com popularidade até <b>30</b>.")

    def test_nothing_selected_asks_for_a_criterion(self) -> None:
        assert texto_status([], [], [], 18) == (
            "Buscando por <b>escolha ao menos um critério acima</b>, "
            "com popularidade até <b>18</b>.")

    @pytest.mark.parametrize("vibes, generos, favoritos, esperado", [
        (["foco"], [], [], "vibe <b>Foco</b>"),
        ([], ["Punk"], [], "gênero <b>Punk</b>"),
        ([], [], ["MC Vitrine"], "parecido com <b>MC Vitrine</b>"),
    ])
    def test_a_single_group_names_only_itself(self, vibes: list[str],
                                              generos: list[str],
                                              favoritos: list[str],
                                              esperado: str) -> None:
        assert texto_status(vibes, generos, favoritos, 18) == (
            f"Buscando por {esperado}, com popularidade até <b>18</b>.")
```

- [ ] **Step 2: Run it and confirm it fails.**
      `python -m pytest tests/test_recomendacao.py -q`
      Expected: `ImportError: cannot import name 'texto_status' from 'src.recomendacao'`.

- [ ] **Step 3: Implement.**

```python
def texto_status(vibes: Sequence[str], generos: Sequence[str],
                 favoritos: Sequence[str], teto: int) -> str:
    """Frase do passo 3: lista os critérios ativos e o teto de popularidade."""
    partes = []
    if vibes:
        partes.append("vibe <b>" + " + ".join(VIBES[v]["nome"] for v in vibes) + "</b>")
    if generos:
        partes.append("gênero <b>" + " + ".join(generos) + "</b>")
    if favoritos:
        partes.append("parecido com <b>" + ", ".join(favoritos) + "</b>")
    descricao = ", ".join(partes) or "<b>escolha ao menos um critério acima</b>"
    return f"Buscando por {descricao}, com popularidade até <b>{teto}</b>."
```

- [ ] **Step 4: Run it and confirm it passes.**
      `python -m pytest tests/test_recomendacao.py -q`
      Expected: `71 passed`.

- [ ] **Step 5: Commit.**

```bash
git add src/recomendacao.py tests/test_recomendacao.py
git commit -m "feat(model): status sentence listing every active criterion

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: `montar_resultado()` takes the three criterion lists

**Files:**
- Modify: `src/recomendacao.py` — replace `montar_resultado()`, lines 118–152.
- Test: `tests/test_recomendacao.py` — one class.

**Interfaces:**
- Consumes: `universo()`, `criterios_ativos()`, `media_de_vetores()`,
  `precisao_combinada()` (Tasks 1–3); `garimpar()`, `cobertura()`, `round_js()`
  (existing); `LIMA` from `src.tema`; `VIBES` from `src.dados`.
- Produces:
  `montar_resultado(catalogo, artistas, vibes, generos, favoritos, teto) -> dict[str, Any]`
  with the same keys it returns today — `titulo`, `ctx`, `precisao`,
  `cobertura`, `faixas`, `media_match`, `legenda`, `sub_match`,
  `sub_cobertura`, `cor` — so `src/ui/resultados.py` needs no change.

Background: the old signature was
`(catalogo, artistas, modo, vibe, genero, favoritos, teto)` and branched on
`modo`. The `modo`, `vibe` and `genero` scalars are gone; three lists replace
them. `titulo` becomes `Joias — ` + the criterion titles joined with `" · "`,
and `ctx` the criterion contexts joined with `" e "`, both from the prototype.
`cor` tints the results heading's mascot: keep the vibe's colour when exactly
one vibe is selected, otherwise the prototype's lime — with several vibes there
is no single source for the tint. Calling it with nothing selected is a
programming error, not a listener error: the UI disables the dig button, so
raise rather than divide by zero inside `media_de_vetores()`. That message is
engineering, so it is English. Leave `montar_resultado_conta()` alone.

- [ ] **Step 1: Write the failing test.**

```python
class TestMontarResultado:
    CATALOGO = catalog(
        {**track(popularidade=8), "faixa": "MPB baixa", "genero": "MPB",
         "energia": .34, "bpm": 96, "artista": "Beira de Rio",
         "cidade": "Paraty", "ano": 2022},
        {**track(popularidade=15), "faixa": "MPB média", "genero": "MPB",
         "energia": .38, "bpm": 100, "artista": "Lume",
         "cidade": "Florianópolis", "ano": 2023},
        {**track(popularidade=9), "faixa": "Punk", "genero": "Punk",
         "energia": .95, "bpm": 152, "artista": "Britadeira Social",
         "cidade": "São Paulo", "ano": 2023},
    )
    ARTISTAS = catalog(
        {**track(), "artista": "Dora Lima", "genero": "MPB", "energia": .42},
    )

    def montar(self, vibes: list[str], generos: list[str],
               favoritos: list[str], teto: int = 18) -> dict:
        return montar_resultado(self.CATALOGO, self.ARTISTAS, vibes, generos,
                                favoritos, teto)

    def test_a_genre_narrows_the_universe(self) -> None:
        resultado = self.montar([], ["MPB"], [])
        assert {f["genero"] for f in resultado["faixas"]} == {"MPB"}

    def test_no_genre_searches_every_genre(self) -> None:
        resultado = self.montar(["treino"], [], [])
        assert {f["genero"] for f in resultado["faixas"]} == {"MPB", "Punk"}

    def test_the_title_lists_every_active_criterion(self) -> None:
        assert self.montar(["chill"], ["MPB"], ["Dora Lima"])["titulo"] == (
            "Joias — Chill · MPB · parecido com Dora Lima")

    def test_the_context_joins_the_criteria_with_e(self) -> None:
        assert self.montar(["chill"], ["MPB"], [])["ctx"] == (
            "bate com a vibe Chill e representa o som de MPB")

    def test_precision_follows_the_number_of_active_groups(self) -> None:
        assert self.montar(["chill"], [], [])["precisao"] == 87
        assert self.montar(["chill"], ["MPB"], [])["precisao"] == 90
        assert self.montar(["chill"], ["MPB"], ["Dora Lima"])["precisao"] == 91

    def test_coverage_is_measured_against_the_narrowed_universe(self) -> None:
        # Inside MPB, both tracks are at or below 15, so a ceiling of 15 keeps
        # everything — even though one of the three catalogue tracks is out.
        assert self.montar([], ["MPB"], [], teto=15)["cobertura"] == 100

    def test_one_vibe_tints_the_heading_with_its_colour(self) -> None:
        assert self.montar(["chill"], [], [])["cor"] == VIBES["chill"]["cor"]

    def test_several_vibes_fall_back_to_lime(self) -> None:
        assert self.montar(["chill", "treino"], [], [])["cor"] == LIMA

    def test_no_vibe_falls_back_to_lime(self) -> None:
        assert self.montar([], ["MPB"], [])["cor"] == LIMA

    def test_nothing_selected_is_a_programming_error(self) -> None:
        with pytest.raises(ValueError, match="at least one active criterion"):
            self.montar([], [], [])

    def test_an_empty_result_still_reports_zero_average_match(self) -> None:
        assert self.montar(["chill"], [], [], teto=1)["faixas"] == []
        assert self.montar(["chill"], [], [], teto=1)["media_match"] == 0
```

Add `VIBES` and `montar_resultado` to the imports at the top of the test file
(`LIMA` is already imported).

- [ ] **Step 2: Run it and confirm it fails.**
      `python -m pytest tests/test_recomendacao.py -q -k MontarResultado`
      Expected: `TypeError: montar_resultado() takes 7 positional arguments but ...`
      / `ImportError` for `montar_resultado` if it is not yet in the import block.

- [ ] **Step 3: Implement.** Replace `montar_resultado()` with:

```python
def montar_resultado(catalogo: pd.DataFrame, artistas: pd.DataFrame,
                     vibes: Sequence[str], generos: Sequence[str],
                     favoritos: Sequence[str], teto: int) -> dict[str, Any]:
    """Garimpa com os critérios combinados do passo 1 e devolve o que a UI exibe.

    Gênero(s) filtram o universo de busca; vibe(s), gênero(s) e artista(s)
    formam o alvo, um vetor por grupo escolhido.
    """
    base = universo(catalogo, generos)
    criterios = criterios_ativos(catalogo, artistas, vibes, generos, favoritos)
    if not criterios:
        raise ValueError("montar_resultado needs at least one active criterion")

    alvo = media_de_vetores([criterio.alvo for criterio in criterios])
    achadas = garimpar(base, alvo, teto)
    return {
        "titulo": "Joias — " + " · ".join(c.titulo for c in criterios),
        "ctx": " e ".join(c.ctx for c in criterios),
        "precisao": precisao_combinada(len(criterios)),
        "cobertura": cobertura(base, teto),
        "faixas": achadas.to_dict("records"),
        "media_match": round_js(achadas["match"].mean()) if len(achadas) else 0,
        "legenda": "Clique em cada faixa pra ver os atributos de áudio.",
        "sub_match": "afinidade com o alvo escolhido",
        "sub_cobertura": "do catálogo elegível cabe neste filtro",
        # com várias vibes não há uma cor só; o protótipo usa lima no cabeçalho
        "cor": VIBES[vibes[0]]["cor"] if len(vibes) == 1 else LIMA,
    }
```

- [ ] **Step 4: Run it and confirm it passes.**
      `python -m pytest -q`
      Expected: `83 passed`.

- [ ] **Step 5: Commit.**

```bash
git add src/recomendacao.py tests/test_recomendacao.py
git commit -m "feat(model): combine step-1 criteria into a single averaged target

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Three selection lists replace mode, vibe and genre

**Files:**
- Modify: `src/ui/estado.py` — `PADROES` (lines 11–29) and `iniciar_estado()`
  (lines 32–37).
- Modify: `src/dados.py` — delete `MODOS` (line 178).
- Modify: `app.py` — the `iniciar_estado(generos)` call (line 42).

**Interfaces:**
- Consumes: nothing new.
- Produces: `iniciar_estado() -> None` — no longer takes the genre list;
  session keys `vibes: list[str]`, `generos: list[str]`, `favoritos: list[str]`
  replace `modo`, `vibe`, `genero`, `favoritos`.

Background: `iniciar_estado(generos)` existed only to default `genero` to the
first genre in the catalogue. Nothing is selected on first load now, so the
parameter goes with it — leave `generos = listar_generos(catalogo)` in `app.py`
alone, `pagina_descobrir()` still needs it. `PADROES` copies list values on
setdefault already (`valor.copy() if isinstance(valor, list)`), which the two
new lists rely on: without the copy every session would share one list object.
`MODOS` has exactly two readers, `src/ui/estado.py` and `src/ui/descobrir.py`,
and both stop needing it — Task 7 removes the second.

There is no test for this task: it is `st.session_state` wiring, verified by
running the app in Task 8. Confirm instead that nothing still references the
dead names.

- [ ] **Step 1: Write the failing check** — grep is the test here:
      `grep -rn "MODOS\|session_state.modo\|session_state.vibe\b\|session_state.genero\b" --include=*.py app.py src tests`
      Expected before the change: hits in `src/dados.py`, `src/ui/estado.py`
      and `src/ui/descobrir.py`.

- [ ] **Step 2: Confirm the app is broken by the earlier tasks** —
      `python -c "import src.ui.descobrir"` still imports fine, but
      `montar_resultado` now has the new signature while `descobrir.py` calls
      the old one. Task 7 closes that; do not run the app between Tasks 6 and 7.

- [ ] **Step 3: Implement.** In `src/ui/estado.py`, drop the
      `from src.dados import MODOS` line and change the first entries of
      `PADROES` to:

```python
PADROES: dict[str, Any] = {
    "vibes": [],
    "generos": [],
    "favoritos": [],
    "teto": 18,
```

and reduce `iniciar_estado()` to:

```python
def iniciar_estado() -> None:
    """Garante as chaves do session_state na primeira execução."""
    for chave, valor in PADROES.items():
        st.session_state.setdefault(chave, valor.copy() if isinstance(valor, list) else valor)
```

In `src/dados.py`, delete the `MODOS` line, keeping `PAGINAS`. In `app.py`,
change the call to `iniciar_estado()`.

- [ ] **Step 4: Run it and confirm it passes.**
      `python -m pytest -q` → `83 passed` (unchanged; no test touches state).
      `grep -rn "MODOS" --include=*.py app.py src tests` → no output.

- [ ] **Step 5: Commit.**

```bash
git add app.py src/dados.py src/ui/estado.py
git commit -m "refactor(ui): replace the search mode with three selection lists

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Step 1 becomes three optional, combinable groups

**Files:**
- Modify: `src/ui/descobrir.py` — delete `seletor_modo()` (lines 18–26) and
  `_texto_alvo()` (lines 86–95); rewrite `_selecao_vibe()`, `_selecao_genero()`,
  the Step 1 card and the Step 3 card.
- Modify: `src/ui/estilo.py` — add `.gf-grupo`; delete the dead
  segmented-control rules at lines 229–246, 284–301 and 302–315.

**Interfaces:**
- Consumes: `texto_status()` and `montar_resultado()` from `src.recomendacao`
  (Tasks 4–5); session keys `vibes`, `generos`, `favoritos` (Task 6);
  `bloco()`, `container_com_chave()`, `cartao()`, `passo()` from
  `src.ui.componentes`.
- Produces: nothing другие modules consume.

Background copy, all from the prototype:

- Step 1 help: `Combine quantos critérios quiser: <b>vibe</b>, <b>gênero</b> e
  <b>artistas que você já ama</b>. Quanto mais você escolher, mais fino fica o
  garimpo.`
- Group labels: `Vibe` / `opcional`; `Gênero` / `opcional`;
  `Artista favorito` / `opcional · até 3`.
- Artist counter with nothing chosen: `Nenhum artista escolhido ainda.`
- Empty-state hint: `Aumenta a popularidade máxima no passo 2 ou ajusta os
  critérios do passo 1.`

The vibe cards keep their trick — an invisible `st.button` stretched over the
card by the `st-key-vibecard-*` CSS — and only the selected test changes from
`==` to `in`. The genre chips lose their "always one selected" fallback. The
`.gf-grupo` class mirrors the prototype's `.grupo-lbl`; the display font needs
`!important` to beat Streamlit's own markdown styles, the pattern already used
by `.gf-vibe strong` at line 104. The segmented-control CSS is dead once
`seletor_modo()` is gone: `[data-testid="stButtonGroup"]` has no other user in
this repo (`st.radio` in the sidebar renders `[role="radiogroup"]` instead).
Inside the deleted 640px media block, keep the one rule that is not about the
button group: `.gf-metrics{grid-template-columns:1fr;}`.

No automated test: this is Streamlit UI, verified by running the app (Task 8).

- [ ] **Step 1: Write the failing test** — none. Per `CLAUDE.md`, Streamlit UI
      is verified by running the app, not by mocking widgets. The behaviour this
      task exposes is already pinned by Tasks 1–5.

- [ ] **Step 2: Confirm it is broken** — `streamlit run app.py`, open Descobrir.
      Expected: `TypeError` from `montar_resultado()` being called with the old
      seven arguments, or an `AttributeError` on `st.session_state.modo`.

- [ ] **Step 3: Implement.** In `src/ui/descobrir.py`, the imports become:

```python
from src.dados import VIBES
from src.recomendacao import montar_resultado, rotulo_profundidade, texto_status
```

Delete `seletor_modo()` and `_texto_alvo()`, and add the toggle helper plus the
group label:

```python
def _alternar(selecionados: list[str], valor: str) -> None:
    """Liga ou desliga um item na lista de selecionados do passo 1."""
    if valor in selecionados:
        selecionados.remove(valor)
    else:
        selecionados.append(valor)


def _grupo(titulo: str, nota: str) -> None:
    """Rótulo de um dos três grupos opcionais do passo 1."""
    bloco(f'<p class="gf-grupo">{titulo} <span>{nota}</span></p>')
```

`_selecao_vibe()` and `_selecao_genero()` become multi-select:

```python
def _selecao_vibe() -> None:
    """Os 4 cards de vibe, um por coluna — o card inteiro é clicável, e alterna."""
    for coluna, (chave, vibe) in zip(st.columns(4), VIBES.items()):
        with coluna:
            escolhida = chave in st.session_state.vibes
            classe = "gf-vibe on" if escolhida else "gf-vibe"
            fundo = vibe["cor"] if escolhida else "#fff"
            with container_com_chave(f"vibecard-{chave}"):
                bloco(f'<div class="{classe}" style="background:{fundo}">'
                      f'{mascote(vibe["cor"], vibe["humor"], 56)}<strong>{vibe["nome"]}</strong>'
                      f'<span>{vibe["desc"]}</span></div>')
                # botão invisível cobrindo o card (o rótulo fica pro leitor de tela)
                if st.button(vibe["nome"], key=f"btn_vibe_{chave}"):
                    _alternar(st.session_state.vibes, chave)
                    st.rerun()


def _selecao_genero(catalogo: pd.DataFrame, generos: list[str]) -> None:
    """Chips com os 12 gêneros e a contagem de faixas — os escolhidos ficam em lima."""
    contagem = catalogo["genero"].value_counts()
    with container_com_chave("chips-generos"):
        for genero in generos:
            escolhido = genero in st.session_state.generos
            if st.button(f"{genero} :gray[{contagem[genero]} faixas]",
                         key=f"chip_gen_{genero}",
                         type="primary" if escolhido else "secondary"):
                _alternar(st.session_state.generos, genero)
                st.rerun()
```

In `_selecao_artista()`, change only the empty-selection caption to
`st.caption("Nenhum artista escolhido ainda.")`.

The Step 1 card becomes:

```python
    with cartao("passo1"):
        passo("PASSO 1", "De onde a gente parte?",
              "Combine quantos critérios quiser: <b>vibe</b>, <b>gênero</b> e "
              "<b>artistas que você já ama</b>. Quanto mais você escolher, mais "
              "fino fica o garimpo.")
        _grupo("Vibe", "opcional")
        _selecao_vibe()
        _grupo("Gênero", "opcional")
        _selecao_genero(catalogo, generos)
        _grupo("Artista favorito", "opcional · até 3")
        _selecao_artista(artistas)
```

and the Step 3 card:

```python
    with cartao("passo3"):
        passo("PASSO 3", "Garimpe!",
              "O modelo compara os atributos de áudio de cada faixa com o seu alvo "
              "e ranqueia por afinidade.")
        vibes, generos_sel = st.session_state.vibes, st.session_state.generos
        favoritos = st.session_state.favoritos
        tem_criterio = bool(vibes or generos_sel or favoritos)
        bloco(f'<p class="gf-status">'
              f'{texto_status(vibes, generos_sel, favoritos, teto)}</p>')
        if st.button("Garimpar joias", type="primary", key="btn_garimpar",
                     disabled=not tem_criterio):
            with st.spinner("Garimpando…"):
                time.sleep(1.15)
            st.session_state.res_desc = montar_resultado(
                catalogo, artistas, vibes, generos_sel, favoritos, teto)
            st.session_state.pl_desc = None
            achadas = len(st.session_state.res_desc["faixas"])
            if achadas:
                st.toast(f"{achadas} joias encontradas!", icon="💎")
```

The status line carries the warning when nothing is selected — the button is
disabled, so the old post-click `st.warning` goes away with it. Finally, update
the empty-state hint in the `mostrar_resultados()` call at the bottom of
`pagina_descobrir()` to `"Aumenta a popularidade máxima no passo 2 ou ajusta os
critérios do passo 1."`.

In `src/ui/estilo.py`, add beside `.gf-status` (after line 99):

```css
.gf-grupo{font-family:var(--d) !important;font-size:14.5px;font-weight:600;
  margin:20px 0 10px;display:flex;align-items:baseline;gap:8px;}
.gf-grupo span{font-family:var(--f) !important;font-size:11.5px;font-weight:600;
  color:var(--mute);}
```

then delete the segmented-control rules (the comment at line 229 through line
246), and both media-query blocks that target `[data-testid="stButtonGroup"]`
— keeping `.gf-metrics{grid-template-columns:1fr;}` inside a plain
`@media (max-width:640px)` block.

- [ ] **Step 4: Run it and confirm it passes.**
      `python -m pytest -q` → `83 passed`.
      `streamlit run app.py` → Step 1 shows the three labelled groups, the dig
      button is disabled with nothing selected. Full walkthrough is Task 8.
      `wc -l src/ui/estilo.py` → expect about 277, back under the ~300 ceiling.

- [ ] **Step 5: Commit.**

```bash
git add src/ui/descobrir.py src/ui/estilo.py
git commit -m "feat(ui): combinable vibe, genre and artist blocks in step 1

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Verify in the running app, then commit the prototype

**Files:**
- Modify: `docs/constitution.md` — only if a referent moved.
- Commit: `docs/gems-finder-prototipo.html` (already changed in the working
  tree), `docs/specs/2026-09-01-combinable-search-criteria/`.

**Interfaces:**
- Consumes: everything above.
- Produces: nothing.

Background: the prototype was updated before the code and is the reason this
job exists, so it ships in the same branch. The constitution cites the `TODO`
on `PRECISAO_8` at `src/dados.py:134` and `src/ui/estilo.py`'s line count;
Task 2 rewrote that comment block and Task 7 shrank the stylesheet, so both
citations need checking. A wrong citation makes the file worthless.

- [ ] **Step 1: Write the failing test** — none. This task is the spec's §6
      verification list, run by hand against the app.

- [ ] **Step 2: Check the referents.**
      `grep -n "TODO" src/dados.py` → confirm the `TODO` line number, and fix
      `docs/constitution.md` if it is no longer 134.
      `wc -l src/ui/estilo.py` → if it is no longer the number the constitution
      quotes, update that sentence to the measured value and name this branch.

- [ ] **Step 3: Walk the app.** `streamlit run app.py`, then confirm every
      numbered check in §6 of the spec — in particular: nothing selected on
      first load with the dig button disabled; clicking a vibe twice clears it;
      two genres return tracks from both; vibe Chill + genre MPB + artist Dora
      Lima at ceiling 18 gives the status line
      `Buscando por vibe Chill, gênero MPB, parecido com Dora Lima, com
      popularidade até 18.` and a Precisão @8 of 91; a narrow genre at a low
      ceiling shows the empty state.

- [ ] **Step 4: Run the suite one last time.**
      `python -m pytest -q` → `83 passed`.

- [ ] **Step 5: Commit.**

```bash
git add docs/gems-finder-prototipo.html docs/specs/2026-09-01-combinable-search-criteria
git commit -m "docs(specs): record the combinable step-1 criteria and update the prototype

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>"
```

(If Step 2 changed `docs/constitution.md`, add it to that commit.)

---

## Spec coverage check

| Spec requirement | Task |
|---|---|
| Three optional, always-visible groups | 7 |
| Vibe and genre accept multiple selections | 7 |
| Genres narrow the universe | 1 (`universo`), 5 |
| Vibes and artists only form the target | 3, 5 |
| Target is the mean of one vector per group | 1, 3, 5 |
| Status line lists everything active | 4, 7 |
| Dig button disabled with a visible reason | 4, 7 |
| Precisão @8 rises per criterion, still a placeholder | 2 |
| Result heading and "why" list every criterion | 3, 5 |
| The mode concept is deleted | 6, 7 |
| Heading tint falls back to lime | 5 |
| Nothing selected on first load | 6 |
| Portuguese copy comes from the prototype | 7, 8 |
| §6 verification list | 8 |
| Constitution referents stay true | 8 |
