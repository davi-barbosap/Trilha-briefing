"""O caminho de volta: o retorno do Trilha-ads (contrato retorno) nas hipóteses do briefing."""

import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from trilha_briefing.__main__ import main
from trilha_briefing.esquema import carregar_cliente
from trilha_briefing.resultados import RetornoInvalido, registrar

EXEMPLO = Path(__file__).parent.parent / "clientes" / "_exemplo"


def retorno(pt01_leads=60, pt02_leads=52, **extra):
    return {
        "retorno": 1, "cliente": "_exemplo", "periodo": {"inicio": "2026-10-20", "fim": "2026-11-19"}, "leads": 130,
        "por_codigo": {
            "PT01": {"leads": pt01_leads, "qualificados": 20, "agendamentos": 9, "comparecimentos": 7, "vendas": 3,
                     "gasto": 1800.0, "cpl": 1800.0 / pt01_leads},
            "PT02": {"leads": pt02_leads, "qualificados": 15, "agendamentos": 6, "comparecimentos": 5, "vendas": 2,
                     "gasto": 2100.0, "cpl": 2100.0 / pt02_leads},
            "GB01": {"leads": 18, "qualificados": 10, "agendamentos": 5, "comparecimentos": 4, "vendas": 2},
            "sem código": {"leads": 4, "qualificados": 1, "agendamentos": 0, "comparecimentos": 0, "vendas": 0},
        },
        "motivos_perda": [{"motivo": "Achou caro", "categoria": "comercial", "leads": 14},
                          {"motivo": "Não respondeu às tentativas de contato", "categoria": "atendimento", "leads": 9}],
        **extra,
    }


class TestCaminhoDeVolta(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pasta = self.tmp / "_exemplo"
        shutil.copytree(EXEMPLO, self.pasta)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def gravar(self, dados, nome="2026-10-20_2026-11-19.yaml"):
        caminho = self.tmp / nome
        caminho.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")
        return caminho

    def hipotese(self, hid):
        return next(h for h in carregar_cliente(self.pasta).hipoteses.hipoteses if h.id == hid)

    def rodar(self, *args):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            rc = main([str(a) for a in args])
        return rc, saida.getvalue()

    def test_registra_medicao_e_guarda_o_retorno(self):
        antes = (self.pasta / "hipoteses.yaml").read_text(encoding="utf-8")
        rel = registrar(self.gravar(retorno()), self.pasta)
        self.assertIsNone(rel.erro)
        h01 = self.hipotese("h01-gancho-travar")
        self.assertEqual((h01.resultado, h01.conversoes_obtidas), ("rodando", 52))  # a variação mais fraca
        m = next(x for x in rel.medicoes if x.hipotese.id == "h01-gancho-travar")
        self.assertTrue(m.pronta)
        self.assertEqual(m.por_codigo["PT01"], (60, 30.0))
        self.assertTrue((self.pasta / "resultados" / "2026-10-20_2026-11-19.yaml").exists())
        depois = (self.pasta / "hipoteses.yaml").read_text(encoding="utf-8")
        self.assertIn("# O que está sendo testado", depois)  # comentários ficam
        self.assertEqual(len(depois.splitlines()), len(antes.splitlines()) + 1)  # só entrou conversoes_obtidas

    def test_sem_volume_nao_esta_pronta(self):
        rel = registrar(self.gravar(retorno(pt02_leads=31)), self.pasta)
        m = next(x for x in rel.medicoes if x.hipotese.id == "h01-gancho-travar")
        self.assertFalse(m.pronta)
        self.assertIn("ainda sem volume: a variação mais fraca tem 31 de 50", self.rodar("registrar-resultados",
                      self.gravar(retorno(pt02_leads=31), "b.yaml"), self.pasta)[1])

    def test_variacoes_que_nao_sao_codigos(self):
        _, saida = self.rodar("registrar-resultados", self.gravar(retorno()), self.pasta)
        self.assertIn("h02-pagina-vs-whatsapp", saida)
        self.assertIn("as 2 variações não são códigos diferentes", saida)
        self.assertIn("GB01", saida)  # resultado sem hipótese aparece como só medição
        self.assertIn("14  Achou caro (comercial)", saida)

    def test_cliente_errado_e_arquivo_que_nao_e_retorno(self):
        rel = registrar(self.gravar(retorno(cliente="outro")), self.pasta)
        self.assertIn("é de 'outro'", rel.erro)
        self.assertFalse((self.pasta / "resultados").exists())
        with self.assertRaises(RetornoInvalido):
            registrar(self.gravar({"qualquer": 1}, "x.yaml"), self.pasta)

    def test_decidir(self):
        rc, saida = self.rodar("decidir", self.pasta, "h01-gancho-travar", "validada")
        self.assertEqual(rc, 1)
        self.assertIn("diga o aprendizado", saida)
        rc, saida = self.rodar("decidir", self.pasta, "h01-gancho-travar", "validada", "--aprendizado",
                               "O gancho da frase que não sai trouxe lead 23% mais barato", "--fim", "2026-11-20")
        self.assertEqual(rc, 0, saida)
        h01 = self.hipotese("h01-gancho-travar")
        self.assertEqual((h01.resultado, str(h01.fim)), ("validada", "2026-11-20"))
        self.assertIn("23% mais barato", h01.aprendizado)
        self.assertEqual(self.rodar("decidir", self.pasta, "nao-existe", "refutada", "--aprendizado", "x")[0], 1)

    def test_aprendizado_vai_para_a_copy(self):
        from trilha_briefing.exportar import pacote_copy
        self.rodar("decidir", self.pasta, "h01-gancho-travar", "validada", "--aprendizado", "gancho da frase venceu")
        h = next(x for x in pacote_copy(carregar_cliente(self.pasta))["hipoteses"] if x["id"] == "h01-gancho-travar")
        self.assertEqual((h["resultado"], h["aprendizado"]), ("validada", "gancho da frase venceu"))


if __name__ == "__main__":
    unittest.main()


try:
    from trilha.core import retorno as retorno_ads  # Trilha-ads 0.9.0+
    TEM_RETORNO = True
except ImportError:
    TEM_RETORNO = False


@unittest.skipUnless(TEM_RETORNO, "Trilha-ads com o retorno (0.9.0+) não instalado")
class TestContratoRetorno(unittest.TestCase):
    """O retorno que o Trilha-ads grava é o que o briefing lê."""

    def test_retorno_do_trilha_ads_entra_nas_hipoteses(self):
        from datetime import datetime, timezone

        import trilha
        from trilha.core.funil import LeadFunil, raio_x
        from trilha.core.perfil import carregar_perfil
        from trilha.core.playbook import carregar_playbook

        t0 = datetime(2026, 10, 21, 10, tzinfo=timezone.utc)
        leads = [LeadFunil(lead_id=i, etapas={"lead": t0}, criativo="PT01" if i % 2 else "PT02 | v1", pessoa=f"p{i}",
                           canal="Meta Ads") for i in range(120)]
        perfil = carregar_perfil(Path(trilha.__file__).parent.parent / "clientes" / "_exemplo" / "perfil.yaml")
        playbook = carregar_playbook("padrao")
        r = raio_x(leads, playbook, gasto_por_codigo={"PT01": 1800.0, "PT02": 2100.0})
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp) / "_exemplo"
            shutil.copytree(EXEMPLO, pasta)
            caminho = retorno_ads.gravar_retorno(retorno_ads.montar_retorno(r, leads, perfil, playbook), Path(tmp) / "ret")
            rel = registrar(caminho, pasta)
            self.assertIsNone(rel.erro)
            m = next(x for x in rel.medicoes if x.hipotese.id == "h01-gancho-travar")
            self.assertEqual(m.por_codigo["PT01"][0], 60)
            self.assertTrue(m.pronta)
