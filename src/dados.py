"""Dados SIMULADOS do Gems Finder e constantes de produto.

Tudo mora aqui dentro: 32 faixas fictícias de artistas underground, 10 artistas
de referência mainstream fictícios, os alvos das vibes e as "mais ouvidas" do
testador. Nenhum CSV externo, nenhuma credencial.
"""

from __future__ import annotations

import unicodedata
from typing import Any

import pandas as pd
import streamlit as st

from src import artefatos, generos
from src.tema import LIMA, PERI, ROSA

ATRIBUTOS: tuple[str, ...] = (
    "energia",
    "valencia",
    "dancabilidade",
    "instrumentalidade",
    "acustica",
)

# Pesos da distância ponderada (constante W do protótipo).
PESOS: dict[str, float] = {
    "energia": 0.25,
    "valencia": 0.25,
    "dancabilidade": 0.20,
    "instrumentalidade": 0.15,
    "acustica": 0.15,
}

# Rótulos das barras de atributo de áudio.
ROTULOS_ATRIBUTOS: tuple[tuple[str, str], ...] = (
    ("energia", "Energia"),
    ("valencia", "Humor (valência)"),
    ("dancabilidade", "Dançabilidade"),
    ("instrumentalidade", "Instrumental"),
    ("acustica", "Acústica"),
)


# Vetores-alvo por vibe — constante VIBES do HTML.
# As cinco vibes vêm dos clusters medidos, não de alvos escritos à mão: o
# alvo de cada uma é o perfil médio real do seu cluster. Assim o app e o
# notebook concordam por construção, sem ninguém copiar número de um pro
# outro. Cor e expressão de cada vibe ficam em src/artefatos.py::APRESENTACAO.
VIBES: dict[str, dict[str, Any]] = artefatos.vibes()


# "Mais ouvidas" simuladas do testador conectado — constante TOPS do HTML.
TOPS: tuple[tuple[str, str], ...] = (
    ("Meia-Noite em Copacabana", "Dora Lima"),
    ("Antídoto", "Feras do Cerrado"),
    ("Vista Cansada", "Otávio Rey"),
    ("Linha Amarela", "Bruno Sacchi"),
    ("Nunca Foi Sorte", "MC Vitrine"),
)

# Perfil médio de áudio do testador conectado.
PERFIL_USUARIO: dict[str, float] = {
    "energia": .62,
    "valencia": .41,
    "dancabilidade": .55,
    "instrumentalidade": .29,
    "acustica": .44,
}
TETO_CONTA = 20

ETAPAS_OAUTH: tuple[str, ...] = (
    "Autorizando acesso via OAuth",
    "Lendo suas 50 faixas mais ouvidas",
    "Calculando seu perfil médio de áudio",
    "Cruzando com as 114.000 faixas do catálogo",
)

PERMISSOES: tuple[str, ...] = (
    "Ler suas faixas e artistas mais ouvidos",
    "Ler os atributos de áudio dessas faixas",
    "Criar uma playlist privada na sua conta",
)

PAGINAS: tuple[str, ...] = ("⛏️ Descobrir", "🎧 Minha conta")


@st.cache_data
def carregar_catalogo() -> pd.DataFrame:
    """O catálogo real: 89.740 faixas do dataset processado.

    Mesma interface de antes — as colunas seguem em português. `ano` e
    `cidade` saíram porque o dataset não os tem, e inventá-los violaria o
    princípio 2 da constituição.
    """
    return artefatos.catalogo()


@st.cache_data
def carregar_artistas() -> pd.DataFrame:
    """Artistas conhecidos que servem de referência no seletor.

    São consolidados de propósito: a pessoa escolhe quem reconhece e o
    garimpo devolve joia de artista independente com o mesmo perfil sonoro.
    """
    return artefatos.artistas()


def _chave_pt(texto: str) -> str:
    """Chave de ordenação sem acento, imitando o localeCompare('pt') do JS."""
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def listar_generos(catalogo: pd.DataFrame) -> list[str]:
    """As famílias de gênero que o seletor oferece.

    O dataset traz 114 `track_genre`, que é vocabulário de catálogo: 114
    fichas não formam um seletor. O agrupamento em famílias está em
    `src/generos.py`, e é ele que a interface mostra.
    """
    del catalogo  # a taxonomia é fixa, não depende do que veio no catálogo
    return generos.familias()


def contar_por_genero(catalogo: pd.DataFrame) -> dict[str, int]:
    """Quantas faixas cada família de gênero tem.

    Conta a lista completa de gêneros de cada faixa, não a coluna `genero`
    (o primeiro em ordem alfabética): a contagem tem que casar com o que o
    filtro devolve, senão o número na ficha mente sobre o resultado.
    """
    if "generos" not in catalogo.columns:
        return catalogo["genero"].value_counts().to_dict()

    contagem: dict[str, int] = {familia: 0 for familia in generos.familias()}
    for lista in catalogo["generos"]:
        # `set` para uma faixa em dois gêneros da mesma família contar uma vez
        for familia in {generos.familia_de(g) for g in lista}:
            if familia is not None:
                contagem[familia] += 1
    return contagem
