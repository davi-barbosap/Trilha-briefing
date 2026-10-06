# 002 — Questionário como dado e formulário próprio

**Status:** aceita (out/2026).

## Contexto

O questionário era Markdown gerado por código. O cliente respondia num documento, e o assessor copiava as respostas à mão para os arquivos YAML. Isso trazia três problemas:

- **Transcrição:** cada resposta passava por uma cópia manual, sujeita a erro e esquecimento, e a resposta original se perdia.
- **Edição:** mudar uma pergunta exigia mexer em código. Nada conferia se o campo citado ainda existia no esquema.
- **Experiência do cliente:** um documento longo, sem progresso salvo, sem saber quanto falta.

Alternativas consideradas:

| Alternativa | Por que não |
|---|---|
| Google Forms ou Typeform | As respostas ficam num serviço de terceiro (LGPD). A ligação entre coluna e campo depende do título da pergunta. A condição entre perguntas não acompanha o esquema. |
| Wizard do `briefing-trilha` (Streamlit) | Precisa de servidor e é preenchido pelo assessor, não pelo cliente. |
| Continuar em Markdown | Mantém os três problemas. |

## Decisão

1. **As perguntas são dado.** Tudo fica em `trilha_briefing/questionario/perguntas.yaml`: texto, ajuda, tipo, opções, obrigatoriedade, campo que preenche, o que alimenta e condição. O arquivo é conferido ao carregar:
   - o campo existe no esquema;
   - as opções cabem no campo;
   - a condição cita uma pergunta anterior que o cliente vê, com valores que ela tem.
2. **O formulário é um arquivo HTML só**, gerado a partir do `perguntas.yaml`:
   - não depende de servidor nem de internet;
   - salva o progresso no aparelho;
   - as respostas só saem quando o cliente baixa ou copia o arquivo e envia.

   Há duas formas de entregar:
   - **Arquivo por cliente** (`--cliente "Nome"`). Funciona bem no computador. No celular, depende do aplicativo abrir HTML no navegador: o WhatsApp no iPhone costuma mostrar só a prévia, sem rodar o formulário.
   - **Formulário publicado num endereço fixo** (gerado sem `--cliente`), com o nome no link: `?cliente=Escola%20X&quem=Davi`. Funciona em qualquer aparelho. A página só tem perguntas, e as respostas não vão para o servidor. É o caminho recomendado quando o cliente responde pelo celular.
3. **A importação preenche pouco, e só o que é seguro.** Ela preenche só campos simples (texto, número, escolha, lista) dos arquivos de uma instância só: briefing, pesquisa, plataforma e estratégia.
   - **Afirmações:** entram como `fonte: empresa`, `status: hipotese`.
   - **Campo já preenchido:** nunca é sobrescrito; volta como conflito.
   - **Validação:** cada campo é conferido na hora contra o esquema. O que não cabe volta para "levar à mão", com o motivo, sem derrubar o resto.
   - **Pasta inválida:** se a pasta inteira ficaria inválida, nada é gravado.
   - **Comentários:** os comentários dos arquivos são mantidos, porque a edição é por linha.
4. **As respostas cruas ficam guardadas** em `respostas/<data>-questionario.json` e `.md`, na pasta do cliente no Trilha-clientes, que é privado. São a fonte das afirmações com `fonte: empresa`.
5. **Fica com o assessor:** personas, ofertas, provas e tudo o que é lista de estruturas. A importação lista o que levar e para onde.

## Consequências

- Mudar o `id` de uma pergunta desfaz a ligação com respostas antigas. A importação avisa quando a versão é diferente e lista as respostas de perguntas que não existem mais. Mude o texto à vontade, mas não o `id`.
- Os testes não dependem do texto das perguntas: conferem a estrutura e o caminho pergunta → formulário → respostas → pasta.
- O comportamento do formulário no navegador foi testado à mão, no Chromium, em tela de celular. O CI testa a geração e a importação, não o navegador.
