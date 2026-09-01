"""Tests for src/recomendacao.py — the logic that decides which gem a user sees.

Only pure functions are covered. The Streamlit UI is verified by running the
app (see CLAUDE.md), not by mocking widgets. Fixtures build small DataFrames by
hand rather than calling carregar_catalogo(), which is @st.cache_data-wrapped
and expects a script context.

Assertions compare against Portuguese strings on purpose: those are UI copy,
and UI copy stays Portuguese.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.dados import ATRIBUTOS
from src.recomendacao import (
    cobertura,
    criterios_ativos,
    email_valido,
    garimpar,
    humor_da_faixa,
    match,
    media_de_vetores,
    nome_do_email,
    precisao_combinada,
    rar,
    rotulo_profundidade,
    round_js,
    texto_status,
    universo,
)
from src.tema import LIMA, PERI, ROSA

# The five audio attributes at dead centre, so a test can move one at a time.
NEUTRAL: dict[str, float] = {atributo: .5 for atributo in ATRIBUTOS}


def track(popularidade: int = 30, **atributos: float) -> dict[str, float]:
    """A track with neutral audio attributes, overridable one by one.

    Popularity defaults to 30, the value at which match()'s obscurity bonus is
    exactly zero — so a test that does not care about popularity gets no bonus
    silently skewing its expected score.
    """
    return {**NEUTRAL, **atributos, "popularidade": popularidade}


def catalog(*linhas: dict) -> pd.DataFrame:
    """A catalogue DataFrame from hand-written rows, in the given order."""
    return pd.DataFrame(list(linhas))


class TestRoundJs:
    @pytest.mark.parametrize("valor, esperado", [
        (2.4, 2),
        (2.5, 3),      # half rounds up, not to even
        (-2.5, -2),    # ...which for negatives means toward zero
        (-2.6, -3),
        (0.0, 0),
    ])
    def test_matches_javascript_math_round(self, valor: float, esperado: int) -> None:
        assert round_js(valor) == esperado


class TestMatch:
    def test_clamps_at_99_for_a_perfect_fit(self) -> None:
        # Identical attributes and popularity 30 give a raw score of 100.
        assert match(track(), NEUTRAL) == 99

    def test_clamps_at_31_for_the_worst_possible_fit(self) -> None:
        # Every attribute maximally far: distance 1.0, raw score -35.
        longe = {atributo: 1.0 for atributo in ATRIBUTOS}
        alvo = {atributo: 0.0 for atributo in ATRIBUTOS}
        assert match({**longe, "popularidade": 30}, alvo) == 31

    def test_lower_popularity_earns_the_obscurity_bonus(self) -> None:
        # 0.2 away on the 0.25-weight axis: distance 0.05, raw score 93.25
        # before the bonus, plus (30 - popularidade) * 0.15.
        alvo = {**NEUTRAL, "energia": .7}
        assert match(track(popularidade=30), alvo) == 93
        assert match(track(popularidade=10), alvo) == 96


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


class TestRar:
    @pytest.mark.parametrize("popularidade, selo, cor", [
        (0, "Joia bruta", LIMA),
        (8, "Joia bruta", LIMA),        # boundary: <= 8 is still raw
        (9, "Rara", ROSA),
        (17, "Rara", ROSA),             # boundary: <= 17 is still rare
        (18, "Pouco ouvida", PERI),
    ])
    def test_boundaries(self, popularidade: int, selo: str, cor: str) -> None:
        assert rar(popularidade) == (selo, cor)


class TestRotuloProfundidade:
    @pytest.mark.parametrize("teto, esperado", [
        (5, "Praticamente invisível"),
        (10, "Praticamente invisível"),  # boundary
        (11, "Bem underground"),
        (20, "Bem underground"),         # boundary
        (21, "Conhecida em nicho"),
        (30, "Conhecida em nicho"),      # boundary
        (31, "Começando a aparecer"),
    ])
    def test_boundaries(self, teto: int, esperado: str) -> None:
        assert rotulo_profundidade(teto) == esperado


class TestHumorDaFaixa:
    def test_sadness_wins_over_high_energy(self) -> None:
        assert humor_da_faixa(track(valencia=.2, energia=.9)) == "triste"

    def test_high_energy_wins_over_instrumental(self) -> None:
        assert humor_da_faixa(track(energia=.8, instrumentalidade=.9)) == "treino"

    def test_instrumental_when_calm(self) -> None:
        assert humor_da_faixa(track(instrumentalidade=.8)) == "foco"

    def test_chill_is_the_default(self) -> None:
        assert humor_da_faixa(track()) == "chill"

    def test_every_boundary_value_falls_through(self) -> None:
        # All three comparisons are strict, so the exact threshold is NOT a hit.
        limite = track(valencia=.3, energia=.75, instrumentalidade=.7)
        assert humor_da_faixa(limite) == "chill"


class TestGarimpar:
    def test_drops_tracks_above_the_ceiling(self) -> None:
        base = catalog(
            {**track(popularidade=5), "faixa": "A"},
            {**track(popularidade=50), "faixa": "B"},
        )
        assert list(garimpar(base, NEUTRAL, teto=20)["faixa"]) == ["A"]

    def test_empty_result_still_has_an_int64_match_column(self) -> None:
        # Callers read result["match"] unconditionally; a missing column or an
        # object dtype would break them.
        base = catalog({**track(popularidade=90), "faixa": "A"})
        resultado = garimpar(base, NEUTRAL, teto=20)
        assert resultado.empty
        assert resultado["match"].dtype == "int64"

    def test_ties_keep_catalog_order(self) -> None:
        # Identical attributes and popularity give an identical score, so only
        # the stable sort decides the order.
        base = catalog(
            {**track(popularidade=5), "faixa": "first"},
            {**track(popularidade=5), "faixa": "second"},
        )
        assert list(garimpar(base, NEUTRAL, teto=20)["faixa"]) == ["first", "second"]

    def test_ranks_the_closest_match_first(self) -> None:
        alvo = {**NEUTRAL, "energia": 1.0}
        base = catalog(
            {**track(popularidade=5, energia=.1), "faixa": "far"},
            {**track(popularidade=5, energia=.9), "faixa": "near"},
        )
        assert list(garimpar(base, alvo, teto=20)["faixa"]) == ["near", "far"]

    def test_respects_the_limit(self) -> None:
        base = catalog(*[
            {**track(popularidade=5), "faixa": f"t{i}"} for i in range(12)
        ])
        assert len(garimpar(base, NEUTRAL, teto=20)) == 8          # default
        assert len(garimpar(base, NEUTRAL, teto=20, limite=3)) == 3

    def test_resets_the_index(self) -> None:
        base = catalog(
            {**track(popularidade=50), "faixa": "dropped"},
            {**track(popularidade=5), "faixa": "kept"},
        )
        assert list(garimpar(base, NEUTRAL, teto=20).index) == [0]


class TestCobertura:
    def test_percentage_of_the_eligible_universe(self) -> None:
        base = catalog(*[
            {**track(popularidade=p), "faixa": str(p)} for p in (5, 10, 50, 60)
        ])
        assert cobertura(base, 20) == 50

    def test_empty_base_returns_zero_instead_of_dividing_by_zero(self) -> None:
        assert cobertura(pd.DataFrame(), 20) == 0


class TestEmailValido:
    @pytest.mark.parametrize("email", [
        "amanda@unb.br",
        "  amanda@unb.br  ",              # stripped before matching
        "a.b-c_d@aluno.unb.br",
    ])
    def test_accepts(self, email: str) -> None:
        assert email_valido(email)

    @pytest.mark.parametrize("email", [
        "amanda@unb",                     # no dot in the domain
        "amanda unb@x.br",                # inner space
        "@unb.br",
        "amanda@",
        "amanda@@unb.br",
        "",
    ])
    def test_rejects(self, email: str) -> None:
        assert not email_valido(email)


class TestNomeDoEmail:
    @pytest.mark.parametrize("email, esperado", [
        ("amanda.elisa@aluno.unb.br", "Amanda Elisa"),
        ("maria-carolina@x.br", "Maria Carolina"),
        ("wingrid_costa@x.br", "Wingrid Costa"),
        ("arthur@x.br", "Arthur"),
    ])
    def test_derives_a_presentable_name(self, email: str, esperado: str) -> None:
        assert nome_do_email(email) == esperado
