"""Rota tranquila: o caminho com menos exposicao a ruido (Dijkstra).

Problema do Galene: quem tem sensibilidade auditiva nao quer so o caminho
mais curto ate a faculdade ou o trabalho; quer o caminho que evita as ruas
mais barulhentas, mesmo que fique um pouco mais longo.

Modelagem como grafo:
    - vertices: locais do bairro (casa, estacao, praca, faculdade...);
    - arestas: trechos de rua, com comprimento em metros e ruido medio em dB;
    - custo de um trecho = metros * peso do ruido daquele trecho.

O grafo e um dicionario de listas de adjacencia:
    {"casa": [("padaria", 200, 52), ("rua_arvores", 350, 42)], ...}
Cada vizinho e uma tupla (destino, metros, decibeis).

Todas as funcoes deste modulo sao puras: recebem dados, devolvem dados,
nao fazem print nem input.
"""

# heapq e a fila de prioridade do Python (um "heap" de minimo):
# heappush coloca um item e heappop tira sempre o MENOR, os dois em O(log n).
import heapq

from galene.ruido import classificar_ruido, NOMES_DAS_FAIXAS

# Custo de um local que ainda nao sabemos como alcancar.
INFINITO = float("inf")


def custo_do_trecho(metros, decibeis, sensibilidade):
    """Custo de andar um trecho, considerando o ruido. O(1).

    sensibilidade = 0 -> so a distancia conta (rota mais curta);
    sensibilidade = 1 -> peso padrao do ruido;
    sensibilidade = 2 -> pessoa muito sensivel, o ruido pesa o dobro.

    >>> custo_do_trecho(100, 30, 1)      # Silencioso, fator 1.0
    100.0
    >>> custo_do_trecho(100, 80, 1)      # Intenso, fator 2.5
    250.0
    >>> custo_do_trecho(100, 80, 0)      # sensibilidade 0: so metros
    100.0
    """
    # Validacoes: o Dijkstra so funciona com custos que nao sao negativos.
    if metros < 0:
        raise ValueError("O comprimento do trecho não pode ser negativo.")
    if sensibilidade < 0:
        raise ValueError("A sensibilidade não pode ser negativa.")

    # Descobre o fator da faixa de ruido do trecho (1.0 a 4.0).
    _, fator = classificar_ruido(decibeis)

    # (fator - 1) e o "extra" de incomodo daquela faixa.
    # Multiplicamos esse extra pela sensibilidade da pessoa:
    #   sensibilidade 0 -> custo = metros (o ruido some da conta)
    #   sensibilidade 1 -> custo = metros * fator
    #   sensibilidade 2 -> o extra do ruido conta em dobro
    return metros * (1 + sensibilidade * (fator - 1))


def dijkstra(grafo, origem, sensibilidade=1):
    """Menor custo da origem ate todos os locais, com fila de prioridade.

    Devolve (custos, anteriores):
        custos[v]     = menor custo para chegar em v (INFINITO se nao chega)
        anteriores[v] = de onde viemos para chegar em v pelo melhor caminho

    Complexidade: O((V + E) log V), com V locais e E trechos de rua.
    Cada trecho coloca no maximo um item no heap, e cada operacao no heap
    custa O(log). Itens velhos (com custo maior que o atual) sao ignorados
    ao sair do heap ("remocao preguicosa"), em vez de procurar e apagar.
    """
    # Se a origem nao existe no grafo, nao ha o que calcular.
    if origem not in grafo:
        raise ValueError(f"Local de origem desconhecido: {origem}")

    # No comeco, nao sabemos chegar em nenhum lugar: todos com custo infinito.
    custos = {local: INFINITO for local in grafo}
    # E ninguem tem "anterior" ainda (None = nao sabemos de onde viemos).
    anteriores = {local: None for local in grafo}
    # Chegar na propria origem nao custa nada.
    custos[origem] = 0.0

    # A fila de prioridade guarda tuplas (custo ate aqui, local).
    # O heap compara pelo primeiro item da tupla, entao sai sempre
    # o local com MENOR custo conhecido.
    fila = [(0.0, origem)]

    while fila:
        # Tira da fila o local mais barato de alcancar ate agora. O(log V)
        custo_atual, local = heapq.heappop(fila)

        # Remocao preguicosa: o mesmo local pode estar na fila mais de uma vez.
        # Se este item tem custo maior que o melhor ja registrado, ele e velho.
        if custo_atual > custos[local]:
            continue

        # Olha todos os trechos que saem deste local ("relaxamento").
        for vizinho, metros, decibeis in grafo[local]:
            # Custo para chegar no vizinho passando por 'local'.
            novo_custo = custo_atual + custo_do_trecho(metros, decibeis, sensibilidade)

            # Achamos um caminho melhor do que o que conheciamos?
            if novo_custo < custos[vizinho]:
                custos[vizinho] = novo_custo     # guarda o novo melhor custo
                anteriores[vizinho] = local      # lembra por onde viemos
                heapq.heappush(fila, (novo_custo, vizinho))  # agenda o vizinho, O(log V)

    return custos, anteriores


def dijkstra_ingenuo(grafo, origem, sensibilidade=1):
    """Mesmo resultado do dijkstra, mas SEM heap: O(V^2).

    A cada passo, procura o local nao visitado de menor custo percorrendo
    todos os locais. Existe apenas para a analise de eficiencia, para
    mostrar na pratica a diferenca que a fila de prioridade faz.
    """
    if origem not in grafo:
        raise ValueError(f"Local de origem desconhecido: {origem}")

    # Mesma inicializacao do dijkstra com heap.
    custos = {local: INFINITO for local in grafo}
    anteriores = {local: None for local in grafo}
    custos[origem] = 0.0
    visitados = set()  # locais cujo menor custo ja e definitivo

    # Repete no maximo V vezes: em cada volta, um local vira definitivo.
    for _ in range(len(grafo)):
        # Busca linear do menor custo entre os nao visitados: O(V).
        # E exatamente esta busca que o heap troca por O(log V).
        local = None
        for candidato in grafo:
            if candidato not in visitados and (local is None or custos[candidato] < custos[local]):
                local = candidato

        # Se o melhor que sobrou e infinito, o resto do grafo e inalcancavel.
        if local is None or custos[local] == INFINITO:
            break
        visitados.add(local)

        # Relaxamento igual ao da versao com heap (so que sem fila).
        for vizinho, metros, decibeis in grafo[local]:
            novo_custo = custos[local] + custo_do_trecho(metros, decibeis, sensibilidade)
            if novo_custo < custos[vizinho]:
                custos[vizinho] = novo_custo
                anteriores[vizinho] = local

    return custos, anteriores


def reconstruir_caminho(anteriores, origem, destino):
    """Monta a lista de locais da origem ao destino. O(tamanho do caminho).

    Devolve [] se o destino nao e alcancavel.

    >>> reconstruir_caminho({"a": None, "b": "a", "c": "b"}, "a", "c")
    ['a', 'b', 'c']
    >>> reconstruir_caminho({"a": None, "b": None}, "a", "b")
    []
    """
    # Caso especial: ja estamos no destino.
    if destino == origem:
        return [origem]

    # Se o destino nao tem anterior, o Dijkstra nunca chegou nele.
    if anteriores.get(destino) is None:
        return []

    # Anda de tras para frente: destino -> anterior -> anterior ... -> origem.
    caminho = []
    local = destino
    while local is not None:
        caminho.append(local)
        local = anteriores[local]  # a origem tem anterior None, e o laco para

    # O caminho foi montado ao contrario; invertemos para ir da origem ao destino.
    caminho.reverse()
    return caminho


def buscar_trecho(grafo, de, para):
    """Devolve (metros, decibeis) do trecho mais curto entre dois locais vizinhos."""
    # Junta todos os trechos que ligam 'de' a 'para' (normalmente e so um).
    trechos = [(metros, db) for vizinho, metros, db in grafo[de] if vizinho == para]
    if not trechos:
        raise ValueError(f"Não existe trecho entre {de} e {para}.")
    # min compara primeiro os metros: fica com o trecho mais curto.
    return min(trechos)


def resumir_caminho(grafo, caminho):
    """Calcula os numeros de um caminho: metros, ruido medio e metros por faixa.

    O ruido medio e ponderado pelos metros (um trecho longo pesa mais).
    """
    # Contador de metros em cada faixa, comecando em zero: {"Silencioso": 0, ...}
    metros_por_faixa = {nome: 0 for nome in NOMES_DAS_FAIXAS}
    metros_total = 0
    soma_db_ponderada = 0  # soma de (metros * dB), para a media ponderada
    pior_db = 0            # trecho mais barulhento do caminho

    # Percorre os trechos do caminho: (local 0 -> 1), (1 -> 2), ...
    for i in range(len(caminho) - 1):
        metros, decibeis = buscar_trecho(grafo, caminho[i], caminho[i + 1])
        faixa, _ = classificar_ruido(decibeis)
        metros_por_faixa[faixa] += metros
        metros_total += metros
        soma_db_ponderada += metros * decibeis
        pior_db = max(pior_db, decibeis)

    # Media ponderada: um trecho de 400 m conta mais que um de 100 m.
    # O if evita divisao por zero quando o caminho tem um local so.
    ruido_medio = soma_db_ponderada / metros_total if metros_total > 0 else 0

    return {
        "metros_total": metros_total,
        "ruido_medio_db": round(ruido_medio, 1),
        "pior_trecho_db": pior_db,
        "pior_faixa": classificar_ruido(pior_db)[0] if metros_total > 0 else "-",
        "metros_por_faixa": metros_por_faixa,
        # Indicador de impacto do projeto: metros nas faixas acima de 70 dB.
        "metros_intenso_ou_critico": metros_por_faixa["Intenso"] + metros_por_faixa["Crítico"],
    }


def rota_mais_tranquila(grafo, origem, destino, sensibilidade=1):
    """Funcao principal: a rota de menor exposicao a ruido e o resumo dela.

    Devolve um dicionario com o caminho, o custo e o resumo,
    ou None se o destino nao for alcancavel a partir da origem.
    """
    if destino not in grafo:
        raise ValueError(f"Local de destino desconhecido: {destino}")

    # 1) Calcula o menor custo da origem para todos os locais.
    custos, anteriores = dijkstra(grafo, origem, sensibilidade)

    # 2) Monta o caminho ate o destino escolhido.
    caminho = reconstruir_caminho(anteriores, origem, destino)
    if not caminho:
        return None  # nao ha como chegar

    # 3) Devolve o caminho com os numeros que a interface vai mostrar.
    return {
        "caminho": caminho,
        "custo": round(custos[destino], 1),
        "resumo": resumir_caminho(grafo, caminho),
    }


def comparar_rotas(grafo, origem, destino, sensibilidade=1):
    """Compara a rota mais curta (so metros) com a rota mais tranquila.

    Devolve (rota_curta, rota_tranquila). Qualquer uma pode ser None
    se nao houver caminho.
    """
    # Mesmo algoritmo, so muda a sensibilidade:
    # com 0 o ruido nao entra na conta, entao sai a rota mais curta.
    rota_curta = rota_mais_tranquila(grafo, origem, destino, sensibilidade=0)
    rota_tranquila = rota_mais_tranquila(grafo, origem, destino, sensibilidade)
    return rota_curta, rota_tranquila
