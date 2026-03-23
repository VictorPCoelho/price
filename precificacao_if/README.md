# precificacao_if — Engine de Precificação de Crédito

Sistema de automação de cálculo de fluxo financeiro para Instituições Financeiras,
baseado no manual de precificação (módulos 2 a 7), com seleção dinâmica de fórmulas Z/F por slot.

## Estrutura

```
precificacao_if/
├── main.py                  ← Ponto de entrada (CLI)
├── engine_core.py           ← Motor de cálculo (loop t=0..T)
├── formula_registry.py      ← Catálogo de todas as fórmulas Z/F
├── recipe.py                ← Templates de produto (receitas)
├── exporters.py             ← Exportação Excel / CSV
├── modulos/
│   ├── ativo.py             ← Módulo 3 (Z036..Z082)
│   ├── passivo.py           ← Módulo 4 (Z103..Z173)
│   ├── fluxo.py             ← Módulo 5 (Z175..F1062)
│   ├── encargos.py          ← Módulo 2 (F1070..F1211)
│   ├── performance.py       ← Módulo 6 (F1064..F1233)
│   └── metodos_iterativos.py ← Módulo 7 (Secante)
└── tests/
    └── test_cdc_pps.py      ← Testes de regressão
```

## Uso rápido

```bash
# Executa CDC PPS (parâmetros padrão)
python main.py

# Outros produtos
python main.py --receita CONSIGNADO_SAC
python main.py --receita IPCA_MAIS

# Sobrescreve parâmetros sem alterar a receita
python main.py --receita CDC_PPS --taxa 1.55 --prazo 48 --capital 200000

# Análise de sensibilidade
python main.py --stress
python main.py --comparar CDC_PPS CONSIGNADO_SAC

# Inspeciona fórmulas disponíveis
python main.py --listar
python main.py --formulas ativo JA
python main.py --catalogo
```

## Adicionando um produto novo

```python
# recipe.py — adicione uma entrada em RECEITAS
NOVO_PRODUTO = {
    "nome":      "NOVO_PRODUTO",
    "descricao": "Descrição do produto",
    "produto":   "FAMILIA",
    "params_op": dict(C=50000, T=36, tc=0, i_am=1.99, ...),
    "params_custo": dict(...),
    "params_risco": dict(FPR=75.0, K=11.0, Kp=9.75, F=10.950, FCC=20.0, ...),
    "params_margem": dict(lamb_am=0.20),
    "slots": {
        "ativo.JA":    "z036",   # ← troca aqui para mudar a fórmula
        "ativo.EBP":   "ebp_z3",
        "fluxo.MG":    "z182",
        ...
    },
}
RECEITAS["NOVO_PRODUTO"] = NOVO_PRODUTO
```

## Análise de sensibilidade via código

```python
from recipe import clonar
from engine_core import executar

# Testa impacto de trocar JA de flat para pro-rata DU/252
r1 = clonar("CDC_PPS", {"slots.ativo.JA": "z036"})  # flat (padrão)
r2 = clonar("CDC_PPS", {"slots.ativo.JA": "z16"})   # pro-rata DU/252

for r in [r1, r2]:
    res = executar(r)
    print(res["resumo"]["RSPLE %"], res["resumo"]["FLA VP (Σ) → 0"])
```

## Mapeamento Z-codes (planilha → Python)

| Coluna Excel | Z-code  | Variável      | Slot no engine     |
|--------------|---------|---------------|--------------------|
| G            | Z036    | JA            | ativo.JA → z036    |
| H            | Z043    | EJA           | calculado interno  |
| I            | F1023   | SJA           | calculado interno  |
| J            | Z061    | LCA           | calculado interno  |
| K            | Z067    | ECA           | calculado interno  |
| L            | Z063    | SCA           | calculado interno  |
| M            | Z079    | PMTA          | ativo.PMTA         |
| N            | Z082    | SDA           | ativo.SDA          |
| O            | Z103    | EBP           | passivo.EBP        |
| P            | Z109    | EEBP          | calculado interno  |
| Q            | F1037   | SEBP          | calculado interno  |
| R            | Z154    | LCP           | calculado interno  |
| S            | Z407    | ECP           | passivo.ECP → z407 |
| T            | F1042   | SCP           | calculado interno  |
| U            | Z161    | PMTP          | calculado interno  |
| V            | Z173    | SDP           | calculado interno  |
| Y            | Z175    | SP            | fluxo.SP           |
| AH           | Z182    | MG            | fluxo.MG           |
| AI           | Z196    | MC            | fluxo.MC           |
| AE/AF        | Z276/Z444 | DPE/EPE     | fluxo.DPE → ipp    |
| AC           | Z306    | PASEP+COF     | fluxo.PASEP        |
| AR           | Z355    | IR/CS         | fluxo.IR_CS        |
| AS           | F1060   | FLA           | calculado interno  |
| AT           | F1062   | FLA_VP        | calculado interno  |
"# price" 
