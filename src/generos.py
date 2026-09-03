"""Famílias de gênero — a taxonomia que os seletores mostram.

O agrupamento dos 114 `track_genre` do dataset em famílias é **decisão de
dado**, então mora no notebook (`Grupo_9_Sound_Hunters.ipynb`, seção 9.1), onde
fica documentado e validado: lá há `assert` garantindo cobertura total e
ausência de repetição. Daqui a gente só **lê** o que foi exportado.

Manter uma segunda cópia do mapa neste arquivo pareceria mais simples, e
divergiria do notebook no primeiro ajuste — a UI mostraria uma taxonomia e a
análise, outra.
"""

from __future__ import annotations

from functools import lru_cache

from src import artefatos


@lru_cache(maxsize=1)
def _mapa() -> dict[str, frozenset[str]]:
    """As famílias, como o notebook as exportou."""
    bruto = artefatos.modelo().get("familias_de_genero")
    if not bruto:
        raise KeyError(
            "modelo.joblib não traz 'familias_de_genero'. Rode a seção 9.1 do "
            "notebook e reexporte os artefatos."
        )
    return {familia: frozenset(generos) for familia, generos in bruto.items()}


@lru_cache(maxsize=1)
def _de_genero_para_familia() -> dict[str, str]:
    """Índice inverso: gênero do dataset -> família."""
    return {genero: familia
            for familia, generos in _mapa().items()
            for genero in generos}


def familias() -> list[str]:
    """Os nomes das famílias, na ordem em que a interface deve mostrá-las."""
    return list(_mapa())


def expandir(nomes: object) -> set[str]:
    """Traduz nomes escolhidos na interface para gêneros do dataset.

    Aceita nome de família ou de gênero cru. O gênero cru passa direto, o que
    mantém válida qualquer chamada que use o vocabulário do dataset — inclusive
    os testes, que trabalham com catálogos pequenos e gêneros inventados.
    """
    if isinstance(nomes, str):
        nomes = [nomes]
    mapa = _mapa()
    saida: set[str] = set()
    for nome in nomes:  # type: ignore[union-attr]
        saida |= mapa.get(nome, frozenset({nome}))
    return saida


def familia_de(genero: str) -> str | None:
    """A família de um gênero do dataset, ou None se ele não estiver no mapa."""
    return _de_genero_para_familia().get(genero)
