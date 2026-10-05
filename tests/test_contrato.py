"""Contrato com o Trilha e a Trilha-LP: o que exportamos passa nos esquemas deles.

Os repositórios não dependem um do outro, então este teste só roda com os dois ao lado:

    PYTHONPATH=../Trilha:../Trilha-LP python -m unittest tests.test_contrato -v

Sem eles, os testes são pulados (a CI deste repositório não tem acesso aos outros).
"""

import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from trilha_briefing.economia import calcular
from trilha_briefing.esquema import carregar_cliente
from trilha_briefing.exportar import exportar_lp, exportar_trilha

try:
    from trilha.core import economia as trilha_economia
    from trilha.core.oferta import carregar_oferta
    from trilha.core.perfil import Economia as EconomiaTrilha
    from trilha_lp.esquema import carregar as carregar_pagina
    TEM_REPOS = True
except ImportError:
    TEM_REPOS = False

EXEMPLO = Path(__file__).parent.parent / "clientes" / "_exemplo"


@unittest.skipUnless(TEM_REPOS, "Trilha e Trilha-LP fora do PYTHONPATH")
class TestContrato(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.c = carregar_cliente(EXEMPLO)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_ofertas_passam_no_trilha(self):
        exportar_trilha(self.c, self.tmp)
        for arquivo in (self.tmp / "_exemplo" / "ofertas").glob("*.yaml"):
            carregar_oferta(arquivo)

    def test_economia_igual_a_do_trilha(self):
        exportar_trilha(self.c, self.tmp)
        perfil = yaml.safe_load((self.tmp / "_exemplo" / "perfil.parcial.yaml").read_text(encoding="utf-8"))
        deles = trilha_economia.calcular(EconomiaTrilha.model_validate(perfil["economia"]))
        nossos = calcular(self.c.estrategia.economia)
        self.assertAlmostEqual(deles.cac_max, nossos.cac_max)
        for evento, custo in nossos.custo_max.items():
            self.assertAlmostEqual(deles.custo_max(evento), custo)
        self.assertAlmostEqual(deles.verba_minima_viavel, nossos.verba_minima_viavel)

    def test_pagina_da_oferta_principal_passa_na_trilha_lp(self):
        for caminho, pend in exportar_lp(self.c, self.tmp, oferta="conversacao-adultos"):
            self.assertEqual(pend, [])
            carregar_pagina(caminho)

    def test_pagina_sem_whatsapp_nao_passa(self):
        dados = yaml.safe_load((EXEMPLO / "briefing.yaml").read_text(encoding="utf-8"))
        dados["cliente"]["whatsapp"] = ""
        pasta = self.tmp / "_exemplo"
        shutil.copytree(EXEMPLO, pasta)
        (pasta / "briefing.yaml").write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
        (caminho, _), = exportar_lp(carregar_cliente(pasta), self.tmp / "lp", oferta="conversacao-adultos", origens=("meta",))
        with self.assertRaises(Exception):
            carregar_pagina(caminho)


if __name__ == "__main__":
    unittest.main()
