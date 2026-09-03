"""Página Minha conta — login com o Spotify.

Modo REAL quando .streamlit/secrets.toml tem a seção [spotify]; senão cai no
modo SIMULADO do protótipo (OAuth encenado, dados fictícios).
"""

from __future__ import annotations

import time

import requests
import streamlit as st

from src import spotify
from src.dados import ETAPAS_OAUTH, PERMISSOES, TOPS, carregar_catalogo
from src.recomendacao import (descrever_perfil, email_valido,
                             montar_resultado_conta, nome_do_email,
                             perfil_do_usuario)
from src.tema import ROSA
from src.ui.componentes import barras_atributos_html, bloco, cartao, hero, passo
from src.ui.estado import limpar_conta
from src.ui.mascote import mascote
from src.ui.resultados import mostrar_resultados


def _conectar(email: str, quem: dict | None = None, token: str = "",
              tops: list[tuple[str, str]] | None = None) -> None:
    """Guarda a sessão conectada (real ou simulada) e recarrega a página."""
    st.session_state.conectado = True
    st.session_state.email = email
    st.session_state.token = token
    st.session_state.sp_user = quem
    catalogo = carregar_catalogo()
    # Perfil real: cruza as faixas mais ouvidas com o catálogo por track_id.
    # Sem faixas reais (login encenado) cai no exemplo, que a tela marca.
    perfil = perfil_do_usuario(catalogo, tops or [])
    st.session_state.tops = tops or _tops_de_exemplo()
    st.session_state.perfil_conta = perfil
    st.session_state.res_conta = montar_resultado_conta(catalogo, perfil)
    st.session_state.pl_conta = None
    st.session_state.festa_conta = True
    st.rerun()


def voltando_do_spotify() -> bool:
    """True quando a URL traz o retorno do consentimento (?code= ou ?error=)."""
    return bool(st.query_params.get("code") or st.query_params.get("error"))


def _processar_callback(cfg: dict[str, str]) -> None:
    """Troca o ?code= devolvido pelo Spotify por token e monta a sessão real."""
    if st.session_state.conectado:
        return
    if st.query_params.get("error"):
        st.query_params.clear()
        st.warning("Você não autorizou o acesso — sem problema, tenta de novo "
                   "quando quiser.", icon="🎧")
        return
    code = st.query_params.get("code")
    if not code:
        return
    st.query_params.clear()
    try:
        with st.spinner("Conectando na sua conta…"):
            token = spotify.trocar_code_por_token(cfg, code)
            quem = spotify.perfil(token)
            tops = spotify.top_faixas(token)
    except requests.RequestException as erro:
        st.error(f"Não consegui conectar no Spotify: {erro}", icon="🚫")
        return
    _conectar(quem["email"] or quem["nome"], quem, token, tops)


def _tela_login_real(cfg: dict[str, str]) -> None:
    """Login de verdade: botão-link pro consentimento OAuth do Spotify."""
    with cartao("login"):
        passo("PASSO 1", "Entrar com o Spotify",
              "Entra com a conta cadastrada na lista de testadores do app.")
        bloco('<ul class="gf-perm">'
              + "".join(f"<li>{permissao}</li>" for permissao in PERMISSOES)
              + "</ul>")
        st.link_button("Conectar Spotify", spotify.url_login(cfg), type="primary")
        st.caption("Você vai pro site do Spotify autorizar e volta pra cá.")


def _tela_login_simulada() -> None:
    """Fallback do protótipo: e-mail + as 4 etapas do OAuth encenadas."""
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
            with st.status("Conectando na sua conta…", expanded=True) as estado:
                for etapa in ETAPAS_OAUTH:
                    st.write(f"✓ {etapa}")
                    time.sleep(0.47)
                estado.update(label="Tudo pronto, já sei o que você ouve!",
                              state="complete", expanded=False)
            _conectar(email)
        st.caption("Modo simulado — preencha o `.streamlit/secrets.toml` pra "
                   "conectar numa conta Spotify de verdade.")


def _tops_de_exemplo() -> list[dict[str, str]]:
    """As mais ouvidas do protótipo, no formato que a API devolve."""
    return [{"id": "", "faixa": titulo, "artista": artista}
            for titulo, artista in TOPS]


def _aviso_do_perfil(perfil, conectado_de_verdade: bool) -> str:
    """Diz de onde veio o perfil — e quando ele não é da pessoa, diz isso.

    A tela mostrava as faixas reais de quem conectava e recomendava a partir
    de um perfil fixo no código. Quem lesse acreditaria que o cálculo usou o
    que estava na tela.
    """
    if perfil.e_real:
        return (f"Perfil calculado das suas faixas: {perfil.encontradas} das "
                f"suas {perfil.pedidas} mais ouvidas estão no nosso catálogo, "
                "e os atributos de áudio delas viraram seu perfil. Os "
                "atributos vêm do nosso dataset, nunca da API — o Spotify "
                "descontinuou esse endpoint para apps novos.")
    if conectado_de_verdade:
        return (f"Nenhuma das suas {perfil.pedidas} mais ouvidas está no nosso "
                "catálogo, então o perfil abaixo é um exemplo, não o seu — e "
                "as joias saem dele.")
    return ("Login encenado: o perfil abaixo é um exemplo, para ver o fluxo. "
            "Conecte de verdade para usar o seu.")


def _tela_conectada() -> None:
    """Perfil do testador, mais ouvidas, métricas e joias recomendadas."""
    if st.session_state.festa_conta:
        st.session_state.festa_conta = False
        st.balloons()

    real = bool(st.session_state.token)
    email = st.session_state.email
    quem = st.session_state.sp_user
    nome = (quem["nome"] if real and quem else nome_do_email(email)) or "Testador"
    tops = st.session_state.tops or _tops_de_exemplo()
    perfil = st.session_state.get("perfil_conta") or perfil_do_usuario(
        carregar_catalogo(), [])
    origem = "direto da sua conta" if real else "exemplo, para ver o fluxo"

    with cartao("perfil"):
        bloco(f'<div class="gf-who"><div class="gf-avatar">{nome[0]}</div>'
              f'<div><strong>Oi, {nome}!</strong><span>{email}</span></div>'
              '<span class="gf-pill">Conectado</span></div>'
              f'<p class="gf-help" style="margin:20px 0 0"><b>Suas 5 mais ouvidas</b> — '
              f'{origem}.</p>'
              '<div class="gf-tops">'
              + "".join(f'<span class="gf-top">{f["faixa"]} <s>· {f["artista"]}</s></span>'
                        for f in tops[:5])
              + '</div>'
              f'<p class="gf-help" style="margin:18px 0 8px">Perfil detectado: '
              f'<b>{descrever_perfil(perfil.alvo)}</b>.</p>'
              + barras_atributos_html(perfil.alvo))
        st.caption(_aviso_do_perfil(perfil, real))

    mostrar_resultados(
        st.session_state.res_conta, "conta",
        dica_vazia="Cavei fundo e não achei nada que combine com o seu perfil "
                   "nessa profundidade.")

    if st.button("Desconectar", key="btn_out"):
        limpar_conta()
        st.toast("Desconectei da sua conta. Até a próxima!", icon="👋")
        st.rerun()


def pagina_conta() -> None:
    """Login (real ou simulado) e recomendações pelo perfil de áudio."""
    hero(mascote(ROSA, "chill", 88), "Deixa eu ouvir o que você ouve",
         "Modo dos testadores. Conectamos na sua conta, lemos suas mais ouvidas, "
         "montamos seu perfil de áudio e devolvemos só o que é raro e combina.",
         "Só leitura, prometo 🎧")
    cfg = spotify.config()
    if cfg:
        _processar_callback(cfg)
    if st.session_state.desconectou:
        st.session_state.desconectou = False
        st.success("Pronto, desconectei da sua conta — não guardei nada seu por aqui. "
                   "É só entrar de novo quando quiser garimpar mais.", icon="👋")
    if st.session_state.conectado:
        _tela_conectada()
    elif cfg:
        _tela_login_real(cfg)
    else:
        _tela_login_simulada()
