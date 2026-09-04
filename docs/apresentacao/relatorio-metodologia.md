# Relatório — seção 2, Metodologia (texto corrigido)

Substitui a versão anterior. Cada número aqui sai do notebook executado
(`notebook/Grupo_9_Sound_Hunters.ipynb`); as correções em relação ao texto
antigo estão listadas no fim do arquivo.

---

## 2. Metodologia

Para o desenvolvimento do Gems Finder adotou-se uma abordagem de
**Content-Based Filtering** (filtragem baseada em conteúdo), na qual as
faixas e o perfil de escuta são descritos por metadados e atributos de áudio
estruturados. A escolha se impõe pelo problema: não há histórico de
interação de usuários a explorar, e o objetivo é justamente recomendar
faixas que quase ninguém ouviu — para as quais um sistema colaborativo, por
construção, não teria sinal algum.

O dataset de trabalho é o *Spotify Tracks Dataset*: 114.000 linhas, 114
gêneros e 20 colunas. Após o tratamento descrito na seção 2.2, o catálogo
efetivo é de **89.740 faixas únicas**.

### 2.1. Evolução do protótipo e estratégia de busca

O projeto evoluiu iterativamente a partir de um protótipo conceitual. As
primeiras versões exploravam parâmetros isolados; o modelo refinado permite
uma busca multifacetada, em que o usuário combina **Vibe + Gênero +
Artista** simultaneamente, em vez de depender de seleções excludentes.

A combinação, porém, só passou a ter significado depois de duas correções
que a validação empírica expôs, e cada critério hoje cumpre um papel
distinto e verificável:

| Critério | Papel |
|---|---|
| **Vibe** | Restringe o universo ao *cluster* do K-Means correspondente |
| **Gênero** | Restringe o universo à família de gêneros escolhida |
| **Artista / faixa** | Torna-se **semente** e busca vizinhos no próprio território sonoro e de gênero |

A distinção mais importante é a última. Uma implementação anterior reduzia
todos os critérios a um único vetor-alvo médio, e a média de gostos
heterogêneos converge para um ponto que não corresponde a nenhum deles.
Verificado com o login real de uma integrante do grupo: suas oito faixas
mais ouvidas distribuíam-se em quatro *moods* distintos, e a média resultante
situava-se a distância 2,01 do próprio centroide que ajudara a formar. No
modelo atual cada faixa ou artista de referência realiza sua própria busca, e
os resultados são intercalados — o que elevou a aderência de gênero de
**0 para 8** entre as oito recomendações e ampliou a dispersão do índice de
afinidade exibido de **3 para 51 pontos percentuais**.

### 2.2. Tratamento dos dados e engenharia de atributos

**Deduplicação.** A remoção de linhas idênticas eliminou apenas 451 registros,
mas **24.259 `track_id` permaneciam duplicados**: o dataset registra a mesma
faixa uma vez por gênero. A consolidação passou a manter uma linha por
faixa, preservando os gêneros como lista e agregando a popularidade por
**máximo** — decisão fundamentada em outro achado, descrito adiante.

**Popularidade zero não significa ausência de audiência.** Há 9.347 faixas
com `popularity = 0`. A inspeção de casos como faixas do Arctic Monkeys, com
o padrão `[0, 0, 44]` entre duplicatas, indica **falha de captura** e não
ausência de execuções. Por isso a agregação usa `max`, e as faixas em zero
são excluídas de qualquer cálculo de mediana ou percentil.

**Imputação de medições inválidas.** Identificaram-se 157 faixas com
`tempo = 0` **e** `danceability = 0` simultaneamente, concentradas no gênero
`sleep` (138 das 157).

A hipótese de que se trate de valor legítimo — música para dormir tem, de
fato, baixa dançabilidade — foi testada e rejeitada por três evidências:

1. **As condições nunca ocorrem separadas.** Não há no dataset uma única
   faixa com `tempo = 0` e `danceability` válida, nem o inverso. Fossem
   valores legítimos, esperar-se-ia dançabilidade nula acompanhada de
   andamento medido.
2. **O gênero `sleep` não tem dançabilidade nula por natureza:** sua mediana
   é 0,161. É baixa, como se espera, mas não zero — e os 138 zeros do gênero
   são exatamente as 138 faixas com `tempo = 0`.
3. **A `energy` mediana dessas faixas é 0,001.** Três atributos colapsam para
   zero simultaneamente, o que caracteriza ausência de análise e não silêncio
   medido.

Zero BPM, por fim, não descreve música lenta: descreve medição que não
ocorreu. Os valores foram imputados pela mediana do gênero (89,9 BPM e
0,198), decisão registrada no notebook em comparação com as alternativas de
descarte, *capping* e transformação.

**Seleção de features.** Foram extraídos os atributos numéricos que definem o
"DNA" técnico das faixas e aplicadas **sete técnicas de filtro**:

1. **Variance Threshold** — remoção de variáveis de baixa variabilidade
2. **Mean Absolute Difference (MAD)** — dispersão média absoluta
3. **Dispersion Ratio** — razão entre média aritmética e geométrica
4. **Pearson's Correlation Coefficient** — relações lineares e multicolinearidade
5. **Chi-quadrado e Cramér's V** — associação das variáveis categóricas
6. **Information Gain** (informação mútua) — relevância em relação ao gênero
7. **Fisher's Score** — poder discriminante entre classes

O placar consolidado por *rank* médio elegeu, nesta ordem, `acousticness`,
`energy`, `instrumentalness`, `valence` e `danceability` — **exatamente as
cinco variáveis adotadas no modelo final**. A seleção foi respaldada
empiricamente, e não fixada a priori.

Dois resultados merecem registro por terem alterado decisões de projeto:

- **`loudness` foi descartado por redundância** com `energy` (r ≈ 0,76).
  Embora apresente bom desempenho individual (Fisher = 0,855), não acrescenta
  informação ao vetor.
- **A ordem das etapas mudou a conclusão.** Com o catálogo completo,
  `speechiness` ocupava a 2ª posição de 14 no Fisher Score (0,906). Após a
  remoção do conteúdo falado — *podcasts*, *stand-up* e audiolivros
  identificados por `speechiness > 0,66` combinado com gênero e duração —, cai
  para a 8ª posição (0,195), uma queda de 4,6×. As demais variáveis
  permaneceram praticamente inalteradas. Selecionar antes de limpar teria
  mantido no modelo uma variável cujo poder discriminante vinha do ruído.

### 2.3. Segmentação em perfis sonoros (moods)

O catálogo foi segmentado por **K-Means** sobre as cinco variáveis
selecionadas, padronizadas com `StandardScaler`. O número de agrupamentos
foi validado de K = 3 a K = 8 por quatro critérios:

| K | Silhueta | Davies-Bouldin | Calinski-Harabasz | Inércia |
|---|---|---|---|---|
| 3 | 0,263 | 1,359 | 35.834 | 246.277 |
| 4 | 0,276 | 1,237 | 33.829 | 207.712 |
| **5** | **0,292** | **1,116** | 35.318 | 171.816 |
| 6 | 0,267 | 1,206 | 33.019 | 155.700 |
| 7 | 0,259 | 1,159 | 31.466 | 142.414 |
| 8 | 0,263 | 1,182 | 30.406 | 131.066 |

Adotou-se **K = 5**, respaldado por **três dos quatro critérios**: silhueta
máxima, Davies-Bouldin mínimo e o joelho da curva de inércia (a redução cai
de 17,3% entre K = 4 e K = 5 para 9,4% entre K = 5 e K = 6). O
Calinski-Harabasz aponta K = 3, divergência que se registra por
transparência. Os cinco perfis receberam os nomes **Foco, Aconchego, Treino,
Heavy e Gingado**; a nomenclatura é decisão de produto, mas os vetores-alvo
de cada um são os centroides medidos, sem valores escritos manualmente.

### 2.4. O diferencial de negócio: filtro de viés de popularidade

Para mitigar o viés de popularidade das plataformas de *streaming*, o sistema
classifica cada artista pela **maior popularidade entre suas faixas**
(`pop_max`). A escolha do máximo, e não da média, é deliberada: Sam Smith
seria classificado como independente pela média, deprimida por dezenas de
faixas de álbum, ainda que *Unholy* alcance popularidade 100. A pergunta
pertinente é "alguém já ouviu este artista?", e é o máximo que a responde.

A classificação é feita em **três faixas**, e não em duas. O corte binário
originalmente adotado em 50 não media o que se propunha: popularidade 50
corresponde a faixas de álbum de artistas como Linkin Park e a repertório
gospel litúrgico. Verificando quem efetivamente ocupa cada patamar de
`pop_max` — Bad Bunny 97, BTS 92, Adele 85, The Beatles 82 —, constatou-se
que sete pontos separavam Zeca Pagodinho (50, classificado *Consolidado*) de
Chico Buarque (47, *Independente*), enquanto Chico compartilhava
classificação com o Foals, cuja melhor faixa tem popularidade 4.

| Faixa | `pop_max` | Faixas do catálogo | Recomendável |
|---|---|---|---|
| **Independente** | < 40 | 25.982 | sim |
| **Conhecido** | 40 – 65 | 38.618 | sim |
| **Consolidado** | ≥ 65 | 25.140 | não |

A regra de negócio aplicada antes da entrega é `status_artista != 'Consolidado'`,
combinada ao piso de popularidade e à exclusão de conteúdo falado — o que
resulta em **58.612 faixas elegíveis**. Manter os artistas *Conhecido* entre
os recomendáveis é decisão de produto fundamentada: Elis Regina, com
popularidade 44 no Spotify, não corresponde ao que a audiência majoritária
consome, ainda que integre o cânone da música brasileira.

A adoção da faixa intermediária resolveu, sem qualquer lista de exceções, um
defeito que a análise havia documentado: sob o critério binário, Gilberto
Gil (43), Tim Maia (44), Chico Buarque (47), Roberto Carlos (44) e Maria
Bethânia (45) eram classificados como *Independente*, e o sistema oferecia o
cânone brasileiro como descoberta obscura. A causa é que `popularity` é
ponderada por recência — mede o que toca hoje, não a estatura do artista.

### 2.5. Arquitetura e reprodutibilidade

A arquitetura adotada é **model-in-app**: o treinamento ocorre integralmente
no *notebook*, que exporta artefatos versionados, e a aplicação Streamlit os
carrega em memória, sem recalcular nada.

```
notebook/            →   data/processed/          →   app.py
(treino, 127 células)    modelo.json                  (inferência)
                         catalogo.parquet
                         artistas.parquet
                         embeddings.npy
```

| Componente | Decisão |
|---|---|
| **Serialização** | `modelo.json` — parâmetros do *scaler*, centroides, limiares e taxonomia como dado puro. O `modelo.joblib` continua sendo exportado para quem retomar o treino, mas a aplicação **não o lê** |
| **Versionamento** | Cada artefato carrega uma versão derivada do conteúdo (hash SHA-256 das *features*, K, centroides, parâmetros e limiares) e a data de treino, de modo que se saiba de qual modelo saiu cada resultado |
| **Interface** | Aplicação web interativa em **Streamlit**, com CSS próprio fiel ao protótipo aprovado |
| **Testes** | **123 testes** automatizados (`pytest`) sobre a lógica de recomendação |

**Sobre FastAPI e Docker.** Ambos foram avaliados e **deliberadamente não
adotados**. Uma API exposta se justifica com múltiplos consumidores, modelo
de grande porte ou necessidade de escalar a inferência separadamente da
interface — nenhuma condição presente neste projeto: o modelo ocupa poucos
KB, a inferência sobre 89 mil faixas é resolvida em milissegundos em memória
e há um único consumidor. Acrescentá-los introduziria um segundo serviço a
implantar, um novo modo de falha e latência de rede onde hoje há acesso a
memória. Adicionalmente, o Streamlit Community Cloud executa um único
processo e não aceita `Dockerfile`, de forma que a adoção exigiria migrar de
plataforma. A decisão está registrada em
`docs/specs/2026-09-03-real-model-in-the-app/spec.md`.

Como consequência, `requirements.txt` — instalado no *deploy* — contém apenas
`streamlit`, `pandas`, `numpy`, `requests` e `pyarrow`. `scikit-learn`,
`joblib` e as bibliotecas de análise permanecem em `requirements-dev.txt`,
restritas ao treinamento.

### 2.6. Representação aprendida

Como extensão da filtragem baseada em conteúdo, os 114 gêneros do dataset
foram codificados em matriz binária esparsa (89.740 × 114) e reduzidos por
**TruncatedSVD** a 48 dimensões latentes, concatenadas aos cinco atributos de
áudio padronizados. Cada bloco é normalizado separadamente antes da
ponderação, e a similaridade é o **cosseno** entre vetores unitários.

A avaliação foi comparativa e o resultado, parcial: varridos cinco valores de
K por quatro pesos, nenhuma configuração superou simultaneamente a
implementação por regras em coerência de gênero e variedade. O espaço
aprendido é, portanto, aplicado apenas onde as regras não têm resposta — quando
o gênero de uma semente não possui cauda de baixa popularidade. Nesse cenário
a diferença é qualitativa: uma semente de forró, cujo gênero não apresenta
faixas elegíveis em tetos baixos, retornava resultados sem relação com a
consulta e passou a retornar *honky-tonk*, análogo estadunidense do forró como
música country de dança. Trata-se de vizinhança que nenhuma regra do sistema
codifica: emergiu da coocorrência de gêneros no dataset.

---

## O que foi corrigido em relação ao texto anterior

| Trecho anterior | Problema | Correção |
|---|---|---|
| **2.2** listava cinco técnicas de seleção | Foram aplicadas **sete**; faltavam Dispersion Ratio, Chi-quadrado e Cramér's V | Lista completa e numerada |
| "relevância preditiva em relação aos agrupamentos de humor **e popularidade**" | Áudio **não** prevê popularidade — o maior \|r\| é 0,128, e no Fisher Score contra "faixa obscura" o máximo é 0,05 | Relevância declarada em relação ao **gênero** |
| **2.3** `is_consolidated == 'Independente'` | Nome de coluna inexistente (é `status_artista`) e critério **binário**, substituído por três faixas | Regra atual: `status_artista != 'Consolidado'` |
| "similaridade sonora com grandes sucessos" | A recomendação parte das faixas **da própria pessoa**, não de *hits* | Reescrito em 2.1 |
| **2.4** "Exposição de Serviços: API robusta utilizando **FastAPI**" | **Descartado** pelo grupo, com justificativa registrada em *spec* | Nova subseção explicando a decisão |
| **2.4** "Conteinerização com **Docker**" | **Descartado** — o Community Cloud não aceita `Dockerfile` | Idem |
| **2.4** "Serialização via **joblib**" | O `joblib` é exportado, mas a aplicação lê `modelo.json`; um `joblib` em `requirements.txt` já quebrou um *deploy* | Descrito o que a aplicação efetivamente carrega |
| "a arquitetura foi **planned**" | Termo em inglês no texto em português | "a arquitetura adotada é" |
| Ausente | A validação de K, a deduplicação, a imputação e a representação aprendida não constavam | Seções 2.2, 2.3 e 2.6 |
| "falha ... para músicas estilo Ambient/Sleep" | Afirmação sem evidência, e a objeção é pertinente: música para dormir tem baixa dançabilidade por natureza | Substituída pelas três evidências que sustentam a leitura de falha — coocorrência perfeita das condições, mediana 0,161 do gênero `sleep` e `energy` mediana 0,001 |
