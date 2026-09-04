"""Lógica de recomendação do Gems Finder.

Tradução fiel das funções match(), media(), centro() e rar() do protótipo
HTML, mais o garimpo (filtro + ranking) e as métricas exibidas na UI.
"""

from __future__ import annotations

import math
import random
import re
from typing import Any, Mapping, NamedTuple, Sequence

import numpy as np
import pandas as pd

from src import artefatos
from src import generos as familias
from src.dados import ATRIBUTOS, PESOS, PERFIL_USUARIO, TETO_CONTA, VIBES
from src.tema import CREME, LIMA, PERI, ROSA


def round_js(valor: float) -> int:
    """Arredonda meio-para-cima, igual ao Math.round() do JavaScript."""
    return math.floor(valor + 0.5)


def match(faixa: Mapping[str, Any], alvo: Mapping[str, float]) -> int:
    """Afinidade sonora 31–99 entre uma faixa e um vetor-alvo, e só isso.

    É distância ponderada absoluta entre os atributos de áudio, sem nenhum
    componente de raridade. O bônus de obscuridade saiu daqui: ele dava pontos
    a uma faixa por ser impopular, não por soar parecida, e num app onde tudo é
    impopular por construção isso inflava o número que a usuária lê como
    "afinidade".

    Cinco atributos não separam gênero, e esta função satura: para o perfil de
    uma usuária real, 610 faixas do catálogo elegível empatam acima de 90%.
    Por isso ela não decide sozinha o que aparece — quem estreita o universo é
    o gênero da semente, em `garimpar_por_sementes`.
    """
    pesos = np.array([PESOS[a] for a in ATRIBUTOS])
    diferencas = np.abs(
        np.array([float(faixa[a]) for a in ATRIBUTOS])
        - np.array([float(alvo[a]) for a in ATRIBUTOS])
    )
    distancia = float(np.dot(pesos, diferencas))
    return max(31, min(99, round_js(100 - distancia * 135)))


def media(faixas: pd.DataFrame) -> dict[str, float]:
    """Média de cada atributo de áudio de um conjunto de faixas ou artistas."""
    return {atributo: float(faixas[atributo].mean()) for atributo in ATRIBUTOS}


def _do_genero(catalogo: pd.DataFrame, generos: Sequence[str]) -> pd.DataFrame:
    """Faixas que pertencem a qualquer um dos gêneros dados.

    Uma faixa pertence a vários gêneros, e a coluna `generos` guarda todos. A
    coluna `genero` é só o primeiro deles em ordem alfabética — estável para
    exibir, mas errada para filtrar: escolher "rock" perderia uma faixa cujos
    gêneros são ["alt-rock", "rock"]. Sem a lista, cai na coluna simples.

    Só gênero de verdade decide família — nem etiqueta de playlist, nem
    nacionalidade. As duas atravessam o catálogo inteiro, então bastava uma
    delas para arrastar música de qualquer estilo para dentro de qualquer
    família. Medido: 19% do universo "Indie" entrava só por `chill` ou `sad`,
    metade de "Clássica e instrumental" só por `piano`, `guitar`, `sleep` ou
    `study`, e uma busca por Indie devolvia três faixas francesas em oito
    porque `french` mora nessa família.

    Faixa sem nenhum gênero de verdade não entra em família nenhuma. São 2.746
    delas, e é a resposta honesta: o dataset não diz o que Indila toca, só que
    ela canta em francês. Continuam achaveis pela vibe e pela busca sem filtro
    de gênero.
    """
    procurados = familias.expandir(generos)
    if "generos" in catalogo.columns:
        return catalogo[_marca_de_pertencimento(catalogo, procurados)]
    return catalogo[catalogo["genero"].isin(list(procurados))]


def _genero_visivel(faixa: Mapping[str, Any], procurados: set[str]) -> str:
    """O gênero que o cartão deve mostrar, dado o que a pessoa procurou.

    A coluna `genero` é o primeiro da lista em ordem ALFABÉTICA, o que faz o
    cartão responder coisa diferente da pergunta: buscando Indie, uma faixa
    com `['indian', 'indie', 'indie-pop']` se anuncia como *indian* e parece
    erro de recomendação quando é acerto.

    Prefere um gênero da família pedida; sem filtro de gênero, prefere um
    gênero de verdade a uma etiqueta de playlist.
    """
    # `or []` não serve: `generos` chega como array do numpy, e testar a
    # verdade de um array com vários itens levanta ValueError.
    crus = faixa.get("generos")
    lista = [] if crus is None else list(crus)
    if not lista:
        return str(faixa.get("genero", ""))
    de_verdade = [g for g in lista if g not in artefatos.nao_definem_familia()]
    da_familia = [g for g in de_verdade if g in procurados]
    for candidatos in (da_familia, de_verdade,
                       [g for g in lista if g in procurados], lista):
        if candidatos:
            return str(candidatos[0])
    return str(faixa.get("genero", ""))


def _marca_de_pertencimento(catalogo: pd.DataFrame,
                            procurados: set[str]) -> pd.Series:
    """Máscara booleana: quais faixas pertencem a `procurados`.

    Regra única para o filtro de gênero e para o universo de cada semente —
    as duas travessias precisam concordar, senão a semente reintroduz pela
    etiqueta o que o filtro de gênero acabou de tirar.
    """
    def pertence(lista: Any) -> bool:
        # Só gênero de verdade coloca faixa numa família. Sem nenhum, a faixa
        # não entra em família alguma: dizer que uma faixa marcada apenas
        # `french` é Indie, ou que uma marcada apenas `chill` é Indie, é
        # inventar informação que o dataset não tem. Ela continua achável pela
        # vibe e pela busca sem filtro de gênero.
        de_verdade = set(lista) - artefatos.nao_definem_familia()
        return bool(procurados & de_verdade)

    return catalogo["generos"].apply(pertence)


def centro(catalogo: pd.DataFrame, genero: str) -> dict[str, float]:
    """Centroide de atributos de áudio das faixas de um gênero."""
    return media(_do_genero(catalogo, [genero]))


def media_de_vetores(vetores: Sequence[Mapping[str, float]]) -> dict[str, float]:
    """Média elemento a elemento de vários vetores-alvo de atributos de áudio.

    O `media()` acima resume um DataFrame de faixas; este resume vetores soltos
    — o alvo de uma vibe é um dicionário, não uma linha do catálogo.
    """
    return {atributo: sum(float(v[atributo]) for v in vetores) / len(vetores)
            for atributo in ATRIBUTOS}


def universo(catalogo: pd.DataFrame, generos: Sequence[str],
             vibes: Sequence[str] = ()) -> pd.DataFrame:
    """Universo de busca: o catálogo, estreitado pelos critérios de conjunto.

    Gênero e vibe **filtram**; artista não, porque artista é semente e semente
    procura, não restringe.

    A vibe passou a filtrar por causa de um defeito medido: quando havia
    artista escolhido, o alvo combinado era calculado e depois descartado, e as
    sementes assumiam o ranqueamento sozinhas. Na prática escolher *Heavy* ou
    *Aconchego* junto com dois artistas devolvia resultado idêntico — a vibe
    não fazia nada. Como cada faixa carrega o `mood` do cluster a que pertence,
    filtrar por ele é a leitura direta do que a pessoa pediu.
    """
    base = catalogo if not generos else _do_genero(catalogo, generos)
    if vibes and "mood" in base.columns:
        nomes = {VIBES[v]["nome"] for v in vibes if v in VIBES}
        if nomes:
            do_mood = base[base["mood"].isin(nomes)]
            # Um universo vazio ajudaria ninguém: se a interseção não existe,
            # a vibe volta a ser só alvo, e o gênero manda.
            if not do_mood.empty:
                return do_mood
    return base


class Criterio(NamedTuple):
    """Um critério ativo do passo 1: seu vetor-alvo e como ele se descreve."""

    alvo: dict[str, float]
    titulo: str
    ctx: str


def criterios_ativos(catalogo: pd.DataFrame, artistas: pd.DataFrame,
                     vibes: Sequence[str], generos: Sequence[str],
                     favoritos: Sequence[str]) -> list[Criterio]:
    """Um Criterio por grupo escolhido no passo 1, na ordem em que a UI os mostra.

    Cada grupo vira UM critério, quantas fichas tenha: duas vibes viram um só
    alvo médio, então o alvo final fica no meio entre "as vibes" e "o artista",
    não a dois terços da vibe.
    """
    ativos: list[Criterio] = []
    if vibes:
        nomes = " + ".join(VIBES[vibe]["nome"] for vibe in vibes)
        ativos.append(Criterio(
            media_de_vetores([VIBES[vibe]["alvo"] for vibe in vibes]),
            nomes, f"bate com a vibe {nomes}"))
    if generos:
        nomes = " + ".join(generos)
        ativos.append(Criterio(
            media_de_vetores([centro(catalogo, genero) for genero in generos]),
            nomes, f"representa o som de {nomes}"))
    if favoritos:
        escolhidos = artistas[artistas["artista"].isin(list(favoritos))]
        ativos.append(Criterio(
            media(escolhidos),
            "parecido com " + " + ".join(favoritos),
            "chega perto de " + " e ".join(favoritos)))
    return ativos


def texto_status(vibes: Sequence[str], generos: Sequence[str],
                 favoritos: Sequence[str], teto: int) -> str:
    """Frase do passo 3: lista os critérios ativos e o teto de popularidade."""
    partes = []
    if vibes:
        partes.append("vibe <b>" + " + ".join(VIBES[v]["nome"] for v in vibes) + "</b>")
    if generos:
        partes.append("gênero <b>" + " + ".join(generos) + "</b>")
    if favoritos:
        partes.append("parecido com <b>" + ", ".join(favoritos) + "</b>")
    descricao = ", ".join(partes) or "<b>escolha ao menos um critério acima</b>"
    return f"Buscando por {descricao}, com popularidade até <b>{teto}</b>."


# Limites das faixas de raridade: são os quartis da popularidade das faixas
# elegíveis até 50, então as quatro bandas têm tamanho parecido (28% / 24% /
# 24% / 25%). Os antigos 8 e 17 foram calibrados para um slider que ia até 40
# e deixavam a banda de cima com metade do catálogo.
BANDAS_DE_RARIDADE: tuple[tuple[int, str, str], ...] = (
    (20, "Joia bruta", LIMA),
    (27, "Rara", ROSA),
    (36, "Pouco ouvida", PERI),
)
SELO_MAIS_ALTO = ("Em ascensão", CREME)


def rar(popularidade: int) -> tuple[str, str]:
    """Selo de raridade e a cor correspondente, a partir da popularidade."""
    for teto, nome, cor in BANDAS_DE_RARIDADE:
        if popularidade <= teto:
            return nome, cor
    return SELO_MAIS_ALTO


def elegiveis_para_garimpo(base: pd.DataFrame) -> pd.DataFrame:
    """Só as faixas que podem ser recomendadas.

    A coluna `elegivel` vem do catálogo processado e junta as três condições
    que o modelo definiu: popularidade acima do piso (popularidade 0 é faixa
    não capturada, não faixa sem streams), artista independente, e ser música
    e não conteúdo falado.

    É aqui que o diferencial de negócio chega ao app. Sem isso o garimpo
    devolve lado-B de artista consolidado, que tem popularidade baixa sem ser
    joia escondida de ninguém.

    Catálogo sem a coluna passa direto — é o caso dos testes, que montam
    DataFrames pequenos à mão.
    """
    if "elegivel" not in base.columns:
        return base
    return base[base["elegivel"]]


def garimpar(base: pd.DataFrame, alvo: Mapping[str, float], teto: int,
             limite: int = 8, variar: bool = False) -> pd.DataFrame:
    """Filtra por elegibilidade e popularidade <= teto, e ranqueia por match.

    A ordem é só afinidade. Havia aqui um bônus de 0,15 por ponto de
    popularidade abaixo de 30 — até 4,5 pontos, mais que a distância inteira
    entre o 1º e o 71º colocado. Como centenas de faixas empatam no topo do
    match, era o bônus que escolhia as oito exibidas: o app ranqueava por
    raridade e mostrava o número como se fosse afinidade. Foi assim que um
    medley de festa infantil com 94% em popularidade 8 passou na frente de uma
    faixa de 96%.

    A obscuridade continua garantida por dois filtros que ninguém burla: a
    coluna `elegivel` e o teto de popularidade. Ela não precisa também ganhar
    os empates.
    """
    base = elegiveis_para_garimpo(base)
    elegiveis = base[base["popularidade"] <= teto].copy()
    if elegiveis.empty:
        return elegiveis.assign(match=pd.Series(dtype="int64"))
    elegiveis["match"] = [match(linha, alvo) for _, linha in elegiveis.iterrows()]
    # kind="stable" preserva a ordem do catálogo nos empates, como o sort do JS.
    ordenada = elegiveis.sort_values("match", ascending=False, kind="stable")
    return _diversificar(ordenada, limite, variar).reset_index(drop=True)


# Quantos pontos de match ainda contam como "praticamente empatado". Medido:
# no universo da vibe Aconchego, 102 faixas cabem em três pontos e 208 em
# quatro, espalhadas por dezenas de gêneros. Cinco atende também o garimpo
# por artista, onde o pool é menor: com catálogo largo (David Guetta, Bad
# Bunny) as 16 primeiras diferem em 4 pontos, então sortear entre elas é
# honesto. Com pool curto (Kim Petras, 23 faixas) a faixa de empate fica
# pequena sozinha, e o garimpo continua determinístico — o que é correto:
# variar ali seria mostrar faixa 20 pontos pior só para parecer variado.
EMPATE_TECNICO = 5


def _diversificar(ordenada: pd.DataFrame, limite: int,
                  variar: bool = False) -> pd.DataFrame:
    """As melhores, sem repetir gênero enquanto houver alternativa igual de boa.

    Sem isto, uma busca só por vibe devolvia oito faixas quase idênticas:
    Aconchego trazia dois cantopop, dois spanish e um mandopop, porque dentro
    de três pontos do topo cabem 102 faixas e o desempate acabava sendo a
    ordem do catálogo — que não significa nada.

    Só reordena dentro do empate técnico. Uma faixa claramente mais parecida
    com o alvo nunca perde lugar para uma pior de outro gênero: a primeira
    passada leva uma por gênero, a segunda completa pela nota.

    Com `variar`, sorteia dentro do empate a cada garimpo, então clicar de
    novo traz joias novas. Não é enfeite: entre 102 faixas que diferem em três
    pontos, escolher sempre as mesmas oito é arbitrário, não é mais preciso —
    o desempate hoje é a ordem do catálogo, que não significa nada. O sorteio
    nunca cruza a fronteira do empate, então nenhuma faixa pior sobe.

    `variar=False` por padrão: os testes precisam de ordem previsível.
    """
    if "genero" not in ordenada.columns or len(ordenada) <= limite:
        return ordenada.head(limite)
    corte = int(ordenada["match"].iloc[0]) - EMPATE_TECNICO
    empatadas = ordenada[ordenada["match"] >= corte]
    if variar and len(empatadas) > limite:
        embaralhada = list(empatadas.index)
        random.shuffle(embaralhada)
        empatadas = empatadas.loc[embaralhada]

    escolhidas: list[Any] = []
    generos_usados: set[str] = set()
    for indice, linha in empatadas.iterrows():
        if len(escolhidas) >= limite:
            break
        genero = str(linha.get("genero", ""))
        if genero and genero in generos_usados:
            continue
        generos_usados.add(genero)
        escolhidas.append(indice)

    # Faltou gênero distinto? completa — primeiro com o resto das empatadas,
    # que já estão sorteadas, e só depois descendo na nota. Completar pela
    # ordem original desfazia o sorteio justamente onde ele mais importa: um
    # artista com poucos gêneros no catálogo caía sempre nas mesmas oito.
    if len(escolhidas) < limite:
        ja = set(escolhidas)
        restantes = ([i for i in empatadas.index if i not in ja]
                     + [i for i in ordenada.index
                        if i not in ja and i not in set(empatadas.index)])
        escolhidas += restantes[:limite - len(escolhidas)]
    return ordenada.loc[escolhidas]


class Semente(NamedTuple):
    """Uma referência concreta de gosto, e o vocabulário em que ela procura.

    O contrário de um centroide: uma semente é *uma* faixa que a pessoa ouve
    ou *um* artista que ela escolheu, não a média de tudo junto. A média de
    oito faixas espalhadas por quatro moods cai num ponto que não é nenhuma
    delas — medido: a faixa `Promise`, do Ben Howard, fica a 2,01 de distância
    do próprio centroide que ajudou a formar.
    """

    alvo: dict[str, float]
    rotulo: str                        # "Only Love", "blink-182"
    generos: tuple[str, ...] = ()      # gêneros crus; vazio = não estreita
    # Linhas do catálogo que originaram a semente. Só servem para achar o
    # vetor aprendido dela em `embeddings()`, que é alinhado por posição.
    # Uma faixa tem uma linha; um artista tem todas as dele.
    linhas: tuple[int, ...] = ()


# Nível em que a cascata desistiu do gênero: o vocabulário da semente e a
# família dela vieram vazios, e só resta o universo inteiro.
SEM_GENERO = 2


def _pool_da_semente(base: pd.DataFrame, semente: Semente,
                     nivel_minimo: int = 0) -> tuple[pd.DataFrame, int]:
    """Candidatas de uma semente, do vocabulário mais estreito ao mais largo.

    A cascata existe porque nem todo gênero deste catálogo tem cauda obscura:
    os brasileiros só começam entre 23 e 43 de popularidade, então um gênero
    pequeno pode não ter joia nenhuma abaixo do teto.

    1. Os gêneros crus da própria semente. É o único nível que separa
       `punk-rock` de `j-idol`, cujos vetores de áudio ficam a três pontos um
       do outro.
    2. As famílias desses gêneros. Mais largo — "Eletrônica" guarda dubstep e
       trance juntos —, mas ainda dentro do mesmo território.
    3. O universo inteiro. Último recurso, decidido pelo grupo para que a tela
       nunca devolva menos de oito joias. É o nível que pode trazer faixa de
       gênero distante, e o grupo aceitou a troca sabendo disso.

    `nivel_minimo` começa a cascata mais larga de propósito: é assim que o
    complemento do garimpo pede o nível 1 (família) depois de já ter usado o
    nível 0 (gênero cru). Alargar a cascata para *todas* as sementes só porque
    faltaram joias foi tentado e medido: derrubou a precisão de gênero de 8/8
    para 1/8 e trouxe `j-dance` de volta. Cada semente continua estrita; quem
    completa o número é `_completar`.
    """
    if not semente.generos or "generos" not in base.columns:
        # Sem vocabulário para estreitar, a semente já está no nível mais
        # largo — é o mesmo caso de ter perdido o gênero na cascata.
        return base, SEM_GENERO
    # Os gêneros DE VERDADE da semente: o Joji vem com `chill` na lista, e
    # procurar por `chill` traz o catálogo inteiro de volta.
    proprios = set(semente.generos) - artefatos.nao_definem_familia() or set(semente.generos)
    niveis = (proprios,
              familias.expandir(sorted({f for g in proprios
                                        if (f := familias.familia_de(g))})))
    for passo, procurados in enumerate(niveis[nivel_minimo:], start=nivel_minimo):
        if not procurados:
            continue
        pool = base[_marca_de_pertencimento(base, procurados)]
        if not pool.empty:
            return pool, passo
    return base, SEM_GENERO


def _ordenar_por_vetor(candidatas: pd.DataFrame, sementes: Sequence[Semente]
                       ) -> tuple[list[int], list[str]] | None:
    """Afinidade e semente de cada candidata pelo espaço aprendido.

    Devolve None quando não dá para usar — artefato antigo sem
    `embeddings.npy`, semente sem linha de catálogo, ou catálogo de teste
    montado à mão. Aí quem chama volta ao caminho por atributos de áudio.

    A similaridade é cosseno, que num espaço de vetores unitários é só
    produto escalar: uma multiplicação de matriz em numpy, sem scikit-learn.
    O número exibido é remapeado para a mesma escala 31–99 do `match`, porque
    o cartão mostra "match" e duas réguas diferentes na mesma coluna
    confundiriam quem lê.
    """
    matriz = artefatos.embeddings()
    if matriz is None:
        return None
    uteis = [s for s in sementes if s.linhas]
    if not uteis:
        return None
    try:
        alvo = candidatas.index.to_numpy()
        blocos = matriz[alvo]
        vetores = []
        for s in uteis:
            v = matriz[list(s.linhas)].mean(axis=0)
            norma = float(np.linalg.norm(v))
            if norma:
                vetores.append(v / norma)
        if not vetores:
            return None
        semelhancas = blocos @ np.array(vetores).T     # candidatas x sementes
    except (IndexError, ValueError):
        return None
    melhor = semelhancas.argmax(axis=1)
    valores = semelhancas.max(axis=1)
    # Cosseno vive em [-1, 1]; a faixa útil aqui é positiva. 31–99 mantém a
    # coluna comparável com o resto da tela.
    notas = [max(31, min(99, round_js(31 + max(0.0, float(v)) * 68)))
             for v in valores]
    return notas, [uteis[int(i)].rotulo for i in melhor]


def _completar(base: pd.DataFrame, sementes: Sequence[Semente],
               escolhidas: list[pd.Series], vistas: set[Any],
               limite: int) -> None:
    """Preenche o que faltou para chegar a `limite`, alargando aos poucos.

    O grupo decidiu que a tela nunca devolve menos de oito joias. Quando os
    gêneros das sementes não têm cauda obscura suficiente, o complemento vem
    primeiro das famílias e só então do universo inteiro — e cada faixa entra
    com a semente de quem melhor combina com ela, para o cartão continuar
    dizendo de onde veio.
    """
    for nivel in (1, 2):
        if len(escolhidas) >= limite:
            return
        pools = ([_pool_da_semente(base, s, nivel_minimo=nivel)[0]
                  for s in sementes] if nivel == 1 else [base])
        # Desduplica pelo índice, não pelas colunas: `generos` é uma lista, e
        # drop_duplicates não sabe comparar lista.
        candidatas = pd.concat(pools)
        candidatas = candidatas[~candidatas.index.duplicated()]
        if candidatas.empty:
            continue
        candidatas = candidatas.copy()
        # No nível 2 o gênero acabou: sem ele, cinco atributos de áudio não
        # separam nada e o resultado é ruído — a semente de forró da Calcinha
        # Preta devolvia j-idol. O espaço aprendido carrega gênero dentro do
        # vetor e devolve honky-tonk, que é o análogo musical do forró.
        por_vetor = _ordenar_por_vetor(candidatas, sementes) if nivel == 2 else None
        if por_vetor is not None:
            candidatas["match"], candidatas["semente"] = por_vetor
        else:
            # Cada candidata vale o quanto vale para a semente mais próxima.
            melhores = [max(((match(linha, s.alvo), s.rotulo) for s in sementes),
                            key=lambda par: par[0])
                        for _, linha in candidatas.iterrows()]
            candidatas["match"] = [m for m, _ in melhores]
            candidatas["semente"] = [r for _, r in melhores]
        for _, linha in candidatas.sort_values(
                "match", ascending=False, kind="stable").iterrows():
            if len(escolhidas) >= limite:
                return
            chave = linha.get("track_id", (linha["faixa"], linha["artista"]))
            if chave in vistas:
                continue
            vistas.add(chave)
            escolhidas.append(linha)


def _vazio_com_semente(base: pd.DataFrame) -> pd.DataFrame:
    """Zero linhas, com as colunas que a UI lê sem checar antes."""
    return base.iloc[0:0].assign(match=pd.Series(dtype="int64"),
                                 semente=pd.Series(dtype="object"))


def garimpar_por_sementes(base: pd.DataFrame, sementes: Sequence[Semente],
                          teto: int, limite: int = 8,
                          variar: bool = False) -> pd.DataFrame:
    """Vizinhos de cada semente, intercalados — não vizinhos da média delas.

    Cada semente procura no próprio vocabulário e ranqueia por afinidade com o
    próprio vetor. Depois as listas são intercaladas em rodízio, para que as
    oito joias cubram a amplitude de quem ouve, em vez de serem oito variações
    da faixa mais representativa dela.

    Devolve a coluna `semente` com o rótulo de quem trouxe cada joia, que a UI
    exibe: saber que uma faixa entrou "porque você ouve Only Love" transforma
    uma recomendação ruim em algo legível, em vez de misteriosa.
    """
    base = elegiveis_para_garimpo(base)
    base = base[base["popularidade"] <= teto]
    if base.empty or not sementes:
        return _vazio_com_semente(base)

    filas: list[list[pd.Series]] = []
    for semente in sementes:
        pool, nivel = _pool_da_semente(base, semente)
        pool = pool.copy()
        if pool.empty:
            continue
        # Semente que perdeu o gênero procura no espaço aprendido. É o caso
        # da Calcinha Preta com teto baixo: forró não tem cauda obscura, e
        # ranquear o catálogo inteiro por cinco atributos de áudio devolvia
        # j-idol. O vetor carrega gênero dentro e devolve honky-tonk.
        por_vetor = (_ordenar_por_vetor(pool, [semente])
                     if nivel == SEM_GENERO else None)
        if por_vetor is not None:
            pool["match"], pool["semente"] = por_vetor
        else:
            pool["match"] = [match(linha, semente.alvo)
                             for _, linha in pool.iterrows()]
            pool["semente"] = semente.rotulo
        ordenada = pool.sort_values("match", ascending=False, kind="stable")
        # Cada semente também escolhe entre empatadas por variedade e por
        # sorteio: sem isto, garimpar duas vezes com o mesmo artista devolvia
        # exatamente as mesmas joias.
        escolha = _diversificar(ordenada, limite, variar)
        filas.append([linha for _, linha in escolha.iterrows()])

    # Rodízio: a melhor de cada semente, depois a segunda melhor de cada.
    escolhidas: list[pd.Series] = []
    vistas: set[Any] = set()
    for rodada in range(limite):
        for fila in filas:
            if len(escolhidas) >= limite:
                break
            if rodada >= len(fila):
                continue
            linha = fila[rodada]
            chave = linha.get("track_id", (linha["faixa"], linha["artista"]))
            if chave in vistas:
                continue
            vistas.add(chave)
            escolhidas.append(linha)
        if len(escolhidas) >= limite:
            break
    # As sementes procuram estrito; se faltou, o complemento alarga.
    if len(escolhidas) < limite:
        _completar(base, sementes, escolhidas, vistas, limite)
    if not escolhidas:
        return _vazio_com_semente(base)
    # O rodízio decide QUAIS oito, não em que ordem elas aparecem. Deixar a
    # ordem do rodízio vazar para a tela intercala 68%, 84%, 77%, 98% e parece
    # aleatório para quem lê. A seleção continua cobrindo todas as sementes; a
    # exibição é do melhor para o pior.
    return (pd.DataFrame(escolhidas)
            .sort_values("match", ascending=False, kind="stable")
            .reset_index(drop=True))


def teto_minimo_util(base: pd.DataFrame) -> int | None:
    """Menor teto de popularidade que ainda devolve alguma joia neste universo.

    Existe porque alguns gêneros deste catálogo não têm cauda obscura: os
    quatro brasileiros só aparecem a partir de 23 a 43 de popularidade, então
    na posição padrão do slider eles vêm sempre vazios. Dizer "aumenta a
    popularidade" sem dizer até quanto deixa a pessoa tateando.

    Devolve None quando não há faixa elegível nenhuma — aí subir o slider não
    resolve, e a dica tem que ser outra.
    """
    elegiveis = elegiveis_para_garimpo(base)
    if elegiveis.empty:
        return None
    return int(elegiveis["popularidade"].min())


def cobertura(base: pd.DataFrame, teto: int) -> int:
    """% do universo elegível que passa no filtro de popularidade.

    Mede sobre o mesmo universo que o garimpo percorre, senão o número na
    tela descreveria uma busca diferente da que aconteceu.
    """
    base = elegiveis_para_garimpo(base)
    if base.empty:
        return 0
    return round_js(len(base[base["popularidade"] <= teto]) / len(base) * 100)


def rotulo_profundidade(teto: int) -> str:
    """Nome amigável da faixa de popularidade escolhida no slider.

    Usa os mesmos limites do selo de raridade, para o texto do slider e o selo
    do cartão nunca discordarem.
    """
    if teto <= BANDAS_DE_RARIDADE[0][0]:
        return "Praticamente invisível"
    if teto <= BANDAS_DE_RARIDADE[1][0]:
        return "Bem underground"
    if teto <= BANDAS_DE_RARIDADE[2][0]:
        return "Conhecida em nicho"
    return "Começando a aparecer"


def humor_da_faixa(faixa: Mapping[str, Any]) -> str:
    """Expressão da mascote que combina com a faixa.

    Se a faixa já traz o mood do cluster, usamos a expressão daquele mood: a
    carinha ao lado do nome não pode discordar do rótulo mostrado logo abaixo
    dela. Sem essa coluna, cai nos limiares herdados do protótipo.
    """
    mood = faixa.get("mood")
    if mood:
        apresentacao = artefatos.APRESENTACAO.get(mood)
        if apresentacao:
            return apresentacao["humor"]

    if float(faixa["valencia"]) < .3:
        return "triste"
    if float(faixa["energia"]) > .75:
        return "treino"
    if float(faixa["instrumentalidade"]) > .7:
        return "foco"
    return "chill"


def email_valido(email: str) -> bool:
    """Valida o e-mail com a mesma regex do protótipo."""
    return bool(re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email.strip()))


def nome_do_email(email: str) -> str:
    """Deriva um nome apresentável a partir do trecho antes do @."""
    local = re.sub(r"[._-]", " ", email.split("@")[0])
    return re.sub(r"\b\w", lambda m: m.group().upper(), local).strip()


def montar_resultado(catalogo: pd.DataFrame, artistas: pd.DataFrame,
                     vibes: Sequence[str], generos: Sequence[str],
                     favoritos: Sequence[str], teto: int) -> dict[str, Any]:
    """Garimpa com os critérios combinados do passo 1 e devolve o que a UI exibe.

    Gênero(s) filtram o universo de busca; vibe(s), gênero(s) e artista(s)
    formam o alvo, um vetor por grupo escolhido.
    """
    base = universo(catalogo, generos, vibes)
    criterios = criterios_ativos(catalogo, artistas, vibes, generos, favoritos)
    if not criterios:
        raise ValueError("montar_resultado needs at least one active criterion")

    alvo = media_de_vetores([criterio.alvo for criterio in criterios])
    # Artistas escolhidos viram sementes: cada um procura nos próprios
    # gêneros, e a média entre dois artistas distantes deixa de ser o alvo.
    # Sem artista escolhido não há semente e a busca segue como sempre foi —
    # vibe é a média medida de um cluster, então ali o centroide é honesto.
    sementes = sementes_de_artistas(catalogo, artistas, favoritos)
    achadas = (garimpar_por_sementes(base, sementes, teto, variar=True)
               if sementes else garimpar(base, alvo, teto, variar=True))
    if not achadas.empty and "generos" in achadas.columns:
        procurados = familias.expandir(generos) if generos else set()
        achadas = achadas.copy()
        achadas["genero"] = [_genero_visivel(linha, procurados)
                             for _, linha in achadas.iterrows()]
    return {
        "teto_minimo": teto_minimo_util(base),
        "titulo": "Joias — " + " · ".join(c.titulo for c in criterios),
        "ctx": " e ".join(c.ctx for c in criterios),
        "cobertura": cobertura(base, teto),
        "faixas": achadas.to_dict("records"),
        "media_match": round_js(achadas["match"].mean()) if len(achadas) else 0,
        "legenda": "Clique em cada faixa pra ver os atributos de áudio.",
        "sub_match": "afinidade com o alvo escolhido",
        "sub_cobertura": "do catálogo elegível cabe neste filtro",
        # com várias vibes não há uma cor só; o protótipo usa lima no cabeçalho
        "cor": VIBES[vibes[0]]["cor"] if len(vibes) == 1 else LIMA,
    }


# Abaixo disto a média das faixas encontradas é ruído, não perfil: uma ou duas
# faixas descrevem um momento, não um gosto.
MINIMO_DE_FAIXAS_CRUZADAS = 5


class PerfilDoUsuario(NamedTuple):
    """O perfil de áudio de quem está conectado, e de onde ele veio."""

    alvo: dict[str, float]
    encontradas: int      # faixas do usuário que existem no nosso catálogo
    pedidas: int          # faixas que o Spotify devolveu
    e_real: bool          # False quando caiu no perfil de exemplo
    origem: str = "exemplo"   # "faixas" | "generos" | "exemplo"
    generos_usados: tuple[str, ...] = ()
    # As faixas cruzadas, uma a uma. O `alvo` acima segue existindo porque a
    # tela desenha as barras do perfil a partir dele; a recomendação usa
    # estas, que preservam o que a média destrói.
    sementes: tuple[Semente, ...] = ()
    # Onde as faixas cruzadas caem no eixo da popularidade. None quando não há
    # base para a leitura — perfil de exemplo, ou poucas faixas cruzadas.
    raridade: "GostoDeRaridade | None" = None


def perfil_do_usuario(catalogo: pd.DataFrame,
                      faixas_do_usuario: Sequence[Mapping[str, Any]],
                      generos_do_usuario: Sequence[str] | None = None
                      ) -> PerfilDoUsuario:
    """Monta o perfil de áudio cruzando as faixas do usuário com o catálogo.

    Os atributos nunca vêm da API — o Spotify descontinuou `/v1/audio-features`
    para apps novos. Eles vêm do nosso catálogo, e o `track_id` é a chave. O
    catálogo já está deduplicado por `track_id`, que é o que torna esse
    cruzamento seguro: no dado bruto a mesma faixa aparece uma vez por gênero e
    um merge direto multiplicaria linhas.

    Quando o cruzamento não acha nada, devolve o perfil de exemplo com
    `e_real=False`, para a tela poder dizer isso em vez de fingir.
    """
    pedidas = len(faixas_do_usuario)
    ids = {f["id"] for f in faixas_do_usuario if f.get("id")}
    if ids and "track_id" in catalogo.columns:
        encontradas = catalogo[catalogo["track_id"].isin(ids)]
    else:
        encontradas = catalogo.iloc[0:0]

    # 1. Caminho bom: cada faixa que a pessoa ouve e nós temos vira semente.
    if len(encontradas) >= MINIMO_DE_FAIXAS_CRUZADAS:
        return PerfilDoUsuario(media(encontradas), len(encontradas), pedidas,
                               True, "faixas",
                               sementes=sementes_de_faixas(encontradas),
                               raridade=gosto_de_raridade(catalogo, encontradas))

    # 2. Rede: os gêneros dos artistas favoritos, aproximados pelo centroide
    #    deles no catálogo. Menos preciso, e a tela diz que foi por aqui.
    alvo_generos, usados = _centroide_dos_generos(catalogo, generos_do_usuario)
    if alvo_generos is not None:
        return PerfilDoUsuario(alvo_generos, len(encontradas), pedidas,
                               True, "generos", usados)

    # 3. Sem nada em que se apoiar: exemplo, dito como exemplo.
    return PerfilDoUsuario(dict(PERFIL_USUARIO), len(encontradas), pedidas,
                           False, "exemplo")


def sementes_de_faixas(faixas: pd.DataFrame) -> tuple[Semente, ...]:
    """Uma semente por faixa do catálogo — o vetor e os gêneros de cada uma."""
    saida: list[Semente] = []
    for indice, linha in faixas.iterrows():
        generos = tuple(linha["generos"]) if "generos" in faixas.columns else ()
        # Nome e artista: só o nome obriga a pessoa a adivinhar de qual faixa
        # dela veio a recomendação — "Manchete dos Jornais" não diz Calcinha
        # Preta para quem tem cinquenta faixas mais ouvidas.
        artista = (str(linha["artista"]).split(";")[0].strip()
                   if "artista" in faixas.columns else "")
        rotulo = f"{linha['faixa']} ({artista})" if artista else str(linha["faixa"])
        saida.append(Semente({a: float(linha[a]) for a in ATRIBUTOS},
                             rotulo, generos, (int(indice),)))
    return tuple(saida)


def sementes_de_artistas(catalogo: pd.DataFrame, artistas: pd.DataFrame,
                         favoritos: Sequence[str]) -> tuple[Semente, ...]:
    """Uma semente por artista escolhido, com os gêneros do catálogo dele.

    Os gêneros vêm das faixas do artista no catálogo, não da coluna `genero`
    da tabela de artistas: aquela guarda um rótulo só, e um artista costuma
    ocupar vários gêneros vizinhos que servem de vocabulário de busca.
    """
    escolhidos = artistas[artistas["artista"].isin(list(favoritos))]
    saida: list[Semente] = []
    for _, linha in escolhidos.iterrows():
        nome = str(linha["artista"])
        generos: tuple[str, ...] = ()
        if "generos" in catalogo.columns:
            dele = catalogo[catalogo["artista"].str.contains(
                nome, regex=False, na=False)]
            generos = tuple(sorted({g for lista in dele["generos"]
                                    for g in lista}))
        linhas = tuple(int(i) for i in dele.index) if "generos" in catalogo.columns else ()
        saida.append(Semente({a: float(linha[a]) for a in ATRIBUTOS},
                             nome, generos, linhas))
    return tuple(saida)


def _centroide_dos_generos(catalogo: pd.DataFrame,
                           generos_do_usuario: Sequence[str] | None
                           ) -> tuple[dict[str, float] | None, tuple[str, ...]]:
    """Centroide das faixas do catálogo nos gêneros que o usuário mais ouve.

    O Spotify devolve gêneros por artista com vocabulário próprio ("brazilian
    rock", "mpb"), que nem sempre existe no nosso `track_genre`. Ficamos só com
    os que existem — se nenhum existir, não há aproximação a fazer.
    """
    if not generos_do_usuario:
        return None, ()
    coluna = "generos" if "generos" in catalogo.columns else None
    if coluna is None:
        return None, ()
    procurados = {g.lower() for g in generos_do_usuario}
    pertence = catalogo[coluna].apply(
        lambda lista: any(str(g).lower() in procurados for g in lista))
    faixas = catalogo[pertence]
    if faixas.empty:
        return None, ()
    presentes = {str(g).lower() for lista in faixas[coluna] for g in lista}
    return media(faixas), tuple(sorted(procurados & presentes))


# Quartis da popularidade do catálogo, ignorando as faixas em 0 — que são
# dado não capturado, não música sem ouvintes. São os limites do selo, e vêm
# da forma do catálogo em vez de números redondos que alguém escolheu.
QUARTIS_DE_POPULARIDADE = (22, 37, 50)

# Do mais escondido ao mais conhecido, na ordem dos quartis acima. O selo
# descreve as FAIXAS, não a pessoa: com oito faixas cruzadas de cinquenta,
# "você é um garimpeiro nato" seria horóscopo, e "suas faixas são mais
# escondidas que 78% do catálogo" é medição.
SELOS_DE_GOSTO: tuple[tuple[str, str], ...] = (
    ("Garimpeiro de raridade", "suas faixas vivem na parte escondida do catálogo"),
    ("Fora do óbvio",          "você já ouve longe do que toca no rádio"),
    ("Um pé no mainstream",    "metade conhecida, metade escondida"),
    ("Fã de hits",             "você ouve o que muita gente ouve, então tem joia esperando"),
)


class GostoDeRaridade(NamedTuple):
    """Onde as faixas cruzadas de alguém caem no eixo da popularidade."""

    selo: str
    descricao: str
    popularidade: int      # mediana das faixas cruzadas
    percentil: int         # % do catálogo abaixo dessa mediana
    faixas_usadas: int     # quantas entraram na conta


def gosto_de_raridade(catalogo: pd.DataFrame,
                      encontradas: pd.DataFrame) -> GostoDeRaridade | None:
    """Lê o quão fora do comum são as faixas que a pessoa já ouve.

    Mediana, não média: são poucas faixas, e um hit solto no meio delas não
    deve mover a leitura.

    Faixas em popularidade 0 saem da conta. É a mesma decisão que o notebook
    tomou ao agregar com `max`: zero significa não capturado, e contá-lo
    entregaria um selo de raridade conquistado por falha nossa.

    Devolve None quando não há base — sem faixas cruzadas não há leitura, e
    inventar uma violaria o princípio 2 da constituição.
    """
    if encontradas.empty or "popularidade" not in encontradas.columns:
        return None
    validas = encontradas[encontradas["popularidade"] > 0]
    if len(validas) < MINIMO_DE_FAIXAS_CRUZADAS:
        return None

    mediana = float(validas["popularidade"].median())
    catalogo_valido = catalogo[catalogo["popularidade"] > 0]["popularidade"]
    percentil = float((catalogo_valido < mediana).mean() * 100)

    posicao = sum(mediana > limite for limite in QUARTIS_DE_POPULARIDADE)
    selo, descricao = SELOS_DE_GOSTO[posicao]
    return GostoDeRaridade(selo, descricao, round_js(mediana),
                           round_js(percentil), len(validas))


def descrever_perfil(alvo: Mapping[str, float]) -> str:
    """Frase curta sobre o perfil, derivada dos números e não escrita à mão."""
    # Adjetivos, não substantivos: eles precisam se juntar com "e" e soar como
    # frase. Uma versão anterior devolvia "com vocais com elétrica".
    ADJETIVOS = {
        "energia": ("calma", "energética"),
        "valencia": ("melancólica", "alegre"),
        "dancabilidade": ("pouco dançante", "dançante"),
        "instrumentalidade": ("cantada", "instrumental"),
        "acustica": ("elétrica", "acústica"),
    }
    # Os dois atributos que mais se afastam do meio são os que caracterizam.
    fortes = sorted(ATRIBUTOS, key=lambda a: -abs(float(alvo[a]) - .5))[:2]
    return " e ".join(ADJETIVOS[a][float(alvo[a]) >= .5] for a in fortes)


def montar_resultado_conta(catalogo: pd.DataFrame,
                           perfil: PerfilDoUsuario | None = None) -> dict[str, Any]:
    """Garimpo do modo testador: cruza o perfil do usuário com o catálogo."""
    if perfil is None:
        perfil = PerfilDoUsuario(dict(PERFIL_USUARIO), 0, 0, False)
    # Com faixas cruzadas, cada uma procura no próprio território. Sem elas
    # (perfil por gênero ou de exemplo) só resta o centroide.
    if perfil.sementes:
        achadas = garimpar_por_sementes(catalogo, perfil.sementes, TETO_CONTA,
                                        variar=True)
        ctx = "ela é vizinha de uma das suas mais ouvidas"
    else:
        achadas = garimpar(catalogo, perfil.alvo, TETO_CONTA)
        ctx = "ela combina com o perfil médio das suas mais ouvidas"
    if not achadas.empty and "generos" in achadas.columns:
        achadas = achadas.copy()
        achadas["genero"] = [_genero_visivel(linha, set())
                             for _, linha in achadas.iterrows()]
    return {
        "titulo": "Joias pra você",
        "ctx": ctx,
        "cobertura": cobertura(catalogo, TETO_CONTA),
        "faixas": achadas.to_dict("records"),
        "media_match": round_js(achadas["match"].mean()) if len(achadas) else 0,
        "perfil": perfil,
        "legenda": f"Nenhuma passa de {TETO_CONTA} de popularidade.",
        "sub_match": "afinidade com o seu perfil",
        "sub_cobertura": "do catálogo elegível para o seu perfil",
        "cor": ROSA,
    }
