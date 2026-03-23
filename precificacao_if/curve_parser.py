"""
curve_parser.py
═══════════════
Parser e interpolador das curvas DIFIN (arquivo TXT padrão BB).

Formato do arquivo:
  HDR CURVAS DIFIN 2024.01.19.17:41:15 23/01/2024   ← cabeçalho
  01 20240123 000001 000001 0001165000               ← dados

  Campo 1 (2): tipo da curva
    01 = CDI-PSC  (curva de desconto / funding principal)
    02 = CDI-PCC  (curva de crédito privado)
    03 = TR       (taxa referencial — mensal)
    04 = TJLP     (taxa juros longo prazo — anual)
    09 = IPCA     (projeção mensal IPCA)

  Campo 2 (8): data YYYYMMDD
  Campo 3 (6): DU acumulados desde a data base
  Campo 4 (6): DC acumulados (999999 para curvas mensais)
  Campo 5 (10): taxa × 100000 → taxa % direta
    Ex: 0001165000 → 1165000 / 100000 = 11.65%

Tipos de taxa por curva:
  01/02 (CDI): zero-coupon anualizado % a.a. (base 252 DU)
  03 (TR):     taxa mensal direta % a.m.
  04 (TJLP):   taxa anual % a.a.
  09 (IPCA):   taxa mensal % a.m.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, date
import bisect

TIPOS_CURVA = {
    1: "CDI-PSC",
    2: "CDI-PCC",
    3: "TR",
    4: "TJLP",
    9: "IPCA",
}

TIPO_BASE = {
    1: "DU252_anual",    # zero-coupon a.a., interpola forward DU
    2: "DU252_anual",
    3: "mensal_direto",  # valor mensal direto
    4: "anual_direto",   # taxa anual fixa
    9: "mensal_direto",  # projeção mensal direta
}


@dataclass
class NoCurva:
    tipo:  int
    data:  date
    du:    int      # dias úteis acumulados desde data base
    dc:    int      # dias corridos acumulados (999999 se mensal)
    taxa:  float    # taxa em % (já convertida)


@dataclass
class CurvaDIFIN:
    """Representa uma curva completa carregada do arquivo DIFIN."""
    tipo:        int
    nome:        str
    data_base:   Optional[date]
    nos:         list = field(default_factory=list)   # List[NoCurva], ordenado por DU

    def taxa_para_du(self, du_alvo: int) -> float:
        """
        Retorna a taxa % para um DU específico, interpolando entre os nós.

        Para CDI (base DU252_anual): retorna a taxa zero-coupon % a.a. para aquele prazo.
        Para TR/IPCA (mensal_direto): retorna a taxa % a.m. do mês correspondente ao DU.
        Para TJLP (anual_direto): retorna a taxa % a.a. vigente.
        """
        if not self.nos:
            return 0.0

        dus = [n.du for n in self.nos]

        # Fora do range → extrapola com o valor extremo
        if du_alvo <= dus[0]:
            return self.nos[0].taxa
        if du_alvo >= dus[-1]:
            return self.nos[-1].taxa

        # Encontra os dois nós vizinhos
        idx = bisect.bisect_left(dus, du_alvo)
        n0 = self.nos[idx - 1]
        n1 = self.nos[idx]

        if n0.du == du_alvo:
            return n0.taxa
        if n1.du == du_alvo:
            return n1.taxa

        base = TIPO_BASE.get(self.tipo, "linear")

        if base == "DU252_anual":
            # Interpolação flat-forward entre os dois nós
            # Converte zero-coupon → forward entre DU0 e DU1
            r0 = n0.taxa / 100
            r1 = n1.taxa / 100
            fator0 = (1 + r0) ** (n0.du / 252)
            fator1 = (1 + r1) ** (n1.du / 252)
            fator_alvo_interp = fator0 * ((fator1 / fator0) ** (
                (du_alvo - n0.du) / (n1.du - n0.du)
            ))
            taxa_zc_alvo = (fator_alvo_interp ** (252 / du_alvo) - 1) * 100
            return taxa_zc_alvo

        else:
            # Interpolação linear simples (TR, IPCA, TJLP)
            frac = (du_alvo - n0.du) / (n1.du - n0.du)
            return n0.taxa + frac * (n1.taxa - n0.taxa)

    def taxa_forward_periodo(self, du_ini: int, du_fim: int) -> float:
        """
        Calcula a taxa forward anualizada (% a.a.) entre dois DUs.
        Usada para EBP/EBA período a período (base DU252).
        """
        if self.tipo not in (1, 2):
            # Para TR/IPCA: retorna o valor do período como mensal
            return self.taxa_para_du(max(du_ini, 1))

        if du_ini <= 0:
            du_ini = 0
            f0 = 1.0
        else:
            r0 = self.taxa_para_du(du_ini) / 100
            f0 = (1 + r0) ** (du_ini / 252)

        r1 = self.taxa_para_du(du_fim) / 100
        f1 = (1 + r1) ** (du_fim / 252)

        du_delta = du_fim - du_ini
        if du_delta <= 0:
            return 0.0

        fwd_anual = (f1 / f0) ** (252 / du_delta) - 1
        return fwd_anual * 100

    def taxa_periodo_du(self, du_ini: int, du_fim: int) -> float:
        """
        Retorna a taxa do período (não anualizada) entre du_ini e du_fim.
        Usada como fator de capitalização: EBP = SDP × taxa_periodo
        """
        fwd_aa = self.taxa_forward_periodo(du_ini, du_fim)
        du_delta = du_fim - du_ini
        if du_delta <= 0:
            return 0.0

        if self.tipo in (1, 2):
            # CDI: capitaliza pelo período
            return (1 + fwd_aa / 100) ** (du_delta / 252) - 1
        elif self.tipo == 3:
            # TR: taxa mensal direta
            return self.taxa_para_du(max(du_ini, 1)) / 100
        elif self.tipo == 4:
            # TJLP: converte anual para o período
            return (1 + fwd_aa / 100) ** (du_delta / 252) - 1
        elif self.tipo == 9:
            # IPCA: taxa mensal direta
            return self.taxa_para_du(max(du_ini, 1)) / 100
        else:
            return 0.0


# ─────────────────────────────────────────────────────────────────────────────

def parse_difin(conteudo: str) -> dict:
    """
    Lê o conteúdo do arquivo DIFIN e retorna dict {tipo_int: CurvaDIFIN}.

    Parâmetro:
        conteudo: string com todo o conteúdo do arquivo .txt

    Retorna:
        {1: CurvaDIFIN(CDI-PSC), 2: CurvaDIFIN(CDI-PCC), 3: CurvaDIFIN(TR), ...}
    """
    curvas: dict[int, CurvaDIFIN] = {}
    data_base = None

    for linha in conteudo.splitlines():
        linha = linha.strip()
        if not linha:
            continue

        # Cabeçalho: HDR CURVAS DIFIN ...
        if linha.startswith("HDR"):
            partes = linha.split()
            if len(partes) >= 5:
                try:
                    data_base = datetime.strptime(partes[-1], "%d/%m/%Y").date()
                except ValueError:
                    pass
            continue

        partes = linha.split()
        if len(partes) < 5:
            continue

        try:
            tipo = int(partes[0])
            data_str = partes[1]
            du   = int(partes[2])
            dc_  = int(partes[3])
            raw  = int(partes[4])
        except (ValueError, IndexError):
            continue

        # Ignora tipos não mapeados
        if tipo not in TIPOS_CURVA:
            continue

        # Converte taxa
        taxa = raw / 100000.0  # → % direto

        # Parse data
        try:
            data_no = datetime.strptime(data_str, "%Y%m%d").date()
        except ValueError:
            continue

        if tipo not in curvas:
            curvas[tipo] = CurvaDIFIN(
                tipo=tipo,
                nome=TIPOS_CURVA[tipo],
                data_base=data_base,
                nos=[],
            )

        curvas[tipo].nos.append(NoCurva(tipo=tipo, data=data_no,
                                         du=du, dc=dc_, taxa=taxa))

    # Garante ordenação por DU
    for curva in curvas.values():
        curva.nos.sort(key=lambda n: n.du)

    return curvas


def resumo_curvas(curvas: dict) -> str:
    """Retorna string de resumo das curvas carregadas."""
    linhas = []
    for tipo, curva in sorted(curvas.items()):
        n = len(curva.nos)
        if n == 0:
            continue
        taxa_ini = curva.nos[0].taxa
        taxa_fim = curva.nos[-1].taxa
        data_ini = curva.nos[0].data
        data_fim = curva.nos[-1].data
        linhas.append(
            f"  Tipo {tipo:02d} ({curva.nome:8s}): {n:>4} nós  "
            f"{data_ini} → {data_fim}  "
            f"taxa: {taxa_ini:.5f}% → {taxa_fim:.5f}%"
        )
    return "\n".join(linhas)


# ─── Teste rápido ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    txt_sample = """HDR CURVAS DIFIN 2024.01.19.17:41:15 23/01/2024
01 20240123 000001 000001 0001165000
01 20240201 000008 000010 0001165400
01 20240301 000027 000039 0001131000
01 20240401 000047 000070 0001118400
01 20240502 000069 000101 0001102000
03 20240122 000001 999999 0000002279
03 20240222 000002 999999 0000005953
04 20240101 000001 999999 0000653000
04 20240201 000002 999999 0000653000
09 20240101 000001 999999 0000038000
09 20240201 000002 999999 0000064000
"""
    curvas = parse_difin(txt_sample)
    print(resumo_curvas(curvas))
    print()

    cdi = curvas[1]
    for du in [1, 5, 8, 15, 21, 27]:
        taxa = cdi.taxa_para_du(du)
        fwd  = cdi.taxa_periodo_du(0, du)
        print(f"  CDI DU={du:>3}  ZC={taxa:.5f}% a.a.  período={fwd*100:.6f}%")
