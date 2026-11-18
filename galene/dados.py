"""Leitura e validacao dos dados simulados (arquivos JSON da pasta dados/).

A leitura do arquivo fica separada da montagem do grafo:
    - carregar_json faz o acesso ao disco e trata os erros;
    - montar_grafo e validar_sons sao funcoes puras.
"""

import json               # para ler os arquivos .json
from pathlib import Path  # para montar caminhos de pasta que funcionam no Windows e no Linux

# Pasta dados/ do projeto, calculada a partir deste arquivo.
# Assim o programa acha os JSON de qualquer pasta em que for executado.
#   __file__        -> .../galene_dp/galene/dados.py
#   .parent         -> .../galene_dp/galene
#   .parent.parent  -> .../galene_dp
PASTA_DADOS = Path(__file__).resolve().parent.parent / "dados"

# Unicos tipos de som que a playlist conhece.
TIPOS_DE_SOM = {"binaural", "lofi", "mascaramento", "natureza"}


class ErroDeDados(Exception):
    """Erro com mensagem amigavel para quando um arquivo de dados tem problema.

    Criar uma excecao propria permite que o main.py trate so os erros de
    dados, mostrando uma mensagem clara em vez de um traceback.
    """


def carregar_json(nome_arquivo, pasta=PASTA_DADOS):
    """Le um arquivo JSON da pasta de dados e devolve o conteudo."""
    caminho = Path(pasta) / nome_arquivo
    try:
        # encoding="utf-8" para ler os acentos corretamente no Windows.
        with open(caminho, encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        # O arquivo nao esta na pasta dados/.
        raise ErroDeDados(f"Arquivo não encontrado: {caminho}")
    except json.JSONDecodeError as erro:
        # O arquivo existe, mas o conteudo nao e um JSON valido (virgula sobrando etc.).
        raise ErroDeDados(f"O arquivo {caminho.name} não é um JSON válido (linha {erro.lineno}).")


def montar_grafo(locais, trechos):
    """Monta o grafo nao dirigido {local: [(vizinho, metros, db), ...]}. O(V + E).

    >>> g = montar_grafo({"a": "A", "b": "B"}, [["a", "b", 100, 50]])
    >>> g["a"], g["b"]
    ([('b', 100, 50)], [('a', 100, 50)])
    """
    # Cada local comeca com uma lista vazia de vizinhos.
    grafo = {local: [] for local in locais}

    # enumerate(..., start=1) numera os trechos a partir de 1, para a
    # mensagem de erro dizer "trecho 3" como uma pessoa contaria.
    for posicao, trecho in enumerate(trechos, start=1):
        # Cada trecho precisa ter exatamente 4 valores.
        try:
            origem, destino, metros, decibeis = trecho
        except (TypeError, ValueError):
            raise ErroDeDados(f"Trecho {posicao} mal formado: {trecho}")

        # Os dois locais do trecho precisam existir na lista de locais.
        if origem not in grafo or destino not in grafo:
            raise ErroDeDados(f"Trecho {posicao} usa um local que não existe: {origem} - {destino}")

        # Metros precisam ser positivos e dB nao pode ser negativo.
        if metros <= 0 or decibeis < 0:
            raise ErroDeDados(f"Trecho {posicao} com metros ou decibéis inválidos.")

        # Rua de mao dupla: o trecho vale nos dois sentidos.
        grafo[origem].append((destino, metros, decibeis))
        grafo[destino].append((origem, metros, decibeis))
    return grafo


def validar_sons(sons):
    """Confere se cada som tem os campos certos. Devolve a propria lista."""
    for som in sons:
        # Diferenca de conjuntos: campos obrigatorios que NAO estao no som.
        faltando = {"id", "nome", "tipo", "duracao_min", "afinidade"} - set(som)
        if faltando:
            raise ErroDeDados(f"Som sem os campos {sorted(faltando)}: {som}")

        # O tipo precisa ser um dos tipos conhecidos.
        if som["tipo"] not in TIPOS_DE_SOM:
            raise ErroDeDados(f"Tipo de som desconhecido: {som['tipo']}")

        # Duracao positiva e afinidade entre 1 e 5.
        if som["duracao_min"] <= 0 or not 1 <= som["afinidade"] <= 5:
            raise ErroDeDados(f"Duração ou afinidade inválida no som {som['nome']}")
    return sons


def carregar_bairro(nome_arquivo="bairro.json"):
    """Devolve (grafo, nomes_dos_locais, texto_da_fonte)."""
    dados = carregar_json(nome_arquivo)
    try:
        locais = dados["locais"]
        grafo = montar_grafo(locais, dados["trechos"])
    except KeyError as erro:
        # O JSON nao tem a chave "locais" ou "trechos".
        raise ErroDeDados(f"Falta a chave {erro} no arquivo {nome_arquivo}")
    # .get devolve "" se a chave "fonte" nao existir, sem dar erro.
    return grafo, locais, dados.get("fonte", "")


def carregar_sons(nome_arquivo="sons.json"):
    """Devolve (lista_de_sons, texto_da_fonte)."""
    dados = carregar_json(nome_arquivo)
    try:
        sons = validar_sons(dados["sons"])
    except KeyError as erro:
        # O JSON nao tem a chave "sons".
        raise ErroDeDados(f"Falta a chave {erro} no arquivo {nome_arquivo}")
    return sons, dados.get("fonte", "")
