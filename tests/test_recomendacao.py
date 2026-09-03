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

from src.dados import ATRIBUTOS, VIBES
from src.recomendacao import (
    cobertura,
    criterios_ativos,
    email_valido,
    garimpar,
    humor_da_faixa,
    match,
    perfil_do_usuario,
    garimpar_por_sementes,
    Semente,
    media_de_vetores,
    descrever_perfil,
    montar_resultado,
    nome_do_email,
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

    Popularity defaults to 30, which is the top of the recommendable range —
    a test that does not care about popularity gets a track that is eligible
    without being at either extreme.
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

    def test_popularity_does_not_move_the_match(self) -> None:
        # 0.2 away on the 0.25-weight axis: distance 0.05, score 93.25.
        # The obscurity bonus used to live here and made the same sound score
        # 96 when the track was obscure - which read as sonic affinity while
        # being a discount for being unknown. It moved to the ranking.
        alvo = {**NEUTRAL, "energia": .7}
        assert match(track(popularidade=30), alvo) == 93
        assert match(track(popularidade=10), alvo) == 93
        assert match(track(popularidade=0), alvo) == 93


class TestRarityDoesNotRank:
    """Ser impopular não compra posição — a obscuridade é filtro, não bônus.

    O bônus antigo somava 0,15 por ponto abaixo de 30, até 4,5 pontos. Como
    centenas de faixas empatam no topo do match, era ele quem escolhia as oito
    exibidas, e ele seleciona o que há de mais estranho no catálogo.
    """

    def test_the_closer_track_wins_even_when_it_is_more_popular(self) -> None:
        alvo = {**NEUTRAL, "energia": 1.0}
        base = catalog(
            {**track(popularidade=1, energia=.5), "faixa": "obscura e distante"},
            {**track(popularidade=29, energia=.95), "faixa": "conhecida e perto"},
        )
        assert list(garimpar(base, alvo, teto=30)["faixa"])[0] == "conhecida e perto"

    def test_equally_similar_tracks_keep_catalog_order(self) -> None:
        alvo = {**NEUTRAL, "energia": .7}
        base = catalog(
            {**track(popularidade=30), "faixa": "primeira"},
            {**track(popularidade=1), "faixa": "mais obscura"},
        )
        assert list(garimpar(base, alvo, teto=30)["faixa"]) == [
            "primeira", "mais obscura"]


def seed(rotulo: str, *generos: str, **atributos: float) -> Semente:
    """A seed at the neutral point, with the given genres and overrides."""
    return Semente({**NEUTRAL, **atributos}, rotulo, generos)


class TestGarimparPorSementes:
    """Vizinhos de cada semente, não vizinhos da média das sementes.

    O defeito que isto conserta: as oito faixas mais ouvidas de uma usuária
    real caíam em quatro moods diferentes, e a média delas era um ponto que
    não era nenhuma delas — o app recomendava j-idol e festa infantil para
    quem ouve blink-182 e Ben Howard.
    """

    def test_each_seed_searches_inside_its_own_genres(self) -> None:
        base = catalog(
            {**track(popularidade=5), "faixa": "punk gem",
             "artista": "X", "generos": ["punk"]},
            {**track(popularidade=5), "faixa": "folk gem",
             "artista": "Y", "generos": ["folk"]},
        )
        # limite=1: o gênero da semente já tem candidatas suficientes, então a
        # cascata não precisa alargar e a folk fica de fora.
        achadas = garimpar_por_sementes(
            base, [seed("blink", "punk")], teto=30, limite=1)
        assert list(achadas["faixa"]) == ["punk gem"]

    def test_widens_when_the_genre_has_fewer_gems_than_asked_for(self) -> None:
        # Não basta o gênero ter alguma coisa: com uma joia punk e oito
        # pedidas, parar no punk devolveria uma só. Sobe de nível.
        base = catalog(
            {**track(popularidade=5), "faixa": "punk gem",
             "artista": "X", "generos": ["punk"]},
            {**track(popularidade=5), "faixa": "folk gem",
             "artista": "Y", "generos": ["folk"]},
        )
        achadas = garimpar_por_sementes(
            base, [seed("blink", "punk")], teto=30, limite=8)
        assert len(achadas) == 2

    def test_the_average_would_have_missed_what_the_seeds_find(self) -> None:
        # Duas sementes opostas. A média delas é o ponto neutro, e a faixa
        # neutra ganharia do que cada semente realmente procura.
        base = catalog(
            {**track(popularidade=5, energia=.95), "faixa": "energética",
             "artista": "A", "generos": ["punk"]},
            {**track(popularidade=5, energia=.05), "faixa": "calma",
             "artista": "B", "generos": ["folk"]},
            {**track(popularidade=5, energia=.50), "faixa": "morna",
             "artista": "C", "generos": ["punk", "folk"]},
        )
        sementes = [seed("alta", "punk", energia=1.0),
                    seed("baixa", "folk", energia=0.0)]
        achadas = garimpar_por_sementes(base, sementes, teto=30, limite=2)
        assert set(achadas["faixa"]) == {"energética", "calma"}
        assert "morna" not in list(achadas["faixa"])

    def test_interleaves_so_every_seed_is_represented(self) -> None:
        base = catalog(*(
            [{**track(popularidade=5), "faixa": f"p{i}", "artista": "A",
              "generos": ["punk"]} for i in range(5)]
            + [{**track(popularidade=5), "faixa": f"f{i}", "artista": "B",
                "generos": ["folk"]} for i in range(5)]
        ))
        achadas = garimpar_por_sementes(
            base, [seed("um", "punk"), seed("dois", "folk")],
            teto=30, limite=4)
        # Rodízio: uma de cada, uma de cada — não quatro da primeira.
        assert list(achadas["semente"]) == ["um", "dois", "um", "dois"]

    def test_records_which_seed_brought_each_gem(self) -> None:
        base = catalog({**track(popularidade=5), "faixa": "A", "artista": "X",
                        "generos": ["punk"]})
        achadas = garimpar_por_sementes(
            base, [seed("Only Love", "punk")], teto=30, limite=8)
        assert list(achadas["semente"]) == ["Only Love"]

    def test_never_repeats_a_track_across_seeds(self) -> None:
        base = catalog({**track(popularidade=5), "faixa": "única",
                        "artista": "X", "generos": ["punk", "folk"]})
        achadas = garimpar_por_sementes(
            base, [seed("um", "punk"), seed("dois", "folk")],
            teto=30, limite=8)
        assert len(achadas) == 1

    def test_falls_back_to_the_whole_universe_when_the_genre_is_empty(self) -> None:
        # Decisão do grupo: a tela nunca devolve menos de oito por falta de
        # cauda obscura no gênero. O nível 3 é largo de propósito.
        base = catalog({**track(popularidade=5), "faixa": "distante",
                        "artista": "X", "generos": ["techno"]})
        achadas = garimpar_por_sementes(
            base, [seed("semente", "genero-que-nao-existe")],
            teto=30, limite=8)
        assert list(achadas["faixa"]) == ["distante"]

    def test_respects_the_ceiling_and_the_limit(self) -> None:
        base = catalog(*[
            {**track(popularidade=5 if i < 3 else 90), "faixa": f"t{i}",
             "artista": "A", "generos": ["punk"]} for i in range(6)
        ])
        achadas = garimpar_por_sementes(
            base, [seed("s", "punk")], teto=30, limite=2)
        assert len(achadas) == 2
        assert (achadas["popularidade"] <= 30).all()

    def test_no_seeds_gives_an_empty_frame_with_the_expected_columns(self) -> None:
        base = catalog({**track(popularidade=5), "faixa": "A", "artista": "X",
                        "generos": ["punk"]})
        achadas = garimpar_por_sementes(base, [], teto=30)
        assert achadas.empty
        assert {"match", "semente"} <= set(achadas.columns)


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
            {**track(), "faixa": "A", "genero": "Choro"},
            {**track(), "faixa": "B", "genero": "Punk"},
        )
        assert list(universo(base, [])["faixa"]) == ["A", "B"]

    def test_one_genre_narrows_to_that_genre(self) -> None:
        base = catalog(
            {**track(), "faixa": "A", "genero": "Choro"},
            {**track(), "faixa": "B", "genero": "Punk"},
        )
        assert list(universo(base, ["Choro"])["faixa"]) == ["A"]

    def test_several_genres_keep_every_one_of_them(self) -> None:
        base = catalog(
            {**track(), "faixa": "A", "genero": "Choro"},
            {**track(), "faixa": "B", "genero": "Punk"},
            {**track(), "faixa": "C", "genero": "Techno"},
        )
        assert list(universo(base, ["Choro", "Techno"])["faixa"]) == ["A", "C"]


class TestUniversoComFamilias:
    """A UI escolhe FAMÍLIA de gênero; o catálogo guarda o gênero cru.

    Nenhum teste cobria essa tradução, e foi exatamente ela que quebrou quando
    a taxonomia passou a ter uma família chamada "MPB": o nome da família
    colide com o nome de um gênero, e `expandir` dá preferência à família.
    """

    def test_a_family_name_expands_to_its_genres(self) -> None:
        from src import generos

        expandido = generos.expandir("MPB, samba, pagode e bossa nova")
        assert expandido == {"mpb", "brazil", "samba", "pagode"}

    def test_a_raw_genre_passes_through_unchanged(self) -> None:
        from src import generos

        # Gênero que não é família nenhuma continua valendo como ele mesmo,
        # que é o que mantém os catálogos pequenos dos testes funcionando.
        assert generos.expandir("Choro") == {"Choro"}

    def test_the_filter_finds_tracks_by_their_raw_genre(self) -> None:
        from src import generos

        base = catalog(
            {**track(), "faixa": "A", "generos": ["samba"], "genero": "samba"},
            {**track(), "faixa": "B", "generos": ["techno"], "genero": "techno"},
        )
        # A pessoa clicou na ficha da família; a faixa está como "samba".
        assert list(universo(base, ["MPB, samba, pagode e bossa nova"])["faixa"]) == ["A"]


class TestCriteriosAtivos:
    ARTISTAS = catalog(
        {**track(), "artista": "Dora Lima", "genero": "Choro", "energia": .42},
        {**track(), "artista": "MC Vitrine", "genero": "Funk BR", "energia": .90},
    )
    CATALOGO = catalog(
        {**track(popularidade=8), "faixa": "A", "genero": "Choro", "energia": .3},
        {**track(popularidade=15), "faixa": "B", "genero": "Choro", "energia": .5},
        {**track(popularidade=9), "faixa": "C", "genero": "Punk", "energia": .9},
    )

    def test_nothing_selected_gives_no_criteria(self) -> None:
        assert criterios_ativos(self.CATALOGO, self.ARTISTAS, [], [], []) == []

    def test_one_group_per_selection_kind_in_ui_order(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS,
                                  ["aconchego"], ["Choro"], ["Dora Lima"])
        assert [c.titulo for c in ativos] == ["Aconchego", "Choro", "parecido com Dora Lima"]

    def test_several_vibes_collapse_into_one_averaged_criterion(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS,
                                  ["aconchego", "treino"], [], [])
        assert len(ativos) == 1
        assert ativos[0].titulo == "Aconchego + Treino"
        # The expected value is derived from VIBES rather than hard-coded:
        # the targets are measured cluster centroids, so they move whenever the
        # notebook re-runs. What must hold is the averaging, not the number.
        esperado = (VIBES["aconchego"]["alvo"]["energia"]
                    + VIBES["treino"]["alvo"]["energia"]) / 2
        assert ativos[0].alvo["energia"] == pytest.approx(esperado)

    def test_a_genre_criterion_is_that_genre_average_over_the_whole_catalogue(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS, [], ["Choro"], [])
        assert ativos[0].alvo["energia"] == pytest.approx(.4)   # (.3 + .5) / 2
        assert ativos[0].ctx == "representa o som de Choro"

    def test_several_genres_average_their_centroids_not_their_tracks(self) -> None:
        # Choro averages .3 and .5 to .4; Punk is a single .9 track. The mean of
        # the two centroids is .65 — a per-track mean would give .5667.
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS, [], ["Choro", "Punk"], [])
        assert ativos[0].alvo["energia"] == pytest.approx(.65)
        assert ativos[0].titulo == "Choro + Punk"

    def test_artists_join_with_plus_in_the_title_and_with_e_in_the_context(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS, [], [],
                                  ["Dora Lima", "MC Vitrine"])
        assert ativos[0].titulo == "parecido com Dora Lima + MC Vitrine"
        assert ativos[0].ctx == "chega perto de Dora Lima e MC Vitrine"
        assert ativos[0].alvo["energia"] == pytest.approx(.66)  # (.42 + .90) / 2

    def test_the_vibe_context_names_every_selected_vibe(self) -> None:
        ativos = criterios_ativos(self.CATALOGO, self.ARTISTAS, ["aconchego", "foco"], [], [])
        assert ativos[0].ctx == "bate com a vibe Aconchego + Foco"


class TestTextoStatus:
    def test_lists_all_three_groups_in_ui_order(self) -> None:
        assert texto_status(["aconchego"], ["Choro"], ["Dora Lima"], 18) == (
            "Buscando por vibe <b>Aconchego</b>, gênero <b>Choro</b>, "
            "parecido com <b>Dora Lima</b>, com popularidade até <b>18</b>.")

    def test_joins_several_vibes_and_genres_with_plus(self) -> None:
        assert texto_status(["aconchego", "treino"], ["Choro", "Samba"], [], 7) == (
            "Buscando por vibe <b>Aconchego + Treino</b>, gênero <b>Choro + Samba</b>, "
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


class TestMontarResultado:
    CATALOGO = catalog(
        {**track(popularidade=8), "faixa": "Choro baixa", "genero": "Choro",
         "energia": .34, "bpm": 96, "artista": "Beira de Rio",
         "cidade": "Paraty", "ano": 2022},
        {**track(popularidade=15), "faixa": "Choro média", "genero": "Choro",
         "energia": .38, "bpm": 100, "artista": "Lume",
         "cidade": "Florianópolis", "ano": 2023},
        {**track(popularidade=9), "faixa": "Punk", "genero": "Punk",
         "energia": .95, "bpm": 152, "artista": "Britadeira Social",
         "cidade": "São Paulo", "ano": 2023},
    )
    ARTISTAS = catalog(
        {**track(), "artista": "Dora Lima", "genero": "Choro", "energia": .42},
    )

    def montar(self, vibes: list[str], generos: list[str],
               favoritos: list[str], teto: int = 18) -> dict:
        return montar_resultado(self.CATALOGO, self.ARTISTAS, vibes, generos,
                                favoritos, teto)

    def test_a_genre_narrows_the_universe(self) -> None:
        resultado = self.montar([], ["Choro"], [])
        assert {f["genero"] for f in resultado["faixas"]} == {"Choro"}

    def test_no_genre_searches_every_genre(self) -> None:
        resultado = self.montar(["treino"], [], [])
        assert {f["genero"] for f in resultado["faixas"]} == {"Choro", "Punk"}

    def test_the_title_lists_every_active_criterion(self) -> None:
        assert self.montar(["aconchego"], ["Choro"], ["Dora Lima"])["titulo"] == (
            "Joias — Aconchego · Choro · parecido com Dora Lima")

    def test_the_context_joins_the_criteria_with_e(self) -> None:
        assert self.montar(["aconchego"], ["Choro"], [])["ctx"] == (
            "bate com a vibe Aconchego e representa o som de Choro")

    def test_coverage_is_measured_against_the_narrowed_universe(self) -> None:
        # Inside Choro, both tracks are at or below 15, so a ceiling of 15 keeps
        # everything — even though one of the three catalogue tracks is out.
        assert self.montar([], ["Choro"], [], teto=15)["cobertura"] == 100

    def test_one_vibe_tints_the_heading_with_its_colour(self) -> None:
        assert self.montar(["aconchego"], [], [])["cor"] == VIBES["aconchego"]["cor"]

    def test_several_vibes_fall_back_to_lime(self) -> None:
        assert self.montar(["aconchego", "treino"], [], [])["cor"] == LIMA

    def test_no_vibe_falls_back_to_lime(self) -> None:
        assert self.montar([], ["Choro"], [])["cor"] == LIMA

    def test_nothing_selected_is_a_programming_error(self) -> None:
        with pytest.raises(ValueError, match="at least one active criterion"):
            self.montar([], [], [])

    def test_an_empty_result_still_reports_zero_average_match(self) -> None:
        assert self.montar(["aconchego"], [], [], teto=1)["faixas"] == []
        assert self.montar(["aconchego"], [], [], teto=1)["media_match"] == 0


class TestRar:
    # Os limites são os quartis da popularidade das faixas elegíveis até 50,
    # então as quatro bandas têm tamanho parecido. Os antigos 8 e 17 vinham de
    # um slider que ia só até 40.
    @pytest.mark.parametrize("popularidade, selo", [
        (3, "Joia bruta"),
        (20, "Joia bruta"),        # limite
        (21, "Rara"),
        (27, "Rara"),             # limite
        (28, "Pouco ouvida"),
        (36, "Pouco ouvida"),     # limite
        (37, "Em ascensão"),
        (50, "Em ascensão"),
    ])
    def test_boundaries(self, popularidade: int, selo: str) -> None:
        assert rar(popularidade)[0] == selo

    def test_every_band_has_its_own_colour(self) -> None:
        cores = {rar(p)[1] for p in (3, 21, 28, 37)}
        assert len(cores) == 4

class TestRotuloProfundidade:
    @pytest.mark.parametrize("teto, esperado", [
        (5, "Praticamente invisível"),
        (20, "Praticamente invisível"),  # limite
        (21, "Bem underground"),
        (27, "Bem underground"),         # limite
        (28, "Conhecida em nicho"),
        (36, "Conhecida em nicho"),      # limite
        (37, "Começando a aparecer"),
        (50, "Começando a aparecer"),
    ])
    def test_boundaries(self, teto: int, esperado: str) -> None:
        assert rotulo_profundidade(teto) == esperado

    def test_it_agrees_with_the_rarity_seal(self) -> None:
        # O texto do slider e o selo do cartão usam os mesmos limites: se
        # divergirem, a tela diz duas coisas sobre a mesma faixa.
        from src.recomendacao import BANDAS_DE_RARIDADE
        for teto, _, _ in BANDAS_DE_RARIDADE:
            assert rotulo_profundidade(teto) != rotulo_profundidade(teto + 1)

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

class TestPerfilDoUsuario:
    """O perfil vinha de uma constante no código enquanto a tela mostrava as
    faixas reais de quem conectava. Estes testes travam a ligação entre as duas
    coisas: o perfil sai das faixas que a pessoa realmente ouve."""

    # Seis faixas: precisa passar de MINIMO_DE_FAIXAS_CRUZADAS para o perfil
    # sair das faixas em vez de descer para a aproximação por gênero.
    CATALOGO = catalog(
        *[{**track(popularidade=40, energia=e), "track_id": tid, "faixa": tid.upper()}
          for tid, e in [("aaa", .9), ("bbb", .9), ("ccc", .9),
                         ("ddd", .1), ("eee", .1), ("fff", .1)]],
    )
    SEIS = [{"id": t} for t in ("aaa", "bbb", "ccc", "ddd", "eee", "fff")]

    def test_the_profile_is_the_mean_of_the_matched_tracks(self) -> None:
        perfil = perfil_do_usuario(self.CATALOGO, self.SEIS)
        assert perfil.e_real
        assert perfil.encontradas == 6
        assert perfil.alvo["energia"] == pytest.approx(.5)   # três .9 e três .1

    def test_it_counts_what_was_asked_and_what_was_found(self) -> None:
        # A tela mostra essa fração à pessoa, e mentir nela seria pior que não
        # mostrar.
        perfil = perfil_do_usuario(
            self.CATALOGO, self.SEIS + [{"id": "zzz"}, {"id": "yyy"}])
        assert (perfil.encontradas, perfil.pedidas) == (6, 8)

    def test_no_match_falls_back_and_says_so(self) -> None:
        perfil = perfil_do_usuario(self.CATALOGO, [{"id": "zzz"}])
        assert not perfil.e_real
        assert perfil.encontradas == 0

    def test_no_tracks_at_all_is_not_a_real_profile(self) -> None:
        # É o caso do login encenado: sem faixas, nada a cruzar.
        assert not perfil_do_usuario(self.CATALOGO, []).e_real


class TestDescreverPerfil:
    """A frase do perfil era fixa no código e diria a mesma coisa para
    qualquer pessoa."""

    def test_it_names_the_two_most_extreme_attributes(self) -> None:
        alvo = {**NEUTRAL, "energia": .95, "acustica": .02}
        frase = descrever_perfil(alvo)
        assert "energética" in frase
        assert "elétrica" in frase
        assert " e " in frase        # tem que ler como frase, não como lista

    def test_the_opposite_profile_gets_the_opposite_words(self) -> None:
        alvo = {**NEUTRAL, "energia": .05, "acustica": .98}
        frase = descrever_perfil(alvo)
        assert "calma" in frase
        assert "acústica" in frase

    def test_two_different_profiles_do_not_share_a_description(self) -> None:
        intenso = {**NEUTRAL, "energia": .95, "valencia": .9}
        melancolico = {**NEUTRAL, "energia": .1, "valencia": .05}
        assert descrever_perfil(intenso) != descrever_perfil(melancolico)

class TestCascataDoPerfil:
    """Três níveis, do mais preciso ao mais grosso, e a tela precisa saber por
    qual deles passou — senão diz "seu perfil" sobre uma aproximação."""

    CATALOGO = catalog(
        *[{**track(popularidade=40, energia=.9), "track_id": f"r{i}",
           "generos": ["rock"], "genero": "rock", "faixa": f"R{i}"} for i in range(6)],
        *[{**track(popularidade=40, energia=.1), "track_id": f"j{i}",
           "generos": ["jazz"], "genero": "jazz", "faixa": f"J{i}"} for i in range(6)],
    )

    def test_enough_matched_tracks_uses_their_mean(self) -> None:
        pedidas = [{"id": f"r{i}"} for i in range(6)]
        perfil = perfil_do_usuario(self.CATALOGO, pedidas, ["jazz"])
        assert perfil.origem == "faixas"
        # Usou as faixas, não os gêneros: energia .9 é do rock.
        assert perfil.alvo["energia"] == pytest.approx(.9)

    def test_too_few_tracks_falls_back_to_the_genre_centroid(self) -> None:
        # Duas faixas são um momento, não um gosto — abaixo do mínimo.
        perfil = perfil_do_usuario(
            self.CATALOGO, [{"id": "r0"}, {"id": "r1"}], ["jazz"])
        assert perfil.origem == "generos"
        assert perfil.generos_usados == ("jazz",)
        assert perfil.alvo["energia"] == pytest.approx(.1)
        # Continua sendo um perfil da pessoa, só que aproximado.
        assert perfil.e_real

    def test_it_keeps_only_the_genres_our_catalogue_knows(self) -> None:
        # O Spotify usa vocabulário próprio ("brazilian rock") que nem sempre
        # existe no nosso track_genre.
        perfil = perfil_do_usuario(
            self.CATALOGO, [{"id": "r0"}], ["jazz", "vaporwave-inexistente"])
        assert perfil.generos_usados == ("jazz",)

    def test_no_tracks_and_no_known_genre_is_an_example(self) -> None:
        perfil = perfil_do_usuario(self.CATALOGO, [{"id": "zzz"}], ["inexistente"])
        assert perfil.origem == "exemplo"
        assert not perfil.e_real

    def test_the_counts_survive_the_fallback(self) -> None:
        # A tela mostra "N das suas M": os números não podem sumir só porque
        # a cascata desceu um nível.
        perfil = perfil_do_usuario(
            self.CATALOGO, [{"id": "r0"}, {"id": "zz"}, {"id": "yy"}], ["jazz"])
        assert (perfil.encontradas, perfil.pedidas) == (1, 3)
