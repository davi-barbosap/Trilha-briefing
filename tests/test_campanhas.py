import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from trilha_briefing.__main__ import main
from trilha_briefing.apresentar import gerar_html
from trilha_briefing.campanhas import ErroRegras, regras_do_plano, sugerir
from trilha_briefing.esquema import ErroCliente, PlanoCampanhas, carregar_cliente
from trilha_briefing.lacunas import bloqueios_aprovacao, lacunas
from trilha_briefing.revisao import avisos_do_plano

EXEMPLO = Path(__file__).parent.parent / "clientes" / "_exemplo"


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

    def regras(self, **regras):
        self.editar("campanhas.yaml", lambda d: d.update(regras=regras))

    def avisos(self, nivel=None):
        return [a.texto for a in avisos_do_plano(carregar_cliente(self.pasta)) if nivel is None or a.nivel == nivel]

    def campanha(self, cid):
        def mudar(d):
            return next(cp for cp in d["campanhas"] if cp["id"] == cid)
        return mudar

    def rodar(self, *args):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            rc = main([str(a) for a in args])
        return rc, saida.getvalue()


def contem(lista, trecho):
    return any(trecho in t for t in lista)


class TestRegras(Base):
    def test_padrao_do_repositorio(self):
        r = regras_do_plano(PlanoCampanhas())
        self.assertEqual(r.aprendizado.eventos_por_semana["meta"], 50)
        self.assertIsNone(r.aprendizado.eventos_por_semana["google"])
        self.assertEqual(r.fases.ordem, ["fundacao", "validacao", "otimizacao", "escala"])
        self.assertFalse(r.plano.obrigatorio_para_aprovar)

    def test_cliente_muda_so_o_que_precisa(self):
        r = regras_do_plano(PlanoCampanhas(regras={"aprendizado": {"eventos_por_semana": {"meta": 10}}}))
        self.assertEqual(r.aprendizado.eventos_por_semana["meta"], 10)
        self.assertEqual(r.aprendizado.eventos_por_semana["tiktok"], 50)  # o resto continua o padrão
        self.assertEqual(r.aprendizado.nivel, "atencao")

    def test_chave_errada_ou_campo_de_nome_desconhecido_e_recusado(self):
        with self.assertRaises(ErroRegras):
            regras_do_plano(PlanoCampanhas(regras={"aprendizdo": {"nivel": "sugestao"}}))
        with self.assertRaises(ErroRegras):
            regras_do_plano(PlanoCampanhas(regras={"nomes": {"anuncio": "{codigo} {cor}"}}))
        self.regras(fases={"ordem": ["teste", "escala"]})  # fases.entrar cita validacao e otimizacao
        with self.assertRaises(ErroCliente) as e:
            carregar_cliente(self.pasta)
        self.assertIn("regras do plano inválidas", str(e.exception))

    def test_regra_desligada_some_e_gravidade_muda(self):
        self.assertTrue(contem(self.avisos("atencao"), "aprendizado limitado"))
        self.regras(aprendizado={"nivel": "sugestao"})
        self.assertTrue(contem(self.avisos("sugestao"), "aprendizado limitado"))
        self.regras(aprendizado={"nivel": "desligada"})
        self.assertFalse(contem(self.avisos(), "aprendizado"))


class TestPlano(Base):
    def test_exemplo(self):
        c = carregar_cliente(EXEMPLO)
        self.assertEqual([cp.id for cp in c.campanhas.campanhas], ["google-marca", "google-ingles-adultos", "meta-profissional"])
        avisos = avisos_do_plano(c)
        self.assertFalse(any(a.nivel == "bloqueia" for a in avisos))
        textos = [a.texto for a in avisos]
        self.assertTrue(contem(textos, "meta-profissional: cerca de 13 leads por semana"))
        self.assertTrue(contem(textos, "células sem campanha: VA01"))
        self.assertTrue(contem(textos, "hipótese h02-pagina-vs-whatsapp sem teste"))
        self.assertTrue(contem(textos, "canal remarketing (meta)"))
        self.assertTrue(contem(textos, "resultado é direcional"))
        self.assertEqual(bloqueios_aprovacao(c), [])

    def test_referencias(self):
        casos = [
            (lambda d: self.campanha("google-marca")(d).update(canal="display_video"), "canal 'display_video'"),
            (lambda d: self.campanha("meta-profissional")(d)["conjuntos"][0]["celulas"].append("ZZ99"), "células fora da grade"),
            (lambda d: self.campanha("meta-profissional")(d)["testes"].append({"hipotese": "h99"}), "hipóteses inexistentes"),
            (lambda d: self.campanha("google-marca")(d).update(fase="lancamento"), "fase 'lancamento'"),
            (lambda d: self.campanha("google-marca")(d).update(id_plataforma="123"), "ids_da_plataforma está desligado"),
        ]
        for mudar, trecho in casos:
            shutil.copyfile(EXEMPLO / "campanhas.yaml", self.pasta / "campanhas.yaml")
            self.editar("campanhas.yaml", mudar)
            with self.assertRaises(ErroCliente, msg=trecho) as e:
                carregar_cliente(self.pasta)
            self.assertIn(trecho, str(e.exception))
        shutil.copyfile(EXEMPLO / "campanhas.yaml", self.pasta / "campanhas.yaml")
        self.editar("campanhas.yaml", lambda d: (self.campanha("google-marca")(d).update(id_plataforma="123"),
                                                 d.update(regras={"espelho": {"ids_da_plataforma": True}})))
        carregar_cliente(self.pasta)

    def test_verba_sem_valor_divide_a_fatia_do_canal_e_soma_confere(self):
        # busca_produto tem 35% de R$ 5.000; duas campanhas sem verba dividem a fatia
        def duas(d):
            nova = dict(self.campanha("google-ingles-adultos")(d), id="google-ingles-2")
            nova["conjuntos"] = [dict(nova["conjuntos"][0], celulas=[])]
            d["campanhas"].append(nova)
        self.editar("campanhas.yaml", duas)
        rc, saida = self.rodar("plano", self.pasta)
        self.assertEqual(saida.count("busca produto · Google · fase validação · otimiza por lead · R$ 875,00/mês"), 2)
        self.editar("campanhas.yaml", lambda d: self.campanha("meta-profissional")(d).update(verba_mensal=9000))
        self.assertTrue(contem(self.avisos("bloqueia"), "acima do teto combinado"))
        self.editar("campanhas.yaml", lambda d: self.campanha("meta-profissional")(d).update(verba_mensal=3500))
        self.assertTrue(contem(self.avisos("atencao"), "as campanhas somam R$ 5.750/mês e a estratégia diz R$ 5.000"))

    def test_conjuntos_alem_do_que_a_verba_aguenta(self):
        self.regras(aprendizado={"eventos_por_semana": {"meta": 10}})  # 13 leads/semana: cabe 1 conjunto
        self.assertFalse(contem(self.avisos(), "aprendizado"))

        def tres(d):
            cj = self.campanha("meta-profissional")(d)["conjuntos"]
            cj[:] = [dict(cj[0], id=x, celulas=[c]) for x, c in (("a", "PT01"), ("b", "PT02"), ("c", "PT03"))]
        self.editar("campanhas.yaml", tres)
        self.assertTrue(contem(self.avisos("atencao"), "3 conjuntos, mas a verba aguenta 1"))

    def test_testes(self):
        self.editar("campanhas.yaml", lambda d: self.campanha("meta-profissional")(d).update(testes=[{"hipotese": "h01-gancho-travar"}]))
        self.assertTrue(contem(self.avisos("atencao"), "teste da h01-gancho-travar sem método"))
        self.regras(testes={"metodo_padrao": "conjuntos_separados"})
        self.assertTrue(contem(self.avisos("atencao"), "usa conjuntos separados, mas as variações estão no mesmo conjunto"))
        self.editar("campanhas.yaml", lambda d: self.campanha("meta-profissional")(d).update(verba_mensal=1000))
        self.assertTrue(contem(self.avisos("atencao"), "precisa de 100 leads; a campanha compra cerca de 5 por semana"))

    def test_nome_de_anuncio_sem_codigo_bloqueia_a_aprovacao(self):
        self.regras(nomes={"anuncio": "{campanha} v{versao}"})
        self.assertTrue(contem(self.avisos("bloqueia"), "regras.nomes.anuncio sem {codigo}"))
        self.assertTrue(contem(bloqueios_aprovacao(carregar_cliente(self.pasta)), "regras.nomes.anuncio sem {codigo}"))

    def test_fase_exige_medicao(self):
        self.editar("estrategia.yaml", lambda d: d["medicao"].update(codigo_criativo=False))
        self.assertTrue(contem(self.avisos("atencao"), "google-marca: em validação, mas a medição não está completa (codigo_criativo)"))
        self.editar("campanhas.yaml", lambda d: [cp.update(fase="fundacao") for cp in d["campanhas"]])
        self.assertFalse(contem(self.avisos(), "medição não está completa"))


class TestSugestaoEAprovacao(Base):
    def test_sem_plano_vira_lacuna_e_so_bloqueia_se_a_regra_mandar(self):
        (self.pasta / "campanhas.yaml").unlink()
        c = carregar_cliente(self.pasta)
        self.assertTrue(contem(lacunas(c)["estrategia"], "plano de campanhas"))
        self.assertEqual(bloqueios_aprovacao(c), [])
        (self.pasta / "campanhas.yaml").write_text("regras: { plano: { obrigatorio_para_aprovar: true } }\ncampanhas: []\n",
                                                   encoding="utf-8")
        self.assertTrue(contem(bloqueios_aprovacao(carregar_cliente(self.pasta)), "sem plano de campanhas"))

    def test_sugerir_grava_um_plano_valido_e_nao_sobrescreve(self):
        (self.pasta / "campanhas.yaml").unlink()
        plano = sugerir(carregar_cliente(self.pasta))
        self.assertEqual([cp.id for cp in plano.campanhas],
                         ["google-busca-marca", "google-busca-produto", "meta-interesses", "meta-remarketing"])
        meta = plano.campanhas[2]
        self.assertEqual([cj.id for cj in meta.conjuntos], ["amplo"])  # a verba não aguenta um conjunto por persona
        self.assertEqual(meta.conjuntos[0].celulas, ["PT01", "PT02", "PT03", "VA01"])
        self.assertEqual([t.hipotese for t in meta.testes], ["h01-gancho-travar", "h02-pagina-vs-whatsapp"])
        rc, saida = self.rodar("plano", self.pasta, "--sugerir")
        self.assertEqual(rc, 0, saida)
        self.assertIn("SUGESTÃO", (self.pasta / "campanhas.yaml").read_text(encoding="utf-8"))
        self.assertEqual(len(carregar_cliente(self.pasta).campanhas.campanhas), 4)
        self.assertEqual(self.rodar("plano", self.pasta, "--sugerir")[0], 1)

    def test_comando_plano(self):
        rc, saida = self.rodar("plano", self.pasta)
        self.assertEqual(rc, 0, saida)
        for trecho in ("Plano de campanhas — Escola Exemplo de Inglês", "Nome: _exemplo | meta-profissional",
                       "utm_content={codigo}", "PT01 | v1", "Para entrar em otimização: custo por lead até R$ 64,58 (1,3× o teto)",
                       "Negativas: grátis"):
            self.assertIn(trecho, saida)
        self.regras(nomes={"anuncio": "{campanha} v{versao}"})
        self.assertEqual(self.rodar("plano", self.pasta)[0], 1)  # algo bloqueia

    def test_apresentacao_mostra_a_divisao_da_verba(self):
        html = gerar_html(carregar_cliente(EXEMPLO))
        self.assertIn("Como a verba se divide", html)
        self.assertIn("R$ 2.750", html)
        self.assertNotIn("utm_content", html)  # nomes e UTMs são internos


if __name__ == "__main__":
    unittest.main()
