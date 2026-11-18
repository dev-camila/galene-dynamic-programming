"""Testes automaticos do Galene.

Como rodar (de dentro da pasta galene_dp):  python -m unittest discover testes

Cada metodo que comeca com test_ e um teste. Os assertXxx conferem se o
resultado e o esperado; se algum falhar, o unittest mostra qual e por que.
"""

import random
import unittest

from galene.ruido import classificar_ruido
from galene.dados import montar_grafo, carregar_bairro, carregar_sons, ErroDeDados
from galene.rota_tranquila import (dijkstra, dijkstra_ingenuo, reconstruir_caminho,
                                   rota_mais_tranquila, comparar_rotas)
from galene.playlist_foco import melhor_playlist, melhor_nota_forca_bruta, montar_playlist
from galene.eficiencia import gerar_bairro_em_grade, mesmos_custos


class TestRuido(unittest.TestCase):
    """Testes das faixas de ruido."""

    def test_limites_das_faixas(self):
        # Confere os valores exatamente na fronteira entre uma faixa e outra.
        self.assertEqual(classificar_ruido(40)[0], "Silencioso")
        self.assertEqual(classificar_ruido(41)[0], "Tranquilo")
        self.assertEqual(classificar_ruido(70)[0], "Moderado")
        self.assertEqual(classificar_ruido(85)[0], "Intenso")
        self.assertEqual(classificar_ruido(86)[0], "Crítico")

    def test_negativo(self):
        # assertRaises confere que a funcao REALMENTE levanta o erro.
        with self.assertRaises(ValueError):
            classificar_ruido(-1)


class TestRotaTranquila(unittest.TestCase):
    """Testes da Rota Tranquila (Dijkstra)."""

    def setUp(self):
        # setUp roda antes de CADA teste da classe, criando um grafo novo.
        # a-b-d e curto mas barulhento; a-c-d e longo mas silencioso.
        self.grafo = montar_grafo(
            {"a": "A", "b": "B", "c": "C", "d": "D", "ilha": "Ilha"},
            [["a", "b", 100, 90], ["b", "d", 100, 90], ["a", "c", 150, 35], ["c", "d", 150, 35]],
        )

    def test_mais_curta_x_mais_tranquila(self):
        # A curta passa pelo barulho; a tranquila desvia dele.
        curta, tranquila = comparar_rotas(self.grafo, "a", "d")
        self.assertEqual(curta["caminho"], ["a", "b", "d"])
        self.assertEqual(tranquila["caminho"], ["a", "c", "d"])
        self.assertEqual(tranquila["resumo"]["metros_intenso_ou_critico"], 0)

    def test_destino_inalcancavel(self):
        # "ilha" nao tem nenhum trecho: nao ha como chegar.
        self.assertIsNone(rota_mais_tranquila(self.grafo, "a", "ilha"))

    def test_local_desconhecido(self):
        # Origem que nao existe no grafo deve dar erro, e nao resultado errado.
        with self.assertRaises(ValueError):
            dijkstra(self.grafo, "xyz")

    def test_reconstruir_origem_igual_destino(self):
        self.assertEqual(reconstruir_caminho({"a": None}, "a", "a"), ["a"])

    def test_heap_e_ingenuo_concordam(self):
        # As duas versoes do Dijkstra precisam dar os mesmos custos,
        # para as tres sensibilidades, num bairro em grade sorteado.
        grafo = gerar_bairro_em_grade(12, semente=7)
        for sensibilidade in (0, 1, 2):
            c1, _ = dijkstra(grafo, (0, 0), sensibilidade)
            c2, _ = dijkstra_ingenuo(grafo, (0, 0), sensibilidade)
            self.assertTrue(mesmos_custos(c1, c2))

    def test_bairro_real_do_projeto(self):
        # Usa o bairro.json do projeto: a rota tranquila pode ser mais longa,
        # mas precisa ter menos metros em ruido Intenso/Critico.
        grafo, _, _ = carregar_bairro()
        curta, tranquila = comparar_rotas(grafo, "casa", "faculdade")
        self.assertLessEqual(curta["resumo"]["metros_total"], tranquila["resumo"]["metros_total"])
        self.assertLess(tranquila["resumo"]["metros_intenso_ou_critico"],
                        curta["resumo"]["metros_intenso_ou_critico"])


class TestPlaylist(unittest.TestCase):
    """Testes da Playlist de Foco (tabulacao)."""

    def test_exemplo_pequeno(self):
        # Sons de 20 e 30 min (nota 50 + 70 = 120) cabem certinho em 50 min.
        self.assertEqual(melhor_playlist([20, 30, 25], [50, 70, 60], 50), (120, [0, 1]))

    def test_nada_cabe(self):
        # Nenhum som cabe em 10 min: nota 0 e playlist vazia.
        self.assertEqual(melhor_playlist([30, 40], [10, 20], 10), (0, []))

    def test_igual_forca_bruta_em_casos_aleatorios(self):
        # Compara a tabulacao com a forca bruta (que testa tudo) em 200 casos sorteados.
        sorteio = random.Random(123)
        for _ in range(200):
            n = sorteio.randint(0, 10)
            duracoes = [sorteio.randint(1, 20) for _ in range(n)]
            notas = [sorteio.randint(1, 50) for _ in range(n)]
            minutos = sorteio.randint(0, 60)
            nota, escolhidos = melhor_playlist(duracoes, notas, minutos)
            self.assertEqual(nota, melhor_nota_forca_bruta(duracoes, notas, minutos))
            # A escolha reconstruida precisa caber e somar a nota informada.
            self.assertLessEqual(sum(duracoes[i] for i in escolhidos), minutos)
            self.assertEqual(sum(notas[i] for i in escolhidos), nota)
            self.assertEqual(len(set(escolhidos)), len(escolhidos))  # sem repetir

    def test_entrada_invalida(self):
        # Listas de tamanhos diferentes e duracao zero devem dar erro.
        with self.assertRaises(ValueError):
            melhor_playlist([10], [1, 2], 30)
        with self.assertRaises(ValueError):
            melhor_playlist([0], [5], 30)

    def test_ambiente_critico_prefere_mascaramento(self):
        # Com 90 dB (Critico), a playlist deve trazer som de mascaramento.
        sons, _ = carregar_sons()
        playlist = montar_playlist(sons, 90, 30)
        self.assertLessEqual(playlist["minutos_usados"], 30)
        self.assertTrue(any(s["tipo"] == "mascaramento" for s in playlist["sons"]))


class TestDados(unittest.TestCase):
    """Testes da leitura e validacao dos dados."""

    def test_trecho_com_local_inexistente(self):
        # O local "b" nao foi cadastrado: o grafo nao pode ser montado.
        with self.assertRaises(ErroDeDados):
            montar_grafo({"a": "A"}, [["a", "b", 10, 50]])


if __name__ == "__main__":
    unittest.main()
