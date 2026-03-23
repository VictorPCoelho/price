"""
main.py
═══════
Ponto de entrada do sistema de precificação.

Uso básico:
    python main.py                           # roda CDC_PPS com defaults
    python main.py --receita CONSIGNADO_SAC  # outro produto
    python main.py --receita CDC_PPS --taxa 1.55 --prazo 48

Sensibilidade (testa múltiplas variações):
    python main.py --stress                  # stress-test de taxa ativa
    python main.py --comparar CDC_PPS CONSIGNADO_SAC

Listar receitas e fórmulas disponíveis:
    python main.py --listar
    python main.py --formulas ativo JA       # fórmulas do slot JA no módulo ativo
"""
import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from recipe           import RECEITAS, carregar, clonar, listar
from engine_core      import executar
from exporters        import para_excel, para_csv
from formula_registry import listar_slot, modulos_disponiveis, catalogo_resumido


def _banner(titulo: str):
    print("\n" + "═"*60)
    print(f"  {titulo}")
    print("═"*60)


def _imprimir_resumo(res: dict):
    """Imprime resumo formatado no terminal."""
    r = res["resumo"]
    _banner(f"{r['receita']}  —  {r['produto']}")
    print(f"  Capital:       R$ {r['Capital (C)']:>14,.2f}")
    print(f"  Prazo:         {r['Prazo (T)']} períodos")
    print(f"  Taxa ativa:    {r['Taxa ativa % a.m.']}% a.m.")
    print(f"  CDI:           {r['CDI % a.m.']}% a.m.")
    print(f"  λ Margem:      {r['λ Margem % a.m.']}% a.m.  /  {r['λ Margem % a.a.']}% a.a.")
    if r.get("PMTA Price"):
        print(f"  PMTA Price:    R$ {r['PMTA Price']:>12,.4f}")
    print(f"  SDA final:     R$ {r['SDA final']:>12,.2f}  (deve ser ≈0)")
    print()
    print(f"  Total PMTA:    R$ {r['Total PMTA']:>12,.2f}")
    print(f"  Total JA:      R$ {r['Total JA']:>12,.2f}")
    print(f"  Total EBP:     R$ {r['Total EBP (CDI)']:>12,.2f}")
    print(f"  Total Spread:  R$ {r['Total SP']:>12,.2f}")
    print(f"  Total MG:      R$ {r['Total MG']:>12,.2f}")
    print(f"  Total IPP:     R$ {r['Total IPP Fase1']:>12,.2f}")
    print(f"  Total EPE:     R$ {r['Total EPE']:>12,.2f}")
    print(f"  Total Trib.:   R$ {(r.get('Total PASEP+COF',0) + r.get('Total IR/CS',0)):>12,.2f}")
    print(f"  FLA VP (Σ):    {r['FLA VP (Σ) → 0']:>14.4f}  ← deve → 0")
    print()
    print(f"  MG % a.a.:     {r['MG % a.a.']:>8.4f}%")
    print(f"  RSPLE:         {r['RSPLE %']:>8.4f}%")
    print(f"  RAR_G:         {r['RAR_G % (gestão, F1183)']:>8.4f}%")
    tir = r.get('TIR % a.a.')
    tpp = r.get('Resultado PPS % a.m.')
    if tir: print(f"  TIR:           {tir:>8.4f}% a.a.")
    if tpp: print(f"  Resultado PPS: {tpp:>8.4f}% a.m.")
    print(f"  Duration:      {r['Duration (meses)']:>8.2f} meses")
    print()
    print(f"  Fórmulas ativas:")
    print(f"    JA={r.get('fórmula JA','—')}  EBP={r.get('fórmula EBP','—')}  "
          f"PMTA={r.get('fórmula PMTA','—')}  MG={r.get('fórmula MG','—')}")
    print()


def _stress_taxa(receita_base: str, taxas: list[float]) -> None:
    """Análise de sensibilidade: varia a taxa ativa e compara RSPLE/RAR_G/FLA_VP."""
    _banner(f"STRESS — Taxa ativa  |  base: {receita_base}")
    print(f"  {'Taxa a.m.':>10}  {'RSPLE%':>10}  {'RAR_G%':>10}  {'FLA_VP':>12}  {'SDA final':>12}")
    print("  " + "─"*58)
    for taxa in taxas:
        rc = clonar(receita_base, {"params_op.i_am": taxa,
                                    "params_op.PMTA_fixo": None})
        res = executar(rc)
        r   = res["resumo"]
        print(f"  {taxa:>10.4f}%  {r['RSPLE %']:>10.4f}  "
              f"{r['RAR_G % (gestão, F1183)']:>10.4f}  "
              f"{r['FLA VP (Σ) → 0']:>12.4f}  {r['SDA final']:>12.2f}")
    print()


def _comparar(nomes: list[str]) -> None:
    """Compara múltiplas receitas lado a lado."""
    resultados = [(n, executar(carregar(n))["resumo"]) for n in nomes]
    _banner("COMPARAÇÃO DE RECEITAS")
    campos = ["Taxa ativa % a.m.", "CDI % a.m.", "λ Margem % a.m.",
              "Total SP", "Total MG", "RSPLE %", "RAR_G % (gestão, F1183)",
              "TIR % a.a.", "Resultado PPS % a.m.", "FLA VP (Σ) → 0"]
    col_w = 18
    print(f"  {'':30}", end="")
    for n, _ in resultados:
        print(f"  {n:>{col_w}}", end="")
    print()
    print("  " + "─"*(30 + (col_w+2)*len(resultados)))
    for campo in campos:
        print(f"  {campo:<30}", end="")
        for _, r in resultados:
            v = r.get(campo)
            if v is None:
                print(f"  {'—':>{col_w}}", end="")
            elif isinstance(v, float):
                print(f"  {v:>{col_w}.4f}", end="")
            else:
                print(f"  {str(v):>{col_w}}", end="")
        print()
    print()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Sistema de precificação de crédito — IF"
    )
    parser.add_argument("--receita",   default="CDC_PPS",
                        help="Nome da receita (padrão: CDC_PPS)")
    parser.add_argument("--taxa",      type=float, default=None,
                        help="Sobrescreve taxa ativa % a.m.")
    parser.add_argument("--prazo",     type=int,   default=None,
                        help="Sobrescreve prazo (períodos)")
    parser.add_argument("--capital",   type=float, default=None,
                        help="Sobrescreve capital financiado")
    parser.add_argument("--margem",    type=float, default=None,
                        help="Sobrescreve λ margem % a.m.")
    parser.add_argument("--cdi",       type=float, default=None,
                        help="Sobrescreve CDI % a.m.")
    parser.add_argument("--saida",     default=None,
                        help="Caminho do arquivo Excel de saída")
    parser.add_argument("--csv",       action="store_true",
                        help="Exporta CSV além do Excel")
    parser.add_argument("--listar",    action="store_true",
                        help="Lista receitas disponíveis e sai")
    parser.add_argument("--formulas",  nargs=2, metavar=("MODULO","SLOT"),
                        help="Lista fórmulas de um slot: --formulas ativo JA")
    parser.add_argument("--catalogo",  action="store_true",
                        help="Mostra catálogo resumido de todos os Z/F")
    parser.add_argument("--stress",    action="store_true",
                        help="Stress-test de taxa ativa (0.5% a 3.0%)")
    parser.add_argument("--comparar",  nargs="+",
                        help="Compara múltiplas receitas: --comparar CDC_PPS CONSIGNADO_SAC")

    args = parser.parse_args()

    if args.listar:
        listar()
        return

    if args.formulas:
        listar_slot(args.formulas[0], args.formulas[1])
        return

    if args.catalogo:
        catalogo_resumido()
        return

    if args.comparar:
        _comparar(args.comparar)
        return

    if args.stress:
        taxas = [round(t*0.1, 1) for t in range(5, 31)]  # 0.5% a 3.0%
        _stress_taxa(args.receita, taxas)
        return

    # ── Execução principal ────────────────────────────────────────────────────
    alteracoes = {}
    if args.taxa:    alteracoes["params_op.i_am"]       = args.taxa
    if args.prazo:   alteracoes["params_op.T"]           = args.prazo
    if args.capital: alteracoes["params_op.C"]           = args.capital
    if args.margem:  alteracoes["params_margem.lamb_am"] = args.margem
    if args.cdi:     alteracoes["params_op.cdi_am"]      = args.cdi
    if alteracoes:
        alteracoes["params_op.PMTA_fixo"] = None  # reconstrói Price se mudar parâmetros

    if alteracoes:
        receita = clonar(args.receita, alteracoes)
    else:
        receita = carregar(args.receita)

    resultado = executar(receita)
    _imprimir_resumo(resultado)

    # ── Exporta ───────────────────────────────────────────────────────────────
    saida = args.saida or f"/mnt/user-data/outputs/Precificacao_{receita['nome']}.xlsx"
    os.makedirs(os.path.dirname(saida), exist_ok=True)
    para_excel(resultado, saida)
    if args.csv:
        para_csv(resultado, saida.replace(".xlsx", ".csv"))


if __name__ == "__main__":
    main()
