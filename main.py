"""Galene - Dynamic Programming (Global Solution 2026.2 - CitizenTech).

Interface de terminal. Este arquivo so cuida de conversar com o usuario
(input/print). Toda a logica fica nas funcoes puras do pacote galene/.

Como rodar:  python main.py
"""

import sys  # usado para encerrar o programa com sys.exit se os dados nao carregarem

# Importa so o que a interface precisa de cada modulo do pacote galene/.
from galene.dados import carregar_bairro, carregar_sons, ErroDeDados
from galene.ruido import classificar_ruido
from galene.rota_tranquila import comparar_rotas
from galene.playlist_foco import montar_playlist
from galene import eficiencia

# Opcoes de sensibilidade mostradas no menu da rota.
# Chave = numero que o usuario digita; valor = (texto do menu, peso usado no calculo).
SENSIBILIDADES = {
    1: ("Baixa (o ruído pesa pouco)", 0.5),
    2: ("Padrão", 1.0),
    3: ("Alta (o ruído pesa o dobro)", 2.0),
}


# ---------------------------------------------------------------- entrada

def ler_inteiro(mensagem, minimo, maximo):
    """Pede um numero inteiro ate o usuario digitar um valor valido."""
    # Repete ate receber um valor valido: o programa nunca quebra por digitacao errada.
    while True:
        try:
            # .strip() tira espacos antes e depois; int() converte o texto em numero.
            valor = int(input(mensagem).strip())
            if minimo <= valor <= maximo:
                return valor
            print(f"  Digite um número entre {minimo} e {maximo}.")
        except ValueError:
            # int() levanta ValueError quando o texto nao e um numero (ex.: "abc").
            print("  Isso não é um número inteiro. Tente de novo.")


def escolher_local(mensagem, codigos, locais):
    """Mostra os locais numerados e devolve o codigo do escolhido."""
    numero = ler_inteiro(mensagem, 1, len(codigos))
    # O usuario digita a partir de 1, mas a lista comeca em 0: por isso o - 1.
    codigo = codigos[numero - 1]
    print(f"  -> {locais[codigo]}")  # confirma o nome do local escolhido
    return codigo


# ---------------------------------------------------------------- saida

def imprimir_rota(titulo, rota, locais):
    """Mostra uma rota e o resumo de exposicao a ruido."""
    print(f"\n  {titulo}")
    if rota is None:
        print("    Não há caminho entre esses locais.")
        return
    resumo = rota["resumo"]
    # Troca os codigos ("casa", "metro") pelos nomes bonitos e junta com setas.
    print("    " + " -> ".join(locais[c] for c in rota["caminho"]))
    print(f"    Distância: {resumo['metros_total']} m | "
          f"ruído médio: {resumo['ruido_medio_db']} dB | "
          f"pior trecho: {resumo['pior_trecho_db']} dB ({resumo['pior_faixa']})")
    print(f"    Metros em nível Intenso ou Crítico: {resumo['metros_intenso_ou_critico']} m")


def imprimir_tabela(cabecalho, linhas):
    """Imprime uma tabela simples alinhada."""
    # zip(cabecalho, *linhas) agrupa os valores por coluna.
    # A largura de cada coluna e o tamanho do maior texto dela.
    larguras = [max(len(str(x)) for x in coluna) for coluna in zip(cabecalho, *linhas)]
    for linha in [cabecalho] + linhas:
        celulas = []
        for x, w in zip(linha, larguras):
            texto = str(x)
            # Numeros alinhados a direita, textos a esquerda.
            celulas.append(texto.rjust(w) if texto[:1].isdigit() else texto.ljust(w))
        print("  " + "  ".join(celulas))


def formatar_segundos(segundos):
    """Converte segundos para texto em milissegundos."""
    # :.2f mostra duas casas decimais.
    return f"{segundos * 1000:.2f} ms"


# ---------------------------------------------------------------- telas

def tela_rota(grafo, locais):
    """Tela da Rota Tranquila: pede origem, destino e sensibilidade e mostra as rotas."""
    print("\n=== ROTA TRANQUILA (Dijkstra) ===")
    print("Encontra o caminho com menos exposição a ruído, não só o mais curto.\n")

    # Lista os locais numerados a partir de 1.
    codigos = list(locais)
    for i, codigo in enumerate(codigos, start=1):
        print(f"  {i:2}. {locais[codigo]}")  # :2 alinha os numeros de 1 e 2 digitos

    origem = escolher_local("\nDe onde você sai? ", codigos, locais)
    destino = escolher_local("Para onde você vai? ", codigos, locais)
    if origem == destino:
        print("  Origem e destino são o mesmo lugar: você já chegou!")
        return

    print("\nQual a sua sensibilidade ao ruído?")
    for numero, (nome, _) in SENSIBILIDADES.items():
        print(f"  {numero}. {nome}")
    # Pega so o peso (segundo item da tupla) da opcao escolhida.
    _, sensibilidade = SENSIBILIDADES[ler_inteiro("Escolha: ", 1, 3)]

    # Chama a funcao pura que roda o Dijkstra duas vezes (curta e tranquila).
    rota_curta, rota_tranquila = comparar_rotas(grafo, origem, destino, sensibilidade)
    imprimir_rota("Rota mais curta:", rota_curta, locais)
    imprimir_rota("Rota mais tranquila (Galene):", rota_tranquila, locais)

    # Mostra a "troca": quantos metros a mais para evitar quanto ruido.
    if rota_curta and rota_tranquila:
        a_mais = rota_tranquila["resumo"]["metros_total"] - rota_curta["resumo"]["metros_total"]
        evitado = (rota_curta["resumo"]["metros_intenso_ou_critico"]
                   - rota_tranquila["resumo"]["metros_intenso_ou_critico"])
        if rota_curta["caminho"] == rota_tranquila["caminho"]:
            print("\n  A rota mais curta já é a mais tranquila.")
        else:
            print(f"\n  Andando {a_mais} m a mais, você evita {evitado} m de ruído Intenso/Crítico.")


def tela_playlist(sons):
    """Tela da Playlist de Foco: pede o ruido e o tempo e mostra a playlist."""
    print("\n=== PLAYLIST DE FOCO (tabulação / mochila 0/1) ===")
    print("Monta a melhor playlist sem repetir sons, dentro do tempo da sessão.\n")

    # No app real, o dB viria do microfone; aqui o usuario digita o valor.
    decibeis = ler_inteiro("Ruído medido no ambiente agora (dB, 0 a 130): ", 0, 130)
    print(f"  -> Nível {classificar_ruido(decibeis)[0]}")
    minutos = ler_inteiro("Duração da sessão de foco (minutos, 5 a 240): ", 5, 240)

    # Chama a funcao pura que resolve a mochila por tabulacao.
    playlist = montar_playlist(sons, decibeis, minutos)
    if not playlist["sons"]:
        print("\n  Nenhum som cabe nesse tempo. Tente uma sessão mais longa.")
        return

    print(f"\n  Playlist para ambiente {playlist['faixa_do_ambiente']}:")
    # Uma linha da tabela por som escolhido.
    linhas = [[s["nome"], s["tipo"], f"{s['duracao_min']} min", s["nota"]] for s in playlist["sons"]]
    imprimir_tabela(["Som", "Tipo", "Duração", "Nota"], linhas)
    print(f"\n  Total: {playlist['minutos_usados']} de {playlist['minutos_da_sessao']} min "
          f"| nota {playlist['nota_total']}")


def tela_eficiencia():
    """Tela da analise pratica: roda as medicoes de tempo e mostra as tabelas."""
    print("\n=== ANÁLISE DE EFICIÊNCIA (medição de tempo) ===")
    print("Pode levar alguns segundos: as versões ingênuas são lentas de propósito.\n")

    # 1) Dijkstra com heap x sem heap.
    # "Ganho" = quantas vezes a versao com heap foi mais rapida.
    print("1) Rota: Dijkstra com heap O((V+E) log V) x sem heap O(V²)")
    linhas = [[r["esquinas"], formatar_segundos(r["tempo_heap"]), formatar_segundos(r["tempo_ingenuo"]),
               f"{r['tempo_ingenuo'] / r['tempo_heap']:.0f}x", "sim" if r["mesmo_resultado"] else "NÃO"]
              for r in eficiencia.comparar_dijkstras()]
    imprimir_tabela(["Esquinas", "Com heap", "Sem heap", "Ganho", "Mesmo resultado"], linhas)

    # Mostra que a versao com heap continua rapida em bairros bem maiores.
    print("\n   Dijkstra com heap em bairros grandes:")
    linhas = [[r["esquinas"], formatar_segundos(r["tempo_heap"])] for r in eficiencia.escalar_dijkstra()]
    imprimir_tabela(["Esquinas", "Com heap"], linhas)

    # 2) Tabulacao x forca bruta.
    print("\n2) Playlist (sessão de 90 min): tabulação O(n·T) x força bruta O(2^n)")
    linhas = [[r["sons"], formatar_segundos(r["tempo_tabulacao"]), formatar_segundos(r["tempo_forca_bruta"]),
               f"{r['tempo_forca_bruta'] / r['tempo_tabulacao']:.0f}x", "sim" if r["mesmo_resultado"] else "NÃO"]
              for r in eficiencia.comparar_playlists()]
    imprimir_tabela(["Sons", "Tabulação", "Força bruta", "Ganho", "Mesmo resultado"], linhas)

    # Mostra que a tabulacao continua rapida com muitos sons.
    print("\n   Tabulação com bibliotecas grandes (sessão de 180 min):")
    linhas = [[r["sons"], formatar_segundos(r["tempo_tabulacao"])] for r in eficiencia.escalar_playlist()]
    imprimir_tabela(["Sons", "Tabulação"], linhas)


def tela_fontes(fonte_bairro, fonte_sons):
    """Mostra de onde vieram os dados (exigencia da GS: dados simulados e com origem)."""
    print("\n=== DE ONDE VÊM OS DADOS ===")
    print(f"\n  Bairro: {fonte_bairro}")
    print(f"\n  Sons: {fonte_sons}")


# ---------------------------------------------------------------- menu

def main():
    """Carrega os dados e mostra o menu principal ate o usuario escolher sair."""
    # Carrega os arquivos JSON uma vez so, no inicio.
    try:
        grafo, locais, fonte_bairro = carregar_bairro()
        sons, fonte_sons = carregar_sons()
    except ErroDeDados as erro:
        # Sem dados nao da para continuar: mostra o motivo e encerra.
        print(f"Não foi possível carregar os dados: {erro}")
        sys.exit(1)

    # Dicionario de opcoes: numero -> (texto do menu, funcao da tela).
    # lambda cria uma funcao sem argumentos que chama a tela com os dados certos.
    # Assim, para acrescentar uma opcao nova, basta uma linha aqui.
    opcoes = {
        1: ("Rota tranquila", lambda: tela_rota(grafo, locais)),
        2: ("Playlist de foco", lambda: tela_playlist(sons)),
        3: ("Análise de eficiência", tela_eficiencia),
        4: ("De onde vêm os dados", lambda: tela_fontes(fonte_bairro, fonte_sons)),
    }

    print("=" * 56)
    print("  GALENE · Som que se adapta ao seu mundo")
    print("  Global Solution 2026.2 · Dynamic Programming")
    print("=" * 56)

    while True:
        print("\nMENU")
        for numero, (nome, _) in opcoes.items():
            print(f"  {numero}. {nome}")
        print("  0. Sair")
        escolha = ler_inteiro("Escolha uma opção: ", 0, len(opcoes))
        if escolha == 0:
            print("Até mais! 🌊")
            break
        try:
            # opcoes[escolha][1] e a funcao da tela; os () no final a executam.
            opcoes[escolha][1]()
        except ValueError as erro:
            # Erros de validacao das funcoes puras voltam ao menu, sem quebrar.
            print(f"  Não deu para concluir: {erro}")


# So roda o menu quando o arquivo e executado diretamente (python main.py),
# e nao quando ele e importado por outro arquivo.
if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C ou fim da entrada: encerra com uma mensagem, sem traceback.
        print("\nPrograma encerrado.")
