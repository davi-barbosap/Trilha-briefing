"""Formulário do questionário (★ cliente) num arquivo HTML só, para mandar ao cliente.

- Funciona sem internet e sem servidor: abre no navegador do celular ou do computador.
- Salva o progresso no próprio aparelho (localStorage); fechar e voltar continua de onde parou.
- No fim, gera o arquivo de respostas (JSON) que o cliente envia de volta, e que entra com `importar-respostas`.
- Nada sai do aparelho sem o cliente baixar ou copiar as respostas.
- Gerado sem cliente, serve para todos: publicado num endereço, o link leva o nome (`?cliente=Escola%20X&quem=Davi`)
  e o progresso fica separado por cliente.
"""

from __future__ import annotations

import json
import re
import unicodedata

from trilha_briefing.questionario import Questionario, carregar
from trilha_briefing.questionario.importar import FORMULARIO


def _slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "cliente"


def dados_do_formulario(q: Questionario, cliente: str, quem_recebe: str) -> dict:
    blocos = []
    for b in q.blocos:
        ps = [p for p in q.do_momento("cliente") if p.bloco == b.id]
        if not ps:
            continue
        blocos.append({
            "id": b.id, "titulo": b.titulo, "objetivo": b.objetivo, "tempo_min": b.tempo_min,
            "perguntas": [{
                "id": p.id, "pergunta": p.pergunta, "ajuda": p.ajuda, "tipo": p.tipo, "obrigatoria": p.obrigatoria,
                "opcoes": [o.model_dump() for o in p.opcoes],
                "condicao": p.condicao.model_dump() if p.condicao else None,
            } for p in ps],
        })
    return {"formulario": FORMULARIO, "versao": q.versao, "cliente": cliente, "quem_recebe": quem_recebe,
            "chave": f"trilha-questionario:{q.versao}:{_slug(cliente)}", "arquivo": f"respostas-{_slug(cliente)}",
            "blocos": blocos}


def gerar_formulario(cliente: str = "", quem_recebe: str = "a sua assessoria") -> str:
    dados = dados_do_formulario(carregar(), cliente, quem_recebe)
    minutos = sum(b["tempo_min"] or 0 for b in dados["blocos"])
    embutido = json.dumps(dados, ensure_ascii=False).replace("</", "<\\/")
    titulo = f"Questionário de início{' — ' + cliente if cliente else ''}"
    return (_HTML.replace("__TITULO__", _escapar(titulo))
            .replace("__MINUTOS__", f"cerca de {minutos} minutos" if minutos else "alguns minutos")
            .replace("__QUEM__", _escapar(quem_recebe))
            .replace("__DADOS__", embutido))


def _escapar(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


_HTML = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITULO__</title>
<style>
:root {
  --fundo: #f7f6f2; --cartao: #ffffff; --texto: #1d1d1b; --suave: #5f5e5a; --linha: #dcdad3;
  --destaque: #1f5f4a; --destaque-texto: #ffffff; --aviso: #8a4b00; --foco: #2f7d63;
}
@media (prefers-color-scheme: dark) {
  :root { --fundo: #151514; --cartao: #1f1f1d; --texto: #ecebe6; --suave: #a8a69f; --linha: #3a3935;
          --destaque: #5fb592; --destaque-texto: #0f1a15; --aviso: #f0b162; --foco: #7fd0ad; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--fundo); color: var(--texto);
       font: 17px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
main { max-width: 720px; margin: 0 auto; padding: 24px 16px 96px; }
h1 { font-size: 1.5rem; line-height: 1.25; margin: 0 0 8px; }
h2 { font-size: 1.25rem; margin: 0 0 4px; }
p { margin: 0 0 12px; }
.suave { color: var(--suave); }
.barra { position: sticky; top: 0; background: var(--fundo); padding: 12px 0; z-index: 1; }
.progresso { height: 6px; background: var(--linha); border-radius: 3px; overflow: hidden; }
.progresso > div { height: 100%; background: var(--destaque); width: 0; transition: width .2s; }
.passo { font-size: .875rem; color: var(--suave); margin-top: 6px; }
.cartao { background: var(--cartao); border: 1px solid var(--linha); border-radius: 12px; padding: 20px 16px; margin: 16px 0; }
.cartao > h2 + p, .cartao > h2:last-child { margin-bottom: 24px; }
.cartao > h2:not(:last-child) { margin-bottom: 8px; }
.pergunta { margin: 0 0 28px; }
.pergunta label.enunciado, .pergunta legend { display: block; font-weight: 600; margin-bottom: 4px; }
.pergunta .ajuda { font-size: .9rem; color: var(--suave); margin-bottom: 8px; }
.obrig { color: var(--aviso); font-weight: 600; }
input[type=text], input[type=url], textarea {
  width: 100%; font: inherit; color: inherit; background: transparent; border: 1px solid var(--linha);
  border-radius: 8px; padding: 10px 12px; }
textarea { min-height: 96px; resize: vertical; }
fieldset { border: 0; padding: 0; margin: 0; }
.opcao { display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; }
.opcao input { margin-top: 5px; width: 18px; height: 18px; }
.naosei { display: flex; gap: 8px; align-items: center; font-size: .9rem; color: var(--suave); margin-top: 8px; }
:focus-visible { outline: 3px solid var(--foco); outline-offset: 2px; }
.acoes { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px; }
button { font: inherit; border-radius: 8px; padding: 12px 18px; cursor: pointer; border: 1px solid var(--linha);
         background: transparent; color: var(--texto); }
button.principal { background: var(--destaque); color: var(--destaque-texto); border-color: var(--destaque); font-weight: 600; }
.unidade { display: flex; gap: 8px; align-items: center; }
.unidade input { flex: 1; }
ul.faltando { padding-left: 20px; }
.ok { color: var(--destaque); font-weight: 600; }
[hidden] { display: none !important; }
</style>
</head>
<body>
<main>
  <header>
    <h1 id="titulo">__TITULO__</h1>
    <p class="suave">Responda com as suas palavras, do jeito que falaria com um cliente. Não existe resposta errada, e
      "não sei" também ajuda. Leva __MINUTOS__. O que você escrever fica salvo neste aparelho: pode parar e voltar depois.</p>
  </header>
  <div class="barra" aria-hidden="false">
    <div class="progresso" role="progressbar" aria-label="Progresso" aria-valuemin="0" aria-valuemax="100"><div id="preenchido"></div></div>
    <div class="passo" id="passo"></div>
  </div>
  <section id="conteudo" aria-live="polite"></section>
  <nav class="acoes" id="navegacao">
    <button type="button" id="voltar">Voltar</button>
    <button type="button" class="principal" id="avancar">Continuar</button>
  </nav>
  <p class="suave" style="margin-top:32px;font-size:.85rem">As respostas só saem deste aparelho quando você baixar ou
    copiar o arquivo no final e enviar para <span id="quem">__QUEM__</span>.</p>
</main>
<script id="dados" type="application/json">__DADOS__</script>
<script>
(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("dados").textContent);
  function slug(t) {
    return t.normalize("NFKD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "cliente";
  }
  try {
    var url = new URLSearchParams(location.search);
    if (!D.cliente && url.get("cliente")) {
      D.cliente = url.get("cliente").slice(0, 120);
      D.chave = "trilha-questionario:" + D.versao + ":" + slug(D.cliente);
      D.arquivo = "respostas-" + slug(D.cliente);
      document.getElementById("titulo").textContent = document.title = "Questionário de início — " + D.cliente;
    }
    if (url.get("quem")) { D.quem_recebe = url.get("quem").slice(0, 80); document.getElementById("quem").textContent = D.quem_recebe; }
  } catch (e) { /* navegador sem URLSearchParams: segue com o que veio embutido */ }
  var estado = { respostas: {}, nao_sei: [], passo: 0 };
  try {
    var salvo = JSON.parse(localStorage.getItem(D.chave) || "null");
    if (salvo && salvo.respostas) { estado = salvo; }
  } catch (e) { /* sem armazenamento: o formulário funciona, só não lembra */ }

  function salvar() {
    try { localStorage.setItem(D.chave, JSON.stringify(estado)); } catch (e) {}
  }
  function el(tag, attrs, filhos) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "texto") { n.textContent = attrs[k]; } else if (attrs[k] !== null && attrs[k] !== undefined) { n.setAttribute(k, attrs[k]); }
    });
    (filhos || []).forEach(function (f) { if (f) { n.appendChild(f); } });
    return n;
  }
  function todas() { return D.blocos.reduce(function (acc, b) { return acc.concat(b.perguntas); }, []); }
  function visivel(p) {
    if (!p.condicao) { return true; }
    var r = estado.respostas[p.condicao.pergunta];
    var lista = Array.isArray(r) ? r : (r === undefined ? [] : [r]);
    return lista.some(function (v) { return p.condicao.em.indexOf(String(v)) >= 0; });
  }
  function respondida(p) {
    if (estado.nao_sei.indexOf(p.id) >= 0) { return true; }
    var r = estado.respostas[p.id];
    if (Array.isArray(r)) { return r.length > 0; }
    return r !== undefined && String(r).trim() !== "";
  }
  function atualizarProgresso() {
    var vis = todas().filter(visivel);
    var feitas = vis.filter(respondida).length;
    var pct = vis.length ? Math.round(feitas / vis.length * 100) : 0;
    document.getElementById("preenchido").style.width = pct + "%";
    document.querySelector(".progresso").setAttribute("aria-valuenow", pct);
    var total = D.blocos.length;
    document.getElementById("passo").textContent = estado.passo < total
      ? "Parte " + (estado.passo + 1) + " de " + total + " · " + pct + "% respondido"
      : "Revisão e envio · " + pct + "% respondido";
  }
  function atualizarVisiveis() {
    var b = D.blocos[estado.passo];
    if (!b) { return; }
    b.perguntas.forEach(function (p) {
      var caixa = document.getElementById("p-" + p.id);
      if (caixa) { caixa.hidden = !visivel(p); }
    });
  }
  function definir(p, valor) {
    if (valor === "" || (Array.isArray(valor) && !valor.length)) { delete estado.respostas[p.id]; }
    else { estado.respostas[p.id] = valor; }
    salvar(); atualizarVisiveis(); atualizarProgresso();
  }
  function campo(p) {
    var id = "q-" + p.id, atual = estado.respostas[p.id];
    var ajuda = p.ajuda ? el("div", { "class": "ajuda", id: id + "-ajuda", texto: p.ajuda }) : null;
    var rotulo = [el("span", { texto: p.pergunta })];
    if (p.obrigatoria) { rotulo.push(el("span", { "class": "obrig", texto: " *" })); }
    var bloco;
    if (p.tipo === "escolha" || p.tipo === "multipla" || p.tipo === "sim_nao") {
      var opcoes = p.tipo === "sim_nao" ? [{ valor: "sim", rotulo: "Sim" }, { valor: "nao", rotulo: "Não" }] : p.opcoes;
      var multi = p.tipo === "multipla";
      bloco = el("fieldset", { "aria-describedby": ajuda ? id + "-ajuda" : null }, [el("legend", {}, rotulo), ajuda]);
      opcoes.forEach(function (o, i) {
        var marcado = multi ? (Array.isArray(atual) && atual.indexOf(o.valor) >= 0) : atual === o.valor;
        var inp = el("input", { type: multi ? "checkbox" : "radio", name: id, id: id + "-" + i, value: o.valor });
        inp.checked = marcado;
        inp.addEventListener("change", function () {
          if (multi) {
            var vals = Array.prototype.slice.call(bloco.querySelectorAll("input[name='" + id + "']:checked")).map(function (x) { return x.value; });
            definir(p, vals);
          } else { definir(p, o.valor); }
        });
        bloco.appendChild(el("div", { "class": "opcao" }, [inp, el("label", { "for": id + "-" + i, texto: o.rotulo })]));
      });
    } else {
      var longo = p.tipo === "texto_longo" || p.tipo === "lista";
      var inp = el(longo ? "textarea" : "input", {
        id: id, type: longo ? null : (p.tipo === "link" ? "url" : (p.tipo === "telefone" ? "tel" : "text")),
        inputmode: ["numero", "moeda", "porcentagem"].indexOf(p.tipo) >= 0 ? "decimal" : (p.tipo === "telefone" ? "tel" : null),
        placeholder: p.tipo === "lista" ? "Um item por linha" : (p.tipo === "telefone" ? "(11) 98765-4321" : null),
        "aria-describedby": ajuda ? id + "-ajuda" : null, autocomplete: "off"
      });
      inp.value = Array.isArray(atual) ? atual.join("\\n") : (atual || "");
      inp.addEventListener("input", function () {
        if (p.tipo === "lista") {
          definir(p, inp.value.split("\\n").map(function (x) { return x.trim(); }).filter(Boolean));
        } else { definir(p, inp.value); }
      });
      var entrada = inp;
      if (p.tipo === "moeda" || p.tipo === "porcentagem") {
        entrada = el("div", { "class": "unidade" }, p.tipo === "moeda"
          ? [el("span", { texto: "R$" }), inp] : [inp, el("span", { texto: "%" })]);
      }
      bloco = el("div", {}, [el("label", { "class": "enunciado", "for": id }, rotulo), ajuda, entrada]);
    }
    var caixa = el("div", { "class": "pergunta", id: "p-" + p.id }, [bloco]);
    if (!p.obrigatoria) {
      var ns = el("input", { type: "checkbox", id: id + "-naosei" });
      ns.checked = estado.nao_sei.indexOf(p.id) >= 0;
      ns.addEventListener("change", function () {
        estado.nao_sei = estado.nao_sei.filter(function (x) { return x !== p.id; });
        if (ns.checked) { estado.nao_sei.push(p.id); }
        salvar(); atualizarProgresso();
      });
      caixa.appendChild(el("div", { "class": "naosei" }, [ns, el("label", { "for": id + "-naosei", texto: "Não sei, prefiro falar na reunião" })]));
    }
    return caixa;
  }
  function arquivo() {
    var vis = todas().filter(visivel).map(function (p) { return p.id; });
    var respostas = {};
    Object.keys(estado.respostas).forEach(function (k) { if (vis.indexOf(k) >= 0) { respostas[k] = estado.respostas[k]; } });
    return { formulario: D.formulario, versao: D.versao, cliente: D.cliente,
             preenchido_em: new Date().toISOString().slice(0, 16),
             respostas: respostas, nao_sei: estado.nao_sei.filter(function (k) { return vis.indexOf(k) >= 0; }) };
  }
  function final() {
    var faltam = todas().filter(function (p) { return visivel(p) && p.obrigatoria && !respondida(p); });
    var caixa = el("div", { "class": "cartao" }, [el("h2", { texto: "Revisão e envio" })]);
    if (faltam.length) {
      caixa.appendChild(el("p", { texto: "Ainda faltam estas perguntas obrigatórias:" }));
      var ul = el("ul", { "class": "faltando" });
      faltam.forEach(function (p) {
        var idx = D.blocos.findIndex(function (b) { return b.perguntas.indexOf(p) >= 0; });
        var b = el("button", { type: "button", texto: p.pergunta });
        b.addEventListener("click", function () { estado.passo = idx; salvar(); renderizar(true, p.id); });
        ul.appendChild(el("li", {}, [b]));
      });
      caixa.appendChild(ul);
    } else {
      caixa.appendChild(el("p", { "class": "ok", texto: "Tudo pronto." }));
    }
    caixa.appendChild(el("p", { texto: "Baixe o arquivo de respostas e envie para " + D.quem_recebe + " (WhatsApp ou e-mail). Se baixar não funcionar no seu aparelho, copie as respostas e cole na conversa." }));
    var baixar = el("button", { type: "button", "class": "principal", texto: "Baixar respostas" });
    baixar.addEventListener("click", function () {
      var blob = new Blob([JSON.stringify(arquivo(), null, 2)], { type: "application/json" });
      var a = el("a", { href: URL.createObjectURL(blob), download: D.arquivo + "-" + new Date().toISOString().slice(0, 10) + ".json" });
      document.body.appendChild(a); a.click(); a.remove();
    });
    var copiar = el("button", { type: "button", texto: "Copiar respostas" });
    var aviso = el("p", { "class": "suave", role: "status" });
    copiar.addEventListener("click", function () {
      var texto = JSON.stringify(arquivo());
      function feito() { aviso.textContent = "Respostas copiadas. Cole na conversa com " + D.quem_recebe + "."; }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(texto).then(feito, function () { manual(texto); });
      } else { manual(texto); }
      function manual(t) {
        var area = el("textarea", { readonly: "readonly" }); area.value = t;
        caixa.appendChild(area); area.select(); aviso.textContent = "Selecione o texto acima, copie e cole na conversa.";
      }
    });
    caixa.appendChild(el("div", { "class": "acoes" }, [baixar, copiar]));
    caixa.appendChild(aviso);
    return caixa;
  }
  function renderizar(rolar, foco) {
    var c = document.getElementById("conteudo");
    c.textContent = "";
    var total = D.blocos.length;
    if (estado.passo < total) {
      var b = D.blocos[estado.passo];
      var caixa = el("div", { "class": "cartao" }, [el("h2", { texto: b.titulo }),
        b.objetivo ? el("p", { "class": "suave", texto: b.objetivo }) : null]);
      // todas as perguntas do bloco entram; as condicionais aparecem e somem sem refazer a tela (o foco não se perde)
      b.perguntas.forEach(function (p) { var q = campo(p); q.hidden = !visivel(p); caixa.appendChild(q); });
      c.appendChild(caixa);
    } else {
      c.appendChild(final());
    }
    document.getElementById("voltar").hidden = estado.passo === 0;
    document.getElementById("avancar").hidden = estado.passo >= total;
    document.getElementById("avancar").textContent = estado.passo === total - 1 ? "Revisar e enviar" : "Continuar";
    atualizarProgresso();
    if (foco) { var alvo = document.getElementById("p-" + foco); if (alvo) { alvo.scrollIntoView(); var i = alvo.querySelector("input,textarea"); if (i) { i.focus(); } } }
    else if (rolar) { window.scrollTo(0, 0); }
  }
  document.getElementById("avancar").addEventListener("click", function () { estado.passo += 1; salvar(); renderizar(true); });
  document.getElementById("voltar").addEventListener("click", function () { estado.passo = Math.max(0, estado.passo - 1); salvar(); renderizar(true); });
  renderizar(false);
})();
</script>
</body>
</html>
"""
