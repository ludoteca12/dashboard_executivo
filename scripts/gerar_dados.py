"""
Gera o dataset sintético do Dashboard Executivo de Vendas.

Saída (pasta ../data, UTF-8, separador vírgula, datas ISO, decimal com ponto):
    dCliente.csv  - 100 clientes fictícios (segmento, região, país)
    dProduto.csv  - 27 produtos (3 categorias x 3 subcategorias x 3 linhas)
    fVendas.csv   - ~5.000 vendas entre 2024-01-01 e 2026-12-31

O calendário (dCalendario) não é gerado aqui: ele é construído no Power Query
a partir do intervalo de datas da fato.

Comportamentos simulados para o dashboard contar uma história:
    - sazonalidade mensal (pico no 4º trimestre, vale em jan/fev);
    - tendência anual diferente por subcategoria (nuvem cresce, consultoria cai);
    - preço ligado ao custo do produto (markup por subcategoria) + reajuste anual;
    - quantidade e desconto dependentes do segmento do cliente;
    - concentração de receita em poucos clientes (distribuição de Pareto).

Uso:
    python scripts/gerar_dados.py            # semente padrão (reprodutível)
    python scripts/gerar_dados.py --seed 7   # outra variação
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

PASTA_SAIDA = Path(__file__).resolve().parent.parent / "data"

ANOS = (2024, 2025, 2026)
PEDIDOS_POR_ANO = {2024: 1610, 2025: 1680, 2026: 1710}  # total = 5.000
REAJUSTE_ANUAL = 0.04  # reajuste de tabela de preços ao ano

# Peso relativo de cada mês (sazonalidade)
SAZONALIDADE = [0.75, 0.80, 0.95, 0.95, 1.00, 1.00, 0.90, 0.95, 1.05, 1.10, 1.20, 1.35]

# Região -> {país: nº de clientes}
CLIENTES_POR_PAIS = {
    "América Latina": {"Brasil": 12, "Chile": 14, "Colômbia": 14, "Argentina": 8, "México": 9},
    "América do Norte": {"Estados Unidos": 10, "Canadá": 13},
    "Europa": {"Espanha": 7, "Reino Unido": 6, "França": 5, "Alemanha": 2},
}

# Segmento: (probabilidade, faixa de quantidade, prob. de desconto, faixa % desconto)
SEGMENTOS = {
    "Corporativo": (0.28, (4, 14), 0.70, (0.03, 0.12)),
    "PME": (0.52, (2, 9), 0.50, (0.02, 0.08)),
    "Consumidor": (0.20, (1, 4), 0.30, (0.02, 0.06)),
}

# Categoria -> Subcategoria -> (nome base do produto, custos por linha, margem alvo, tendência a.a.)
PORTFOLIO = {
    "Hardware": {
        "Notebooks": ("Notebook", (620, 1290, 2180), 0.17, -0.06),
        "Monitores": ("Monitor", (460, 990, 1710), 0.27, 0.00),
        "Acessórios": ("Kit de Acessórios", (170, 450, 980), 0.42, 0.03),
    },
    "Software": {
        "Licenças em Nuvem": ("Licença Nuvem", (170, 720, 1670), 0.48, 0.22),
        "Suítes de Segurança": ("Suíte de Segurança", (130, 460, 1060), 0.66, 0.12),
        "Ferramentas de Analytics": ("Plataforma Analytics", (340, 990, 1900), 0.36, 0.15),
    },
    "Serviços": {
        "Implantação": ("Pacote de Implantação", (1140, 1800, 2470), 0.08, -0.04),
        "Serviços Gerenciados": ("Serviço Gerenciado", (1480, 2090, 2720), 0.04, 0.08),
        "Consultoria": ("Consultoria", (570, 1240, 1900), 0.50, -0.10),
    },
}
LINHAS = ("Essencial", "Profissional", "Premium")
PESO_LINHAS = (0.50, 0.33, 0.17)

# Peças para nomes de empresas fictícias
PREFIXOS = ["Al", "Bra", "Cor", "Del", "Ev", "Fa", "Gra", "Hel", "Ix", "Jun", "Kal", "Lu",
            "Mar", "Nor", "Or", "Pra", "Quan", "Ri", "Sol", "Tav", "Ul", "Ver", "Xa", "Zen"]
SUFIXOS = ["va", "ton", "ris", "lix", "dora", "mex", "tia", "quia", "nis", "ro", "ena", "vix"]
SETORES = ["Tecnologia", "Logística", "Varejo", "Saúde", "Engenharia", "Alimentos",
           "Energia", "Educação", "Financeira", "Telecom", "Construtora", "Agro"]


def gerar_clientes(rng: random.Random) -> list[dict]:
    nomes_usados: set[str] = set()
    clientes = []
    segmentos = list(SEGMENTOS)
    pesos_seg = [s[0] for s in SEGMENTOS.values()]
    n = 0
    for regiao, paises in CLIENTES_POR_PAIS.items():
        for pais, qtd in paises.items():
            for _ in range(qtd):
                n += 1
                while True:
                    nome = f"{rng.choice(PREFIXOS)}{rng.choice(SUFIXOS)} {rng.choice(SETORES)}"
                    if nome not in nomes_usados:
                        nomes_usados.add(nome)
                        break
                clientes.append({
                    "ID Cliente": f"CLI-{n:04d}",
                    "Cliente": nome,
                    "Segmento": rng.choices(segmentos, pesos_seg)[0],
                    "Região": regiao,
                    "País": pais,
                    # peso de compra (não exportado): poucos clientes concentram a receita
                    "_peso": rng.paretovariate(1.6),
                })
    return clientes


def gerar_produtos() -> list[dict]:
    produtos = []
    n = 0
    for categoria, subcats in PORTFOLIO.items():
        for subcat, (nome_base, custos, margem, tendencia) in subcats.items():
            for linha, custo, peso in zip(LINHAS, custos, PESO_LINHAS):
                n += 1
                produtos.append({
                    "ID Produto": f"PRD-{n:03d}",
                    "Produto": f"{nome_base} {linha}",
                    "Categoria": categoria,
                    "Subcategoria": subcat,
                    "Custo Padrão": f"{custo:.2f}",
                    "_preco_lista": custo / (1 - margem),
                    "_tendencia": tendencia,
                    "_peso_linha": peso,
                })
    return produtos


def gerar_vendas(rng: random.Random, clientes: list[dict], produtos: list[dict]) -> list[dict]:
    pesos_clientes = [c["_peso"] for c in clientes]
    linhas_brutas = []
    for ano in ANOS:
        anos_decorridos = ano - ANOS[0]
        # peso do produto no ano = peso da linha x tendência acumulada da subcategoria
        pesos_produtos = [p["_peso_linha"] * (1 + p["_tendencia"]) ** anos_decorridos for p in produtos]
        pedidos_mes = _distribuir(PEDIDOS_POR_ANO[ano], SAZONALIDADE)
        for mes, qtd_pedidos in enumerate(pedidos_mes, start=1):
            inicio = date(ano, mes, 1)
            dias_no_mes = ((inicio.replace(month=mes % 12 + 1, day=1) if mes < 12
                            else date(ano + 1, 1, 1)) - inicio).days
            for _ in range(qtd_pedidos):
                cliente = rng.choices(clientes, pesos_clientes)[0]
                produto = rng.choices(produtos, pesos_produtos)[0]
                _, faixa_qtd, prob_desc, faixa_desc = SEGMENTOS[cliente["Segmento"]]
                quantidade = rng.randint(*faixa_qtd)
                preco = produto["_preco_lista"] * (1 + REAJUSTE_ANUAL) ** anos_decorridos
                preco = round(preco * rng.uniform(0.97, 1.03), 2)
                desconto = 0.0
                if rng.random() < prob_desc:
                    desconto = round(quantidade * preco * rng.uniform(*faixa_desc), 2)
                linhas_brutas.append({
                    "Data Pedido": inicio + timedelta(days=rng.randrange(dias_no_mes)),
                    "ID Cliente": cliente["ID Cliente"],
                    "ID Produto": produto["ID Produto"],
                    "Quantidade": quantidade,
                    "Preço Unitário": f"{preco:.2f}",
                    "Valor Desconto": f"{desconto:.2f}",
                })
    linhas_brutas.sort(key=lambda r: r["Data Pedido"])
    vendas = []
    for i, r in enumerate(linhas_brutas, start=1):
        vendas.append({"ID Venda": f"VND-{i:05d}", **r, "Data Pedido": r["Data Pedido"].isoformat()})
    return vendas


def _distribuir(total: int, pesos: list[float]) -> list[int]:
    """Distribui um inteiro proporcionalmente aos pesos, preservando a soma."""
    soma = sum(pesos)
    brutos = [total * p / soma for p in pesos]
    inteiros = [int(b) for b in brutos]
    restos = sorted(range(len(pesos)), key=lambda i: brutos[i] - inteiros[i], reverse=True)
    for i in restos[: total - sum(inteiros)]:
        inteiros[i] += 1
    return inteiros


def salvar_csv(caminho: Path, linhas: list[dict]) -> None:
    colunas = [c for c in linhas[0] if not c.startswith("_")]
    with caminho.open("w", newline="", encoding="utf-8") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--seed", type=int, default=42, help="semente aleatória (padrão: 42)")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    clientes = gerar_clientes(rng)
    produtos = gerar_produtos()
    vendas = gerar_vendas(rng, clientes, produtos)

    PASTA_SAIDA.mkdir(exist_ok=True)
    salvar_csv(PASTA_SAIDA / "dCliente.csv", clientes)
    salvar_csv(PASTA_SAIDA / "dProduto.csv", produtos)
    salvar_csv(PASTA_SAIDA / "fVendas.csv", vendas)
    print(f"{len(clientes)} clientes, {len(produtos)} produtos, {len(vendas)} vendas -> {PASTA_SAIDA}")


if __name__ == "__main__":
    main()
