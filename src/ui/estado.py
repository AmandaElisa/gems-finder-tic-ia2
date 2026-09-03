"""Gerência do st.session_state — os resultados sobrevivem à troca de página."""

from __future__ import annotations

from typing import Any

import streamlit as st

PADROES: dict[str, Any] = {
    # os três critérios do passo 1 se combinam, e nada vem marcado: pré-marcar
    # uma vibe enviesaria em silêncio todo primeiro garimpo
    "vibes": [],
    "generos": [],
    "favoritos": [],
    # 30 e nao 18: varias familias deste catalogo so tem faixa acima de 20, e
    # o padrao baixo abria o app num estado vazio para elas.
    "teto": 30,
    "res_desc": None,
    "pl_desc": None,
    "conectado": False,
    "email": "",
    "token": "",
    "sp_user": None,
    "tops": None,
    "res_conta": None,
    "pl_conta": None,
    "festa_conta": False,
    "desconectou": False,
}


def iniciar_estado() -> None:
    """Garante as chaves do session_state na primeira execução."""
    for chave, valor in PADROES.items():
        st.session_state.setdefault(chave, valor.copy() if isinstance(valor, list) else valor)


def limpar_conta() -> None:
    """Desconecta o testador e volta o session_state da conta ao início."""
    for chave in ("conectado", "email", "token", "sp_user", "tops",
                  "res_conta", "pl_conta", "festa_conta"):
        st.session_state[chave] = PADROES[chave]
    st.session_state.pop("w_email", None)
    # avisa a tela de login que a saída foi de propósito, pra dar retorno visual
    st.session_state.desconectou = True
