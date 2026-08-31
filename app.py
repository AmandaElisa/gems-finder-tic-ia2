"""Gems Finder — garimpeiro de joias ocultas do Spotify.

Protótipo navegável da Residência em IA · UnB (Grupo 9 · Nano-Challenge Spotify).
Porte para Streamlit do protótipo `docs/gems-finder-prototipo.html`: mesmo fluxo,
mesmos textos, mesma paleta e a mesma mascote (Pepita, a gema garimpeira).

AVISOS
------
* Todos os dados são SIMULADOS e moram em `src/dados.py`: 32 faixas fictícias
  de artistas underground e 10 artistas de referência mainstream fictícios.
  Nenhum CSV externo, nenhuma credencial, nenhuma chamada real à Spotify Web
  API (os pontos de integração estão marcados com TODO).
* A métrica "Precisão @8" é PLACEHOLDER (`src/dados.py::PRECISAO_8`) até a
  avaliação real do modelo. A "Cobertura" é calculada de fato.

Rodar:  streamlit run app.py
"""

from __future__ import annotations

import streamlit as st

from src import spotify
from src.dados import PAGINAS, carregar_artistas, carregar_catalogo, listar_generos
from src.ui.componentes import bloco
from src.ui.conta import pagina_conta, voltando_do_spotify
from src.ui.descobrir import pagina_descobrir
from src.ui.estado import iniciar_estado
from src.ui.estilo import CSS
from src.ui.sidebar import barra_lateral


def main() -> None:
    """Monta a página e roteia entre Descobrir e Minha conta."""
    st.set_page_config(page_title="Gems Finder", page_icon="💎", layout="wide",
                       initial_sidebar_state="expanded")
    bloco(CSS)

    catalogo = carregar_catalogo()
    artistas = carregar_artistas()
    generos = listar_generos(catalogo)
    iniciar_estado(generos)

    # O Spotify devolve o usuário pra raiz do app; sem isso ele cairia no
    # "Descobrir" e teria que clicar na aba pra ver o próprio perfil.
    if spotify.config() and voltando_do_spotify():
        st.session_state.w_nav = PAGINAS[1]

    pagina = barra_lateral(catalogo, artistas)
    if pagina == PAGINAS[0]:
        pagina_descobrir(catalogo, artistas, generos)
    else:
        pagina_conta()


if __name__ == "__main__":
    main()
