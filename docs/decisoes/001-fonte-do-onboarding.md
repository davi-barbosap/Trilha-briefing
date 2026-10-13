# 001 — O Trilha-briefing é a fonte do onboarding de estratégia

**Status:** aceita (out/2026). O Trilha-ads registrou a mesma decisão na ADR-005 dele.

## Contexto

O Trilha-ads documentava o wizard do `briefing-trilha` (Streamlit) como a ferramenta de onboarding: ele produziria `perfil.yaml`, `marca.yaml` e `ofertas/*.yaml`.

O Trilha-briefing passou a produzir `marca.yaml`, `ofertas/*.yaml` e a parte econômica do `perfil.yaml`, a partir de uma pesquisa e de um plano que o wizard não cobre: escuta, persona negativa, concorrência, marca, provas, hipóteses e medição.

Duas ferramentas gerando os mesmos arquivos são duas fontes de verdade.

## Decisão

1. **Marca, ofertas e economia:** o Trilha-briefing é a fonte de `marca.yaml`, `ofertas/*.yaml` e do bloco `economia`/`verba`/`metrica_principal` do perfil.
2. **Operação:** o que só existe depois do acesso às contas continua sendo completado no Trilha-ads: `plataformas`, `crm` (funis, mapa de eventos, campos), `conversao`, `freio`, `operacao`.
3. **O wizard do `briefing-trilha`:**
   - segue útil para o que ele faz bem: os fluxos do Kommo (`build_kommo_json.py`), os salesbots e a publicação no ClickUp;
   - não deve gerar `marca.yaml` nem `ofertas/` para clientes que passam por aqui;
   - se isso não for aceitável para quem mantém o wizard, o caminho é ele ler os arquivos exportados daqui, e não manter uma segunda versão.
4. **Contrato de dados, não de código:** a exportação é validada contra os esquemas reais em `tests/test_contrato.py`.

## Consequências

- O ADR-005 do Trilha-ads aponta este repositório como fonte de marca, ofertas e economia.
- Arquivos exportados trazem no topo o aviso "edite lá, não aqui". Edição direta no Trilha-ads se perde na próxima exportação.
