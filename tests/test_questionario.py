"""Questionário: perguntas como dado, formulário do cliente e importação das respostas.

Os testes não dependem do texto das perguntas (que muda em perguntas.yaml); conferem a estrutura e o caminho
pergunta → formulário → respostas → pasta do cliente.
"""

import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date
from pathlib import Path
from unittest import mock

import yaml

from trilha_briefing import questionario
from trilha_briefing.__main__ import main
from trilha_briefing.esquema import Briefing, ErroCliente, carregar_cliente
from trilha_briefing.questionario import Questionario, carregar
from trilha_briefing.questionario.campos import CampoInvalido, resolver
from trilha_briefing.questionario.editor import Arquivo
from trilha_briefing.questionario.formulario import dados_do_formulario, gerar_formulario
from trilha_briefing.questionario.importar import RespostasInvalidas, importar, ler_texto

MODELO = Path(__file__).parent.parent / "trilha_briefing" / "modelo"
HOJE = date(2026, 10, 5)


def silencioso(*args):
    with redirect_stdout(io.StringIO()) as saida:
        codigo = main(list(args))
    return codigo, saida.getvalue()


def valor_valido(campo):
    """Uma resposta, como viria do formulário, que cabe no campo."""
    return {"texto": "Resposta de teste", "inteiro": "12", "numero": "1.200,50", "booleano": "sim",
            "escolha": campo.valores[0] if campo.valores else "", "lista_texto": ["primeiro", "segundo"],
            "lista_item": "Primeira afirmação\nSegunda afirmação"}[campo.tipo_simples]


class Perguntas(unittest.TestCase):
    def test_carrega_e_tem_os_tres_momentos(self):
        q = carregar()
        self.assertTrue(q.versao)
        for momento in ("cliente", "reuniao", "assessor"):
            self.assertTrue(q.do_momento(momento), momento)
        # Só o cliente responde no formulário: obrigatória fora dele não faz sentido
        self.assertFalse([p.id for p in q.perguntas if p.obrigatoria and p.momento != "cliente"])

    def test_toda_pergunta_diz_para_onde_vai(self):
        sem_destino = [p.id for p in carregar().perguntas if not p.campo and not p.alimenta]
        self.assertFalse(sem_destino, "pergunta sem campo nem alimenta: o assessor não sabe onde anotar")

    def test_gerar_tres_visoes(self):
        cliente = questionario.gerar("Escola")
        self.assertNotIn("→ `", cliente)  # o campo de cada pergunta é coisa do assessor
        self.assertNotIn("●", cliente)
        condicional = next(p for p in questionario.perguntas("cliente") if p.condicao)
        self.assertIn(f"{condicional.pergunta}\n   _Só se, em", cliente)
        reuniao = questionario.gerar("Escola", para="reuniao")
        self.assertIn("Roteiro das entrevistas", reuniao)
        assessor = questionario.gerar("Escola", assessor=True)
        self.assertEqual(assessor.count("   - → "), len(questionario.perguntas()))

    def _base(self):
        return {"versao": "t", "blocos": [{"id": "b", "titulo": "B"}], "perguntas": [
            {"id": "tipo", "momento": "cliente", "bloco": "b", "pergunta": "?", "tipo": "escolha",
             "opcoes": ["a", "b"], "alimenta": "x"},
            {"id": "interna", "momento": "assessor", "bloco": "b", "pergunta": "?", "alimenta": "x"},
        ]}

    def test_erros_de_edicao_sao_apontados(self):
        casos = {
            "campo que não existe": {"campo": "briefing.negocio.nao_existe"},
            "condição para pergunta que vem depois": {"condicao": {"pergunta": "depois", "em": ["a"]}},
            "condição com valor que não existe": {"condicao": {"pergunta": "tipo", "em": ["z"]}},
            "condição para pergunta que o cliente não vê": {"condicao": {"pergunta": "interna", "em": ["a"]}},
            "opção fora do campo": {"tipo": "escolha", "opcoes": ["xyz"], "campo": "briefing.negocio.tipo_compra"},
            "escolha sem opções": {"tipo": "escolha"},
        }
        for nome, extra in casos.items():
            dados = self._base()
            dados["perguntas"].append({"id": "nova", "momento": "cliente", "bloco": "b", "pergunta": "?",
                                       "alimenta": "x", **extra})
            dados["perguntas"].append({"id": "depois", "momento": "cliente", "bloco": "b", "pergunta": "?",
                                       "tipo": "sim_nao", "alimenta": "x"})
            with self.subTest(nome), self.assertRaises(ValueError):
                Questionario.model_validate(dados)
        dados = self._base()
        dados["perguntas"].append({"id": "ok", "momento": "cliente", "bloco": "b", "pergunta": "?", "alimenta": "x",
                                   "condicao": {"pergunta": "tipo", "em": ["b"]}})
        Questionario.model_validate(dados)


class Campos(unittest.TestCase):
    def test_resolver(self):
        c = resolver("briefing.negocio.o_que_vende")
        self.assertEqual((c.arquivo, c.partes, c.tipo_simples), ("briefing", ("negocio", "o_que_vende"), "texto"))
        self.assertTrue(c.preenche_sozinho)
        self.assertEqual(resolver("briefing.negocio.tipo_compra").tipo_simples, "escolha")
        self.assertIn("desejo", resolver("briefing.negocio.tipo_compra").valores)
        lista = resolver("pesquisa.personas[].dores")
        self.assertTrue(lista.dentro_de_lista)
        self.assertFalse(lista.preenche_sozinho)  # item de lista: o assessor monta a persona
        self.assertFalse(resolver("ofertas.nome").preenche_sozinho)  # uma por arquivo: o assessor cria
        for ruim in ("negocio.o_que_vende", "briefing.negocio.xyz", "briefing.negocio[].o_que_vende", "briefing"):
            with self.subTest(ruim), self.assertRaises(CampoInvalido):
                resolver(ruim)


class Editor(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.arq = self.tmp / "briefing.yaml"
        shutil.copy(MODELO / "briefing.yaml", self.arq)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_preenche_so_o_valor_e_mantem_comentarios(self):
        antes = self.arq.read_text(encoding="utf-8")
        comentarios = [l for l in antes.splitlines() if l.strip().startswith("#")]
        a = Arquivo(self.arq, MODELO / "briefing.yaml", Briefing)
        self.assertEqual(a.preencher(("negocio", "o_que_vende"), 'Aulas: "inglês" # para adultos'), "preenchido")
        self.assertEqual(a.preencher(("negocio", "o_que_vende"), "outra coisa"), "conflito")
        self.assertEqual(a.preencher(("negocio", "nao_existe"), "x"), "invalido")  # o esquema não aceita a chave
        a.gravar()
        depois = self.arq.read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(depois)["negocio"]["o_que_vende"], 'Aulas: "inglês" # para adultos')
        self.assertEqual(comentarios, [l for l in depois.splitlines() if l.strip().startswith("#")])
        self.assertEqual(len(antes.splitlines()), len(depois.splitlines()))
        a.desfazer()
        self.assertEqual(self.arq.read_text(encoding="utf-8"), antes)


class EditorEstruturas(unittest.TestCase):
    """Chave em mapa em linha, chave que não está escrita e pai vazio (null)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.arq = self.tmp / "x.yaml"
        self.arq.write_text(
            "# cabeçalho\n"
            "historia: { catalisador: \"\", prova: \"\" }   # em linha\n"
            "bloco:\n"
            "  a: \"\"     # comentário de a\n"
            "  # comentário solto\n"
            "economia: null   # vazio\n"
            "fim: 1\n", encoding="utf-8")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_estruturas(self):
        a = Arquivo(self.arq)
        self.assertEqual(a.preencher(("historia", "catalisador"), "começou em 2010"), "preenchido")
        self.assertEqual(a.preencher(("bloco", "b"), ["um", "dois"]), "preenchido")
        self.assertEqual(a.preencher(("bloco", "c", "d"), 3), "preenchido")
        self.assertEqual(a.preencher(("economia", "ticket"), 2.5), "preenchido")
        self.assertEqual(a.preencher(("novo",), "x"), "preenchido")
        a.gravar()
        texto = self.arq.read_text(encoding="utf-8")
        self.assertEqual(yaml.safe_load(texto), {
            "historia": {"catalisador": "começou em 2010", "prova": ""},
            "bloco": {"a": "", "b": ["um", "dois"], "c": {"d": 3}},
            "economia": {"ticket": 2.5}, "fim": 1, "novo": "x"})
        for comentario in ("# cabeçalho", "# em linha", "# comentário de a", "# comentário solto", "# vazio"):
            self.assertIn(comentario, texto)

    def test_validador_desfaz_so_a_mudanca(self):
        from pydantic import BaseModel

        class Economia(BaseModel):
            modelo: str
            ticket: float | None = None

        class X(BaseModel):
            economia: Economia | None = None
            historia: dict = {}
            bloco: dict = {}
            fim: int = 0

        a = Arquivo(self.arq, validador=X)
        self.assertEqual(a.preencher(("economia", "ticket"), 2.5), "invalido")  # falta modelo
        self.assertEqual(a.motivo, "o bloco economia só vale completo (falta modelo); monte o bloco à mão com esta "
                                   "resposta como ponto de partida")
        self.assertIsNone(a.atual(("economia",)))
        self.assertEqual(a.preencher(("historia", "catalisador"), "x"), "preenchido")


class Importar(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        silencioso("novo", "escola", "--pasta", str(self.tmp))
        self.pasta = self.tmp / "escola"
        self.q = carregar()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def respostas(self, respostas, **extra):
        return {"formulario": "trilha-briefing", "versao": self.q.versao, "cliente": "Escola",
                "preenchido_em": "2026-10-05T10:00", "respostas": respostas, **extra}

    def automaticas(self):
        """Uma pergunta do cliente por campo que preenche sozinho, com uma resposta válida."""
        vistas, saida = set(), {}
        for p in self.q.do_momento("cliente"):
            d = p.destino
            if (d and d.preenche_sozinho and p.campo not in vistas and d.tipo_simples in ("texto", "lista_texto")
                    and p.tipo != "telefone" and not (d.info and d.info.metadata)  # campo com regra própria: teste à parte
                    and d.partes[:1] != ("economia",)):  # economia só vale inteira (modelo_receita): teste à parte
                vistas.add(p.campo)
                saida[p.id] = valor_valido(d)
        return saida

    def gravar(self, dados):
        caminho = self.tmp / "respostas.json"
        caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")
        return caminho

    def test_preenche_guarda_e_continua_valido(self):
        respostas = self.automaticas()
        self.assertTrue(respostas, "nenhuma pergunta do cliente preenche campo sozinha")
        rel = importar(self.gravar(self.respostas(respostas, nao_sei=["nao_existe"])), self.pasta, HOJE)
        self.assertIsNone(rel.erro)
        self.assertEqual(len(rel.preenchidos), len(respostas))
        self.assertFalse(rel.conflitos)
        carregar_cliente(self.pasta)  # continua válida
        briefing = yaml.safe_load((self.pasta / "briefing.yaml").read_text(encoding="utf-8"))
        self.assertIn("cliente", briefing["preenchido_por"])
        self.assertEqual(str(briefing["data"]), "2026-10-05")
        guardadas = sorted(p.name for p in (self.pasta / "respostas").iterdir())
        self.assertEqual(guardadas, ["2026-10-05-questionario.json", "2026-10-05-questionario.md"])
        self.assertEqual(rel.nao_sei, [])  # id que não existe não vai para a reunião
        # importar de novo não sobrescreve: vira conflito e as respostas ficam guardadas com outro nome
        rel2 = importar(self.gravar(self.respostas(respostas)), self.pasta, HOJE)
        self.assertEqual(len(rel2.conflitos), len(respostas))
        self.assertTrue((self.pasta / "respostas" / "2026-10-05-questionario-2.json").exists())

    def test_tipos_convertidos(self):
        numeros = [p for p in self.q.do_momento("cliente")
                   if p.destino and p.destino.preenche_sozinho and p.destino.tipo_simples == "numero"]
        escolhas = [p for p in self.q.do_momento("cliente")
                    if p.destino and p.destino.preenche_sozinho and p.destino.tipo_simples == "escolha"]
        respostas = {}
        if numeros:
            respostas[numeros[0].id] = "1.200,50" if numeros[0].tipo != "porcentagem" else "35"
        if escolhas:
            respostas[escolhas[0].id] = escolhas[0].destino.valores[0]
        if not respostas:
            self.skipTest("nenhuma pergunta de número ou escolha preenche sozinha")
        rel = importar(self.gravar(self.respostas(respostas)), self.pasta, HOJE)
        self.assertIsNone(rel.erro)
        c = carregar_cliente(self.pasta)
        numeros = [p for p in numeros[:1] if (p.id, p.campo) in rel.preenchidos]
        if numeros:
            p = numeros[0]
            atual = getattr(c, p.destino.arquivo)
            for parte in p.destino.partes:
                atual = getattr(atual, parte)
            self.assertAlmostEqual(atual, 0.35 if p.tipo == "porcentagem" else 1200.5)

    def test_o_que_nao_converte_vai_para_levar(self):
        numero = next((p for p in self.q.do_momento("cliente") if p.destino and p.destino.preenche_sozinho
                       and p.destino.tipo_simples in ("numero", "inteiro")), None)
        if numero is None:
            self.skipTest("nenhuma pergunta de número preenche sozinha")
        rel = importar(self.gravar(self.respostas({numero.id: "entre 10 e 20", "sumiu": "x"})), self.pasta, HOJE)
        self.assertFalse(rel.preenchidos)
        self.assertEqual([p.id for itens in rel.levar.values() for p, _, _ in itens], [numero.id])
        self.assertEqual(rel.desconhecidas, ["sumiu"])

    def test_pasta_invalida_desfaz_tudo(self):
        antes = {p.name: p.read_text(encoding="utf-8") for p in self.pasta.glob("*.yaml")}
        erro = ErroCliente({"briefing.yaml": "inválido"})
        with mock.patch("trilha_briefing.questionario.importar.carregar_cliente", side_effect=erro):
            rel = importar(self.gravar(self.respostas(self.automaticas())), self.pasta, HOJE)
        self.assertTrue(rel.erro)
        self.assertEqual(antes, {p.name: p.read_text(encoding="utf-8") for p in self.pasta.glob("*.yaml")})
        self.assertFalse((self.pasta / "respostas").exists())

    def test_campo_com_regra_vai_para_levar_com_o_motivo(self):
        p = next((p for p in self.q.do_momento("cliente") if p.campo == "briefing.cliente.whatsapp"), None)
        if p is None:
            self.skipTest("o formulário não pergunta o WhatsApp")
        rel = importar(self.gravar(self.respostas({p.id: "só à tarde"})), self.pasta, HOJE)
        self.assertIsNone(rel.erro)  # um valor fora do padrão não derruba o resto
        [(_, valor, motivo)] = [x for itens in rel.levar.values() for x in itens]
        self.assertTrue(motivo)
        if p.tipo == "telefone":
            importar(self.gravar(self.respostas({p.id: "(11) 98765-4321"})), self.pasta, HOJE)
            self.assertEqual(carregar_cliente(self.pasta).briefing.cliente.whatsapp, "5511987654321")

    def test_versao_diferente_e_avisada(self):
        rel = importar(self.gravar(self.respostas({}, versao="antiga")), self.pasta, HOJE)
        self.assertEqual(rel.versao_diferente, "antiga")

    def test_ler_texto_colado(self):
        dados = self.respostas({"x": "y"})
        colado = "Oi, seguem as respostas:\n" + json.dumps(dados) + "\nAbraço"
        self.assertEqual(ler_texto(colado), dados)
        for ruim in ("sem json", json.dumps({"formulario": "outro", "respostas": {}}), "{quebrado"):
            with self.subTest(ruim), self.assertRaises(RespostasInvalidas):
                ler_texto(ruim)

    def test_linha_de_comando(self):
        caminho = self.gravar(self.respostas(self.automaticas()))
        codigo, saida = silencioso("importar-respostas", str(caminho), str(self.pasta))
        self.assertEqual(codigo, 0, saida)
        self.assertIn("respostas guardadas", saida)
        with mock.patch("sys.stdin", io.StringIO(caminho.read_text(encoding="utf-8"))):
            self.assertEqual(silencioso("importar-respostas", "-", str(self.pasta))[0], 0)
        with mock.patch("sys.stdin", io.StringIO("não é json")):
            self.assertEqual(silencioso("importar-respostas", "-", str(self.pasta))[0], 1)
        self.assertEqual(silencioso("importar-respostas", str(caminho), str(self.tmp))[0], 1)  # não é pasta de cliente


class Formulario(unittest.TestCase):
    def test_so_perguntas_do_cliente_e_dados_embutidos(self):
        html = gerar_formulario("Escola </script><b>X</b>", "Davi")
        self.assertEqual(html.count("</script>"), 2)  # o nome do cliente não fecha o bloco de dados
        self.assertIn("<title>Questionário de início — Escola &lt;/script&gt;&lt;b&gt;X&lt;/b&gt;</title>", html)
        bruto = html.split('<script id="dados" type="application/json">')[1].split("</script>")[0]
        dados = json.loads(bruto)
        q = carregar()
        self.assertEqual(dados, dados_do_formulario(q, "Escola </script><b>X</b>", "Davi"))
        ids = [p["id"] for b in dados["blocos"] for p in b["perguntas"]]
        self.assertEqual(ids, [p.id for b in q.blocos for p in q.do_momento("cliente") if p.bloco == b.id])
        self.assertEqual(dados["formulario"], "trilha-briefing")
        self.assertEqual(dados["chave"], f"trilha-questionario:{q.versao}:escola-script-b-x-b")

    def test_linha_de_comando(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            codigo, saida = silencioso("questionario", "--formulario", str(tmp / "f.html"), "--cliente", "Escola")
            self.assertEqual(codigo, 0)
            self.assertIn("Escola", (tmp / "f.html").read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(tmp)


if __name__ == "__main__":
    unittest.main()
