# 💎 Gems Finder

> Garimpando faixas underground e subestimadas no catálogo do Spotify através de inteligência de dados e perfis sonoros (*moods*).

<p align="center">
  <img src="assets/logo-gems-finder.svg" width="520" alt="Gems Finder">
</p>

---

## 🏛️ Contexto Acadêmico
* **Iniciativa:** Residência em IA – Turma 2
* **Desafio:** Nano-Challenge: Spotify Data
* **Grupo:** Grupo 9

### 👥 Integrantes
* Amanda Elisa de Oliveira Carvalho
* Arthur de Melo Garcia
* Maria Carolina Martins Frota
* Samara Letícia Alves dos Santos
* Wingrid da Costa Silva

---

## 🧭 Sobre o Projeto
O **Gems Finder** é um produto de dados desenvolvido para análises avançadas de engenharia e machine learning. O sistema resolve o viés de popularidade das plataformas de streaming tradicionais, cruzando perfis de áudio de grandes sucessos (*mainstream*) com faixas de baixa popularidade para entregar recomendações de descoberta justa e curadoria independente.

## ✨ Principais Funcionalidades
* **🎛️ Explorador por Vibes:** Segmentação do catálogo em quadrantes de humor (Foco, Treino, Chill, Melancolia) baseados em atributos técnicos (`valence`, `energy`, `acousticness`, `speechiness`).
* **📊 Score de Potencial Oculto:** Métrica proprietária que ranqueia faixas subestimadas de acordo com a similaridade de DNA sonoro com hits consolidados.
* **🎧 Modo Híbrido / Conexão Spotify:** Arquitetura flexível que permite tanto a exploração pública por *vibes* quanto simulações de autenticação via API para perfis de teste.
* **📈 Dashboards Analíticos:** Métricas de precisão, cobertura de catálogo e identificação de artistas independentes.

## 🗂️ Estrutura do Repositório
A organização dos arquivos e pastas do projeto segue o padrão de engenharia de dados:

```text
gems-finder/
├── data/
│   ├── raw/                  # Dataset original
│   └── processed/            # Dados tratados
├── notebooks/
│   └── gems_finder_eda.ipynb # Notebook principal de limpeza dos dados, exploração, métricas e modelo
├── docs/
│   └── gems-finder-prototipo.html # Protótipo HTML aprovado (especificação visual e funcional)
├── assets/                   # Imagens e recursos visuais para a documentação
├── src/                      # Código do app componentizado
│   ├── tema.py               # Paleta de cores compartilhada
│   ├── dados.py              # Dados simulados e constantes de produto
│   ├── recomendacao.py       # Lógica do modelo (match, garimpo, cobertura)
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
O app abre em `http://localhost:8501`. Os dados são simulados dentro do próprio código (sem CSV externo nem credenciais) e a métrica *Precisão @8* é placeholder até a avaliação real do modelo.

## 🛠️ Tecnologias Utilizadas
* **Python** (Pandas, NumPy, Scikit-Learn)
* **Streamlit** (Protótipo navegável)
* **Spotify Web API** (Integração OAuth e metadados)
