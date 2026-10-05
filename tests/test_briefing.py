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
from trilha_briefing.revisao import revisar as _revisar


def revisar(c):
    return [a.texto for a in _revisar(c)]

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


class TestGravidade(Base):
    def test_exemplo_sem_bloqueio_e_cli_ok(self):
        self.assertFalse([a for a in _revisar(carregar_cliente(EXEMPLO)) if a.nivel == "bloqueia"])
        self.assertEqual(main(["revisar", str(EXEMPLO)]), 0)

    def test_bloqueio_vira_lacuna_e_cli_falha(self):
        self.editar("briefing.yaml", lambda d: d["negocio"].update(modelo_receita="venda_direta"))
        c = carregar_cliente(self.pasta)
        self.assertTrue(any("modelo de receita diferente" in b for b in bloqueios_aprovacao(c)))
        self.assertEqual(main(["revisar", str(self.pasta)]), 1)

    def test_ticket_divergente(self):
        self.editar("ofertas/conversacao-adultos.yaml", lambda d: d["condicoes"].update(ticket_medio=900))
        self.assertTrue(any("ticket da oferta principal" in a for a in revisar(carregar_cliente(self.pasta))))

    def test_prova_de_autoridade_precisa_de_fonte_nao_de_autorizacao(self):
        from trilha_briefing.esquema import Prova, Provas
        p = Provas(provas=[Prova(tipo="certificacao", texto="ISO 9001", fonte="certificado nº 123")])
        self.assertEqual(len(p.utilizaveis()), 1)

    def test_melhorar_nao_e_adjetivo_vago(self):
        def dif(d):
            d["diferenciais"] = ["Aulas para melhorar a pronúncia", "O melhor método", "Turmas de até 6"]
        self.editar("ofertas/conversacao-adultos.yaml", dif)
        vagos = [a for a in revisar(carregar_cliente(self.pasta)) if "adjetivo sem fato" in a]
        self.assertEqual(len(vagos), 1)
        self.assertIn("O melhor método", vagos[0])


class TestBriefingCompleto(Base):
    def test_cor_e_preco_validados_na_origem(self):
        self.editar("plataforma.yaml", lambda d: d["identidade_visual"]["cores"].update(primaria="azul"))
        with self.assertRaises(ErroCliente):
            carregar_cliente(self.pasta)
        shutil.rmtree(self.pasta)
        shutil.copytree(EXEMPLO, self.pasta)
        self.editar("plataforma.yaml", lambda d: d["preco"].update(anuncio="sob_consulta"))
        with self.assertRaises(ErroCliente):
            carregar_cliente(self.pasta)

    def test_lacunas_do_briefing(self):
        def tira(d):
            d.pop("area")
            d["capacidade"] = {}
            d["aprovacao"] = {}
        self.editar("briefing.yaml", tira)
        faltas = " | ".join(lacunas(carregar_cliente(self.pasta))["briefing"])
        for trecho in ("área de atuação", "capacidade", "quem aprova", "acessos pendentes"):
            self.assertIn(trecho, faltas)

    def test_verba_acima_da_capacidade(self):
        self.editar("briefing.yaml", lambda d: d["capacidade"].update(leads_dia=2))
        self.assertTrue(any("o time atende bem 2" in a for a in revisar(carregar_cliente(self.pasta))))

    def test_persona_negativa_e_lacuna(self):
        self.editar("pesquisa.yaml", lambda d: d.update(nao_atender=[]))
        self.assertTrue(any("persona negativa" in f for f in lacunas(carregar_cliente(self.pasta))["pesquisa"]))


class TestCanais(Base):
    def test_marketplace_so_quando_existe(self):
        self.assertNotIn("marketplace", [s.canal for s in sugerir(carregar_cliente(EXEMPLO))])
        self.editar("briefing.yaml", lambda d: d["negocio"].update(marketplaces=["Mercado Livre"]))
        self.assertIn("marketplace", [s.canal for s in sugerir(carregar_cliente(self.pasta))])

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
        self.assertEqual(pend, [])  # a oferta principal do exemplo tem benefícios escritos
        self.assertIn("dor", meta)
        self.assertNotIn("dor", google)
        self.assertIn("prova_social", google)
        self.assertTrue(4 <= len(meta["beneficios"]["itens"]) <= 8)
        self.assertEqual(meta["contato"]["whatsapp"], "5541900000000")

    def test_whatsapp_ausente_nao_passa_por_valido(self):
        self.editar("briefing.yaml", lambda d: d["cliente"].update(whatsapp=""))
        c = carregar_cliente(self.pasta)
        pagina, pend = pagina_lp(c, c.oferta("conversacao-adultos"), "meta")
        self.assertNotRegex(pagina["contato"]["whatsapp"], r"^55\d{10,11}$")
        self.assertTrue(any("whatsapp" in p for p in pend))

    def test_subtitulo_nao_repete_a_solucao(self):
        c = carregar_cliente(EXEMPLO)
        pagina, _ = pagina_lp(c, c.oferta("conversacao-adultos"), "meta")
        self.assertNotEqual(pagina["topo"]["subtitulo"], pagina["dor"]["solucao"])

    def test_beneficios_escritos_tem_prioridade(self):
        itens = [{"titulo": f"Benefício {i}", "texto": f"Texto {i}"} for i in range(5)]
        self.editar("ofertas/conversacao-adultos.yaml", lambda d: d.update(beneficios=itens))
        c = carregar_cliente(self.pasta)
        pagina, pend = pagina_lp(c, c.oferta("conversacao-adultos"), "meta")
        self.assertEqual(pagina["beneficios"]["itens"], itens)
        self.assertEqual(pend, [])

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

    def test_hipotese_marcada_e_risco_interno_fora(self):
        html = gerar_html(carregar_cliente(EXEMPLO))
        self.assertIn("Já tentei e não funcionou comigo</li>", html)  # validada: sem marca
        self.assertIn("Aplicativo é mais barato <span class=\"hip\">a confirmar</span>", html)
        self.assertNotIn("Consultora não dá conta", html)
        self.assertIn("Lead agenda e não comparece", html)


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
