"""Faixas de ruido do Galene.

As cinco faixas sao as mesmas da documentacao do projeto (secao 1.2):
Silencioso (ate 40 dB), Tranquilo (40-55), Moderado (55-70),
Intenso (70-85) e Critico (acima de 85).

O "fator" de cada faixa diz o quanto um metro andado naquele nivel
"pesa" para uma pessoa sensivel a ruido. Os valores foram definidos
pelo grupo (sao uma escolha de projeto, nao uma medida cientifica).
"""

# Lista de faixas, da mais silenciosa para a mais barulhenta.
# Cada faixa e uma tupla: (limite superior em dB, nome da faixa, fator de incomodo)
# Exemplo: 62 dB passa do limite 55 (Tranquilo) mas nao do 70, entao e Moderado.
FAIXAS_DE_RUIDO = [
    (40, "Silencioso", 1.0),        # ate 40 dB: nao incomoda, fator neutro
    (55, "Tranquilo", 1.2),         # 40 a 55 dB: incomoda um pouco
    (70, "Moderado", 1.6),          # 55 a 70 dB: ja atrapalha o foco
    (85, "Intenso", 2.5),           # 70 a 85 dB: sobrecarga para quem e sensivel
    (float("inf"), "Crítico", 4.0), # acima de 85 dB: limite infinito pega todo o resto
]

# So os nomes das faixas, na mesma ordem. Usado para montar resumos por faixa.
# (list comprehension: para cada tupla, pega apenas o nome e ignora o resto com _)
NOMES_DAS_FAIXAS = [nome for _, nome, _ in FAIXAS_DE_RUIDO]


def classificar_ruido(decibeis):
    """Devolve (nome_da_faixa, fator) para um nivel de ruido em dB. O(1).

    E O(1) porque a lista tem sempre 5 faixas, nao importa a entrada.

    >>> classificar_ruido(40)
    ('Silencioso', 1.0)
    >>> classificar_ruido(62)
    ('Moderado', 1.6)
    >>> classificar_ruido(90)
    ('Crítico', 4.0)
    """
    # Ruido negativo nao existe: avisamos o erro em vez de devolver algo errado.
    if decibeis < 0:
        raise ValueError("O nível de ruído não pode ser negativo.")

    # Percorre as faixas em ordem. A primeira cujo limite e maior ou igual
    # ao valor medido e a faixa certa.
    for limite, nome, fator in FAIXAS_DE_RUIDO:
        if decibeis <= limite:
            return nome, fator

    # Nunca chega aqui, porque o ultimo limite e infinito.
    # Fica so por seguranca, devolvendo a ultima faixa (Critico).
    return FAIXAS_DE_RUIDO[-1][1], FAIXAS_DE_RUIDO[-1][2]
