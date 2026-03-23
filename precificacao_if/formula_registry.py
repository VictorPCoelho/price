"""
formula_registry.py
═══════════════════
Catálogo central de TODAS as fórmulas Z/F organizadas por slot (variável do fluxo).

Estrutura de cada entrada:
  REGISTRY[modulo][slot][codigo] = {
      "fn":        função Python,
      "descricao": texto do manual,
      "params":    parâmetros que o operador precisa fornecer,
      "base":      base de tempo ("DU252" | "DC360" | "mensal" | "flat" | "—"),
      "quando":    "sempre" | "amortizacao" | "t0" | "tT" | "carencia",
  }

Uso:
    from formula_registry import REGISTRY, get_fn, listar_slot, slots_de

    fn = get_fn("ativo", "JA", "z16")
    listar_slot("ativo", "JA")
    slots_de("fluxo")
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "modulos"))

from ativo             import ModuloAtivo       as A
from passivo           import ModuloPassivo     as P
from fluxo             import ModuloFluxo       as F
from encargos          import ModuloEncargos    as E
from performance       import ModuloPerformance as Perf
from metodos_iterativos import ModuloMetodosIterativos as Solv

# ─────────────────────────────────────────────────────────────────────────────
REGISTRY = {

  # ═══════════════════════════════════════════════════════════════════════════
  # MÓDULO 2 — ENCARGOS (transformações de taxa)
  # ═══════════════════════════════════════════════════════════════════════════
  "encargos": {
    "taxa_ativo": {
      "f1070": dict(fn=E.taxa_padrao_f1070,
                    descricao="Taxa padrão — usa TX_k sem transformação",
                    params=["TX_k"], base="—"),
      "f1071": dict(fn=E.taxa_efetiva_f1071,
                    descricao="Taxa efetiva — converte TN_k por período (ND/NC)",
                    params=["TN_k","n","ND","NC"], base="ND/NC"),
      "f1072": dict(fn=E.taxas_equivalentes_f1072,
                    descricao="Taxas equivalentes — converte TC para base ND/NC",
                    params=["TC","ND","NC"], base="ND/NC"),
      "f1073": dict(fn=E.taxas_proporcionais_f1073,
                    descricao="Taxas proporcionais — TC_b_k / (b/g)",
                    params=["TC_b_k","b","g"], base="—"),
      "f1076": dict(fn=E.taxa_composta_ativo_f1076,
                    descricao="Taxa composta = indexador + sobretaxa + spread",
                    params=["ind_t_k","i_q","i_k"], base="—"),
    },
    "taxa_passivo": {
      "f1077": dict(fn=E.taxa_padrao_passivo_f1077,
                    descricao="Taxa padrão passivo",
                    params=["TX_q"], base="—"),
      "f1079": dict(fn=E.taxas_equivalentes_passivo_f1079,
                    descricao="Taxas equivalentes passivo",
                    params=["TC","ND","NC"], base="ND/NC"),
      "f1081": dict(fn=E.taxa_composta_passivo_f1081,
                    descricao="Taxa composta passivo = indexador + spread",
                    params=["ind_t_q","i_q"], base="—"),
      "f1102": dict(fn=E.taxa_da_poupanca_f1102,
                    descricao="Taxa da poupança (70% SELIC se CVCC≤8,5%)",
                    params=["TX_q","CVCC_t"], base="—"),
    },
    "indexador_ativo": {
      "f1082": dict(fn=E.indexador_padrao_ativo_f1082,
                    descricao="Indexador padrão (passa direto)",
                    params=["INDEX_t_k"], base="—"),
      "f1083": dict(fn=E.taxas_a_termo_ativo_f1083,
                    descricao="Taxa a termo DU/252 (CDI, SELIC, IPCA futuro)",
                    params=["INDEX_1_k","INDEX_t_k","INDEX_t_1_k","du_t","du_t_1"],
                    base="DU252"),
      "f1090": dict(fn=E.taxas_a_termo_ao_mes_ativo_f1090,
                    descricao="Taxa a termo mensal DU/252",
                    params=["INDEX_1_k","INDEX_t_k","INDEX_t_1_k","du_1","du_t","du_t_1"],
                    base="DU252"),
    },
    "indexador_passivo": {
      "f1087": dict(fn=E.indexador_padrao_passivo_f1087,
                    descricao="Indexador padrão passivo",
                    params=["INDEX_t_q"], base="—"),
      "f1088": dict(fn=E.taxas_a_termo_passivo_f1088,
                    descricao="Taxa a termo DU/252 passivo",
                    params=["INDEX_1_q","INDEX_t_q","INDEX_t_1_q","du_t","du_t_1"],
                    base="DU252"),
      "f1091": dict(fn=E.taxas_a_termo_ao_mes_passivo_f1091,
                    descricao="Taxa a termo mensal DU/252 passivo",
                    params=["INDEX_1_q","INDEX_t_q","INDEX_t_1_q","du_1","du_t","du_t_1"],
                    base="DU252"),
    },
  },

  # ═══════════════════════════════════════════════════════════════════════════
  # MÓDULO 3 — ATIVO
  # ═══════════════════════════════════════════════════════════════════════════
  "ativo": {
    "EBA": {   # Débito de Encargos Básicos
      "z1":  dict(fn=A.eba_z1,
                  descricao="EBA flat sobre SDA (indexador proporcional)",
                  params=["SDA_t_1_k","ind_t_k"], base="flat", quando="amortizacao"),
      "z2":  dict(fn=A.eba_z2,
                  descricao="EBA mensal equivalente — (1+ind)^(1/n)−1",
                  params=["SDA_t_1_k","ind_t_k","n"], base="mensal", quando="amortizacao"),
      "z3":  dict(fn=A.eba_z3,
                  descricao="EBA pro-rata DU/252 (CDI, SELIC)",
                  params=["SDA_t_1_k","ind_t_k","DU_t"], base="DU252", quando="sempre"),
    },
    "JA": {    # Juros do Ativo
      "z15": dict(fn=A.ja_z15,
                  descricao="JA mensal equivalente Price — (1+i)^(1/n)−1",
                  params=["SDA_t_1","i","n"], base="mensal", quando="amortizacao"),
      "z16": dict(fn=A.ja_z16,
                  descricao="JA pro-rata DU/252",
                  params=["SDA_t_1","i","DU_t"], base="DU252", quando="sempre"),
      "z17": dict(fn=A.ja_z17,
                  descricao="JA pro-rata DC/360",
                  params=["SDA_t_1","i","DC_t"], base="DC360", quando="sempre"),
    },
    "PMTA": {  # Prestação do Ativo
      "z30": dict(fn=A.pmta_z30,
                  descricao="Bullet — paga SDA+EBA+JA somente em T",
                  params=["SDA_t_1","EBA_t","JA_t"], base="—", quando="tT"),
      "z31": dict(fn=A.pmta_z31,
                  descricao="Periódica de z em z períodos",
                  params=["SDA_t_1","EBA_t","JA_t","z"], base="—", quando="periodica"),
      "z32": dict(fn=A.pmta_z32,
                  descricao="SAC — amortização constante C/n + encargos",
                  params=["SDA_0","EBA_t","JA_t","n"], base="—", quando="amortizacao"),
    },
    "SDA": {   # Saldo Devedor do Ativo
      "z45": dict(fn=A.sda_z45,
                  descricao="SDA = SDA_{t-1} + EBA + JA − PMTA",
                  params=["SDA_t_1","EBA_t","JA_t","PMTA_t"], base="—"),
      "z46": dict(fn=A.sda_z46,
                  descricao="SDA sem JA separado (juros já na PMTA)",
                  params=["SDA_t_1","EBA_t","PMTA_t"], base="—"),
    },
    "VP_ativo": {   # Valor presente — ativo
      "f1026": dict(fn=A.vp_pmta_f1026,  descricao="VP da PMTA",   params=["PMTA_t","CVSC_t","DU_t"], base="DU252"),
      "f1027": dict(fn=A.vp_eba_f1027,   descricao="VP do EBA",    params=["EBA_t","CVSC_t","DU_t"],  base="DU252"),
      "f1030": dict(fn=A.vp_ja_f1030,    descricao="VP dos Juros", params=["JA_t","CVSC_t","DU_t"],   base="DU252"),
      "f1031": dict(fn=A.vp_sda_f1031,   descricao="VP do SDA",    params=["SDA_t","CVSC_t","DU_t"],  base="DU252"),
      "f1033": dict(fn=A.vp_tac_f1033,   descricao="VP da Tarifa", params=["TAC_t","CVSC_t","DU_t"],  base="DU252"),
    },
  },

  # ═══════════════════════════════════════════════════════════════════════════
  # MÓDULO 4 — PASSIVO
  # ═══════════════════════════════════════════════════════════════════════════
  "passivo": {
    "EBP": {   # Encargos Básicos do Passivo
      "ebp_z1": dict(fn=P.ebp_z1,
                     descricao="EBP flat sobre SDP",
                     params=["SDP_t_1_q","ind_t_q"], base="flat"),
      "ebp_z2": dict(fn=P.ebp_z2,
                     descricao="EBP mensal equivalente",
                     params=["SDP_t_1_q","ind_t_q","n"], base="mensal"),
      "ebp_z3": dict(fn=P.ebp_z3,
                     descricao="EBP pro-rata DU/252 (CDI — mais usado)",
                     params=["SDP_t_1_q","ind_t_q","DU_t"], base="DU252"),
      "ebp_z4": dict(fn=P.ebp_z4,
                     descricao="EBP pro-rata DC/360 (internacional)",
                     params=["SDP_t_1_q","ind_t_q","DC_t"], base="DC360"),
    },
    "JP": {    # Juros do Passivo
      "jp_z24": dict(fn=P.jp_z24,
                     descricao="JP mensal equivalente",
                     params=["SDP_t_1_q","EBP_t_q","i_q","n"], base="mensal"),
      "jp_z25": dict(fn=P.jp_z25,
                     descricao="JP pro-rata DU/252",
                     params=["SDP_t_1_q","EBP_t_q","i_q","DU_t"], base="DU252"),
      "jp_z26": dict(fn=P.jp_z26,
                     descricao="JP pro-rata DC/360",
                     params=["SDP_t_1_q","EBP_t_q","i_q","DC_t"], base="DC360"),
    },
    "ECP": {   # Exigibilidade de Capital Passivo
      "ecp_z65": dict(fn=P.ecp_z65,
                      descricao="SAC do passivo — ECP = SCP_{t-1}/n_restante",
                      params=["SCP_t_1_q","z_c"], base="—"),
      "ecp_z67": dict(fn=P.ecp_z67,
                      descricao="Price — ECP = PMTP − EJP − EJPC",
                      params=["PMTP_t_q","EJP_t_q","EJPC_t_q"], base="—"),
      "ecp_z68": dict(fn=P.ecp_z68,
                      descricao="Bullet — ECP total no vencimento T",
                      params=["SCP_t_1_q"], base="—", quando="tT"),
      "z407":    dict(fn=lambda PMTA_t, EJA_t, **_: PMTA_t - EJA_t,
                      descricao="z407 — funding matched (= PMTA − EJA do ativo)",
                      params=["PMTA_t","EJA_t"], base="—"),
    },
    "SDP": {   # Saldo Devedor Passivo
      "sdp_z80": dict(fn=P.sdp_z80,
                      descricao="SDP convencional — soma todos componentes",
                      params=["LCP_t_q","SDP_t_1_q","EBP_t_q","EBPC_t_q",
                              "JP_t_q","JPC_t_q","PMTP_t_q"], base="—"),
      "sdp_z81": dict(fn=P.sdp_z81,
                      descricao="SDP por soma de saldos (SCP+SJP+SJPC+SEBP+SEBPC)",
                      params=["LCP_t_q","SCP_t_q","SJP_t_q","SJPC_t_q",
                              "SEBP_t_q","SEBPC_t_q"], base="—"),
    },
  },

  # ═══════════════════════════════════════════════════════════════════════════
  # MÓDULO 5 — FLUXO FINANCEIRO
  # ═══════════════════════════════════════════════════════════════════════════
  "fluxo": {
    "SP": {    # Spread
      "z175": dict(fn=F.sp_z175,
                   descricao="SP = PMTA − PMTP (simples)",
                   params=["PMTA_t","PMTP_t"]),
      "z176": dict(fn=F.sp_z176,
                   descricao="SP = PMTA − PMTP + EEQL (com equalização)",
                   params=["PMTA_t","PMTP_t","EEQL_t"]),
      "z177": dict(fn=F.sp_z177,
                   descricao="SP = Σ PMTA_k − Σ PMTP_q (multi-ativo/passivo)",
                   params=["soma_PMTA_k","soma_PMTP_q"]),
      "z179": dict(fn=F.sp_z179,
                   descricao="SP = Σ PMTA_k − Σ PMTRP_q (ref. passivo)",
                   params=["soma_PMTA_k","soma_PMTRP_q"]),
    },
    "MG": {    # Margem de Ganho
      "z180": dict(fn=F.mg_z180,
                   descricao="MG DU/252 sobre base",
                   params=["base","lamb","DU_t"], base="DU252"),
      "z181": dict(fn=F.mg_z181,
                   descricao="MG DC/360 sobre base",
                   params=["base","lamb","DC_t"], base="DC360"),
      "z182": dict(fn=F.mg_z182,
                   descricao="MG mensal 1/n sobre soma da base (mais usado)",
                   params=["soma_base","lamb","n"], base="mensal"),
      "z393": dict(fn=F.mg_z393,
                   descricao="MG DU/252 sobre (SDA_{t-1}+JA) — base Price",
                   params=["SDA_t_1","JA_t","lamb","DU_t"], base="DU252"),
      "z441": dict(fn=F.mg_z441,
                   descricao="MG fixo mensal 1/12",
                   params=["base","lamb"], base="fixo_mensal"),
    },
    "MGA": {   # Margem de Ganho (sem receitas adicionais)
      "z601": dict(fn=F.mga_z601,
                   descricao="MGA DU/252",
                   params=["base","phi","DU_t"], base="DU252"),
      "z619": dict(fn=F.mga_z619,
                   descricao="MGA linear DC/360",
                   params=["base","phi","DC_t"], base="DC360_linear"),
    },
    "MC": {    # Margem de Contribuição
      "z188": dict(fn=F.mc_z188,
                   descricao="MC DU/252",
                   params=["base","theta","DU_t"], base="DU252"),
      "z189": dict(fn=F.mc_z189,
                   descricao="MC DC/360",
                   params=["base","theta","DC_t"], base="DC360"),
      "z196": dict(fn=F.mc_z196,
                   descricao="MC = SP − PASEP − COFINS − CP − EPE",
                   params=["SP_t","PASEP_t","COFINS_t","CP_t","EPE_t"]),
      "z392": dict(fn=F.mc_z392,
                   descricao="MC DU/252 sobre (SDA+JA) — Price",
                   params=["SDA_t_1","JA_t","theta","DU_t"], base="DU252"),
    },
    "DPE": {   # Despesa de Perda Esperada
      "z276": dict(fn=F.dpe_z276,
                   descricao="DPE mensal: base × RBA × r × (1/n)",
                   params=["base","RBA","r","n"], base="mensal"),
      "z277": dict(fn=F.dpe_z277,
                   descricao="DPE pro-rata DU/252",
                   params=["base","RBA","r","DU_t"], base="DU252"),
      "z278": dict(fn=F.dpe_z278,
                   descricao="DPE pro-rata DC/365",
                   params=["base","RBA","r","DC_t"], base="DC365"),
    },
    "PASEP": {
      "z306": dict(fn=F.pasep_z306,
                   descricao="PASEP sobre base fiscal — períodos de amortização",
                   params=["base_fiscal","alfa"]),
      "z307": dict(fn=F.pasep_z307,
                   descricao="PASEP sobre base fiscal — somente em t=0",
                   params=["base_fiscal","alfa"], quando="t0"),
    },
    "COFINS": {
      "z311": dict(fn=F.cofins_z311, descricao="COFINS períodos", params=["base_fiscal","alfa"]),
      "z312": dict(fn=F.cofins_z312, descricao="COFINS em t=0",   params=["base_fiscal","alfa"], quando="t0"),
    },
    "ISS": {
      "z316": dict(fn=F.iss_z316, descricao="ISS sobre base fiscal (períodos)",  params=["base_fiscal","alfa"]),
      "z317": dict(fn=F.iss_z317, descricao="ISS sobre tarifas/serviços (t=0)", params=["base_fiscal","alfa"], quando="t0"),
      "iss_tarifa": dict(fn=lambda base_fiscal, alfa, **_: -base_fiscal * (alfa/100),
                         descricao="ISS sobre receita de tarifa por período (planilha real)",
                         params=["base_fiscal","alfa"]),
    },
    "IRPJ": {
      "z321": dict(fn=F.irpj_z321, descricao="IRPJ períodos (25%+adicional)",  params=["base_fiscal","alfa"]),
      "z322": dict(fn=F.irpj_z322, descricao="IRPJ em t=0",                    params=["base_fiscal","alfa"], quando="t0"),
    },
    "CSLL": {
      "z326": dict(fn=F.csll_z326, descricao="CSLL períodos (20% banco)",  params=["base_fiscal","alfa"]),
      "z327": dict(fn=F.csll_z327, descricao="CSLL em t=0",                params=["base_fiscal","alfa"], quando="t0"),
    },
    "IR_CS_combinado": {
      "z355": dict(fn=lambda base_fiscal, alfa, t, T, **_: -base_fiscal*(alfa/100) if 0<t<=T else 0.0,
                   descricao="IR+CSLL combinado (45% banco — IRPJ 25%+10%adicional + CSLL 20%)",
                   params=["base_fiscal","alfa"]),
    },
    "FLA": {   # Fluxos de Caixa
      "f1060": dict(fn=F.fla_f1060,
                    descricao="FLA completo (SP+RA−custos−tributos−CP−MG)",
                    params=["SP","RA","CFVT","EPE","FGC","PASEP","COF",
                            "ISS","ISSL","IRPJ","IRDPJ","CSLL","CP","MG"]),
      "f1099": dict(fn=F.flc_f1099, descricao="FLC — só PMTA (sem RA)", params=["PMTA"]),
      "f1100": dict(fn=F.fld_f1100, descricao="FLD — PMTA + RA (all-in)", params=["PMTA","RA"]),
      "f1101": dict(fn=F.fle_f1101, descricao="FLE — PMTP (passivo, para TPP)", params=["PMTP"]),
      "f1231": dict(fn=F.flf_f1231,
                    descricao="FLF — sem MG (para SPTX)",
                    params=["SP","RA","CFVT","EPE","FGC","PASEP","COF",
                            "ISS","ISSL","IRPJ","IRDPJ","CSLL","CP"]),
    },
    "VP_fluxo": {
      "f1062": dict(fn=F.fvpa_f1062, descricao="FLA a VP",  params=["FLA","CVCC","DU_t"], base="DU252"),
      "f1104": dict(fn=F.fvpd_f1104, descricao="FLD a VP",  params=["FLD","CVCC","DU_t"], base="DU252"),
      "f1105": dict(fn=F.fvpe_f1105, descricao="FLE a VP",  params=["FLE","CVCC","DU_t"], base="DU252"),
      "f1232": dict(fn=F.fvpf_f1232, descricao="FLF a VP",  params=["FLF","CVCC","DU_t"], base="DU252"),
    },
  },

  # ═══════════════════════════════════════════════════════════════════════════
  # MÓDULO 6 — PERFORMANCE
  # ═══════════════════════════════════════════════════════════════════════════
  "performance": {
    "RSPLE": {
      "f1064": dict(fn=Perf.rsple_f1064,
                    descricao="RSPLE = λ/(FPRP×K×(1+(F−1)×FCC))×100",
                    params=["lambda_mg","FPRP","K_basileia","F","FCC"]),
      "f1223": dict(fn=Perf.rsple_f1223_eql,
                    descricao="RSPLE com fator de ponderação FP (equalização)",
                    params=["lambda_mg","FPRP","K_basileia","FP","F","FCC"]),
    },
    "RAR": {
      "f1065": dict(fn=Perf.rar_f1065,
                    descricao="RAR base = (λ_mg / CE) × 100",
                    params=["lambda_mg","CE"]),
      "f1183": dict(fn=Perf.rar_gestao_f1183,
                    descricao="RAR Gestão = (λ_mg / CEIRB) × 100 — capital econômico IRB",
                    params=["lambda_mg","CEIRB"]),
      "f1213": dict(fn=Perf.rar_prudencial_rarp_f1213,
                    descricao="RAR Prudencial = (λ_mg / Kp_pond) × 100",
                    params=["lambda_mg","Kp"]),
      "f1224": dict(fn=Perf.rar_f1224_eql,
                    descricao="RAR com fator de ponderação FP",
                    params=["lambda_mg","CE","FP"]),
      "f1229": dict(fn=Perf.rarsra_f1229,
                    descricao="RAR sem receitas adicionais (φ_mga / Kp)",
                    params=["phi_mga","Kp"]),
    },
    "IE": {
      "f1066": dict(fn=Perf.indice_eficiencia_ie_f1066,
                    descricao="IE = CFVT_VP / SP_VP (eficiência operacional)",
                    params=["CFVTVP","SPVP"]),
    },
    "IR_risco": {
      "f1067": dict(fn=Perf.indice_risco_ir_f1067,
                    descricao="IR = EPE_VP / SP_VP (cobertura de risco)",
                    params=["EPEVP","SPVP"]),
    },
    "IRE": {
      "f1068": dict(fn=Perf.indice_rentabilidade_ire_f1068,
                    descricao="IRE = MG_VP / SP_VP (rentabilidade)",
                    params=["MGVP","SPVP"]),
    },
    "Duration": {
      "f1204": dict(fn=Perf.duration_drt_f1204,
                    descricao="Duration = Σ(t×PMTA_desc) / Σ(PMTA_desc)",
                    params=["soma_t_PMTA_desc","soma_PMTA_desc"]),
    },
    "VA": {
      "f1208": dict(fn=Perf.valor_agregado_va_f1208,
                    descricao="EVA = MG_VP − Custo_Capital_VP",
                    params=["MGVP","custo_capital_vp"]),
    },
  },

  # ═══════════════════════════════════════════════════════════════════════════
  # MÓDULO 7 — MÉTODOS ITERATIVOS (taxas implícitas)
  # ═══════════════════════════════════════════════════════════════════════════
  "iterativo": {
    "TIR": {
      "f1095": dict(fn=Perf.funcao_objetivo_tir_f1095,
                    descricao="TIR — função objetivo sobre Fluxo D",
                    params=["chute_tir","FLD_t","ECA_t","dct"]),
      "f1238": dict(fn=Perf.funcao_objetivo_tir_sr_f1238,
                    descricao="TIR sem RA — função objetivo sobre Fluxo C",
                    params=["chute_tir","FLC_t","ECA_t","dct"]),
    },
    "TPP": {
      "f1096": dict(fn=Perf.funcao_objetivo_tpp_f1096,
                    descricao="TPP (Resultado PPS) — Fluxo E (passivo)",
                    params=["chute_tpp","FLE_t","ECA_t","dct"]),
    },
    "PCDI": {
      "f1097": dict(fn=Perf.funcao_objetivo_pcdi_f1097,
                    descricao="% CDI por equivalência de fluxo (Fluxo C, DU/252)",
                    params=["chute_pcdi","FLC_t","CVSC_t","ECA_t","dut"]),
      "f1098": dict(fn=Perf.funcao_objetivo_pcdiai_f1098,
                    descricao="% CDI All In (Fluxo D, DU/252)",
                    params=["chute_pcdiai","FLD_t","CVSC_t","ECA_t","dut"]),
    },
    "SPTX": {
      "f1233": dict(fn=Perf.funcao_objetivo_sptx_f1233,
                    descricao="Spread em taxa % — Fluxo F (sem MG)",
                    params=["chute_sptx","FLF_t","ECA_t","dct"]),
    },
  },
}


# ─────────────────────────────────────────────────────────────────────────────
# API pública do registry
# ─────────────────────────────────────────────────────────────────────────────

def get_fn(modulo: str, slot: str, codigo: str):
    """Retorna a função Python para modulo/slot/código."""
    try:
        return REGISTRY[modulo][slot][codigo]["fn"]
    except KeyError:
        mods = list(REGISTRY.keys())
        slots = list(REGISTRY.get(modulo, {}).keys())
        codigos = list(REGISTRY.get(modulo, {}).get(slot, {}).keys())
        raise KeyError(
            f"Não encontrado: modulo='{modulo}' slot='{slot}' codigo='{codigo}'\n"
            f"  Módulos: {mods}\n  Slots em '{modulo}': {slots}\n"
            f"  Códigos em '{slot}': {codigos}"
        )


def get_meta(modulo: str, slot: str, codigo: str) -> dict:
    """Retorna metadados (descricao, params, base) de uma fórmula."""
    return REGISTRY[modulo][slot][codigo]


def listar_slot(modulo: str, slot: str) -> None:
    """Imprime todas as fórmulas disponíveis para um slot."""
    entradas = REGISTRY.get(modulo, {}).get(slot, {})
    if not entradas:
        print(f"Slot '{slot}' não encontrado no módulo '{modulo}'.")
        return
    print(f"\n{'─'*60}")
    print(f"  Módulo: {modulo}  |  Slot: {slot}")
    print(f"{'─'*60}")
    for cod, meta in entradas.items():
        print(f"  {cod:<14}  {meta['descricao']}")
        print(f"  {'':14}  Parâmetros: {meta['params']}")
        if "base" in meta:
            print(f"  {'':14}  Base tempo:  {meta['base']}")
        print()


def slots_de(modulo: str) -> list:
    """Lista todos os slots de um módulo."""
    return list(REGISTRY.get(modulo, {}).keys())


def modulos_disponiveis() -> list:
    return list(REGISTRY.keys())


def catalogo_resumido() -> None:
    """Imprime resumo de todos módulos e slots."""
    for mod, slots in REGISTRY.items():
        print(f"\n  [{mod.upper()}]")
        for slot, codigos in slots.items():
            cod_list = list(codigos.keys())
            print(f"    {slot:<22}  {cod_list}")


if __name__ == "__main__":
    catalogo_resumido()
