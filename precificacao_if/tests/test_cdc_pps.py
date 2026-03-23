"""tests/test_cdc_pps.py — Validação do engine contra valores da planilha."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from recipe import carregar, clonar
from engine_core import executar

def checa(nome, obtido, esperado, tol=0.01):
    ok = abs(obtido - esperado) <= tol
    print(f"  {'✓' if ok else '✗'}  {nome:<40} obtido={obtido:.4f}  esp={esperado:.4f}")
    return ok

def test_planilha():
    print("\n  TEST 1 — CDC PPS (valores planilha real)\n")
    r = executar(carregar("CDC_PPS"))
    rs = r["resumo"]; df = r["fluxo"]
    return all([
        checa("JA t=1 (2288)",           df.loc[df.t==1,"JA"].values[0],        2288.00, 1.0),
        checa("EBP t=1 DU/252",          df.loc[df.t==1,"EBP"].values[0],        143.29, 0.5),
        checa("SP t=1",                  df.loc[df.t==1,"SP"].values[0],         2144.71, 1.0),
        checa("SDA final ≈ 0",           abs(rs["SDA final"]),                      0.0, 50.0),
        checa("Total JA ≈ 53932",        rs["Total JA"],                        53932.0, 50.0),
        checa("RSPLE ≈ 7.85%",           rs["RSPLE %"],                           7.852, 0.1),
        checa("RAR_G ≈ 8.86%",           rs["RAR_G % (gestão, F1183)"],           8.859, 0.1),
    ])

def test_sensibilidade():
    print("\n  TEST 2 — FLA VP monotônico crescente com taxa ativa\n")
    prev, ok = -999999, True
    for taxa in [1.2, 1.4, 1.6, 1.8, 2.0]:
        rc = clonar("CDC_PPS", {"params_op.i_am": taxa, "params_op.PMTA_fixo": None})
        fla = executar(rc)["resumo"]["FLA VP (Σ) → 0"]
        ok_ = fla > prev
        print(f"  {'✓' if ok_ else '✗'}  taxa={taxa:.1f}%  FLA_VP={fla:>12.2f}")
        ok = ok and ok_; prev = fla
    return ok

def test_clone():
    print("\n  TEST 3 — Clone altera EBP ao trocar ebp_z3 → ebp_z4\n")
    b = executar(carregar("CDC_PPS"))["resumo"]["Total EBP (CDI)"]
    a = executar(clonar("CDC_PPS",{"slots.passivo.EBP":"ebp_z2","params_op.cdi_am":1.50}))["resumo"]["Total EBP (CDI)"]
    ok = abs(b-a) > 0.01
    print(f"  {'✓' if ok else '✗'}  ebp_z3={b:.2f}  ebp_z4={a:.2f}  Δ={abs(b-a):.4f}")
    return ok

def test_consignado():
    print("\n  TEST 4 — Consignado SAC indicadores\n")
    rs = executar(carregar("CONSIGNADO_SAC"))["resumo"]
    ok = rs["MG % a.m."] > 0 and rs["RSPLE %"] > 0 and abs(rs["SDA final"]) < 5.0
    print(f"  {'✓' if ok else '✗'}  MG={rs['MG % a.m.']}%  RSPLE={rs['RSPLE %']}%  SDA_final={rs['SDA final']:.2f}")
    return ok

if __name__ == "__main__":
    print("═"*58 + "\n  SUITE DE TESTES — precificacao_if\n" + "═"*58)
    results = [test_planilha(), test_sensibilidade(), test_clone(), test_consignado()]
    print(f"\n{'═'*58}\n  {sum(results)}/4 suites passaram\n{'═'*58}")
    sys.exit(0 if all(results) else 1)
