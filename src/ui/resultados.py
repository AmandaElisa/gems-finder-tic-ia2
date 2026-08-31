"""Exibição dos resultados do garimpo e gerador de playlist fictícia."""

from __future__ import annotations

import time
from typing import Any, Mapping

import streamlit as st

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
