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

# Catálogo simulado — constante CAT do HTML, mesmos valores.
# artista, faixa, ano, cidade, popularidade, energia, valencia, dancabilidade,
# instrumentalidade, acustica, bpm, genero
_CATALOGO: tuple[tuple[Any, ...], ...] = (
    ("Núcleo Lento", "Sala de Estudos, 4h", 2021, "Curitiba", 4, .28, .38, .30, .92, .62, 72, "Lo-fi"),
    ("Ana Zíper", "Papel Milimetrado", 2022, "Belo Horizonte", 11, .33, .46, .34, .88, .44, 84, "Lo-fi"),
    ("Hélio Mesa", "Cartografia do Sono", 2019, "Porto Alegre", 7, .25, .30, .26, .95, .78, 60, "Ambiente"),
    ("Kōri Bloom", "Snow Static", 2023, "Sapporo", 14, .30, .42, .31, .90, .55, 76, "Ambiente"),
    ("Oficina Cinza", "Turno da Madrugada", 2020, "Recife", 2, .36, .40, .38, .86, .35, 92, "Pós-rock"),
    ("Marta Vetro", "Vidro Fosco", 2024, "Lisboa", 19, .31, .50, .33, .80, .68, 70, "Ambiente"),
    ("Ruído Doméstico", "Ventilador em Ré", 2018, "São Paulo", 5, .22, .35, .24, .97, .72, 58, "Ambiente"),
    ("Teleférico", "Cabo de Aço", 2022, "Bogotá", 23, .40, .48, .40, .75, .40, 88, "Pós-rock"),
    ("Britadeira Social", "Cadência Bruta", 2023, "São Paulo", 9, .95, .72, .82, .10, .03, 152, "Punk"),
    ("VOLTA SECA", "Corta o Vento", 2024, "Fortaleza", 16, .92, .78, .86, .06, .05, 148, "Funk BR"),
    ("Neon Cavalar", "Trote", 2021, "Goiânia", 6, .90, .66, .79, .22, .08, 160, "Punk"),
    ("Fábrica de Pulso", "Sexta Série", 2022, "Manaus", 12, .88, .60, .84, .35, .04, 138, "Techno"),
    ("Kilo Bruto", "Repetição 12", 2023, "Salvador", 21, .94, .70, .88, .14, .02, 145, "Techno"),
    ("Hard Copy", "Iron Draft", 2020, "Detroit", 27, .89, .63, .76, .28, .06, 150, "Techno"),
    ("Serra Elétrica", "Faísca", 2019, "Blumenau", 3, .97, .55, .72, .18, .02, 168, "Punk"),
    ("Pista Molhada", "Aquaplanagem", 2024, "Rio de Janeiro", 18, .85, .75, .90, .12, .09, 128, "Funk BR"),
    ("Beira de Rio", "Manhã de Terça", 2022, "Paraty", 8, .34, .64, .52, .45, .80, 96, "MPB"),
    ("Lume", "Varanda Aberta", 2023, "Florianópolis", 15, .38, .70, .56, .30, .74, 100, "MPB"),
    ("Verão Baixo", "Chinelo na Areia", 2021, "Maceió", 24, .42, .75, .62, .20, .66, 104, "Samba"),
    ("Cãibra Suave", "Rede Armada", 2020, "Belém", 4, .30, .58, .48, .55, .85, 88, "Bossa nova"),
    ("Coral do Quintal", "Limoeiro", 2024, "Olinda", 13, .36, .68, .50, .38, .82, 92, "Samba"),
    ("Nilo Sereno", "Água Parada", 2019, "Cascais", 20, .28, .55, .44, .50, .88, 84, "Bossa nova"),
    ("Tarde Comprida", "Café Requentado", 2023, "Campinas", 10, .40, .62, .58, .25, .70, 98, "Indie folk"),
    ("Palha & Prata", "Volta pra Casa", 2018, "Tiradentes", 26, .33, .60, .46, .42, .79, 90, "Indie folk"),
    ("Inverno Postal", "Carta Não Enviada", 2021, "Porto Alegre", 7, .26, .12, .28, .35, .72, 68, "Slowcore"),
    ("Duna Cinza", "Setembro Inteiro", 2023, "Brasília", 12, .30, .16, .32, .28, .65, 74, "Shoegaze"),
    ("Casa Vazia", "Móveis Cobertos", 2020, "Petrópolis", 3, .22, .10, .24, .40, .84, 62, "Slowcore"),
    ("Lívia Bruma", "Quase Domingo", 2024, "São Paulo", 17, .34, .20, .35, .22, .58, 80, "Indie folk"),
    ("Pálido Norte", "Estrada de Chão", 2019, "Londrina", 5, .28, .14, .30, .45, .76, 66, "Slowcore"),
    ("Amèlie Fond", "Rue Sans Nom", 2022, "Marselha", 22, .32, .18, .34, .30, .60, 72, "Shoegaze"),
    ("Fim de Feira", "Última Barraca", 2023, "Natal", 9, .25, .08, .26, .38, .80, 58, "Slowcore"),
    ("Sereno Tardio", "Janela Embaçada", 2018, "Gramado", 14, .29, .22, .31, .33, .70, 70, "Shoegaze"),
)

# Artistas de referência mainstream — constante ARTISTAS do HTML.
# artista, genero, popularidade, energia, valencia, dancabilidade,
# instrumentalidade, acustica
_ARTISTAS: tuple[tuple[Any, ...], ...] = (
    ("Dora Lima", "MPB", 84, .42, .60, .58, .10, .62),
    ("Feras do Cerrado", "Rock", 78, .88, .62, .60, .14, .10),
    ("Otávio Rey", "Indie", 73, .36, .24, .34, .20, .55),
    ("Bruno Sacchi", "Pop", 81, .66, .72, .76, .05, .22),
    ("MC Vitrine", "Funk BR", 91, .90, .80, .92, .04, .05),
    ("Clara Bandeira", "Bossa nova", 69, .28, .58, .46, .16, .86),
    ("Nêga Sol", "Samba", 76, .55, .82, .80, .06, .48),
    ("Grupo Contramão", "Pós-rock", 62, .48, .34, .30, .72, .30),
    ("Hana & os Ventos", "Shoegaze", 58, .40, .20, .32, .44, .40),
    ("Léo Quadrado", "Techno", 70, .92, .58, .90, .60, .03),
)

# Vetores-alvo por vibe — constante VIBES do HTML.
VIBES: dict[str, dict[str, Any]] = {
    "foco": {
        "nome": "Foco",
        "desc": "estudar e trabalhar",
        "cor": PERI,
        "humor": "foco",
        "alvo": {"energia": .30, "valencia": .42, "dancabilidade": .32,
                 "instrumentalidade": .88, "acustica": .55},
    },
    "treino": {
        "nome": "Treino",
        "desc": "energia lá em cima",
        "cor": ROSA,
        "humor": "treino",
        "alvo": {"energia": .92, "valencia": .70, "dancabilidade": .83,
                 "instrumentalidade": .16, "acustica": .05},
    },
    "chill": {
        "nome": "Chill",
        "desc": "leve e acústica",
        "cor": LIMA,
        "humor": "chill",
        "alvo": {"energia": .35, "valencia": .66, "dancabilidade": .52,
                 "instrumentalidade": .38, "acustica": .78},
    },
    "melancolia": {
        "nome": "Melancolia",
        "desc": "lenta e sentimental",
        "cor": "#9AD6E8",
        "humor": "triste",
        "alvo": {"energia": .28, "valencia": .15, "dancabilidade": .30,
                 "instrumentalidade": .34, "acustica": .70},
    },
}

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

MODOS: tuple[str, ...] = ("Por vibe", "Por gênero", "Por artista favorito")
PAGINAS: tuple[str, ...] = ("⛏️ Descobrir", "🎧 Minha conta")


@st.cache_data
def carregar_catalogo() -> pd.DataFrame:
    """Devolve as 32 faixas simuladas do catálogo como DataFrame."""
    return pd.DataFrame(
        _CATALOGO,
        columns=["artista", "faixa", "ano", "cidade", "popularidade", "energia",
                 "valencia", "dancabilidade", "instrumentalidade", "acustica",
                 "bpm", "genero"],
    )


@st.cache_data
def carregar_artistas() -> pd.DataFrame:
    """Devolve os 10 artistas de referência mainstream simulados."""
    return pd.DataFrame(
        _ARTISTAS,
        columns=["artista", "genero", "popularidade", "energia", "valencia",
                 "dancabilidade", "instrumentalidade", "acustica"],
    )


def _chave_pt(texto: str) -> str:
    """Chave de ordenação sem acento, imitando o localeCompare('pt') do JS."""
    return unicodedata.normalize("NFD", texto).encode("ascii", "ignore").decode().lower()


def listar_generos(catalogo: pd.DataFrame) -> list[str]:
    """Os 12 gêneros do catálogo, em ordem alfabética de português."""
    return sorted(catalogo["genero"].unique().tolist(), key=_chave_pt)
