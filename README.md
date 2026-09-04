<p align="center">
  <img src="assets/icons_with_headset/logo-gems-finder.svg" width="520" alt="Gems Finder">
</p>

<h2 align="center">💎 Gems Finder</h2>

<p align="center">
  <b>Garimpando faixas underground e subestimadas no catálogo do Spotify através de inteligência de dados e perfis sonoros (<i>moods</i>).</b>
</p>

<p align="center">
  <img src="http://img.shields.io/static/v1?label=status&message=EM%20DESENVOLVIMENTO&color=GREEN&style=for-the-badge"/>
</p>

---

## 🏛️ Contexto Acadêmico
* **Iniciativa:** Residência em IA – UnB – Turma 2
* **Desafio:** Nano-Challenge: Spotify Data
* **Grupo:** Grupo 9

### 👩🏻‍💻👨‍💻 Integrantes
* <a href="https://github.com/AmandaElisa">Amanda Elisa de Oliveira Carvalho</a><br>
* Arthur de Melo Garcia
* Maria Carolina Martins Frota
* <a href="https://github.com/samarawwleticia">Samara Letícia Alves dos Santos</a><br>
* <a href="https://github.com/wincsSI">Wingrid da Costa Silva</a><br>

---

## 🧭 Sobre o Projeto
O **Gems Finder** é um produto de dados desenvolvido para análises avançadas de engenharia e machine learning. O sistema resolve o viés de popularidade das plataformas de streaming tradicionais: em vez de ranquear por quem já toca, ele parte do que a pessoa ouve e busca vizinhos sonoros entre as faixas de baixa popularidade, excluindo apenas os artistas de parada. O catálogo é classificado em três faixas por `pop_max` — **Independente** (< 40), **Conhecido** (40–65) e **Consolidado** (≥ 65) — e só o último fica fora das recomendações.

## ✨ Principais Funcionalidades
* **🎛️ Explorador por Vibes:** Segmentação do catálogo em cinco *moods* — Foco, Aconchego, Treino, Heavy e Gingado — descobertos por **K-Means** sobre `danceability`, `energy`, `valence`, `acousticness` e `instrumentalness`. O K foi validado de 3 a 8 por silhueta, Davies-Bouldin, Calinski-Harabasz e cotovelo.
* **📊 Garimpo por semente:** Cada faixa ou artista de referência procura vizinhos no próprio território sonoro e de gênero, em vez de tudo virar uma média só — a média de gostos distintos cai num ponto que não é nenhum deles.
* **🎧 Conexão Spotify:** Login OAuth real. O perfil sai do cruzamento das suas 50 faixas mais ouvidas com o catálogo, e cada joia diz de qual faixa sua ela veio. Sem conectar, o app funciona inteiro — só o perfil pessoal fica de fora, e a tela marca esse caso como exemplo.
* **📈 Métricas honestas:** Afinidade e cobertura do catálogo elegível, ambas calculadas. Não há métrica de precisão exibida: ela voltará quando existir protocolo de avaliação escrito.

## 🗂️ Estrutura do Repositório
A organização dos arquivos e pastas do projeto segue o padrão de engenharia de dados:

```text
gems-finder/
├── data/
│   ├── raw/                  # Dataset original
│   └── processed/            # Dados tratados
├── notebook/
│   └── Grupo_9_Sound_Hunters.ipynb # Limpeza, EDA, seleção de features, clusters e exportação dos artefatos
├── CLAUDE.md                 # Orquestração: contexto, ciclo de trabalho e convenções
├── docs/
│   ├── gems-finder-prototipo.html # Protótipo HTML aprovado (especificação visual e funcional)
│   ├── constitution.md       # Princípios do projeto
│   ├── templates/            # Modelos de spec, plano e tarefas
│   └── specs/                # Uma pasta por trabalho (spec, plano, tarefas)
├── tests/                    # Suíte pytest da lógica de recomendação
├── assets/                   # Imagens e recursos visuais para a documentação
├── src/                      # Código do app componentizado
│   ├── tema.py               # Paleta de cores compartilhada
│   ├── dados.py              # Constantes de produto (o catálogo vem de data/processed/)
│   ├── artefatos.py          # Fronteira: carrega os artefatos do notebook
│   ├── generos.py            # Famílias de gênero, lidas do modelo
│   ├── spotify.py            # OAuth e Web API
│   ├── recomendacao.py       # Lógica do modelo (match, garimpo, sementes, cobertura)
│   └── ui/                   # Camada visual
│       ├── estilo.py         # CSS (estilo "sticker" do protótipo)
│       ├── mascote.py        # SVGs da mascote Pepita e logo
│       ├── componentes.py    # Cartões, hero, passos, métricas, barras
│       ├── estado.py         # Gerência do session_state
│       ├── sidebar.py        # Marca, navegação e rodapé
│       ├── resultados.py     # Joias encontradas + gerador de playlist
│       ├── descobrir.py      # Página 1 — Descobrir
│       └── conta.py          # Página 2 — Minha conta
├── .streamlit/
│   └── config.toml           # Tema claro e fontes (Fredoka/Figtree)
├── app.py                    # Entrada do protótipo navegável (roteamento)
├── requirements.txt          # Dependências do projeto (bibliotecas Python)
├── .gitignore                # Arquivos ignorados pelo Git
└── README.md                 # Documentação principal
```

## ▶️ Como Rodar o Protótipo
```bash
pip install -r requirements.txt
streamlit run app.py
```
O app abre em `http://localhost:8501` com o catálogo real de **89.740 faixas**,
carregado de `data/processed/`. O login do Spotify é opcional: sem credenciais
em `.streamlit/secrets.toml` o app funciona inteiro, só sem perfil pessoal.

## 🛠️ Arquitetura e Tecnologias

O modelo é **treinado no notebook** e **embarcado no app**: o Streamlit carrega
artefatos prontos de `data/processed/` e nunca recalcula nada. Esse padrão
(*model-in-app*) é o adequado à escala do projeto — o modelo tem poucos KB, a
inferência sobre 89 mil faixas leva milissegundos em memória, e há um único
consumidor.

```
notebook/  →  data/processed/        →  app.py
(treino)      modelo.json                (inferência)
              catalogo.parquet
              artistas.parquet
              embeddings.npy
```

**Por que não FastAPI e Docker.** Uma API exposta faria sentido com vários
consumidores, modelo grande ou necessidade de escalar a inferência separada da
interface — nenhum é o caso aqui. Ela acrescentaria um segundo serviço para
implantar e um modo de falha novo, com latência de rede onde hoje há acesso a
memória. Além disso, o Streamlit Community Cloud executa **um** processo e não
aceita Dockerfile, então adotá-los exigiria sair da plataforma. A decisão está
registrada em `docs/specs/2026-09-03-real-model-in-the-app/spec.md`.

### Camada de dados e modelo
| Ferramenta | Uso |
|---|---|
| **pandas** · **NumPy** | Limpeza, deduplicação e vetorização dos atributos de áudio |
| **scikit-learn** | `StandardScaler`, `KMeans` (moods), as 7 técnicas de seleção de features, métricas de validação e o `TruncatedSVD` da representação aprendida — **só no notebook** |
| **lingua** | Idioma de cada faixa, detectado de título + artista + álbum e guardado com a confiança — **só no notebook** |
| **SciPy** | Testes estatísticos da seleção de features (qui-quadrado, Cramér's V) |
| **matplotlib** · **seaborn** | Gráficos da análise exploratória |
| **PyArrow** | Leitura dos artefatos em Parquet pelo app |

O app **não** depende de scikit-learn, de joblib nem de lingua: tudo isso é
treino. O modelo sai como dado puro — `modelo.json` com parâmetros do scaler,
centroides e limiares, e `embeddings.npy` com os vetores de faixa já
calculados. A similaridade no espaço aprendido é cosseno entre vetores
unitários, ou seja um produto escalar, que o NumPy resolve sozinho. Isso mantém
a produção leve e imune a incompatibilidade de *pickle* entre versões — foi
justamente um `joblib` em `requirements.txt` que quebrou um deploy.

### Aplicação
| Ferramenta | Uso |
|---|---|
| **Streamlit** | Interface completa, com CSS próprio fiel ao protótipo aprovado |
| **Spotify Web API** | OAuth (Authorization Code), faixas e artistas mais ouvidos. A criação de playlist está implementada e é bloqueada pela plataforma — ver limitações abaixo |
| **requests** | Cliente HTTP da API |

> Os atributos de áudio **nunca** vêm da API: o Spotify descontinuou
> `/v1/audio-features` para apps criados após 27/11/2024. O perfil do usuário é
> montado cruzando as faixas mais ouvidas dele com o nosso catálogo, por
> `track_id`.

### Qualidade
| Ferramenta | Uso |
|---|---|
| **pytest** | 123 testes sobre a lógica de recomendação |
| **JupyterLab** | Notebook de treino, executável de ponta a ponta fora do Colab. As dependências dele estão em `requirements-dev.txt`, e precisam ser instaladas no Python do **kernel** do Jupyter, que não é necessariamente o venv do app |

### Modelo em produção
Cada artefato carrega uma **versão derivada do conteúdo** (hash das features,
centroides, parâmetros e limiares) e a data de treino, para que se saiba de
qual modelo saiu cada resultado.

## 🚧 Limitações da API do Spotify

Duas funcionalidades do produto esbarram em restrições da plataforma, não em
decisões nossas. Estão documentadas aqui porque mudam o que o app pode
prometer, e porque a alternativa — simular o resultado — violaria o princípio
2 da [constituição](docs/constitution.md).

### Atributos de áudio não vêm da API

O endpoint `GET /v1/audio-features` foi **descontinuado para apps novos em
27/11/2024**. Por isso os atributos de áudio de uma faixa **nunca** vêm do
Spotify: o perfil de quem conecta é montado cruzando as faixas mais ouvidas
com o nosso catálogo, pela chave `track_id`. É também o motivo de o catálogo
processado precisar estar deduplicado por `track_id` — um cruzamento contra o
dado bruto multiplicaria linhas, porque lá a mesma faixa aparece uma vez por
gênero.

Consequência prática: quem ouve música que não está nas 89.740 faixas do
dataset cai na cascata de fallback, e a tela diz por onde o perfil foi
calculado em vez de fingir precisão.

### A playlist não pode ser criada

**A geração de playlist continua implementada e visível no app**, porque é
parte do produto desenhado. Ela falha com `403 Forbidden`, e a causa é
externa: desde a migração de **9 de março de 2026**, apps do Spotify em
**Development Mode** podem **ler**, mas não **escrever**. Criar playlist e
adicionar faixas são escrita.

Diagnosticado com o próprio app, e não é nenhuma das suspeitas comuns:

| Hipótese | Verificado |
|---|---|
| Falta o escopo `playlist-modify-private` | Não — o token concedido traz o escopo |
| Conta fora da lista de testadores | Não — a conta está em *User Management* |
| Erro na montagem da requisição | Não — a mesma credencial lê `/me` e `/me/top/tracks` |

Sair do Development Mode exige **Extended Quota**, que desde 15/05/2025 só é
concedida a **organização registrada com no mínimo 250 mil usuários ativos
por mês** — inalcançável para um projeto acadêmico.

O app degrada com honestidade: explica a restrição na tela e oferece o que a
plataforma permite, que é **link direto de cada joia** (leitura pura, sem
login e sem permissão) para montar a playlist manualmente.

Fontes: [Quota modes](https://developer.spotify.com/documentation/web-api/concepts/quota-modes)
· [relato do mesmo caso](https://community.spotify.com/t5/Spotify-for-Developers/Web-API-playlist-creation-returns-403-in-Development-Mode-no/td-p/7482480)
· [issue no SDK oficial](https://github.com/spotify/spotify-web-api-ts-sdk/issues/159)
