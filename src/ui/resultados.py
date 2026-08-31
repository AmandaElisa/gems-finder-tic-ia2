"""Exibição dos resultados do garimpo e gerador de playlist (real ou simulada)."""

from __future__ import annotations

import time
from typing import Any, Mapping

import requests
import streamlit as st

from src import spotify
from src.recomendacao import novo_id_playlist
from src.ui.componentes import (barras_atributos_html, bloco, cartao,
                                container_com_chave, estado_vazio_html,
                                gema_topo_html, metricas_html, passo)
from src.ui.mascote import mascote


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


def _gerar_playlist_real(resultado: Mapping[str, Any], chave_url: str) -> None:
    """Cria a playlist privada de verdade na conta conectada via Web API."""
    try:
        with st.spinner("Criando na sua conta…"):
            url = spotify.criar_playlist(
                st.session_state.token, st.session_state.sp_user["id"],
                f"Gems Finder · {resultado['titulo']}", resultado["faixas"])
    except requests.RequestException as erro:
        st.error(f"O Spotify não deixou criar a playlist: {erro}", icon="🚫")
        return
    st.session_state[chave_url] = url
    st.success(f"Playlist criada de verdade na sua conta! Como as {len(resultado['faixas'])} "
               "joias do catálogo são fictícias, ela nasce vazia com a lista na descrição.",
               icon="💎")
    st.balloons()


def _gerar_playlist_simulada(resultado: Mapping[str, Any], chave_url: str) -> None:
    """Fallback do protótipo: link fictício no formato do Spotify."""
    with st.spinner("Criando…"):
        time.sleep(0.9)
    st.session_state[chave_url] = f"https://open.spotify.com/playlist/{novo_id_playlist()}"
    st.success(f"Playlist criada! Guardei suas {len(resultado['faixas'])} joias "
               f"em «{resultado['titulo']}» — é só abrir o link.", icon="💎")
    st.balloons()


def secao_playlist(resultado: Mapping[str, Any], espaco: str) -> None:
    """Passo final: gera o link da playlist privada (real se conectado)."""
    numero = "PASSO 4" if espaco == "desc" else "ÚLTIMO PASSO"
    with cartao(f"playlist-{espaco}"):
        passo(numero, "Leva com você",
              "Criamos uma playlist privada na sua conta com as 8 faixas acima.")
        chave_url = f"pl_{espaco}"
        conectado_real = bool(st.session_state.get("token")) and st.session_state.get("sp_user")
        if st.button("Gerar playlist", type="primary", key=f"btn_pl_{espaco}"):
            if conectado_real:
                _gerar_playlist_real(resultado, chave_url)
            else:
                _gerar_playlist_simulada(resultado, chave_url)

        url = st.session_state.get(chave_url)
        if url:
            st.caption(f"**{resultado['titulo']}** · {len(resultado['faixas'])} faixas →")
            st.code(url, language=None)
        elif not conectado_real and spotify.config():
            st.caption("O link aparece aqui depois de gerar — conecta na aba "
                       "🎧 Minha conta pra criar a playlist de verdade.")
        else:
            st.caption("O link aparece aqui depois de gerar")
