"""Carrega os artefatos que o notebook de clusterização exporta.

O app nunca treina nada: ele lê `data/processed/` e usa o que está lá. Em
particular, o `StandardScaler` exportado é reaplicado como está — criar um
scaler novo compararia vetores em escalas diferentes e devolveria vizinhos
errados sem avisar.

Artefatos esperados (produzidos por `notebook/Grupo_9_Sound_Hunters.ipynb`):

    catalogo.parquet   uma linha por track_id, com mood e status do artista
    artistas.parquet   um artista por linha, com n_faixas, pop_media, pop_max
    modelo.joblib      scaler, kmeans, features do vetor de mood e limiares

Se algum faltar, o carregamento falha em voz alta. Cair de volta nos dados
simulados em silêncio mostraria número inventado como se fosse medido, o que
o princípio 2 da constituição proíbe.
"""

from __future__ import annotations

import unicodedata
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.tema import AZUL, LIMA, PERI, ROSA

# Azul claro do quadrante Melancolia do protótipo, que não está em tema.py
# porque era usado só ali.
AZUL_CLARO = "#9AD6E8"

# Tradução das colunas do dataset para o vocabulário do app. O código do app
# é português (constituição, princípio 1, estado transitório), então a
# tradução acontece aqui, uma vez, na fronteira.
COLUNAS = {
    "track_name": "faixa",
    "artists": "artista",
    "popularity": "popularidade",
    "danceability": "dancabilidade",
    "energy": "energia",
    "valence": "valencia",
    "acousticness": "acustica",
    "instrumentalness": "instrumentalidade",
    "tempo": "bpm",
    "genero_primario": "genero",
}

# Cada mood herda a cor e a expressão da vibe correspondente do protótipo.
# Duas trocas foram decididas pelo grupo: Treino recebe a expressão que era da
# Melancolia (boca reta, que combina com techno constante) e Heavy recebe a
# que era do Treino (boca aberta, que lê como grito).
APRESENTACAO: dict[str, dict[str, str]] = {
    "Foco":      {"cor": PERI,        "humor": "foco",   "desc": "estudar e trabalhar"},
    "Aconchego": {"cor": LIMA,        "humor": "chill",  "desc": "leve e acústica"},
    "Treino":    {"cor": AZUL_CLARO,  "humor": "triste", "desc": "batida constante"},
    "Heavy":     {"cor": ROSA,        "humor": "treino", "desc": "peso e distorção"},
    "Gingado":   {"cor": AZUL,        "humor": "feliz",  "desc": "pra dançar"},
}

# Um artista só entra no seletor de referência se tiver catálogo de verdade —
# pop_max alto com uma faixa só é sorte, não fama.
MINIMO_DE_FAIXAS = 3

# Gêneros que não servem como referência de gosto, mesmo sendo populares:
# ruído branco lidera o cluster Foco por atributo de áudio, mas ninguém
# escolhe "White Noise for Babies" para dizer o que gosta.
GENEROS_FORA_DA_REFERENCIA = {"sleep", "white-noise", "comedy", "children",
                              "kids", "show-tunes"}


def raiz() -> Path:
    """Raiz do repositório, a partir da localização deste arquivo."""
    return Path(__file__).resolve().parent.parent


def pasta() -> Path:
    """Onde os artefatos moram."""
    return raiz() / "data" / "processed"


def _exigir(caminho: Path) -> Path:
    if not caminho.exists():
        raise FileNotFoundError(
            f"Artefato não encontrado: {caminho}\n"
            "Rode notebook/Grupo_9_Sound_Hunters.ipynb até a seção de "
            "exportação para gerá-lo."
        )
    return caminho


@lru_cache(maxsize=1)
def modelo() -> dict[str, Any]:
    """O scaler, o KMeans e os limiares, como o notebook os exportou."""
    return joblib.load(_exigir(pasta() / "modelo.joblib"))


@lru_cache(maxsize=1)
def catalogo() -> pd.DataFrame:
    """O catálogo real, com as colunas no vocabulário do app.

    Uma linha por faixa: o parquet já vem deduplicado por `track_id`, o que é
    o que torna seguro cruzá-lo com as faixas do usuário por essa coluna.
    """
    bruto = pd.read_parquet(_exigir(pasta() / "catalogo.parquet"))
    df = bruto.rename(columns=COLUNAS)
    # `generos` (lista) continua disponível para quem precisar do multi-gênero;
    # `genero` é a coluna de uma-string que a UI exibe.
    return df


@lru_cache(maxsize=1)
def artistas() -> pd.DataFrame:
    """Artistas consolidados que servem de referência no seletor.

    O seletor existe para dar um ponto de partida reconhecível: a pessoa
    escolhe quem já conhece, e o garimpo devolve joia de artista independente
    com o mesmo DNA sonoro. Por isso aqui só entram consolidados.
    """
    tabela = pd.read_parquet(_exigir(pasta() / "artistas.parquet"))
    cons = tabela[(tabela["status"] == "Consolidado")
                  & (tabela["n_faixas"] >= MINIMO_DE_FAIXAS)]

    cat = catalogo()
    por_artista = (cat.assign(nome=cat["artista"].str.split(";"))
                   .explode("nome"))
    por_artista["nome"] = por_artista["nome"].str.strip()
    por_artista = por_artista[por_artista["nome"].isin(cons["artista"])]

    # Fora quem é dominado por gênero que não serve de referência.
    def referenciavel(generos: Any) -> bool:
        return not (GENEROS_FORA_DA_REFERENCIA & set(generos))

    por_artista = por_artista[por_artista["generos"].apply(referenciavel)]

    ATRIBUTOS_APP = ["energia", "valencia", "dancabilidade",
                     "instrumentalidade", "acustica"]
    perfil = (por_artista.groupby("nome")
              .agg(**{a: (a, "mean") for a in ATRIBUTOS_APP},
                   popularidade=("popularidade", "max"),
                   mood=("mood", lambda s: s.mode().iat[0]))
              .reset_index()
              .rename(columns={"nome": "artista"}))

    # O gênero de exibição sai do mais frequente entre TODAS as faixas do
    # artista, não da coluna `genero`: essa é o primeiro item em ordem
    # alfabética da lista de gêneros da faixa, o que é estável mas arbitrário
    # — daí OneRepublic aparecer como "piano".
    generos_do_artista = (por_artista[["nome", "generos"]]
                          .explode("generos")
                          .groupby("nome")["generos"]
                          .agg(lambda s: s.mode().iat[0]))
    perfil["genero"] = perfil["artista"].map(generos_do_artista)

    # Variedade importa mais que popularidade bruta: pegamos os mais
    # conhecidos de cada mood, para o seletor cobrir o espaço sonoro inteiro
    # em vez de mostrar cinco artistas do mesmo grupo.
    escolhidos = (perfil.sort_values("popularidade", ascending=False)
                  .groupby("mood", group_keys=False).head(3))
    return (escolhidos.sort_values("popularidade", ascending=False)
            .reset_index(drop=True))


def vibes() -> dict[str, dict[str, Any]]:
    """As vibes do app, derivadas dos centroides medidos.

    O alvo de cada vibe é o perfil médio real do seu cluster, então o app e o
    notebook concordam por construção — não por alguém ter copiado números de
    um para o outro.
    """
    m = modelo()
    cat = catalogo()
    atributos = [COLUNAS[f] for f in m["features_mood"]]
    perfis = cat.groupby("mood")[atributos].mean()

    saida: dict[str, dict[str, Any]] = {}
    for nome, apres in APRESENTACAO.items():
        if nome not in perfis.index:
            continue
        alvo = {a: float(perfis.loc[nome, a]) for a in atributos}
        # `instrumentalidade` e `acustica` entram no alvo; o app pondera os
        # cinco atributos, e o vetor de mood tem exatamente esses cinco.
        saida[_chave(nome)] = {
            "nome": nome,
            "desc": apres["desc"],
            "cor": apres["cor"],
            "humor": apres["humor"],
            "alvo": alvo,
        }
    return saida


def _chave(nome: str) -> str:
    """Chave estável e sem acento para o nome de um mood."""
    sem_acento = (unicodedata.normalize("NFD", nome)
                  .encode("ascii", "ignore").decode())
    return sem_acento.lower()
