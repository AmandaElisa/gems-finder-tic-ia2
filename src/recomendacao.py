"""Lógica de recomendação do Gems Finder.

Tradução fiel das funções match(), media(), centro() e rar() do protótipo
HTML, mais o garimpo (filtro + ranking) e as métricas exibidas na UI.
"""

from __future__ import annotations

import math
import re
from typing import Any, Mapping, NamedTuple, Sequence

import numpy as np
import pandas as pd

from src import artefatos
from src import generos as familias
from src.dados import ATRIBUTOS, PESOS, PERFIL_USUARIO, TETO_CONTA, VIBES
from src.tema import LIMA, PERI, ROSA


def round_js(valor: float) -> int:
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
    return max(31, min(99, round_js(bruto)))


def media(faixas: pd.DataFrame) -> dict[str, float]:
    """Média de cada atributo de áudio de um conjunto de faixas ou artistas."""
    return {atributo: float(faixas[atributo].mean()) for atributo in ATRIBUTOS}


def _do_genero(catalogo: pd.DataFrame, generos: Sequence[str]) -> pd.DataFrame:
    """Faixas que pertencem a qualquer um dos gêneros dados.

    Uma faixa pertence a vários gêneros, e a coluna `generos` guarda todos. A
    coluna `genero` é só o primeiro deles em ordem alfabética — estável para
    exibir, mas errada para filtrar: escolher "rock" perderia uma faixa cujos
    gêneros são ["alt-rock", "rock"]. Sem a lista, cai na coluna simples.
    """
    procurados = familias.expandir(generos)
    if "generos" in catalogo.columns:
        pertence = catalogo["generos"].apply(
            lambda lista: bool(procurados & set(lista)))
        return catalogo[pertence]
    return catalogo[catalogo["genero"].isin(list(procurados))]


def centro(catalogo: pd.DataFrame, genero: str) -> dict[str, float]:
    """Centroide de atributos de áudio das faixas de um gênero."""
    return media(_do_genero(catalogo, [genero]))


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
    return _do_genero(catalogo, generos)


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


def rar(popularidade: int) -> tuple[str, str]:
    """Selo de raridade e a cor correspondente, a partir da popularidade."""
    if popularidade <= 8:
        return "Joia bruta", LIMA
    if popularidade <= 17:
        return "Rara", ROSA
    return "Pouco ouvida", PERI


def elegiveis_para_garimpo(base: pd.DataFrame) -> pd.DataFrame:
    """Só as faixas que podem ser recomendadas.

    A coluna `elegivel` vem do catálogo processado e junta as três condições
    que o modelo definiu: popularidade acima do piso (popularidade 0 é faixa
    não capturada, não faixa sem streams), artista independente, e ser música
    e não conteúdo falado.

    É aqui que o diferencial de negócio chega ao app. Sem isso o garimpo
    devolve lado-B de artista consolidado, que tem popularidade baixa sem ser
    joia escondida de ninguém.

    Catálogo sem a coluna passa direto — é o caso dos testes, que montam
    DataFrames pequenos à mão.
    """
    if "elegivel" not in base.columns:
        return base
    return base[base["elegivel"]]


def garimpar(base: pd.DataFrame, alvo: Mapping[str, float], teto: int,
             limite: int = 8) -> pd.DataFrame:
    """Filtra por elegibilidade e popularidade <= teto, e ranqueia por match."""
    base = elegiveis_para_garimpo(base)
    elegiveis = base[base["popularidade"] <= teto].copy()
    if elegiveis.empty:
        return elegiveis.assign(match=pd.Series(dtype="int64"))
    elegiveis["match"] = [match(linha, alvo) for _, linha in elegiveis.iterrows()]
    # kind="stable" preserva a ordem do catálogo nos empates, como o sort do JS.
    return (elegiveis.sort_values("match", ascending=False, kind="stable")
            .head(limite).reset_index(drop=True))


def teto_minimo_util(base: pd.DataFrame) -> int | None:
    """Menor teto de popularidade que ainda devolve alguma joia neste universo.

    Existe porque alguns gêneros deste catálogo não têm cauda obscura: os
    quatro brasileiros só aparecem a partir de 23 a 43 de popularidade, então
    na posição padrão do slider eles vêm sempre vazios. Dizer "aumenta a
    popularidade" sem dizer até quanto deixa a pessoa tateando.

    Devolve None quando não há faixa elegível nenhuma — aí subir o slider não
    resolve, e a dica tem que ser outra.
    """
    elegiveis = elegiveis_para_garimpo(base)
    if elegiveis.empty:
        return None
    return int(elegiveis["popularidade"].min())


def cobertura(base: pd.DataFrame, teto: int) -> int:
    """% do universo elegível que passa no filtro de popularidade.

    Mede sobre o mesmo universo que o garimpo percorre, senão o número na
    tela descreveria uma busca diferente da que aconteceu.
    """
    base = elegiveis_para_garimpo(base)
    if base.empty:
        return 0
    return round_js(len(base[base["popularidade"] <= teto]) / len(base) * 100)


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
    """Expressão da mascote que combina com a faixa.

    Se a faixa já traz o mood do cluster, usamos a expressão daquele mood: a
    carinha ao lado do nome não pode discordar do rótulo mostrado logo abaixo
    dela. Sem essa coluna, cai nos limiares herdados do protótipo.
    """
    mood = faixa.get("mood")
    if mood:
        apresentacao = artefatos.APRESENTACAO.get(mood)
        if apresentacao:
            return apresentacao["humor"]

    if float(faixa["valencia"]) < .3:
        return "triste"
    if float(faixa["energia"]) > .75:
        return "treino"
    if float(faixa["instrumentalidade"]) > .7:
        return "foco"
    return "chill"


def email_valido(email: str) -> bool:
    """Valida o e-mail com a mesma regex do protótipo."""
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email.strip()))


def nome_do_email(email: str) -> str:
    """Deriva um nome apresentável a partir do trecho antes do @."""
    local = re.sub(r"[._-]", " ", email.split("@")[0])
    return re.sub(r"\b\w", lambda m: m.group().upper(), local).strip()


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
        "teto_minimo": teto_minimo_util(base),
        "titulo": "Joias — " + " · ".join(c.titulo for c in criterios),
        "ctx": " e ".join(c.ctx for c in criterios),
        "cobertura": cobertura(base, teto),
        "faixas": achadas.to_dict("records"),
        "media_match": round_js(achadas["match"].mean()) if len(achadas) else 0,
        "legenda": "Clique em cada faixa pra ver os atributos de áudio.",
        "sub_match": "afinidade com o alvo escolhido",
        "sub_cobertura": "do catálogo elegível cabe neste filtro",
        # com várias vibes não há uma cor só; o protótipo usa lima no cabeçalho
        "cor": VIBES[vibes[0]]["cor"] if len(vibes) == 1 else LIMA,
    }


def montar_resultado_conta(catalogo: pd.DataFrame) -> dict[str, Any]:
    """Garimpo do modo testador: cruza o perfil médio do usuário com o catálogo."""
    achadas = garimpar(catalogo, PERFIL_USUARIO, TETO_CONTA)
    return {
        "titulo": "Joias pra você",
        "ctx": "ela combina com o perfil médio das suas mais ouvidas",
        "cobertura": cobertura(catalogo, TETO_CONTA),
        "faixas": achadas.to_dict("records"),
        "media_match": round_js(achadas["match"].mean()) if len(achadas) else 0,
        "legenda": f"Nenhuma passa de {TETO_CONTA} de popularidade.",
        "sub_match": "afinidade com o seu perfil",
        "sub_cobertura": "do catálogo elegível para o seu perfil",
        "cor": ROSA,
    }
