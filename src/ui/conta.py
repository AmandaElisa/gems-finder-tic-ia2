"""Página Minha conta — modo dos testadores, com OAuth simulado."""

from __future__ import annotations

import time

import streamlit as st

from src.dados import ETAPAS_OAUTH, PERFIL_USUARIO, PERMISSOES, TOPS, carregar_catalogo
from src.recomendacao import email_valido, montar_resultado_conta, nome_do_email
from src.tema import ROSA
from src.ui.componentes import barras_atributos_html, bloco, cartao, hero, passo
from src.ui.estado import limpar_conta
from src.ui.mascote import mascote
from src.ui.resultados import mostrar_resultados


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
