# 💎 Gems Finder

> Garimpando faixas underground e subestimadas no catálogo do Spotify através de inteligência de dados e perfis sonoros (*moods*).

---

## 🏛️ Contexto Acadêmico
* **Iniciativa:** Residência em IA – Turma 2
* **Desafio:** Nano-Challenge: Spotify Data
* **Grupo:** Grupo 9

### 👥 Integrantes
* Amanda Elisa de Oliveira Carvalho
* Arthur de Melo Garcia
* Eric Luiz Rodrigues de França
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

## 🛠️ Tecnologias Utilizadas
* **Python** (Pandas, NumPy, Scikit-Learn)
* **Streamlit** (Interface Web Interativa)
* **Spotify Web API** (Integração OAuth e metadados)
