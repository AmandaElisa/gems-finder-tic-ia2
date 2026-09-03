"""Exibição dos resultados do garimpo e gerador de playlist (real ou simulada)."""

from __future__ import annotations

from typing import Any, Mapping

import requests
import streamlit as st

from src import spotify
from src.ui.componentes import (barras_atributos_html, bloco, cartao,
                                container_com_chave, estado_vazio_html,
                                gema_topo_html, metricas_html, passo)
from src.ui.mascote import mascote


def _porque(faixa: Mapping[str, Any], ctx: str) -> str:
    """Por que esta joia apareceu — a semente concreta, quando existe.

    Nomear a faixa ou o artista que puxou a recomendação é grátis: quem
    garimpa por sementes já sabe quem foi. E é o que permite julgar o
    resultado, em vez de aceitar um número. Sem semente, a explicação
    continua sendo o critério geral da busca.
    """
    semente = faixa.get("semente")
    if semente:
        return f"Entrou por causa de <b>{semente}</b>"
    return f"Entrou porque {ctx}"


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
                          + f'<p class="gf-why">{_porque(faixa, resultado["ctx"])} — e só '
                            f'{faixa["popularidade"]} de 100 no índice de popularidade.</p>')

    # A playlist exige conta conectada, então mora na aba Minha conta. Aqui
    # cada joia tem seu link direto, que funciona sem login.
    if espaco != "desc":
        secao_playlist(resultado, espaco)


def _gerar_playlist_real(resultado: Mapping[str, Any], chave_url: str) -> None:
    """Cria a playlist privada de verdade na conta conectada via Web API."""
    try:
        with st.spinner("Criando na sua conta…"):
            url = spotify.criar_playlist(
                st.session_state.token, st.session_state.sp_user["id"],
                f"Gems Finder · {resultado['titulo']}", resultado["faixas"])
    except spotify.ErroDoSpotify as erro:
        st.error(f"O Spotify recusou **{erro.etapa}** ({erro.status}): "
                 f"{erro.motivo}", icon="🚫")
        _diagnostico(erro)
        _lista_para_copiar(resultado)
        return
    except requests.RequestException as erro:
        st.error(f"Não consegui falar com o Spotify: {erro}", icon="🚫")
        return
    st.session_state[chave_url] = url
    st.success(f"Playlist criada na sua conta com as {len(resultado['faixas'])} joias "
               "dentro, privada. É só abrir o link.", icon="💎")
    st.balloons()


def _diagnostico(erro: spotify.ErroDoSpotify) -> None:
    """Explica o 403 e mostra o estado real da conexão.

    O 403 daqui é limite de plataforma, não erro do app: desde a migração de
    março de 2026 o Spotify bloqueia operações de **escrita** para apps em
    Development Mode. Leitura continua funcionando — é por isso que as faixas
    mais ouvidas chegam e a playlist não nasce. Sair desse modo exige Extended
    Quota, hoje restrito a empresa registrada com 250 mil usuários ativos por
    mês, o que este projeto não tem como atender.

    Foi verificado que não é escopo (o token traz `playlist-modify-private`)
    nem lista de testadores (a conta está nela).
    """
    if erro.status not in (401, 403):
        return
    concedidos = st.session_state.get("escopos", "") or "(nenhum registrado)"
    usuario = (st.session_state.get("sp_user") or {}).get("id", "(sem id)")
    with st.expander("Por que isso acontece"):
        st.markdown(
            "Apps do Spotify em **modo de desenvolvimento** só podem **ler**. "
            "Criar playlist é escrita, e a plataforma bloqueia desde março de "
            "2026. Liberar exige *Extended Quota*, que hoje pede empresa "
            "registrada com 250 mil usuários ativos por mês.\n\n"
            "Já verificado, e **não** é a causa:\n"
            f"- Escopos concedidos: `{concedidos}` — a permissão de playlist está lá\n"
            f"- Escopos pedidos: `{spotify.ESCOPOS}`\n"
            f"- Usuário: `{usuario}`, presente na lista de testadores do app\n\n"
            "As oito joias continuam abaixo, com link direto pra cada uma.")


def _lista_para_copiar(resultado: Mapping[str, Any]) -> None:
    """As joias em links, que é o que sobra quando a escrita está bloqueada.

    Link de faixa não precisa de login nem de permissão — é leitura pura —
    então esta é a única forma de "levar com você" que a plataforma permite.
    """
    faixas = resultado.get("faixas") or []
    urls = [f"https://open.spotify.com/track/{f['track_id']}"
            for f in faixas if f.get("track_id")]
    if not urls:
        return
    st.caption("Copie e cole no Spotify pra montar a playlist na mão:")
    st.code("\n".join(urls), language=None)


def _pedir_conexao(resultado: Mapping[str, Any]) -> None:
    """Sem conta conectada não há playlist — e não inventamos link.

    A versão anterior gerava uma URL fictícia no formato do Spotify. Ela
    parecia real, abria em "playlist não disponível", e a pessoa achava que
    tinha perdido a playlist. Prometer o que não existe é justamente o que o
    princípio 2 da constituição proíbe.
    """
    st.info(
        f"Pra levar estas {len(resultado['faixas'])} joias, conecte sua conta "
        "do Spotify em **🎧 Minha conta** — a playlist é criada lá, privada e "
        "já com as faixas dentro.",
        icon="🔗",
    )


def secao_playlist(resultado: Mapping[str, Any], espaco: str) -> None:
    """Passo final: gera o link da playlist privada (real se conectado)."""
    numero = "PASSO 4" if espaco == "desc" else "ÚLTIMO PASSO"
    with cartao(f"playlist-{espaco}"):
        passo(numero, "Leva com você",
              "Criamos uma playlist privada na sua conta com as 8 faixas acima.")
        chave_url = f"pl_{espaco}"
        conectado_real = bool(st.session_state.get("token")) and st.session_state.get("sp_user")
        sem_permissao = conectado_real and spotify.falta_escopo_de_playlist(
            st.session_state.get("escopos", ""))
        if sem_permissao:
            st.warning(
                "Sua conexão foi autorizada só para ler suas mais ouvidas — "
                "falta a permissão de criar playlist. Desconecte e conecte de "
                "novo: agora a tela do Spotify aparece pra você autorizar.",
                icon="🔐")
        if st.button("Gerar playlist", type="primary", key=f"btn_pl_{espaco}",
                     disabled=bool(sem_permissao)):
            if conectado_real:
                _gerar_playlist_real(resultado, chave_url)
            else:
                _pedir_conexao(resultado)

        url = st.session_state.get(chave_url)
        if url:
            st.caption(f"**{resultado['titulo']}** · {len(resultado['faixas'])} faixas →")
            st.code(url, language=None)
        elif not conectado_real and spotify.config():
            st.caption("O link aparece aqui depois de gerar — conecta na aba "
                       "🎧 Minha conta pra criar a playlist de verdade.")
        else:
            st.caption("O link aparece aqui depois de gerar")
