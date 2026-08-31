"""Barra lateral: marca, navegação entre páginas e rodapé institucional."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src.dados import PAGINAS
from src.ui.componentes import bloco
from src.ui.mascote import LOGO


def barra_lateral(catalogo: pd.DataFrame, artistas: pd.DataFrame) -> str:
    """Marca, navegação entre as duas páginas e rodapé. Devolve a página ativa."""
    with st.sidebar:
        bloco(f'<div class="gf-brand">{LOGO}<div><h1>Gems Finder</h1>'
              '<small>joias ocultas do Spotify</small></div></div>')
        bloco('<p class="gf-nav-label">Navegação</p>')
        pagina = st.radio("Navegação", PAGINAS, key="w_nav", label_visibility="collapsed")
        bloco('<div class="gf-rail-foot"><b>114.000</b> faixas indexadas<br>'
              f'<b>{catalogo["genero"].nunique()}</b> gêneros · '
              f'<b>{len(artistas)}</b> artistas de referência<br><br>'
              'Residência em IA · UnB<br>'
              'Nano-Challenge: Spotify Data<br>'
              'Grupo 9<br><br>'
              '<b>Integrantes:</b><br>'
              'Amanda Elisa de Oliveira Carvalho<br>'
              'Arthur de Melo Garcia<br>'
              'Eric Luiz Rodrigues de França<br>'
              'Maria Carolina Martins Frota<br>'
              'Samara Letícia Alves dos Santos<br>'
              'Wingrid da Costa Silva</div>')
    return pagina
