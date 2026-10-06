"""Padrão de texto da Trilha no briefing: a cópia dos vocabulários bate com o Trilha-copy e as regras valem aqui.

O arquivo canônico é trilha_copy/regras/padrao.yaml. A CI clona o Trilha-copy (é público) e compara lista a lista:

    PYTHONPATH=../Trilha-copy python -m unittest tests.test_padrao -v
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from trilha_briefing import padrao
from trilha_briefing.esquema import carregar_cliente
from trilha_briefing.exportar import pacote_copy
from trilha_briefing.revisao import revisar

try:
    from trilha_copy import padrao as canonico
    TEM_PADRAO = True
except ImportError:  # Trilha-copy ausente, ou anterior à 0.2.0 (sem o padrão de texto)
    TEM_PADRAO = False

EXEMPLO = Path(__file__).parent.parent / "clientes" / "_exemplo"


@unittest.skipUnless(TEM_PADRAO, "Trilha-copy com o padrão de texto (0.2.0+) não instalado")
class TestCopiaEmDia(unittest.TestCase):
    def test_vocabularios_iguais_aos_do_trilha_copy(self):
        """Se falhar: copie as listas de trilha_copy/regras/padrao.yaml para trilha_briefing/regras/padrao-vocabularios.yaml."""
        c = canonico.carregar()
        nosso = padrao.carregar()
        for nome, itens in nosso["vocabularios"].items():
            self.assertEqual(itens, c.vocabularios[nome], nome)
        self.assertEqual(nosso["registro_por_segmento"], c.parametros["registro_por_segmento"])
        self.assertEqual(nosso["janela_garantia_palavras"], c.parametros["janela_garantia_palavras"])

    def test_casa_igual_ao_trilha_copy(self):
        for nome, texto in [("urgencia", "Corra: só até sexta, isso ocorra ou não"), ("garantia_de_resultado", "Resultado garantido!"),
                            ("adjetivo_vago", "A melhor escola, com qualidade"), ("promessa_de_ganho", "Fature R$ 10 mil")]:
            self.assertEqual(padrao.achar(nome, texto), canonico.achar(nome, texto), nome)


class TestPadraoNoBriefing(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pasta = self.tmp / "_exemplo"
        shutil.copytree(EXEMPLO, self.pasta)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def oferta(self, mudar):
        caminho = self.pasta / "ofertas" / "conversacao-adultos.yaml"
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
        mudar(dados)
        caminho.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
        return [(a.nivel, a.texto) for a in revisar(carregar_cliente(self.pasta))]

    def test_termo_proibido_casa_inteiro(self):
        def mudar(d):
            d["cta"] = "Caso ocorra um imprevisto, você repõe a aula"
        self.assertFalse(any("termo proibido" in t for _, t in self.oferta(mudar)))
        self.assertEqual(padrao.contem_termo("Corra!", "corra"), True)
        self.assertEqual(padrao.contem_termo("isso ocorra", "corra"), False)

    def test_garantia_de_resultado_bloqueia(self):
        avisos = self.oferta(lambda d: d.update(cta="Fluência garantida em 6 meses, agende hoje"))
        self.assertTrue(any(n == "bloqueia" and "garante um resultado" in t for n, t in avisos))

    def test_prazo_no_texto_sem_urgencia_real(self):
        def mudar(d):
            d["urgencia"] = None
            d["escassez"] = None
            d["cta"] = "Últimas vagas: agende hoje"
        self.assertTrue(any(n == "bloqueia" and "não tem urgência ou escassez reais" in t for n, t in self.oferta(mudar)))

    def test_lista_do_segmento(self):
        caminho = self.pasta / "briefing.yaml"
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
        dados["cliente"]["playbook"] = "imobiliario"
        caminho.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
        avisos = self.oferta(lambda d: d.update(cta="Aprovação garantida, sem consulta ao SPC"))
        self.assertTrue(any("proibido no segmento" in t for _, t in avisos))

    def test_regra_de_preco_vai_para_a_copy(self):
        caminho = self.pasta / "plataforma.yaml"
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
        dados["preco"] = {"anuncio": "a_partir_de", "whatsapp": "nunca"}
        caminho.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
        self.assertEqual(pacote_copy(carregar_cliente(self.pasta))["preco"], {"anuncio": "a_partir_de", "whatsapp": "nunca"})


if __name__ == "__main__":
    unittest.main()
