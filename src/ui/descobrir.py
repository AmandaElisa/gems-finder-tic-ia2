"""Página Descobrir — o fluxo público de garimpo em 4 passos."""

from __future__ import annotations

import time

import pandas as pd
import streamlit as st

from src.dados import MODOS, VIBES
from src.recomendacao import montar_resultado, rotulo_profundidade
from src.tema import LIMA
from src.ui.componentes import bloco, cartao, container_com_chave, hero, passo, strata_html
from src.ui.mascote import mascote
from src.ui.resultados import mostrar_resultados


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
    """Os 4 cards de vibe, um por coluna — o card inteiro é clicável."""
    for coluna, (chave, vibe) in zip(st.columns(4), VIBES.items()):
        with coluna:
            escolhida = st.session_state.vibe == chave
            classe = "gf-vibe on" if escolhida else "gf-vibe"
            fundo = vibe["cor"] if escolhida else "#fff"
            with container_com_chave(f"vibecard-{chave}"):
                bloco(f'<div class="{classe}" style="background:{fundo}">'
                      f'{mascote(vibe["cor"], vibe["humor"], 56)}<strong>{vibe["nome"]}</strong>'
                      f'<span>{vibe["desc"]}</span></div>')
                # botão invisível cobrindo o card (o rótulo fica pro leitor de tela)
                if st.button(vibe["nome"], key=f"btn_vibe_{chave}"):
                    st.session_state.vibe = chave
                    st.rerun()


def _selecao_genero(catalogo: pd.DataFrame, generos: list[str]) -> None:
    """Chips com os 12 gêneros e a contagem de faixas — o escolhido fica em lima."""
    contagem = catalogo["genero"].value_counts()
    atual = st.session_state.genero if st.session_state.genero in generos else generos[0]
    with container_com_chave("chips-generos"):
        for genero in generos:
            escolhido = genero == atual
            if st.button(f"{genero} :gray[{contagem[genero]} faixas]",
                         key=f"chip_gen_{genero}",
                         type="primary" if escolhido else "secondary"):
                st.session_state.genero = genero
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
