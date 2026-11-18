"""Playlist de foco: os melhores sons que cabem numa sessao (tabulacao).

Problema do Galene: a pessoa vai estudar por um tempo fixo (ex.: 50 min) e
o Galene Player precisa montar uma playlist sem repetir faixas, que caiba
no tempo da sessao e tenha a maior nota possivel. A nota de cada som vem
do questionario de perfil (afinidade de 1 a 5) e ganha um bonus quando o
tipo de som e o indicado para o nivel de ruido do ambiente naquele momento.

E a mochila 0/1:
    - capacidade da mochila = minutos da sessao;
    - itens               = sons, cada um com duracao (peso) e nota (valor);
    - cada som entra no maximo uma vez.

Resolvida por tabulacao, como na confeitaria da apostila (5.2):
    tabela[i][t] = melhor nota usando so os i primeiros sons em t minutos.

Todas as funcoes deste modulo sao puras: sem print e sem input.
"""

from galene.ruido import classificar_ruido

# Tipos de som que o Galene recomenda em cada faixa de ruido do ambiente.
# Ambiente silencioso: sons suaves. Ambiente barulhento: mascaramento,
# que "cobre" o ruido externo sem precisar aumentar o volume.
TIPOS_RECOMENDADOS = {
    "Silencioso": {"natureza", "binaural"},
    "Tranquilo": {"lofi", "binaural"},
    "Moderado": {"lofi", "binaural"},
    "Intenso": {"mascaramento", "lofi"},
    "Crítico": {"mascaramento"},
}

PONTOS_POR_AFINIDADE = 10    # afinidade 1 a 5 vira 10 a 50 pontos
BONUS_TIPO_RECOMENDADO = 25  # pontos extras se o som combina com o ambiente


def nota_do_som(som, faixa_do_ambiente):
    """Nota de um som para o ambiente atual. O(1).

    >>> nota_do_som({"tipo": "lofi", "afinidade": 4}, "Moderado")
    65
    >>> nota_do_som({"tipo": "lofi", "afinidade": 4}, "Crítico")
    40
    """
    # Parte 1: o quanto a pessoa gosta do som (vem do questionario).
    nota = som["afinidade"] * PONTOS_POR_AFINIDADE

    # Parte 2: bonus se o tipo do som e o indicado para o ruido do momento.
    # .get(..., set()) evita erro se a faixa nao estiver no dicionario.
    if som["tipo"] in TIPOS_RECOMENDADOS.get(faixa_do_ambiente, set()):
        nota += BONUS_TIPO_RECOMENDADO
    return nota


def calcular_notas(sons, decibeis_do_ambiente):
    """Lista de notas, na mesma ordem dos sons. O(n)."""
    # Primeiro descobre a faixa do ambiente (ex.: 78 dB -> "Intenso")...
    faixa, _ = classificar_ruido(decibeis_do_ambiente)
    # ...e depois calcula a nota de cada som para essa faixa.
    return [nota_do_som(som, faixa) for som in sons]


def matriz_de_zeros(linhas, colunas):
    """Mesma funcao da apostila (confeitaria). O(linhas * colunas)."""
    tabela = []
    for _ in range(linhas):
        # Cada linha e uma lista NOVA. (Fazer [[0]*colunas]*linhas seria um
        # erro classico: todas as linhas seriam a mesma lista.)
        tabela.append([0] * colunas)
    return tabela


def melhor_playlist(duracoes, notas, minutos_da_sessao):
    """Mochila 0/1 por tabulacao. Devolve (melhor_nota, indices_escolhidos).

    Complexidade: O(n * T) de tempo e de memoria, com n sons e T minutos.
    Para n = 30 sons e T = 90 minutos sao so cerca de 2.800 casas na tabela,
    contra 2^30 (mais de 1 bilhao) de combinacoes na forca bruta.

    >>> melhor_playlist([20, 30, 25], [50, 70, 60], 50)
    (120, [0, 1])
    """
    # Validacoes da entrada.
    if len(duracoes) != len(notas):
        raise ValueError("Cada som precisa ter uma duração e uma nota.")
    if minutos_da_sessao < 0:
        raise ValueError("O tempo da sessão não pode ser negativo.")
    if any(d <= 0 for d in duracoes):
        raise ValueError("A duração de cada som precisa ser positiva.")

    n = len(duracoes)

    # Tabela com (n + 1) linhas e (minutos + 1) colunas, toda com zero.
    #   linha i  = "posso usar so os i primeiros sons"
    #   coluna t = "tenho t minutos disponiveis"
    # A linha 0 (nenhum som) e a coluna 0 (zero minutos) ficam com nota 0.
    tabela = matriz_de_zeros(n + 1, minutos_da_sessao + 1)

    # Preencher a tabela linha por linha (um som novo por linha).
    for i in range(1, n + 1):
        # O som da linha i e o de indice i - 1 nas listas (que comecam em 0).
        duracao = duracoes[i - 1]
        nota = notas[i - 1]

        for t in range(minutos_da_sessao + 1):
            # Opcao 1: NAO usar este som.
            # A melhor nota e a mesma de antes, com os sons anteriores (linha de cima).
            sem_o_som = tabela[i - 1][t]
            tabela[i][t] = sem_o_som

            # Opcao 2: USAR este som, se ele couber nos t minutos.
            # Sobram t - duracao minutos para os sons anteriores, cuja melhor
            # nota ja esta calculada na linha de cima. Por isso cada som entra
            # no maximo uma vez (olhamos a linha i - 1, e nao a linha i).
            if duracao <= t:
                com_o_som = tabela[i - 1][t - duracao] + nota
                # Fica com a melhor das duas opcoes.
                if com_o_som > sem_o_som:
                    tabela[i][t] = com_o_som

    # A resposta esta na ultima casa: todos os sons e todos os minutos.
    escolhidos = reconstruir_escolhas(tabela, duracoes, minutos_da_sessao)
    return tabela[n][minutos_da_sessao], escolhidos


def reconstruir_escolhas(tabela, duracoes, minutos_da_sessao):
    """Volta pela tabela descobrindo quais sons entraram. O(n).

    Se tabela[i][t] mudou em relacao a linha de cima, o som i-1 foi usado.
    """
    escolhidos = []
    t = minutos_da_sessao  # comeca na ultima coluna (todos os minutos)

    # Sobe da ultima linha ate a linha 1.
    for i in range(len(duracoes), 0, -1):
        # Se o valor mudou em relacao a linha de cima, a "opcao 2" ganhou,
        # ou seja, o som i - 1 entrou na playlist.
        if tabela[i][t] != tabela[i - 1][t]:
            escolhidos.append(i - 1)
            t -= duracoes[i - 1]  # desconta os minutos que esse som ocupou

    # Os sons foram achados do ultimo para o primeiro; invertemos a ordem.
    escolhidos.reverse()
    return escolhidos


def melhor_nota_forca_bruta(duracoes, notas, minutos, i=0):
    """Testa todas as combinacoes (recursao sem memoizacao): O(2^n).

    Existe apenas para a analise de eficiencia e para os testes:
    confirma que a tabulacao acha a mesma resposta, e mostra o quanto
    ela e mais rapida.
    """
    # Caso base: ja decidimos sobre todos os sons.
    if i == len(duracoes):
        return 0

    # Para cada som ha duas escolhas, e testamos as duas (por isso 2^n):
    # 1) pular o som i
    sem_o_som = melhor_nota_forca_bruta(duracoes, notas, minutos, i + 1)

    # Se o som nao cabe no tempo que sobrou, so resta pular.
    if duracoes[i] > minutos:
        return sem_o_som

    # 2) usar o som i e decidir o resto com menos minutos
    com_o_som = notas[i] + melhor_nota_forca_bruta(duracoes, notas, minutos - duracoes[i], i + 1)
    return max(sem_o_som, com_o_som)


def montar_playlist(sons, decibeis_do_ambiente, minutos_da_sessao):
    """Funcao principal: monta a playlist para o ambiente e o tempo informados.

    Devolve um dicionario com a faixa do ambiente, os sons escolhidos,
    a nota total e os minutos usados.
    """
    # 1) Prepara a entrada da mochila: uma nota e uma duracao por som.
    faixa, _ = classificar_ruido(decibeis_do_ambiente)
    notas = calcular_notas(sons, decibeis_do_ambiente)
    duracoes = [som["duracao_min"] for som in sons]

    # 2) Resolve a mochila por tabulacao.
    nota_total, indices = melhor_playlist(duracoes, notas, minutos_da_sessao)

    # 3) Troca os indices pelos sons completos, junto com a nota de cada um.
    # {**som, "nota": ...} copia o dicionario do som e acrescenta a chave "nota".
    escolhidos = []
    for i in indices:
        escolhidos.append({**sons[i], "nota": notas[i]})

    return {
        "faixa_do_ambiente": faixa,
        "sons": escolhidos,
        "nota_total": nota_total,
        "minutos_usados": sum(som["duracao_min"] for som in escolhidos),
        "minutos_da_sessao": minutos_da_sessao,
    }
