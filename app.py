"""Gems Finder — garimpeiro de joias ocultas do Spotify.

Protótipo navegável da Residência em IA · UnB (Grupo 9 · Nano-Challenge Spotify).
Porte para Streamlit do protótipo `gems-finder-v4-ilustrado.html`: mesmo fluxo,
mesmos textos, mesma paleta e a mesma mascote (Pepita, a gema garimpeira).

AVISOS
------
* Todos os dados aqui são SIMULADOS e moram no próprio script: 32 faixas
  fictícias de artistas underground e 10 artistas de referência mainstream
  fictícios. Nenhum CSV externo, nenhuma credencial, nenhuma chamada real à
  Spotify Web API (os pontos de integração estão marcados com TODO).
* A métrica "Precisão @8" é PLACEHOLDER (ver `PRECISAO_8`) até a avaliação real
  do modelo. Já a "Cobertura" é calculada de fato sobre o catálogo simulado.

Rodar:  streamlit run app.py
"""

from __future__ import annotations

import math
import random
import re
import time
import unicodedata
from typing import Any, Mapping

import numpy as np
import pandas as pd
import streamlit as st

# =============================================================================
# 1. DADOS SIMULADOS
# =============================================================================

# --- paleta (idêntica ao :root do protótipo HTML) ----------------------------
LIMA = "#CFF25E"
ROSA = "#F79BD8"
PERI = "#B3BCF7"
AZUL = "#3B45D9"
VERDE = "#1DB954"
VERDE_ESC = "#0E7A36"
CREME = "#FAF6EC"
TINTA = "#141414"
MUTE = "#6E6A63"

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
# Por enquanto são os placeholders herdados do protótipo aprovado.
PRECISAO_8: dict[str, int] = {
    "vibe_foco": 91,
    "vibe_treino": 87,
    "vibe_chill": 84,
    "vibe_melancolia": 89,
    "genero": 86,
    "artista": 90,
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


# =============================================================================
# 2. LÓGICA DE RECOMENDAÇÃO
# =============================================================================

def _round_js(valor: float) -> int:
    """Arredonda meio-para-cima, igual ao Math.round() do JavaScript."""
    return math.floor(valor + 0.5)


def match(faixa: Mapping[str, Any], alvo: Mapping[str, float]) -> int:
    """Afinidade 31–99 entre uma faixa e um vetor-alvo de atributos de áudio.

    Distância ponderada absoluta + bônus de obscuridade pela popularidade baixa.
    """
    pesos = np.array([PESOS[a] for a in ATRIBUTOS])
    diferencas = np.abs(
        np.array([float(faixa[a]) for a in ATRIBUTOS])
        - np.array([float(alvo[a]) for a in ATRIBUTOS])
    )
    distancia = float(np.dot(pesos, diferencas))
    bruto = 100 - distancia * 135 + (30 - float(faixa["popularidade"])) * 0.15
    return max(31, min(99, _round_js(bruto)))


def media(faixas: pd.DataFrame) -> dict[str, float]:
    """Média de cada atributo de áudio de um conjunto de faixas ou artistas."""
    return {atributo: float(faixas[atributo].mean()) for atributo in ATRIBUTOS}


def centro(catalogo: pd.DataFrame, genero: str) -> dict[str, float]:
    """Centroide de atributos de áudio das faixas de um gênero."""
    return media(catalogo[catalogo["genero"] == genero])


def rar(popularidade: int) -> tuple[str, str]:
    """Selo de raridade e a cor correspondente, a partir da popularidade."""
    if popularidade <= 8:
        return "Joia bruta", LIMA
    if popularidade <= 17:
        return "Rara", ROSA
    return "Pouco ouvida", PERI


def garimpar(base: pd.DataFrame, alvo: Mapping[str, float], teto: int,
             limite: int = 8) -> pd.DataFrame:
    """Filtra por popularidade <= teto, ranqueia por match e devolve as N melhores."""
    elegiveis = base[base["popularidade"] <= teto].copy()
    if elegiveis.empty:
        return elegiveis.assign(match=pd.Series(dtype="int64"))
    elegiveis["match"] = [match(linha, alvo) for _, linha in elegiveis.iterrows()]
    # kind="stable" preserva a ordem do catálogo nos empates, como o sort do JS.
    return (elegiveis.sort_values("match", ascending=False, kind="stable")
            .head(limite).reset_index(drop=True))


def cobertura(base: pd.DataFrame, teto: int) -> int:
    """% do universo elegível que passa no filtro de popularidade."""
    if base.empty:
        return 0
    return _round_js(len(base[base["popularidade"] <= teto]) / len(base) * 100)


def rotulo_profundidade(teto: int) -> str:
    """Nome amigável da faixa de popularidade escolhida no slider."""
    if teto <= 10:
        return "Praticamente invisível"
    if teto <= 20:
        return "Bem underground"
    if teto <= 30:
        return "Conhecida em nicho"
    return "Começando a aparecer"


def humor_da_faixa(faixa: Mapping[str, Any]) -> str:
    """Expressão da mascote que combina com os atributos da faixa."""
    if float(faixa["valencia"]) < .3:
        return "triste"
    if float(faixa["energia"]) > .75:
        return "treino"
    if float(faixa["instrumentalidade"]) > .7:
        return "foco"
    return "chill"


def novo_id_playlist(tamanho: int = 22) -> str:
    """ID aleatório no formato usado pelas playlists do Spotify."""
    alfabeto = "abcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(random.choice(alfabeto) for _ in range(tamanho))


def email_valido(email: str) -> bool:
    """Valida o e-mail com a mesma regex do protótipo."""
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email.strip()))


def nome_do_email(email: str) -> str:
    """Deriva um nome apresentável a partir do trecho antes do @."""
    local = re.sub(r"[._-]", " ", email.split("@")[0])
    return re.sub(r"\b\w", lambda m: m.group().upper(), local).strip()


def montar_resultado(catalogo: pd.DataFrame, artistas: pd.DataFrame, modo: str,
                     vibe: str, genero: str, favoritos: list[str],
                     teto: int) -> dict[str, Any]:
    """Roda o garimpo no modo escolhido e devolve tudo que a UI precisa exibir."""
    if modo == "Por vibe":
        base, alvo = catalogo, VIBES[vibe]["alvo"]
        titulo = f"Joias da vibe {VIBES[vibe]['nome']}"
        ctx = f"os atributos de áudio batem com o alvo da vibe {VIBES[vibe]['nome']}"
        precisao = PRECISAO_8[f"vibe_{vibe}"]
    elif modo == "Por gênero":
        base, alvo = catalogo[catalogo["genero"] == genero], centro(catalogo, genero)
        titulo = f"Joias de {genero}"
        ctx = f"ela representa bem o som médio do gênero {genero}"
        precisao = PRECISAO_8["genero"]
    else:
        selecionados = artistas[artistas["artista"].isin(favoritos)]
        base, alvo = catalogo, media(selecionados)
        titulo = "Parecido com " + " + ".join(favoritos)
        ctx = "o perfil sonoro dela chega perto de " + " e ".join(favoritos)
        precisao = PRECISAO_8["artista"]

    achadas = garimpar(base, alvo, teto)
    return {
        "titulo": titulo,
        "ctx": ctx,
        "precisao": precisao,
        "cobertura": cobertura(base, teto),
        "faixas": achadas.to_dict("records"),
        "media_match": _round_js(achadas["match"].mean()) if len(achadas) else 0,
        "legenda": "Clique em cada faixa pra ver os atributos de áudio.",
        "sub_match": "afinidade com o alvo escolhido",
        "sub_cobertura": "do catálogo elegível cabe neste filtro",
        "cor": VIBES[vibe]["cor"] if modo == "Por vibe" else LIMA,
    }


def montar_resultado_conta(catalogo: pd.DataFrame) -> dict[str, Any]:
    """Garimpo do modo testador: cruza o perfil médio do usuário com o catálogo."""
    achadas = garimpar(catalogo, PERFIL_USUARIO, TETO_CONTA)
    return {
        "titulo": "Joias pra você",
        "ctx": "ela combina com o perfil médio das suas mais ouvidas",
        "precisao": PRECISAO_8["conta"],
        "cobertura": cobertura(catalogo, TETO_CONTA),
        "faixas": achadas.to_dict("records"),
        "media_match": _round_js(achadas["match"].mean()) if len(achadas) else 0,
        "legenda": f"Nenhuma passa de {TETO_CONTA} de popularidade.",
        "sub_match": "afinidade com o seu perfil",
        "sub_cobertura": "do catálogo elegível para o seu perfil",
        "cor": ROSA,
    }


# =============================================================================
# 3. INTERFACE
# =============================================================================

# --- 3.1 mascote Pepita (SVG inline, traduzido da função mascot() do HTML) ---

_OLHOS: dict[str, str] = {
    "foco": (
        '<circle class="eye" cx="21" cy="30" r="2.6" fill="#141414"/>'
        '<circle class="eye b" cx="35" cy="30" r="2.6" fill="#141414"/>'
        '<path d="M15 25.5h12M29 25.5h12" stroke="#141414" stroke-width="2" stroke-linecap="round"/>'
    ),
    "treino": (
        '<circle class="eye" cx="21" cy="29" r="3.4" fill="#141414"/>'
        '<circle class="eye b" cx="35" cy="29" r="3.4" fill="#141414"/>'
    ),
    "chill": (
        '<path d="M17 30c2-3 6-3 8 0M31 30c2-3 6-3 8 0" stroke="#141414" '
        'stroke-width="2.2" fill="none" stroke-linecap="round"/>'
    ),
    "triste": (
        '<circle class="eye" cx="21" cy="31" r="2.8" fill="#141414"/>'
        '<circle class="eye b" cx="35" cy="31" r="2.8" fill="#141414"/>'
        '<path d="M17 25.8c2.2-1.4 5-1.4 7.2.6M39 25.8c-2.2-1.4-5-1.4-7.2.6" '
        'stroke="#141414" stroke-width="1.9" fill="none" stroke-linecap="round"/>'
    ),
    "feliz": (
        '<circle class="eye" cx="21" cy="29" r="2.8" fill="#141414"/>'
        '<circle class="eye b" cx="35" cy="29" r="2.8" fill="#141414"/>'
    ),
}

_BOCA: dict[str, str] = {
    "foco": '<path d="M23 39h10" stroke="#141414" stroke-width="2.2" stroke-linecap="round"/>',
    "treino": '<ellipse cx="28" cy="39" rx="5" ry="6" fill="#141414"/>',
    "chill": ('<path d="M22 37c3 4 9 4 12 0" stroke="#141414" stroke-width="2.2" '
              'fill="none" stroke-linecap="round"/>'),
    "triste": ('<path d="M24 39.5h8" stroke="#141414" stroke-width="2.2" fill="none" '
               'stroke-linecap="round"/>'),
    "feliz": ('<path d="M21 37c4 5 10 5 14 0" stroke="#141414" stroke-width="2.2" '
              'fill="none" stroke-linecap="round"/>'),
}

_BRACOS_TREINO = (
    '<path d="M9 34 2 22M47 34l7-12" stroke="#141414" stroke-width="2.2" stroke-linecap="round"/>'
    '<circle cx="2" cy="21" r="3" fill="#141414"/><circle cx="54" cy="21" r="3" fill="#141414"/>'
)
_BRACOS_PADRAO = (
    '<path d="M9 38c-5 2-6 6-5 9M47 38c5 2 6 6 5 9" stroke="#141414" stroke-width="2.2" '
    'fill="none" stroke-linecap="round"/>'
    '<circle cx="4" cy="48" r="3" fill="#141414"/><circle cx="52" cy="48" r="3" fill="#141414"/>'
)


def mascote(cor: str, humor: str = "feliz", tamanho: int = 64) -> str:
    """SVG inline da Pepita. Humores: feliz, foco, treino, chill e triste."""
    bracos = _BRACOS_TREINO if humor == "treino" else _BRACOS_PADRAO
    return (
        f'<svg class="gf-mascote" width="{tamanho}" height="{round(tamanho * 1.15)}" '
        'viewBox="-4 0 64 66" aria-hidden="true">'
        f'{bracos}'
        f'<path d="M28 4 8 17l6 34h28l6-34L28 4z" fill="{cor}" stroke="#141414" '
        'stroke-width="2.4" stroke-linejoin="round"/>'
        '<path d="M28 4 8 17h40L28 4z" fill="#fff" fill-opacity=".35" stroke="#141414" '
        'stroke-width="1.6" stroke-linejoin="round"/>'
        f'{_OLHOS.get(humor, "")}{_BOCA.get(humor, "")}'
        '<path d="M20 55v6M36 55v6" stroke="#141414" stroke-width="2.2" stroke-linecap="round"/>'
        '<path d="M15 62h9M32 62h9" stroke="#141414" stroke-width="2.4" stroke-linecap="round"/>'
        '</svg>'
    )


LOGO = (
    '<svg width="34" height="38" viewBox="0 0 34 38" aria-hidden="true">'
    '<path d="M17 2 4 12l13 24 13-24L17 2z" fill="#CFF25E" stroke="#141414" '
    'stroke-width="2" stroke-linejoin="round"/>'
    '<circle cx="13" cy="17" r="1.9" fill="#141414"/>'
    '<circle cx="21" cy="17" r="1.9" fill="#141414"/>'
    '<path d="M13.5 22c1.8 2 5.2 2 7 0" stroke="#141414" stroke-width="1.8" '
    'fill="none" stroke-linecap="round"/></svg>'
)

# --- 3.2 folha de estilo -----------------------------------------------------

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700;800&family=Fredoka:wght@500;600;700&display=swap');

:root{
  --lima:#CFF25E; --rosa:#F79BD8; --peri:#B3BCF7; --azul:#3B45D9;
  --verde:#1DB954; --verde-esc:#0E7A36; --creme:#FAF6EC; --tinta:#141414; --mute:#6E6A63;
  --f:"Figtree",ui-sans-serif,system-ui,sans-serif;
  --d:"Fredoka",var(--f);
}

/* ---------- base ---------- */
html, body, .stApp, .stMarkdown, p, li, label, input, button, textarea{font-family:var(--f);}
.stApp{
  background-color:var(--creme); color:var(--tinta);
  background-image:radial-gradient(520px 380px at 92% 2%, rgba(179,188,247,.35), transparent 60%),
                   radial-gradient(460px 340px at 2% 96%, rgba(247,155,216,.28), transparent 60%);
  background-attachment:fixed;
}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1180px;padding-top:2rem;padding-bottom:5rem;}
h1,h2,h3,h4{font-family:var(--d);letter-spacing:-.01em;color:var(--tinta);}
:focus-visible{outline:3px solid var(--azul);outline-offset:3px;border-radius:8px;}
hr{border-color:rgba(20,20,20,.15);}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:var(--creme);border-right:2px solid var(--tinta);}
[data-testid="stSidebar"] [role="radiogroup"]{gap:8px;}
[data-testid="stSidebar"] [role="radiogroup"] label{
  background:#fff;border:2px solid var(--tinta);border-radius:14px;padding:9px 12px;
  box-shadow:3px 3px 0 var(--tinta);font-weight:700;transition:.14s;width:100%;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover{transform:translate(-1px,-1px);}
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked){background:var(--lima);}
.gf-brand{display:flex;align-items:center;gap:10px;margin-bottom:6px;}
.gf-brand h1{font-family:var(--d);font-size:21px;font-weight:700;margin:0;}
.gf-brand small{display:block;font-size:11.5px;color:var(--mute);font-weight:600;}
.gf-nav-label{font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;color:var(--mute);
  font-weight:800;margin:14px 0 6px;}
.gf-rail-foot{font-size:12px;color:var(--mute);line-height:1.7;
  border-top:2px dashed rgba(20,20,20,.2);padding-top:14px;margin-top:22px;}
.gf-rail-foot b{color:var(--tinta);}

/* ---------- cartões sticker ---------- */
[class*="st-key-cartao-"]{
  background:#fff;border:2px solid var(--tinta);border-radius:22px;
  padding:20px 24px;box-shadow:5px 5px 0 var(--tinta);margin-bottom:22px;
}
[class*="st-key-gema-"]{
  background:#fff;border:2px solid var(--tinta);border-radius:20px;
  padding:14px 18px 4px;box-shadow:4px 4px 0 var(--tinta);margin-bottom:16px;
}
.gf-card{background:#fff;border:2px solid var(--tinta);border-radius:22px;padding:22px 24px;
  box-shadow:5px 5px 0 var(--tinta);margin-bottom:22px;}

/* ---------- hero ---------- */
.gf-hero{display:flex;align-items:center;gap:22px;flex-wrap:wrap;margin-bottom:26px;}
.gf-title{font-family:var(--d);font-size:40px;font-weight:700;letter-spacing:-.02em;
  margin:0;line-height:1.08;}
.gf-lede{color:var(--mute);margin:8px 0 0;max-width:56ch;font-size:15.5px;}
.gf-bubble{background:#fff;border:2px solid var(--tinta);border-radius:22px 22px 22px 6px;
  padding:12px 18px;font-family:var(--d);font-size:16px;box-shadow:4px 4px 0 var(--tinta);
  animation:gfFloat 3.6s ease-in-out infinite;}
@keyframes gfFloat{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}

/* ---------- passos ---------- */
.gf-step{display:flex;align-items:center;gap:10px;margin-bottom:4px;}
.gf-step b{font-size:11px;font-weight:800;letter-spacing:.08em;background:var(--lima);
  border:2px solid var(--tinta);border-radius:99px;padding:2px 10px;}
.gf-step h3{font-family:var(--d);font-size:19px;font-weight:600;margin:0;}
.gf-help{color:var(--mute);font-size:13.5px;margin:0 0 10px;}
.gf-help b{color:var(--tinta);}
.gf-status{font-size:13.5px;color:var(--mute);margin:0 0 12px;}
.gf-status b{color:var(--tinta);font-weight:800;}

/* ---------- vibes ---------- */
.gf-vibe{border:2px solid var(--tinta);border-bottom:0;border-radius:20px 20px 0 0;
  padding:14px 12px 8px;text-align:center;box-shadow:4px 0 0 var(--tinta);}
.gf-vibe strong{display:block;font-family:var(--d);font-size:17px;font-weight:600;margin-top:6px;}
.gf-vibe span{display:block;font-size:12.5px;color:var(--mute);line-height:1.35;margin-top:2px;}
[class*="st-key-btnvibe-"] button{width:100%;border-radius:0 0 18px 18px !important;
  border-top:0 !important;box-shadow:4px 4px 0 var(--tinta) !important;}
[class*="st-key-btnvibe-"] button:hover{transform:none;}
.st-key-btnvibe-foco-on button{background:#B3BCF7 !important;color:var(--tinta) !important;}
.st-key-btnvibe-treino-on button{background:#F79BD8 !important;color:var(--tinta) !important;}
.st-key-btnvibe-chill-on button{background:#CFF25E !important;color:var(--tinta) !important;}
.st-key-btnvibe-melancolia-on button{background:#9AD6E8 !important;color:var(--tinta) !important;}

/* ---------- profundidade ---------- */
.gf-num{font-family:var(--d);font-size:44px;font-weight:700;line-height:1;}
.gf-num span{font-size:15px;color:var(--mute);font-family:var(--f);font-weight:700;}
.gf-strata{display:flex;align-items:flex-end;gap:3px;height:48px;}
.gf-strata i{flex:1;background:#EAE4D6;border:1px solid rgba(20,20,20,.15);border-bottom:0;
  border-radius:4px 4px 0 0;transition:.22s;}
.gf-strata i.dig{background:var(--lima);border-color:var(--tinta);}
.gf-axis{display:flex;justify-content:space-between;font-size:11.5px;color:var(--mute);
  margin-top:7px;font-weight:600;}

/* ---------- métricas ---------- */
.gf-sec{display:flex;align-items:center;gap:12px;margin:30px 0 12px;flex-wrap:wrap;}
.gf-sec h3{font-family:var(--d);font-size:24px;font-weight:600;margin:0;}
.gf-sec p{margin:0;font-size:13.5px;color:var(--mute);}
.gf-metrics{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px;}
.gf-met{background:#fff;border:2px solid var(--tinta);border-radius:18px;padding:14px 18px;
  box-shadow:4px 4px 0 var(--tinta);}
.gf-met.a{background:var(--lima);} .gf-met.b{background:var(--peri);}
.gf-met p{margin:0;font-size:12px;font-weight:800;}
.gf-met strong{display:block;font-family:var(--d);font-size:34px;font-weight:700;
  letter-spacing:-.02em;margin:2px 0 3px;}
.gf-met small{font-size:11.5px;line-height:1.4;display:block;color:var(--mute);}
.gf-met.modelo strong{color:var(--verde-esc);}
.gf-met.modelo p:after{content:"MODELO";font-size:9px;letter-spacing:.08em;background:var(--tinta);
  color:#fff;border-radius:99px;padding:2px 7px;margin-left:7px;vertical-align:2px;}

/* ---------- faixas ---------- */
.gf-gtop{display:flex;align-items:center;gap:13px;}
.gf-gtop .txt{flex:1;min-width:0;}
.gf-gtop b{display:block;font-family:var(--d);font-size:17px;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gf-gtop i{display:block;font-style:normal;font-size:13px;color:var(--mute);
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.gf-gtop .mt{text-align:right;flex:none;}
.gf-gtop .mt strong{display:block;font-family:var(--d);font-size:23px;font-weight:700;line-height:1.05;}
.gf-gtop .mt small{font-size:10.5px;color:var(--mute);font-weight:700;}
.gf-meta{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px;}
.gf-badge{border:2px solid var(--tinta);border-radius:99px;padding:2px 10px;font-weight:700;
  font-size:11.5px;background:#fff;}
.gf-attr{display:flex;align-items:center;gap:10px;font-size:12.5px;color:var(--mute);margin-bottom:8px;}
.gf-attr span{width:118px;flex:none;color:var(--tinta);font-weight:700;}
.gf-attr i{flex:1;height:9px;background:#fff;border:2px solid var(--tinta);border-radius:99px;
  display:block;overflow:hidden;}
.gf-attr i b{display:block;height:100%;background:var(--rosa);}
.gf-attr em{font-style:normal;width:30px;text-align:right;flex:none;font-weight:700;color:var(--tinta);}
.gf-why{font-size:12.5px;color:var(--mute);margin:10px 0 0;}
.gf-empty{text-align:center;padding:34px;}
.gf-empty p{margin:0;font-family:var(--d);font-size:20px;}

/* ---------- conta ---------- */
.gf-who{display:flex;align-items:center;gap:14px;flex-wrap:wrap;}
.gf-avatar{width:54px;height:54px;border-radius:50%;background:var(--rosa);
  border:2px solid var(--tinta);display:grid;place-items:center;font-family:var(--d);
  font-size:22px;font-weight:700;}
.gf-who strong{display:block;font-family:var(--d);font-size:20px;font-weight:600;}
.gf-who span{font-size:13px;color:var(--mute);}
.gf-pill{margin-left:auto;background:var(--lima);border:2px solid var(--tinta);border-radius:99px;
  padding:6px 15px;font-size:12px;font-weight:800;}
.gf-tops{display:flex;gap:9px;flex-wrap:wrap;margin-top:10px;}
.gf-top{background:#fff;border:2px solid var(--tinta);border-radius:99px;padding:7px 15px;
  font-size:13px;font-weight:700;}
.gf-top s{text-decoration:none;color:var(--mute);font-weight:500;}
.gf-perm{margin:14px 0 4px;padding:0;list-style:none;}
.gf-perm li{font-size:13.5px;color:var(--mute);padding-left:24px;position:relative;margin-bottom:5px;}
.gf-perm li:before{content:"✓";position:absolute;left:0;color:var(--verde-esc);font-weight:800;}

/* ---------- widgets do streamlit ---------- */
.stButton > button{
  border:2px solid var(--tinta) !important;border-radius:99px;background:#fff;color:var(--tinta);
  font-family:var(--d);font-weight:600;font-size:15px;padding:9px 24px;
  box-shadow:4px 4px 0 var(--tinta);transition:.14s;
}
.stButton > button:hover{transform:translate(-2px,-2px);box-shadow:6px 6px 0 var(--tinta);
  color:var(--tinta);background:#fff;}
.stButton > button[kind="primary"], .stButton > button[data-testid="stBaseButton-primary"]{
  background:var(--verde) !important;color:#fff !important;}
.stButton > button[kind="primary"]:hover, .stButton > button[data-testid="stBaseButton-primary"]:hover{
  background:var(--verde) !important;color:#fff !important;}
[data-baseweb="input"], [data-baseweb="base-input"]{background:#fff !important;}
[data-testid="stTextInput"] [data-baseweb="input"]{border:2px solid var(--tinta) !important;
  border-radius:99px;padding:2px 8px;}
[data-baseweb="select"] > div{border:2px solid var(--tinta) !important;border-radius:14px;
  background:#fff !important;}
[data-baseweb="tag"]{background:var(--lima) !important;color:var(--tinta) !important;
  border:2px solid var(--tinta) !important;border-radius:99px !important;font-weight:700;}
[data-baseweb="tag"] span{color:var(--tinta) !important;}
[data-testid="stSegmentedControl"] button{border:2px solid var(--tinta) !important;font-weight:700;}
[data-testid="stSegmentedControl"] button[aria-checked="true"],
[data-testid="stSegmentedControl"] button[data-testid="stBaseButton-segmented_controlActive"]{
  background:var(--tinta) !important;color:#fff !important;}
[data-testid="stSlider"] [role="slider"]{background:var(--rosa) !important;
  border:2px solid var(--tinta) !important;box-shadow:none !important;}
[data-testid="stExpander"]{border:none !important;background:transparent !important;}
[data-testid="stExpander"] details, [data-testid="stExpander"] > div:first-child{
  border:none !important;background:transparent !important;box-shadow:none !important;}
[data-testid="stExpander"] summary{border-top:2px dashed rgba(20,20,20,.18);
  padding:8px 0 4px !important;font-weight:700;font-size:12.5px;color:var(--mute);}
[data-testid="stExpander"] summary:hover{color:var(--tinta);}
[data-testid="stAlert"], [data-testid="stNotification"]{border:2px solid var(--tinta);
  border-radius:16px;box-shadow:3px 3px 0 var(--tinta);}
[data-testid="stStatusWidget"], [data-testid="stExpanderDetails"]{background:transparent;}
.stCode, pre{border-radius:14px !important;}
[data-testid="stCaptionContainer"]{color:var(--mute);}

/* ---------- mascote ---------- */
.gf-mascote{display:block;}
.gf-mascote .eye{animation:gfBlink 5s infinite;}
.gf-mascote .eye.b{animation-delay:.15s;}
@keyframes gfBlink{0%,94%,100%{transform:scaleY(1)}97%{transform:scaleY(.1)}}

@media (max-width:1000px){
  .gf-title{font-size:29px;}
  .gf-metrics{grid-template-columns:1fr 1fr;}
}
@media (prefers-reduced-motion:reduce){*{animation:none !important;transition:none !important}}
</style>
"""


# --- 3.3 blocos de HTML ------------------------------------------------------

def bloco(html: str) -> None:
    """Injeta um trecho de HTML cru na página."""
    st.markdown(html, unsafe_allow_html=True)


def container_com_chave(chave: str):
    """Container com classe CSS `st-key-<chave>` (degrada em Streamlit antigo)."""
    try:
        return st.container(key=chave)
    except TypeError:  # pragma: no cover - versões sem suporte a `key`
        return st.container()


def cartao(nome: str):
    """Container com visual de sticker: borda preta de 2px e sombra deslocada."""
    return container_com_chave(f"cartao-{nome}")


def hero(svg: str, titulo: str, lede: str, balao: str) -> None:
    """Cabeçalho da página: mascote, título, subtítulo e balão de fala."""
    bloco(f'<div class="gf-hero">{svg}<div><h2 class="gf-title">{titulo}</h2>'
          f'<p class="gf-lede">{lede}</p></div><div class="gf-bubble">{balao}</div></div>')


def passo(numero: str, titulo: str, ajuda: str) -> None:
    """Cabeçalho numerado de um passo do fluxo."""
    bloco(f'<div class="gf-step"><b>{numero}</b><h3>{titulo}</h3></div>'
          f'<p class="gf-help">{ajuda}</p>')


def strata_html(teto: int) -> str:
    """Distribuição de popularidade do catálogo indexado, com a faixa liberada em lima.

    A curva representa as 114.000 faixas indexadas (dado simulado do protótipo);
    as barras em lima são a fatia que passa no teto escolhido no slider.
    """
    barras = []
    for i in range(40):
        popularidade = i * 2.5
        altura = max(12.0, math.exp(-((popularidade - 34) ** 2) / 900) * 100)
        classe = "dig" if popularidade <= teto else ""
        barras.append(f'<i class="{classe}" style="height:{altura:.1f}%"></i>')
    return (f'<div class="gf-strata">{"".join(barras)}</div>'
            '<div class="gf-axis"><span>0 · desconhecido</span><span>50</span>'
            '<span>100 · mainstream</span></div>')


def barras_atributos_html(valores: Mapping[str, Any]) -> str:
    """As 5 barras de atributo de áudio (0–100)."""
    linhas = []
    for chave, rotulo in ROTULOS_ATRIBUTOS:
        valor = _round_js(float(valores[chave]) * 100)
        linhas.append(f'<div class="gf-attr"><span>{rotulo}</span>'
                      f'<i><b style="width:{valor}%"></b></i><em>{valor}</em></div>')
    return "".join(linhas)


def metricas_html(resultado: Mapping[str, Any]) -> str:
    """Linha com as 4 métricas; as duas do modelo levam o selo MODELO."""
    return (
        '<div class="gf-metrics">'
        f'<div class="gf-met a"><p>Joias encontradas</p><strong>{len(resultado["faixas"])}</strong>'
        '<small>as 8 melhores do ranking</small></div>'
        f'<div class="gf-met b"><p>Match médio</p><strong>{resultado["media_match"]}%</strong>'
        f'<small>{resultado["sub_match"]}</small></div>'
        f'<div class="gf-met modelo"><p>Precisão @8</p><strong>{resultado["precisao"]}%</strong>'
        '<small>sugestões aprovadas nos testes com usuários</small></div>'
        f'<div class="gf-met modelo"><p>Cobertura</p><strong>{resultado["cobertura"]}%</strong>'
        f'<small>{resultado["sub_cobertura"]}</small></div>'
        '</div>'
    )


def gema_topo_html(faixa: Mapping[str, Any]) -> str:
    """Topo do card de uma faixa: mascote, nome, match e selos."""
    selo, cor = rar(int(faixa["popularidade"]))
    return (
        f'<div class="gf-gtop">{mascote(cor, humor_da_faixa(faixa), 44)}'
        f'<span class="txt"><b>{faixa["faixa"]}</b>'
        f'<i>{faixa["artista"]} · {faixa["cidade"]}, {faixa["ano"]}</i></span>'
        f'<span class="mt"><strong>{faixa["match"]}%</strong><small>match</small></span></div>'
        f'<div class="gf-meta"><span class="gf-badge" style="background:{cor}">{selo}</span>'
        f'<span class="gf-badge">{faixa["genero"]}</span>'
        f'<span class="gf-badge">pop {faixa["popularidade"]}</span>'
        f'<span class="gf-badge">{faixa["bpm"]} BPM</span></div>'
    )


def estado_vazio_html(dica: str) -> str:
    """Cartão de estado vazio, com a Pepita neutra explicando o que fazer."""
    return (f'<div class="gf-card gf-empty">{mascote(PERI, "triste", 70)}'
            '<p>Nada nessa profundidade.</p>'
            f'<p class="gf-help" style="margin-top:6px">{dica}</p></div>')


# --- 3.4 estado --------------------------------------------------------------

PADROES: dict[str, Any] = {
    "modo": MODOS[0],
    "vibe": "foco",
    "genero": "",
    "favoritos": [],
    "teto": 18,
    "res_desc": None,
    "pl_desc": None,
    "conectado": False,
    "email": "",
    "res_conta": None,
    "pl_conta": None,
    "festa_conta": False,
}


def iniciar_estado(generos: list[str]) -> None:
    """Garante as chaves do session_state na primeira execução."""
    for chave, valor in PADROES.items():
        st.session_state.setdefault(chave, valor.copy() if isinstance(valor, list) else valor)
    if not st.session_state.genero:
        st.session_state.genero = generos[0]


def limpar_conta() -> None:
    """Desconecta o testador e volta o session_state da conta ao início."""
    for chave in ("conectado", "email", "res_conta", "pl_conta", "festa_conta"):
        st.session_state[chave] = PADROES[chave]
    st.session_state.pop("w_email", None)


# --- 3.5 sidebar -------------------------------------------------------------

def barra_lateral(catalogo: pd.DataFrame, artistas: pd.DataFrame) -> str:
    """Marca, navegação entre as duas páginas e rodapé. Devolve a página ativa."""
    with st.sidebar:
        bloco(f'<div class="gf-brand">{LOGO}<div><h1>Gems Finder</h1>'
              '<small>joias ocultas do Spotify</small></div></div>')
        bloco('<p class="gf-nav-label">Navegação</p>')
        pagina = st.radio("Navegação", PAGINAS, key="w_nav", label_visibility="collapsed")
        bloco('<div class="gf-rail-foot"><b>114.000</b> faixas indexadas<br>'
              f'<b>{catalogo["genero"].nunique()}</b> gêneros · '
              f'<b>{len(artistas)}</b> artistas de referência<br><br>'
              'Residência em IA · UnB</div>')
    return pagina


# --- 3.6 página 1: descobrir -------------------------------------------------

def seletor_modo() -> str:
    """Segmented control com os três modos de busca (radio como reserva)."""
    atual = st.session_state.modo
    if hasattr(st, "segmented_control"):
        escolha = st.segmented_control("Modo de busca", MODOS, default=atual,
                                       key="w_modo", label_visibility="collapsed")
        return escolha or atual
    return st.radio("Modo de busca", MODOS, index=MODOS.index(atual), horizontal=True,
                    key="w_modo", label_visibility="collapsed")


def _selecao_vibe() -> None:
    """Os 4 cards de vibe, um por coluna."""
    for coluna, (chave, vibe) in zip(st.columns(4), VIBES.items()):
        with coluna:
            escolhida = st.session_state.vibe == chave
            fundo = vibe["cor"] if escolhida else "#fff"
            bloco(f'<div class="gf-vibe" style="background:{fundo}">'
                  f'{mascote(vibe["cor"], vibe["humor"], 56)}<strong>{vibe["nome"]}</strong>'
                  f'<span>{vibe["desc"]}</span></div>')
            sufixo = "-on" if escolhida else ""
            with container_com_chave(f"btnvibe-{chave}{sufixo}"):
                if st.button("Escolhida ✓" if escolhida else "Escolher",
                             key=f"btn_vibe_{chave}"):
                    st.session_state.vibe = chave
                    st.rerun()


def _selecao_genero(catalogo: pd.DataFrame, generos: list[str]) -> None:
    """Selectbox com os 12 gêneros e a contagem de faixas de cada um."""
    contagem = catalogo["genero"].value_counts()
    atual = st.session_state.genero if st.session_state.genero in generos else generos[0]
    escolha = st.selectbox(
        "Gênero", generos, index=generos.index(atual),
        format_func=lambda g: f"{g} · {contagem[g]} faixas",
        key="w_genero", label_visibility="collapsed",
    )
    st.session_state.genero = escolha


def _selecao_artista(artistas: pd.DataFrame) -> None:
    """Multiselect de até 3 artistas de referência."""
    nomes = artistas["artista"].tolist()
    generos = dict(zip(artistas["artista"], artistas["genero"]))
    escolha = st.multiselect(
        "Artistas favoritos", nomes,
        default=[n for n in st.session_state.favoritos if n in nomes],
        max_selections=3, format_func=lambda n: f"{n} · {generos[n]}",
        key="w_favoritos", label_visibility="collapsed",
    )
    st.session_state.favoritos = escolha
    if escolha:
        st.caption(f"{len(escolha)} de 3 escolhidos: {', '.join(escolha)}")
    else:
        st.caption("Escolha de 1 a 3 artistas.")


def _texto_alvo(modo: str) -> str:
    """Frase que resume o alvo da busca, exibida no passo 3."""
    if modo == "Por vibe":
        return f"vibe <b>{VIBES[st.session_state.vibe]['nome']}</b>"
    if modo == "Por gênero":
        return f"gênero <b>{st.session_state.genero}</b>"
    favoritos = st.session_state.favoritos
    if favoritos:
        return f"parecido com <b>{', '.join(favoritos)}</b>"
    return "<b>escolha pelo menos um artista</b>"


def pagina_descobrir(catalogo: pd.DataFrame, artistas: pd.DataFrame,
                     generos: list[str]) -> None:
    """Fluxo público de garimpo, em 4 passos."""
    hero(mascote(LIMA, "feliz", 92), "Bora garimpar?",
         "Me diz o que você curte e eu cavo 114 mil faixas atrás das joias que "
         "quase ninguém ouviu ainda.", "Escolhe aí embaixo 👇")

    # ---- passo 1: de onde partir
    with cartao("passo1"):
        passo("PASSO 1", "De onde a gente parte?",
              "Três caminhos pro mesmo tesouro: pela <b>sensação</b> que a música dá, "
              "pelo <b>gênero</b>, ou pelos <b>artistas que você já ama</b>.")
        modo = seletor_modo()
        st.session_state.modo = modo
        if modo == "Por vibe":
            _selecao_vibe()
        elif modo == "Por gênero":
            _selecao_genero(catalogo, generos)
        else:
            _selecao_artista(artistas)

    # ---- passo 2: profundidade
    with cartao("passo2"):
        passo("PASSO 2", "Quão escondida você aceita?",
              "A popularidade do Spotify vai de 0 (ninguém ouviu) a 100 (hit mundial). "
              "Abaixo de 30 já é território de garimpo.")
        esquerda, direita = st.columns([1, 2.6])
        with esquerda:
            caixa_numero = st.empty()
        with direita:
            caixa_strata = st.empty()
            teto = st.slider("Popularidade máxima", 1, 40, st.session_state.teto,
                             key="w_teto", label_visibility="collapsed")
        st.session_state.teto = teto
        caixa_numero.markdown(
            f'<div class="gf-num">{teto}<span> /100</span></div>'
            f'<p class="gf-help" style="margin:2px 0 0">{rotulo_profundidade(teto)}</p>',
            unsafe_allow_html=True)
        caixa_strata.markdown(strata_html(teto), unsafe_allow_html=True)

    # ---- passo 3: garimpar
    with cartao("passo3"):
        passo("PASSO 3", "Garimpe!",
              "O modelo compara os atributos de áudio de cada faixa com o seu alvo "
              "e ranqueia por afinidade.")
        bloco(f'<p class="gf-status">Buscando {_texto_alvo(modo)}, com popularidade '
              f'até <b>{teto}</b>.</p>')
        if st.button("Garimpar joias", type="primary", key="btn_garimpar"):
            if modo == "Por artista favorito" and not st.session_state.favoritos:
                st.warning("Escolhe pelo menos um artista pra eu saber por onde cavar!",
                           icon="⛏️")
            else:
                with st.spinner("Garimpando…"):
                    time.sleep(1.15)
                st.session_state.res_desc = montar_resultado(
                    catalogo, artistas, modo, st.session_state.vibe,
                    st.session_state.genero, st.session_state.favoritos, teto)
                st.session_state.pl_desc = None
                achadas = len(st.session_state.res_desc["faixas"])
                if achadas:
                    st.toast(f"{achadas} joias encontradas!", icon="💎")

    if st.session_state.res_desc:
        mostrar_resultados(
            st.session_state.res_desc, "desc",
            dica_vazia="Cavei fundo e não achei nada aqui. Aumenta a popularidade "
                       "máxima no passo 2 ou troca a escolha do passo 1.")


# --- 3.7 resultados + playlist (compartilhado pelas duas páginas) ------------

def mostrar_resultados(resultado: Mapping[str, Any], espaco: str, dica_vazia: str) -> None:
    """Métricas do modelo, cards das joias e o gerador de playlist."""
    if not resultado["faixas"]:
        bloco(estado_vazio_html(dica_vazia))
        return

    bloco(f'<div class="gf-sec">{mascote(resultado["cor"], "feliz", 52)}'
          f'<h3>{resultado["titulo"]}</h3><p>{resultado["legenda"]}</p></div>')
    bloco(metricas_html(resultado))

    colunas = st.columns(2)
    for indice, faixa in enumerate(resultado["faixas"]):
        with colunas[indice % 2]:
            with container_com_chave(f"gema-{espaco}-{indice}"):
                bloco(gema_topo_html(faixa))
                with st.expander("Ver atributos de áudio"):
                    bloco(barras_atributos_html(faixa)
                          + f'<p class="gf-why">Entrou porque {resultado["ctx"]} — e só '
                            f'{faixa["popularidade"]} de 100 no índice de popularidade.</p>')

    secao_playlist(resultado, espaco)


def secao_playlist(resultado: Mapping[str, Any], espaco: str) -> None:
    """Passo final: gera o link fictício da playlist privada."""
    numero = "PASSO 4" if espaco == "desc" else "ÚLTIMO PASSO"
    with cartao(f"playlist-{espaco}"):
        passo(numero, "Leva com você",
              "Criamos uma playlist privada na sua conta com as 8 faixas acima.")
        chave_url = f"pl_{espaco}"
        if st.button("Gerar playlist", type="primary", key=f"btn_pl_{espaco}"):
            with st.spinner("Criando…"):
                time.sleep(0.9)
            # TODO: aqui entraria a chamada real da Spotify Web API, com o token OAuth:
            #   POST https://api.spotify.com/v1/users/{user_id}/playlists  -> cria a playlist
            #   POST https://api.spotify.com/v1/playlists/{playlist_id}/tracks -> adiciona as faixas
            st.session_state[chave_url] = f"open.spotify.com/playlist/{novo_id_playlist()}"
            st.success(f"Playlist criada! Guardei suas {len(resultado['faixas'])} joias "
                       f"em «{resultado['titulo']}» — é só abrir o link.", icon="💎")
            st.balloons()

        url = st.session_state.get(chave_url)
        if url:
            st.caption(f"**{resultado['titulo']}** · {len(resultado['faixas'])} faixas →")
            st.code(f"https://{url}", language=None)
        else:
            st.caption("O link aparece aqui depois de gerar")


# --- 3.8 página 2: minha conta ----------------------------------------------

def _tela_login() -> None:
    """Formulário de e-mail, permissões e simulação das 4 etapas do OAuth."""
    with cartao("login"):
        passo("PASSO 1", "Entrar com o Spotify",
              "Use o e-mail cadastrado na lista de testes da residência.")
        email = st.text_input("E-mail", value=st.session_state.email,
                              placeholder="voce@aluno.unb.br", key="w_email",
                              label_visibility="collapsed")
        st.session_state.email = email
        bloco('<ul class="gf-perm">'
              + "".join(f"<li>{permissao}</li>" for permissao in PERMISSOES)
              + "</ul>")
        if st.button("Conectar Spotify", type="primary", key="btn_auth"):
            if not email_valido(email):
                st.error("Digite um e-mail válido para continuar.", icon="✉️")
                return
            # TODO: aqui entraria o fluxo real de OAuth (Authorization Code + PKCE):
            #   GET https://accounts.spotify.com/authorize  -> consentimento
            #   POST https://accounts.spotify.com/api/token -> troca do code pelo token
            with st.status("Conectando na sua conta…", expanded=True) as estado:
                for etapa in ETAPAS_OAUTH:
                    st.write(f"✓ {etapa}")
                    time.sleep(0.47)
                estado.update(label="Tudo pronto, já sei o que você ouve!",
                              state="complete", expanded=False)
            st.session_state.conectado = True
            st.session_state.res_conta = montar_resultado_conta(carregar_catalogo())
            st.session_state.pl_conta = None
            st.session_state.festa_conta = True
            st.rerun()


def _tela_conectado() -> None:
    """Perfil do testador, mais ouvidas, métricas e joias recomendadas."""
    if st.session_state.festa_conta:
        st.session_state.festa_conta = False
        st.balloons()

    email = st.session_state.email
    nome = nome_do_email(email) or "Testador"
    with cartao("perfil"):
        bloco(f'<div class="gf-who"><div class="gf-avatar">{nome[0]}</div>'
              f'<div><strong>Oi, {nome}!</strong><span>{email}</span></div>'
              '<span class="gf-pill">Conectado</span></div>'
              '<p class="gf-help" style="margin:20px 0 0"><b>Suas 5 mais ouvidas</b> — '
              'foi daqui que saiu seu perfil de áudio.</p>'
              '<div class="gf-tops">'
              + "".join(f'<span class="gf-top">{titulo} <s>· {artista}</s></span>'
                        for titulo, artista in TOPS)
              + '</div>'
              '<p class="gf-help" style="margin:18px 0 8px">Perfil detectado: '
              '<b>energia alta com humor baixo</b> — você curte música intensa e melancólica.</p>'
              + barras_atributos_html(PERFIL_USUARIO))

    mostrar_resultados(
        st.session_state.res_conta, "conta",
        dica_vazia="Cavei fundo e não achei nada que combine com o seu perfil "
                   "nessa profundidade.")

    if st.button("Desconectar", key="btn_out"):
        limpar_conta()
        st.rerun()


def pagina_conta() -> None:
    """Modo dos testadores: login simulado e recomendações pelo perfil de áudio."""
    hero(mascote(ROSA, "chill", 88), "Deixa eu ouvir o que você ouve",
         "Modo dos testadores. Conectamos na sua conta, lemos suas mais ouvidas, "
         "montamos seu perfil de áudio e devolvemos só o que é raro e combina.",
         "Só leitura, prometo 🎧")
    if st.session_state.conectado:
        _tela_conectado()
    else:
        _tela_login()


# --- 3.9 entrada -------------------------------------------------------------

def main() -> None:
    """Monta a página e roteia entre Descobrir e Minha conta."""
    st.set_page_config(page_title="Gems Finder", page_icon="💎", layout="wide",
                       initial_sidebar_state="expanded")
    bloco(CSS)

    catalogo = carregar_catalogo()
    artistas = carregar_artistas()
    generos = listar_generos(catalogo)
    iniciar_estado(generos)

    pagina = barra_lateral(catalogo, artistas)
    if pagina == PAGINAS[0]:
        pagina_descobrir(catalogo, artistas, generos)
    else:
        pagina_conta()


if __name__ == "__main__":
    main()
