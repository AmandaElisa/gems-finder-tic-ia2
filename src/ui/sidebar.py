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
        # O número que a busca alcança é o do catálogo tratado, não o do CSV:
        # 24.259 linhas do bruto eram a mesma faixa repetida uma vez por gênero.
        bloco('<div class="gf-rail-foot">'
              # `:n` depende do locale da máquina e saiu sem separador; o
              # ponto de milhar é fixo porque a interface é em português.
              f'<b>{len(catalogo):,}</b>'.replace(",", ".")
              + ' faixas únicas tratadas · <b>114.000</b> linhas no dataset<br>'
              f'<b>{catalogo["genero"].nunique()}</b> gêneros · '
              f'<b>{len(artistas)}</b> artistas de referência<br><br>'
              'Residência em IA · UnB · Instituto ELDORADO<br>'
              'Nano-Challenge: Spotify Data<br>'
              'Grupo 9 &nbsp;·&nbsp; Sound Hunters<br><br>'
              '<b>Integrantes:</b><br>'
              '<a href="https://github.com/AmandaElisa" target="_blank" '
              'rel="noopener">Amanda Elisa de Oliveira Carvalho</a><br>'
              'Arthur de Melo Garcia<br>'
              'Maria Carolina Martins Frota<br>'
              'Samara Letícia Alves dos Santos<br>'
              'Wingrid da Costa Silva</div>')
    return pagina
