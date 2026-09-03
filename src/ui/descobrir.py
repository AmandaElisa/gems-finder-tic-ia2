"""Página Descobrir — o fluxo público de garimpo em 4 passos."""

from __future__ import annotations

import time

import pandas as pd
from typing import Any, Mapping

import streamlit as st

from src.dados import VIBES, contar_por_genero
from src.recomendacao import montar_resultado, rotulo_profundidade, texto_status
from src.tema import LIMA
from src.ui.componentes import (bloco, cartao, container_com_chave, hero,
                                numero_pt, passo, strata_html)
from src.ui.mascote import mascote
from src.ui.resultados import mostrar_resultados


def _alternar(selecionados: list[str], valor: str) -> None:
    """Liga ou desliga um item na lista de selecionados do passo 1."""
    if valor in selecionados:
        selecionados.remove(valor)
    else:
        selecionados.append(valor)


def _grupo(titulo: str, nota: str) -> None:
    """Rótulo de um dos três grupos opcionais do passo 1."""
    bloco(f'<p class="gf-grupo">{titulo} <span>{nota}</span></p>')


def _dica_vazia(resultado: Mapping[str, Any]) -> str:
    """Dica do estado vazio, dizendo até quanto subir o slider.

    Alguns gêneros deste catálogo só existem acima de certa popularidade, e a
    dica genérica deixava a pessoa subindo o slider às cegas.
    """
    minimo = resultado.get("teto_minimo")
    if minimo is None:
        return ("Cavei fundo e não achei joia nenhuma com esses critérios — "
                "nem subindo a popularidade. Tenta trocar os critérios do passo 1.")
    return (f"Cavei fundo e não achei nada nessa profundidade. Aqui as joias "
            f"começam em <b>{minimo}</b> de popularidade — sobe o slider do "
            f"passo 2 até lá.")

def _selecao_vibe() -> None:
    """Os 4 cards de vibe, um por coluna — o card inteiro é clicável, e alterna."""
    for coluna, (chave, vibe) in zip(st.columns(len(VIBES)), VIBES.items()):
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
    """Chips de gênero com a contagem de faixas — os escolhidos ficam em lima."""
    contagem = contar_por_genero(catalogo)
    with container_com_chave("chips-generos"):
        for genero in generos:
            escolhido = genero in st.session_state.generos
            if st.button(f"{genero} :gray[{numero_pt(contagem[genero])} faixas]",
                         key=f"chip_gen_{genero}",
                         type="primary" if escolhido else "secondary"):
                _alternar(st.session_state.generos, genero)
                st.rerun()


def _selecao_artista(artistas: pd.DataFrame) -> None:
    """Chips de artistas de referência, com toggle e máximo de 3."""
    generos = dict(zip(artistas["artista"], artistas["genero"]))
    favoritos = st.session_state.favoritos

    with container_com_chave("chips-artistas"):
        for nome in artistas["artista"]:
            escolhido = nome in favoritos
            if st.button(f"{nome} :gray[{generos[nome]}]",
                         key=f"chip_art_{nome}",
                         type="primary" if escolhido else "secondary"):
                if escolhido:
                    favoritos.remove(nome)
                    st.rerun()
                elif len(favoritos) >= 3:
                    st.toast("Máximo de 3 artistas", icon="✋")
                else:
                    favoritos.append(nome)
                    st.rerun()

    if favoritos:
        st.caption(f"{len(favoritos)} de 3 escolhidos: {', '.join(favoritos)}")
    else:
        st.caption("Nenhum artista escolhido ainda.")


def pagina_descobrir(catalogo: pd.DataFrame, artistas: pd.DataFrame,
                     generos: list[str]) -> None:
    """Fluxo público de garimpo, em 4 passos."""
    hero(mascote(LIMA, "feliz", 92), "Bora garimpar?",
         "Me diz o que você curte e eu cavo 114 mil faixas atrás das joias que "
         "quase ninguém ouviu ainda.", "Escolhe aí embaixo 👇")

    # ---- passo 1: de onde partir
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
        vibes, generos_sel = st.session_state.vibes, st.session_state.generos
        favoritos = st.session_state.favoritos
        tem_criterio = bool(vibes or generos_sel or favoritos)
        # sem critério o botão fica travado, e a frase acima diz o porquê
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

    if st.session_state.res_desc:
        mostrar_resultados(
            st.session_state.res_desc, "desc",
            dica_vazia=_dica_vazia(st.session_state.res_desc))
