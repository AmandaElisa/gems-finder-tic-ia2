# Spec — Integração do modelo real de recomendação

> Documento de encaminhamento pra quando o modelo real sair do notebook
> (`notebook/gems_finder_eda.ipynb`) e substituir os dados simulados do app.
> Guarda as decisões, limitações da API e o passo a passo, pra nada se perder.

**Status:** planejado · **Última atualização:** 2026-08-30

---

## 1. Onde estamos hoje

| Peça | Hoje | Em produção (alvo) |
|---|---|---|
| Catálogo | 32 faixas fictícias em `src/dados.py` | Dataset processado (114.001 faixas, `data/raw/dataset_spotify_raw.csv` → `data/processed/`) |
| Login Spotify | ✅ OAuth real (Authorization Code), já funciona | Igual — só muda o redirect URI (ver §5) |
| Top faixas do usuário | ✅ Reais via `/me/top/tracks` | Igual |
| Perfil de áudio do usuário | Simulado (constante `PERFIL_USUARIO`) | Real, via cruzamento top-tracks × dataset (§3) |
| Playlist | Criada de verdade, mas **vazia** (faixas fictícias não têm ID) | Criada **com as faixas**, via `track_id` do dataset (§4) |
| Precisão @8 | Placeholder (`src/dados.py::PRECISAO_8`, com TODO) | Números da avaliação offline do modelo |

## 2. Limitação da API que motivou este desenho

O Spotify **descontinuou em 27/nov/2024** (para apps criados depois dessa data):
`/v1/audio-features`, `/v1/audio-analysis`, `/v1/recommendations`, related
artists e preview URLs. Ou seja: **não dá para consultar os atributos de áudio
de uma faixa ao vivo pela API**.

O que **continua funcionando** (e o app já usa): OAuth, `/v1/me`,
`/v1/me/top/tracks`, `/v1/me/top/artists`, criação de playlist e adição de
faixas.

**Consequência:** os atributos de áudio vêm sempre do NOSSO dataset, nunca da
API. O dataset já tem tudo que precisamos por faixa:

```
track_id (ID real do Spotify) · artists · track_name · popularity ·
danceability · energy · valence · acousticness · instrumentalness ·
speechiness · liveness · loudness · tempo · track_genre
```

## 3. Perfil de áudio real do usuário (cruzamento top-tracks × dataset)

Substitui a constante `PERFIL_USUARIO` quando o usuário estiver logado de
verdade.

1. `GET /me/top/tracks?limit=50&time_range=medium_term` → lista com
   `track_id` de cada faixa (já implementado em `src/spotify.py::top_faixas`,
   hoje devolvendo só título/artista — passar a devolver o `id` também).
2. Cruzar por **`track_id`** com o dataset (merge direto; sem fuzzy match).
3. Perfil = média dos atributos das faixas encontradas, com os mesmos pesos
   do modelo (`energia`, `valencia`, `dancabilidade`, `instrumentalidade`,
   `acustica`).
4. **Métrica de cobertura do perfil** (mostrar no app, é honesto e didático):
   “N das suas 50 mais ouvidas estão no nosso catálogo”.
5. **Fallbacks em cascata** quando o cruzamento achar poucas faixas:
   - `< 5` faixas encontradas → usar `GET /me/top/artists` (vem com
     `genres`) e aproximar o perfil pelo centroide dos gêneros
     correspondentes no dataset (função `centro()` já existe);
   - sem match nenhum → cair no perfil simulado atual, avisando na UI.

**Onde mexer:** `src/spotify.py` (ids no retorno), `src/dados.py` (loader do
dataset processado com `@st.cache_data`), `src/recomendacao.py` (função
`perfil_do_usuario(top_ids, catalogo)`), `src/ui/conta.py` (usar o perfil
real + exibir a cobertura).

## 4. Playlist com faixas de verdade

Hoje `src/spotify.py::criar_playlist` cria a playlist e para aí (faixas
fictícias). Com o dataset real:

1. Guardar o `track_id` nas recomendações (o DataFrame do garimpo passa a
   carregar a coluna).
2. Depois do `POST /users/{id}/playlists`, chamar:
   `POST /v1/playlists/{playlist_id}/tracks` com
   `{"uris": ["spotify:track:<track_id>", ...]}` (até 100 por chamada; nossas
   8 cabem numa só).
3. Manter a descrição com o resumo do garimpo (já implementado).
4. Remover o aviso “nasce vazia” da UI (`src/ui/resultados.py`).

## 5. Deploy (Streamlit Community Cloud) — checklist

1. Deploy em share.streamlit.io escolhendo o subdomínio
   (ex.: `gems-finder-unb.streamlit.app`).
2. No dashboard do Spotify (developer.spotify.com) → Settings → **adicionar**
   `https://<subdominio>.streamlit.app` como segundo Redirect URI
   (o `http://127.0.0.1:8501` continua cadastrado pro dev local).
3. No painel do Streamlit Cloud → Settings → Secrets → colar a seção
   `[spotify]` com `redirect_uri` apontando pra URL pública.
   O código lê tudo de `st.secrets` — **zero mudança de código**.
4. User Management do app Spotify: cadastrar os e-mails das testadoras
   (modo development, até 25 contas). Abertura ao público geral exigiria
   pedido de extended quota — fora do escopo da residência.

## 6. Substituição do catálogo simulado

- Trocar as constantes `_CATALOGO`/`_ARTISTAS` de `src/dados.py` por um
  loader do dataset processado (parquet/CSV em `data/processed/`), mantendo
  a MESMA interface (`carregar_catalogo()` → DataFrame com as mesmas
  colunas em português). O resto do app não deve perceber a troca.
- Mapear colunas: `track_name→faixa`, `artists→artista`,
  `track_genre→genero`, `danceability→dancabilidade`, `energy→energia`,
  `valence→valencia`, `acousticness→acustica`,
  `instrumentalness→instrumentalidade`, `tempo→bpm`,
  `popularity→popularidade`, e **manter `track_id`**.
- `ano`/`cidade` não existem no dataset → remover dos cards ou derivar de
  outra fonte (decisão do grupo).
- Substituir `PRECISAO_8` pelos números reais da avaliação (TODO já marcado
  no código).

## 7. Perguntas em aberto pro grupo

- [ ] Qual recorte do dataset vira o “catálogo de joias”? (ex.: `popularity ≤ 40`)
- [ ] Os 12 gêneros do protótipo viram um mapeamento dos 114 `track_genre`s?
- [ ] Limiar mínimo de matches pro perfil real (sugestão: 5)?
- [ ] O modo “Por artista favorito” passa a buscar artistas reais do dataset?
- [ ] Precisão @8 real: qual protocolo de avaliação sai do notebook?
