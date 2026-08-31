"""Cliente da Spotify Web API — OAuth (Authorization Code) e criação de playlist.

O app funciona em dois modos:
* REAL — quando `.streamlit/secrets.toml` tem a seção [spotify] preenchida
  (client_id, client_secret, redirect_uri). Login de verdade, top faixas de
  verdade e playlist privada criada de verdade na conta.
* SIMULADO — sem credenciais, tudo continua fake como no protótipo.

Notas:
* O redirect_uri precisa estar cadastrado igualzinho no dashboard do app em
  developer.spotify.com (ex.: http://127.0.0.1:8501 — o Spotify não aceita
  mais `localhost` em apps novos, só o IP de loopback).
* O endpoint /v1/audio-features foi descontinuado para apps novos (nov/2024),
  então o perfil de áudio do usuário segue SIMULADO mesmo no modo real.
* As 32 faixas do catálogo são fictícias, então a playlist real nasce vazia,
  com as joias listadas na descrição.
"""

from __future__ import annotations

import base64
from urllib.parse import urlencode

import requests
import streamlit as st

URL_AUTORIZACAO = "https://accounts.spotify.com/authorize"
URL_TOKEN = "https://accounts.spotify.com/api/token"
URL_API = "https://api.spotify.com/v1"
ESCOPOS = "user-top-read playlist-modify-private"
TIMEOUT = 15


def config() -> dict[str, str] | None:
    """Credenciais da seção [spotify] do secrets.toml, ou None (modo simulado)."""
    try:
        spotify = st.secrets["spotify"]
        cfg = {chave: str(spotify[chave]).strip()
               for chave in ("client_id", "client_secret", "redirect_uri")}
    except (KeyError, FileNotFoundError):
        return None
    if not all(cfg.values()) or "SEU_CLIENT_ID" in cfg["client_id"]:
        return None
    return cfg


def url_login(cfg: dict[str, str]) -> str:
    """URL de consentimento do Spotify (Authorization Code flow)."""
    parametros = {
        "client_id": cfg["client_id"],
        "response_type": "code",
        "redirect_uri": cfg["redirect_uri"],
        "scope": ESCOPOS,
        "show_dialog": "false",
    }
    return f"{URL_AUTORIZACAO}?{urlencode(parametros)}"


def trocar_code_por_token(cfg: dict[str, str], code: str) -> str:
    """Troca o authorization code pelo access token."""
    basic = base64.b64encode(
        f"{cfg['client_id']}:{cfg['client_secret']}".encode()).decode()
    resposta = requests.post(
        URL_TOKEN,
        headers={"Authorization": f"Basic {basic}"},
        data={"grant_type": "authorization_code", "code": code,
              "redirect_uri": cfg["redirect_uri"]},
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    return resposta.json()["access_token"]


def _get(token: str, rota: str, **parametros) -> dict:
    resposta = requests.get(f"{URL_API}{rota}", params=parametros or None,
                            headers={"Authorization": f"Bearer {token}"},
                            timeout=TIMEOUT)
    resposta.raise_for_status()
    return resposta.json()


def perfil(token: str) -> dict[str, str]:
    """Nome, e-mail (se disponível) e id do usuário conectado."""
    dados = _get(token, "/me")
    return {"id": dados["id"],
            "nome": dados.get("display_name") or dados["id"],
            "email": dados.get("email", "")}


def top_faixas(token: str, limite: int = 5) -> list[tuple[str, str]]:
    """As faixas mais ouvidas do usuário: (título, artista)."""
    dados = _get(token, "/me/top/tracks", limit=limite, time_range="medium_term")
    return [(item["name"], ", ".join(artista["name"] for artista in item["artists"]))
            for item in dados.get("items", [])]


def criar_playlist(token: str, user_id: str, nome: str,
                   faixas: list[dict]) -> str:
    """Cria uma playlist privada de verdade e devolve a URL pública dela.

    As faixas do catálogo são fictícias (não existem no Spotify), então a
    playlist nasce vazia com as joias na descrição.
    """
    descricao = ("Garimpada pelo Gems Finder (Residência em IA · UnB · Instituto ELDORADO): "
                 + " · ".join(f'{faixa["faixa"]} ({faixa["artista"]})'
                              for faixa in faixas))[:300]
    resposta = requests.post(
        f"{URL_API}/users/{user_id}/playlists",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": nome, "public": False, "description": descricao},
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    return resposta.json()["external_urls"]["spotify"]
