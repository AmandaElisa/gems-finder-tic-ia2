"""Tests for src/recomendacao.py — the logic that decides which gem a user sees.

Only pure functions are covered. The Streamlit UI is verified by running the
app (see CLAUDE.md), not by mocking widgets. Fixtures build small DataFrames by
hand rather than calling carregar_catalogo(), which is @st.cache_data-wrapped
and expects a script context.

Assertions compare against Portuguese strings on purpose: those are UI copy,
and UI copy stays Portuguese.
"""

from __future__ import annotations

import pytest

from src.dados import ATRIBUTOS
from src.recomendacao import (
    humor_da_faixa,
    match,
    rar,
    rotulo_profundidade,
    round_js,
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
