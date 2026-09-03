"""Componentes visuais reutilizáveis: cartões, hero, passos, métricas e barras."""

from __future__ import annotations

import math
from typing import Any, Mapping

import streamlit as st

from src.dados import ROTULOS_ATRIBUTOS
from src.recomendacao import humor_da_faixa, rar, round_js
from src.tema import PERI
from src.ui.mascote import mascote


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
        valor = round_js(float(valores[chave]) * 100)
        linhas.append(f'<div class="gf-attr"><span>{rotulo}</span>'
                      f'<i><b style="width:{valor}%"></b></i><em>{valor}</em></div>')
    return "".join(linhas)


def metricas_html(resultado: Mapping[str, Any]) -> str:
    """Linha com as métricas; a Cobertura leva o selo MODELO por ser medida.

    A Precisão @8 saiu daqui. Ela era um placeholder herdado do protótipo, e a
    legenda afirmava "sugestões aprovadas nos testes com usuários" — teste que
    nunca aconteceu. Métrica fabricada é pior que métrica ausente; volta quando
    houver protocolo de avaliação escrito.
    """
    return (
        '<div class="gf-metrics">'
        f'<div class="gf-met a"><p>Joias encontradas</p><strong>{len(resultado["faixas"])}</strong>'
        '<small>as 8 melhores do ranking</small></div>'
        f'<div class="gf-met b"><p>Match médio</p><strong>{resultado["media_match"]}%</strong>'
        f'<small>{resultado["sub_match"]}</small></div>'
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
        f'<i>{faixa["artista"]}</i></span>'
        f'<span class="mt"><strong>{faixa["match"]}%</strong><small>match</small></span></div>'
        f'<div class="gf-meta"><span class="gf-badge" style="background:{cor}">{selo}</span>'
        f'<span class="gf-badge">{faixa["genero"]}</span>'
        f'<span class="gf-badge">pop {faixa["popularidade"]}</span>'
        f'<span class="gf-badge">{round(float(faixa["bpm"]))} BPM</span>'
        f'{_link_spotify(faixa)}</div>'
    )


def _link_spotify(faixa: Mapping[str, Any]) -> str:
    """Selo que abre a faixa no Spotify, quando ela tem ID real.

    Não exige login de ninguém: o link de faixa é público. É o que permite
    levar a joia embora mesmo sem conta conectada — a playlist, que exige
    autorização de usuário, vive na aba Minha conta.
    """
    track_id = faixa.get("track_id")
    if not track_id:
        return ""
    return (f'<a class="gf-badge gf-ouvir" target="_blank" rel="noopener" '
            f'href="https://open.spotify.com/track/{track_id}">▶ Ouvir</a>')


def estado_vazio_html(dica: str) -> str:
    """Cartão de estado vazio, com a Pepita neutra explicando o que fazer."""
    return (f'<div class="gf-card gf-empty">{mascote(PERI, "triste", 70)}'
            '<p>Nada nessa profundidade.</p>'
            f'<p class="gf-help" style="margin-top:6px">{dica}</p></div>')
