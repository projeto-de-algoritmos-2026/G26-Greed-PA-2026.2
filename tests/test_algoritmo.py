import itertools
import random
import unittest

from agenda.algoritmo import selecionar_palestras
from agenda.api import processar_requisicao
from agenda.leitor import palestras_de_dicts
from agenda.modelos import Palestra, horario_para_minutos, minutos_para_horario


def P(titulo, inicio, fim):
    return Palestra.de_horarios(titulo, inicio, fim)


def sem_conflitos(palestras):
    return all(not a.conflita_com(b) for a, b in itertools.combinations(palestras, 2))


class TestHorarios(unittest.TestCase):
    def test_conversao_ida_e_volta(self):
        for texto in ["00:00", "08:05", "13:30", "23:59", "24:00"]:
            self.assertEqual(minutos_para_horario(horario_para_minutos(texto)), texto)

    def test_horario_invalido(self):
        for texto in ["8h", "25:00", "10:60", "", "ab:cd"]:
            with self.assertRaises(ValueError):
                horario_para_minutos(texto)

    def test_fim_antes_do_inicio(self):
        with self.assertRaises(ValueError):
            P("X", "10:00", "09:00")


class TestSelecao(unittest.TestCase):
    def test_lista_vazia(self):
        r = selecionar_palestras([])
        self.assertEqual(r.aceitas, [])
        self.assertEqual(r.taxa_ocupacao, 0.0)

    def test_encostadas_nao_conflitam(self):
        r = selecionar_palestras([P("A", "08:00", "09:00"), P("B", "09:00", "10:00")])
        self.assertEqual(len(r.aceitas), 2)
        self.assertEqual(r.taxa_ocupacao, 1.0)

    def test_prefere_quem_termina_primeiro(self):
        longa = P("Longa", "08:00", "12:00")
        curtas = [P("C1", "08:00", "09:00"), P("C2", "09:00", "10:00"), P("C3", "10:00", "11:00")]
        r = selecionar_palestras([longa, *curtas])
        self.assertEqual(r.aceitas, curtas)
        self.assertEqual(r.rejeitadas, [longa])
        self.assertEqual(r.conflitos[longa], curtas)

    def test_respeita_janela(self):
        cedo = P("Cedo", "07:00", "08:30")
        r = selecionar_palestras(
            [cedo, P("Ok", "09:00", "10:00")],
            horario_para_minutos("08:00"), horario_para_minutos("12:00"),
        )
        self.assertEqual([p.titulo for p in r.aceitas], ["Ok"])
        self.assertEqual(r.conflitos[cedo], [])  # rejeitada por estar fora da janela
        self.assertEqual(r.tempo_janela, 240)

    def test_otimo_contra_forca_bruta(self):
        rng = random.Random(42)
        for _ in range(200):
            palestras = []
            for i in range(rng.randint(0, 8)):
                inicio = rng.randrange(0, 20) * 30
                palestras.append(Palestra(f"P{i}", inicio, inicio + rng.randint(1, 6) * 30))
            r = selecionar_palestras(palestras)
            melhor = max(
                (k for k in range(len(palestras) + 1)
                 for c in itertools.combinations(palestras, k) if sem_conflitos(c)),
                default=0,
            )
            self.assertTrue(sem_conflitos(r.aceitas))
            self.assertEqual(len(r.aceitas), melhor)
            self.assertEqual(len(r.aceitas) + len(r.rejeitadas), len(palestras))


class TestEntrada(unittest.TestCase):
    def test_campo_ausente(self):
        with self.assertRaisesRegex(ValueError, "Proposta #1.*fim"):
            palestras_de_dicts([{"titulo": "X", "inicio": "08:00"}])

    def test_api(self):
        resposta = processar_requisicao({
            "palestras": [
                {"titulo": "A", "inicio": "08:00", "fim": "09:00"},
                {"titulo": "B", "inicio": "08:30", "fim": "09:30"},
            ],
            "janela": {"inicio": "08:00", "fim": "10:00"},
        })
        self.assertEqual(resposta["resumo"]["total_aceitas"], 1)
        self.assertEqual(resposta["rejeitadas"][0]["conflita_com"], ["A"])
        self.assertEqual(resposta["resumo"]["tempo_janela_min"], 120)


if __name__ == "__main__":
    unittest.main()
