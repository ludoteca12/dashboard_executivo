# CLAUDE.md: Dashboard Executivo de Vendas

Projeto de portfólio Power BI (Workana) em formato PBIP: modelo em TMDL, relatório em PBIR. Idioma: PT-BR em tudo (modelo, medidas, visuais, commits).

## Convenções
- **Tabelas:** prefixo `f` para fatos (`fVendas`) e `d` para dimensões (`dCliente`, `dProduto`, `dCalendario`). Medidas ficam em `_Medidas`, nas pastas Receita / Pedidos / Clientes / Custo e Margem / Auxiliares.
- **Medidas:** toda medida tem descrição (`///` no TMDL). Formatos: moeda `\R\$ #,0`, percentual `0.0%`, contagem `#,0`.
- **Fonte de dados:** CSVs em `data/`, lidos pela função `fnLerCsv` a partir do parâmetro `PastaDados`. Os dados são sintéticos, gerados por `scripts/gerar_dados.py` (semente 42).

## Cuidados ao editar os arquivos à mão
- Feche o Power BI Desktop **sem salvar** antes de reabrir arquivos editados fora dele. Se salvar, o Desktop sobrescreve as edições.
- Parâmetro de campo: não use `SELECTEDVALUE('Seletor de Métrica'[Métrica])`, porque essa coluna tem chave composta com `[Métrica Campos]`. Leia pela coluna `[Métrica Ordem]`.
- No PBIR, traduza apenas literais de texto (títulos, rótulos). Valores fixos como `visualLink.type = 'Back'` precisam continuar em inglês.

## Validação
`dashboard_executivo.SemanticModel/DAXQueries/Query 1.dax` tem as consultas de conferência. Valores esperados com a semente 42:

| Ano | Receita | Pedidos | Crescimento |
|---|---|---|---|
| 2024 | R$ 12,45 mi | 1.610 | — |
| 2025 | R$ 13,16 mi | 1.680 | +5,7% |
| 2026 | R$ 13,87 mi | 1.710 | +5,5% |

## Git
O usuário faz os commits manualmente; o Claude só sugere a mensagem.
