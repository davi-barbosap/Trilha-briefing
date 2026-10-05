import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from trilha_briefing import questionario
from trilha_briefing.__main__ import main
from trilha_briefing.apresentar import gerar_html
from trilha_briefing.canais import sugerir
from trilha_briefing.economia import calcular, conversoes_na_validacao
from trilha_briefing.esquema import ErroCliente, Item, carregar_cliente
from trilha_briefing.exportar import exportar_lp, oferta_trilha, pagina_lp, perfil_parcial
from trilha_briefing.lacunas import bloqueios_aprovacao, lacunas
from trilha_briefing.revisao import revisar

EXEMPLO = Path(__file__).parent.parent / "clientes" / "_exemplo"

# Campos aceitos pelo esquema de oferta do Trilha (trilha/core/oferta.py, extra="forbid").
CAMPOS_OFERTA_TRILHA = {
    "oferta", "aderencia", "diferenciais", "raridade", "ancoras", "vias_acesso", "valorizacao",
    "critica_localizacao", "condicoes_comerciais", "objecoes", "objecoes_avulsas", "perfil_lead", "assets",
}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pasta = self.tmp / "_exemplo"
        shutil.copytree(EXEMPLO, self.pasta)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def editar(self, arquivo, mudar):
        caminho = self.pasta / arquivo
        dados = yaml.safe_load(caminho.read_text(encoding="utf-8"))
        mudar(dados)
        caminho.write_text(yaml.safe_dump(dados, allow_unicode=True), encoding="utf-8")


class TestEsquema(Base):
    def test_exemplo_valida_e_esta_pronto(self):
        c = carregar_cliente(EXEMPLO)
        self.assertEqual(len(c.ofertas), 2)
        self.assertEqual(bloqueios_aprovacao(c), [])
        self.assertEqual(lacunas(c)["estrategia"], [])

    def test_texto_solto_vira_hipotese_sem_fonte(self):
        it = Item.model_validate("Turmas pequenas")
        self.assertEqual((it.fonte, it.status), ("nao_informada", "hipotese"))

    def test_fonte_cliente_e_recusada(self):
        self.editar("briefing.yaml", lambda d: d["historico"]["funcionou"].append({"texto": "x", "fonte": "cliente"}))
        with self.assertRaises(ErroCliente) as e:
            carregar_cliente(self.pasta)
        self.assertIn("ambígua", e.exception.erros["briefing.yaml"])

    def test_persona_inexistente_na_oferta(self):
        self.editar("ofertas/aula-experimental.yaml", lambda d: d["personas"].append("fantasma"))
        with self.assertRaises(ErroCliente) as e:
            carregar_cliente(self.pasta)
        self.assertIn("ofertas/aula-experimental.yaml", e.exception.erros)

    def test_codigo_repetido_na_grade(self):
        self.editar("estrategia.yaml", lambda d: d["grade"].append(dict(d["grade"][0])))
        with self.assertRaises(ErroCliente) as e:
            carregar_cliente(self.pasta)
        self.assertIn("repetidos", e.exception.erros["estrategia.yaml"])

    def test_economia_incoerente(self):
        self.editar("estrategia.yaml", lambda d: d["economia"].pop("mensalidade"))
        with self.assertRaises(ErroCliente):
            carregar_cliente(self.pasta)

    def test_pasta_e_id_diferentes(self):
        destino = self.tmp / "outro"
        shutil.copytree(EXEMPLO, destino)
        with self.assertRaises(ErroCliente):
            carregar_cliente(destino)


class TestEconomia(unittest.TestCase):
    def test_mesmos_numeros_do_trilha(self):
        # recorrência: 460 × 10 = 4.600; CAC = 4.600 × 0,45 × 0,3 = 621
        c = carregar_cliente(EXEMPLO)
        n = calcular(c.estrategia.economia)
        self.assertAlmostEqual(n.cac_max, 621.0)
        self.assertAlmostEqual(n.custo_max["lead"], 49.68)
        self.assertAlmostEqual(n.custo_max["agendamento"], 248.4)
        self.assertAlmostEqual(n.verba_minima_viavel, 10800.96, places=1)
        self.assertAlmostEqual(conversoes_na_validacao(c.estrategia), 8000 / 248.4)


class TestRevisao(Base):
    def test_exemplo_tem_so_os_avisos_esperados(self):
        avisos = revisar(carregar_cliente(EXEMPLO))
        self.assertTrue(any("sem autorização" in a for a in avisos))
        self.assertTrue(any("mínima viável" in a for a in avisos))
        self.assertFalse(any("escassez" in a for a in avisos))

    def test_regras_criticas(self):
        def oferta(d):
            d["promessa"]["prazo"] = ""
            d["promessa"]["texto"] = "Fluência garantida para todos"
            d["escassez"] = {"texto": "Últimas vagas", "real": False}
        self.editar("ofertas/conversacao-adultos.yaml", oferta)

        def estrategia(d):
            d["canais"][4]["status"] = "teste"
            d["orcamento"]["verba_validacao"] = 2000
        self.editar("estrategia.yaml", estrategia)
        avisos = " | ".join(revisar(carregar_cliente(self.pasta)))
        self.assertIn("promessa sem prazo", avisos)
        self.assertIn("termo proibido", avisos)
        self.assertIn("escassez sem evidência", avisos)
        self.assertIn("busca_concorrente sem aprovação", avisos)
        self.assertIn("h01-gancho-travar precisa de 100 lead (50 × 2 variações)", avisos)

    def test_volume_conta_todas_as_variacoes(self):
        # R$ 8.000 / R$ 49,68 = 161 leads: cabem 50 × 2 variações, não 50 × 4
        self.assertFalse(any("h01" in a for a in revisar(carregar_cliente(EXEMPLO))))
        self.editar("hipoteses.yaml", lambda d: d["hipoteses"][0].update(variacoes=4))
        self.assertTrue(any("h01-gancho-travar precisa de 200 lead" in a for a in revisar(carregar_cliente(self.pasta))))

    def test_evento_de_otimizacao_inviavel(self):
        def est(d):
            d["orcamento"].update(verba_mensal=30000, teto_mensal=30000)
            d["evento_otimizacao"] = "agendamento"
        self.editar("estrategia.yaml", est)
        avisos = revisar(carregar_cliente(self.pasta))
        self.assertTrue(any("otimizar por agendamento" in a and "otimize por lead_qualificado" in a for a in avisos))

    def test_hipotese_concluida_sem_volume(self):
        def hip(d):
            d["hipoteses"][0].update(resultado="validada", conversoes_obtidas=8)
        self.editar("hipoteses.yaml", hip)
        self.assertTrue(any("trate como inconclusiva" in a for a in revisar(carregar_cliente(self.pasta))))

    def test_objecao_so_da_empresa_bloqueia_aprovacao(self):
        def so_empresa(d):
            for o in d["personas"][0]["objecoes"]:
                o["fonte"] = "empresa"
        self.editar("pesquisa.yaml", so_empresa)
        bloqueios = bloqueios_aprovacao(carregar_cliente(self.pasta))
        self.assertTrue(any("profissional-travado" in b for b in bloqueios))

    def test_sem_escuta_bloqueia_aprovacao(self):
        self.editar("pesquisa.yaml", lambda d: d.update(escuta=[]))
        self.assertTrue(any("escuta" in b for b in bloqueios_aprovacao(carregar_cliente(self.pasta))))


class TestCanais(Base):
    def test_desejo_puxa_descoberta(self):
        antes = [s.canal for s in sugerir(carregar_cliente(EXEMPLO))]
        self.editar("briefing.yaml", lambda d: d["negocio"].update(tipo_compra="desejo"))
        depois = [s.canal for s in sugerir(carregar_cliente(self.pasta))]
        self.assertLess(depois.index("interesses"), antes.index("interesses"))
        self.assertLess(depois.index("interesses"), depois.index("busca_produto"))


class TestExportar(Base):
    def test_oferta_no_formato_do_trilha(self):
        c = carregar_cliente(EXEMPLO)
        d = oferta_trilha(c, c.oferta("conversacao-adultos"))
        self.assertLessEqual(set(d), CAMPOS_OFERTA_TRILHA)
        self.assertEqual(d["objecoes"][0]["resposta_do_time"][:6], "Você r")

    def test_perfil_parcial(self):
        d = perfil_parcial(carregar_cliente(EXEMPLO))
        self.assertEqual(d["metrica_principal"], "agendamento")
        self.assertEqual(d["economia"]["modelo_receita"], "recorrencia")
        self.assertEqual(d["verba"]["teto_mensal"], 6000)

    def test_pagina_por_origem(self):
        c = carregar_cliente(EXEMPLO)
        o = c.oferta("conversacao-adultos")
        meta, pend = pagina_lp(c, o, "meta")
        google, _ = pagina_lp(c, o, "google")
        self.assertEqual(pend, [])
        self.assertIn("dor", meta)
        self.assertNotIn("dor", google)
        self.assertIn("prova_social", google)
        self.assertTrue(4 <= len(meta["beneficios"]["itens"]) <= 8)
        self.assertEqual(meta["contato"]["whatsapp"], "5541900000000")

    def test_pendencias_ficam_no_arquivo(self):
        c = carregar_cliente(EXEMPLO)
        escritos = exportar_lp(c, self.tmp / "lp", oferta="aula-experimental", origens=("meta",))
        caminho, pend = escritos[0]
        self.assertTrue(pend)
        self.assertIn("# PENDENTE:", caminho.read_text(encoding="utf-8"))


class TestApresentar(Base):
    def test_html(self):
        self.editar("briefing.yaml", lambda d: d["cliente"].update(nome="Escola <Exemplo> & Cia"))
        html = gerar_html(carregar_cliente(self.pasta))
        self.assertIn("Escola &lt;Exemplo&gt; &amp; Cia", html)
        self.assertIn("O plano", html)
        self.assertNotIn("nao_informada", html)
        self.assertLess(html.index("Inglês para falar no trabalho"), html.index("Aula experimental</h3>"))


class TestCli(Base):
    def test_questionario(self):
        texto = questionario.gerar("Escola", assessor=True)
        self.assertIn("1. O que vocês vendem?", texto)
        self.assertIn("→ `briefing: negocio.o_que_vende`", texto)
        self.assertNotIn("→", questionario.gerar("Escola"))

    def test_novo(self):
        self.assertEqual(main(["novo", "cliente-novo", "--pasta", str(self.tmp)]), 0)
        c = carregar_cliente(self.tmp / "cliente-novo")
        self.assertEqual(c.briefing.cliente.id, "cliente-novo")
        self.assertTrue(bloqueios_aprovacao(c))
        self.assertEqual(main(["novo", "cliente-novo", "--pasta", str(self.tmp)]), 1)


if __name__ == "__main__":
    unittest.main()
