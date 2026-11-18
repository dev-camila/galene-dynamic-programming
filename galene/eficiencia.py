"""Analise pratica de eficiencia: medicao de tempo dos algoritmos.

Gera entradas cada vez maiores (com semente fixa, para o resultado ser
reproduzivel) e mede o tempo com time.perf_counter. Cada medicao compara
a versao eficiente com uma versao ingenua e confere se as duas dao a
mesma resposta, para provar que a versao rapida tambem esta correta.
"""

import math    # math.isclose, para comparar numeros com virgula
import random  # para sortear bairros e sons de teste
import time    # time.perf_counter, o relogio mais preciso do Python

from galene.rota_tranquila import dijkstra, dijkstra_ingenuo
from galene.playlist_foco import melhor_playlist, melhor_nota_forca_bruta


def medir_tempo(funcao, *argumentos):
    """Executa a funcao e devolve (resultado, segundos).

    *argumentos recebe quantos argumentos forem passados e repassa todos
    para a funcao. Assim a mesma medicao serve para qualquer algoritmo.
    """
    inicio = time.perf_counter()        # marca o relogio antes
    resultado = funcao(*argumentos)     # roda o algoritmo
    return resultado, time.perf_counter() - inicio  # tempo = depois - antes


def gerar_bairro_em_grade(lado, semente=42):
    """Bairro em grade lado x lado: cada esquina liga com a da direita e a de baixo.

    V = lado^2 esquinas e E ~ 2 * lado^2 trechos, com metros (50 a 400)
    e ruido (35 a 95 dB) sorteados.
    """
    # random.Random(semente) cria um sorteador proprio. Com a mesma semente,
    # os "sorteios" saem sempre iguais, entao a medicao pode ser repetida.
    sorteio = random.Random(semente)

    # Cada esquina e identificada por (linha, coluna).
    grafo = {(l, c): [] for l in range(lado) for c in range(lado)}

    for l in range(lado):
        for c in range(lado):
            # Liga a esquina com a da direita (l, c+1) e a de baixo (l+1, c).
            for vizinho in ((l, c + 1), (l + 1, c)):
                if vizinho in grafo:  # na borda da grade, o vizinho nao existe
                    metros = sorteio.randint(50, 400)
                    decibeis = sorteio.randint(35, 95)
                    # Mao dupla, como no bairro do projeto.
                    grafo[(l, c)].append((vizinho, metros, decibeis))
                    grafo[vizinho].append(((l, c), metros, decibeis))
    return grafo


def gerar_sons(quantidade, semente=42):
    """Listas de duracoes (5 a 30 min) e notas (10 a 65) sorteadas."""
    sorteio = random.Random(semente)
    duracoes = [sorteio.randint(5, 30) for _ in range(quantidade)]
    notas = [sorteio.randint(10, 65) for _ in range(quantidade)]
    return duracoes, notas


def mesmos_custos(custos_a, custos_b):
    """Compara dois dicionarios de custos com tolerancia de arredondamento.

    Numeros com virgula (float) podem diferir na ultima casa decimal
    dependendo da ordem das somas, por isso usamos math.isclose em vez de ==.
    """
    return custos_a.keys() == custos_b.keys() and all(
        math.isclose(custos_a[k], custos_b[k], rel_tol=1e-9) for k in custos_a
    )


def comparar_dijkstras(lados=(15, 30, 45)):
    """Dijkstra com heap x Dijkstra sem heap, em bairros de tamanho crescente."""
    resultados = []
    for lado in lados:
        grafo = gerar_bairro_em_grade(lado)  # lado 45 -> 2.025 esquinas
        # Roda as duas versoes partindo da esquina (0, 0) e mede o tempo.
        (custos_heap, _), tempo_heap = medir_tempo(dijkstra, grafo, (0, 0))
        (custos_ing, _), tempo_ing = medir_tempo(dijkstra_ingenuo, grafo, (0, 0))
        resultados.append({
            "esquinas": len(grafo),
            "tempo_heap": tempo_heap,
            "tempo_ingenuo": tempo_ing,
            # Prova de correcao: as duas versoes precisam dar os mesmos custos.
            "mesmo_resultado": mesmos_custos(custos_heap, custos_ing),
        })
    return resultados


def escalar_dijkstra(lados=(50, 100, 200)):
    """So o Dijkstra com heap, em bairros grandes (ate 40 mil esquinas).

    A versao sem heap nao entra aqui porque demoraria demais.
    """
    resultados = []
    for lado in lados:
        grafo = gerar_bairro_em_grade(lado)
        _, tempo = medir_tempo(dijkstra, grafo, (0, 0))
        resultados.append({"esquinas": len(grafo), "tempo_heap": tempo})
    return resultados


def comparar_playlists(quantidades=(10, 20, 30), minutos=90):
    """Tabulacao O(n*T) x forca bruta O(2^n), com quantidade crescente de sons.

    A forca bruta ainda corta galhos quando o som nao cabe no tempo que
    sobra, por isso cresce um pouco mais devagar que 2^n puro; mesmo assim
    o tempo dela explode, enquanto o da tabulacao quase nao muda.
    """
    resultados = []
    for quantidade in quantidades:
        duracoes, notas = gerar_sons(quantidade)
        (nota_tab, _), tempo_tab = medir_tempo(melhor_playlist, duracoes, notas, minutos)
        nota_fb, tempo_fb = medir_tempo(melhor_nota_forca_bruta, duracoes, notas, minutos)
        resultados.append({
            "sons": quantidade,
            "tempo_tabulacao": tempo_tab,
            "tempo_forca_bruta": tempo_fb,
            # Prova de correcao: as duas tecnicas precisam achar a mesma nota.
            "mesmo_resultado": nota_tab == nota_fb,
        })
    return resultados


def escalar_playlist(quantidades=(100, 500, 1000), minutos=180):
    """So a tabulacao, com bibliotecas grandes de sons.

    A forca bruta nao entra aqui: com 100 sons seriam 2^100 combinacoes.
    """
    resultados = []
    for quantidade in quantidades:
        duracoes, notas = gerar_sons(quantidade)
        _, tempo = medir_tempo(melhor_playlist, duracoes, notas, minutos)
        resultados.append({"sons": quantidade, "tempo_tabulacao": tempo})
    return resultados
