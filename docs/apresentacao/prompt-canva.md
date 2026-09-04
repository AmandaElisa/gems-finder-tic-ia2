# Prompt para gerar os slides no Canva

Cole o bloco abaixo no **Canva → Magic Studio → Apresentação**. Todos os
números vêm do notebook executado (`notebook/Grupo_9_Sound_Hunters.ipynb`) e
foram conferidos contra a saída das células — se algum mudar num re-treino,
atualize aqui antes de gerar os slides.

> **Nota sobre os gráficos.** O Canva desenha gráficos a partir de dados que
> você cola, mas não lê o notebook. As tabelas de cada gráfico estão prontas
> na seção final deste arquivo: gere o slide e cole os números no gráfico do
> Canva, ou exporte a figura direto do notebook (todas as células de gráfico
> já rodam) e suba como imagem.

---

## O prompt

```
Crie uma apresentação de 16 slides para uma banca acadêmica, em português do
Brasil, sobre um projeto de ciência de dados chamado "Gems Finder".

CONTEXTO
Residência em IA · UnB · Instituto ELDORADO · Turma 2 · Grupo 9 "Sound
Hunters". Desafio: Nano-Challenge Spotify Data. Integrantes: Amanda Elisa de
Oliveira Carvalho, Arthur de Melo Garcia, Maria Carolina Martins Frota,
Samara Letícia Alves dos Santos, Wingrid da Costa Silva.

ESTILO VISUAL
Fundo creme claro (#FAF6EC). Destaques em verde-limão (#CFF25E), rosa
(#F79BD8), lilás (#B3BCF7) e azul (#3B45D9). Texto quase preto (#141414).
Títulos em fonte arredondada e amigável, corpo em sans-serif limpa. Estética
"sticker": cartões com borda escura de 2px e cantos bem arredondados. Cada
slide com no máximo 40 palavras de texto — o resto é gráfico ou tabela.
Nenhum ícone de nota musical genérico; prefira formas geométricas simples.

ESTRUTURA — a apresentação segue a metodologia CBL (Challenge Based
Learning, da Apple), em três fases. Marque a fase no canto de cada slide.

--- FASE 1: ENGAGE (slides 1 a 4) ---

Slide 1 — Capa
Título "Gems Finder". Subtítulo "Garimpando música boa que ninguém ouve".
Nome do grupo e integrantes.

Slide 2 — Big Idea
A grande ideia: DESCOBERTA MUSICAL JUSTA. Plataformas de streaming
recomendam o que já toca, então o que já é popular fica mais popular. Quem
faz música boa e desconhecida nunca é encontrado.

Slide 3 — Essential Question
A pergunta essencial, em destaque grande no centro do slide:
"Como encontrar música que combina com o que eu gosto, entre as faixas que
quase ninguém ouviu?"

Slide 4 — Challenge
O desafio assumido: construir um sistema que parte do gosto real de uma
pessoa e devolve faixas de baixa popularidade com o mesmo DNA sonoro.
Três personas: quem quer descobrir, quem quer curadoria, quem quer contexto.

--- FASE 2: INVESTIGATE (slides 5 a 11) ---

Slide 5 — Guiding Questions
Quatro perguntas que guiaram a investigação, em cartões:
1. Atributos de áudio preveem popularidade?
2. Quantos perfis sonoros existem no catálogo?
3. Quais atributos realmente importam?
4. O que significa "escondido"?
Legenda do slide: "Todas foram respondidas por medição, não por intuição."

Slide 6 — A base de dados (com GRÁFICO DE FUNIL)
Dataset Spotify Tracks: 114.000 linhas, 114 gêneros, 20 colunas.
Gráfico de funil em quatro etapas mostrando a limpeza:
114.000 → 113.549 → 89.740 → 88.945
Destaque: 24.259 linhas eram a MESMA faixa repetida uma vez por gênero.
Redução de 21,3%.

Slide 7 — Qualidade dos dados: três achados
Três cartões:
(a) 9.347 faixas com popularidade 0 — significa "não capturada", não "sem
ouvintes". Descoberto pelo padrão [0, 0, 44] em faixas do Arctic Monkeys.
(b) 157 faixas com tempo=0 E dançabilidade=0 juntos — falha do detector de
batida em música ambiente e guitarra solo. Imputadas pela mediana do gênero.
(c) Faixa marcada em mais gêneros é mais energética (0,630 → 0,726) e muito
menos instrumental (0,189 → 0,032).

Slide 8 — A descoberta que sustenta o projeto (com GRÁFICO DE BARRAS
HORIZONTAIS)
Título: "Áudio não prevê popularidade".
Correlação de cada atributo com popularidade, o maior |r| é 0,128.
Legenda em destaque: "Se o som explicasse o sucesso, não haveria joia
escondida. Como não explica, existe música tão boa quanto os hits e
desconhecida — e é exatamente o que o produto busca."

Slide 9 — Seleção de features (com TABELA)
Sete técnicas de filtro aplicadas: Variance Threshold, MAD, Dispersion
Ratio, Pearson, Chi-quadrado, Cramér's V, Information Gain e Fisher Score.
Resultado: 5 atributos de 8. Dois cartões de destaque:
- `loudness` descartado por redundância com `energy` (r ≈ 0,76)
- `speechiness` cai do 2º para o 8º lugar no Fisher Score quando a limpeza
  vem ANTES da seleção — a ordem das etapas mudou a conclusão

Slide 10 — Escolha do K (com GRÁFICO DE LINHAS, quatro séries)
Validação de K=3 a K=8 por quatro critérios. Seja honesto no slide:
3 dos 4 critérios apontam K=5 (silhueta máxima 0,292, Davies-Bouldin mínimo
1,116, joelho da inércia), e Calinski-Harabasz aponta K=3.
Legenda: "K=5 por maioria de critérios, não por unanimidade."

Slide 11 — Os cinco moods (com GRÁFICO DE RADAR, cinco séries)
Foco, Aconchego, Treino, Heavy e Gingado — nomes escolhidos pelo grupo, mas
os perfis vêm dos centroides medidos do K-Means, não de alvos escritos à mão.

--- FASE 3: ACT (slides 12 a 16) ---

Slide 12 — A solução
Arquitetura em três caixas com setas: notebook (treino) → data/processed/
(modelo.json, catalogo.parquet, embeddings.npy) → app Streamlit (inferência).
Padrão model-in-app: o app carrega artefatos prontos e nunca recalcula.

Slide 13 — Como a recomendação funciona
Três camadas, em cartões:
- VIBE filtra o universo pelo cluster do K-Means
- GÊNERO filtra pela família (16 famílias agrupadas dos 114 do dataset)
- ARTISTA/FAIXA vira semente e PROCURA vizinhos no próprio território
Destaque: cada faixa que a pessoa ouve busca separadamente, em vez de tudo
virar uma média — a média de gostos distintos cai num ponto que não é
nenhum deles.

Slide 14 — Resultado medido (com GRÁFICO DE BARRAS ANTES/DEPOIS)
Testado com o login real de uma integrante do grupo:
- Joias dentro do gênero que ela ouve: de 0/8 para 8/8
- Amplitude do match exibido: de 3 pontos (93–96%) para 51 pontos (42–93%)
- Faixas de categoria infantil no resultado: de 1 para 0

Slide 15 — O filtro de viés de popularidade (com GRÁFICO DE BARRAS)
Classificação do artista em três faixas por `pop_max`, ancoradas em quem se
reconhece: Independente (<40), Conhecido (40–65), Consolidado (≥65).
Âncoras: Bad Bunny 97, BTS 92, Adele 85, Beatles 82, Chico Buarque 47,
Gilberto Gil 43, Foals 4.
Destaque: só o artista de parada fica fora das recomendações.

Slide 16 — Limitações e próximos passos
Seja explícito, em dois grupos.
LIMITAÇÕES DA PLATAFORMA: o endpoint de atributos de áudio foi descontinuado
em nov/2024, então os atributos vêm do nosso dataset; e apps em modo de
desenvolvimento não podem escrever, então a criação de playlist está
implementada mas bloqueada com 403.
LIMITAÇÕES DOS DADOS: o dataset rotula Racionais MC's como "samba" e
Sabotage como "swedish"; 278 faixas só dizem "brazil" sem gênero.
NÃO EXIBIMOS: métrica de precisão, até existir protocolo de avaliação
escrito.
```

---

## Dados dos gráficos, prontos para colar no Canva

### Slide 6 — Funil de limpeza

| Etapa | Linhas |
|---|---|
| CSV original | 114.000 |
| Sem linhas idênticas e sem artista | 113.549 |
| Uma linha por `track_id` | 89.740 |
| Catálogo musical (`e_musica`) | 88.945 |

### Slide 8 — Correlação com popularidade

| Atributo | r |
|---|---|
| instrumentalness | −0,128 |
| loudness | +0,072 |
| danceability | +0,065 |
| speechiness | −0,047 |
| acousticness | −0,039 |
| duration_ms | −0,023 |
| liveness | −0,014 |
| energy | +0,014 |
| valence | −0,012 |
| tempo | +0,008 |

### Slide 10 — Validação do K

| K | Silhueta | Davies-Bouldin | Calinski-Harabasz | Inércia |
|---|---|---|---|---|
| 3 | 0,263 | 1,359 | 35.834 | 246.277 |
| 4 | 0,276 | 1,237 | 33.829 | 207.712 |
| **5** | **0,292** | **1,116** | 35.318 | 171.816 |
| 6 | 0,267 | 1,206 | 33.019 | 155.700 |
| 7 | 0,259 | 1,159 | 31.466 | 142.414 |
| 8 | 0,263 | 1,182 | 30.406 | 131.066 |

Queda da inércia: K=4→5 reduz 17,3%; K=5→6 reduz apenas 9,4% (o joelho).

### Slide 11 — Perfil dos cinco moods (centroides medidos)

| Mood | Dançabilidade | Energia | Valência | Acústica | Instrumental | Faixas |
|---|---|---|---|---|---|---|
| Gingado | 0,697 | 0,720 | 0,719 | 0,236 | 0,022 | 30.365 |
| Treino | 0,572 | 0,765 | 0,337 | 0,087 | 0,790 | 10.258 |
| Foco | 0,373 | 0,197 | 0,206 | 0,855 | 0,847 | 6.716 |
| Aconchego | 0,513 | 0,371 | 0,387 | 0,720 | 0,021 | 18.472 |
| Heavy | 0,477 | 0,798 | 0,346 | 0,075 | 0,031 | 23.134 |

### Slide 15 — Três faixas de artista

| Faixa | `pop_max` | Artistas | Recomendável |
|---|---|---|---|
| Independente | < 40 | 25.982 faixas | sim |
| Conhecido | 40 – 65 | 38.618 faixas | sim |
| Consolidado | ≥ 65 | 25.140 faixas | não |

Âncoras para o gráfico: Bad Bunny 97 · BTS 92 · Arctic Monkeys 92 · Adele 85
· Linkin Park 85 · The Beatles 82 · Zeca Pagodinho 50 · Chico Buarque 47 ·
Tim Maia 44 · Gilberto Gil 43 · Mount Kimbie 8 · Foals 4

---

## Números de apoio, se a banca perguntar

| | |
|---|---|
| Faixas no catálogo tratado | 89.740 |
| Faixas elegíveis para recomendação | 58.612 |
| Famílias de gênero | 16 (agrupadas dos 114 do dataset) |
| Testes automatizados | 123 |
| Células do notebook | 127, executa de ponta a ponta sem erro |
| Popularidade média das recomendações | 36,4 (catálogo: 33,2) |
| Idioma detectado | 20 idiomas, 93% de acerto, com confiança por faixa |

**Se perguntarem "onde está o machine learning":** K-Means com K validado por
quatro critérios; sete técnicas de seleção de features; filtragem baseada em
conteúdo com k-NN; e uma representação aprendida com TruncatedSVD (48
dimensões latentes de gênero + 5 atributos de áudio, similaridade por
cosseno).

**Se perguntarem por resultados negativos** — e eles valem tanto quanto os
positivos: TF-IDF não funciona neste dataset porque ele é balanceado em ~1000
faixas por gênero (IDF varia só de 4,46 a 4,60); adicionar mais dimensões de
áudio PIORA a saturação da métrica de similaridade; e detecção de idioma no
título não serve como filtro, porque excluiria *Jura* do Zeca Pagodinho e
*Geni e o Zepelim* do Chico Buarque.
