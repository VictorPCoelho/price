"""Precificador de Catálogos — app web para precificar catálogos PDF de roupas.

Dois fluxos:
- Catálogo com preços impressos: detecta os preços e carimba o novo valor.
- Catálogo + tabela separada: lê a tabela de códigos e preços (Excel/CSV/PDF),
  localiza cada código no catálogo e carimba o preço de venda ao lado.

Para rodar:  streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from precificador.carimbo import (
    POSICOES_LOGO,
    ItemCarimbo,
    carimbar,
    imagem_pagina,
    inserir_logo,
)
from precificador.extracao import extrair_precos, localizar_codigos
from precificador.regras import (
    ARREDONDAMENTOS,
    MODOS_CARIMBO,
    PerfilMarca,
    RepositorioPerfis,
    calcular_preco,
    formatar_brl,
    hex_para_rgb,
    linhas_da_etiqueta,
)
from precificador.tabela import (
    adivinhar_colunas,
    extrair_linhas,
    ler_planilha,
    ler_tabela_pdf,
)

st.set_page_config(page_title="Precificador de Catálogos", page_icon="👶", layout="wide")

CAMINHO_PERFIS = Path(__file__).parent / "perfis.json"
repo = RepositorioPerfis(CAMINHO_PERFIS)

# ---------------------------------------------------------------- Perfis
st.sidebar.title("👶 Precificador")
perfis = repo.carregar()

nomes = sorted(perfis)
opcoes = nomes + ["➕ Nova marca..."]
escolha = st.sidebar.selectbox("Marca / catálogo", opcoes, index=0 if nomes else len(opcoes) - 1)

if escolha == "➕ Nova marca...":
    nome_novo = st.sidebar.text_input("Nome da nova marca")
    perfil = PerfilMarca(nome=nome_novo or "Nova marca")
else:
    perfil = perfis[escolha]

st.sidebar.divider()
perfil.multiplicador = st.sidebar.number_input(
    "Multiplicador padrão", min_value=0.1, max_value=20.0,
    value=float(perfil.multiplicador), step=0.05, format="%.2f",
    help="O preço de venda = preço do catálogo × multiplicador. "
    "Você pode ajustar item a item depois.",
)
perfil.arredondamento = st.sidebar.selectbox(
    "Arredondamento", list(ARREDONDAMENTOS),
    index=list(ARREDONDAMENTOS).index(perfil.arredondamento),
    format_func=ARREDONDAMENTOS.get,
)
perfil.modo_carimbo = st.sidebar.selectbox(
    "Como escrever o novo preço", list(MODOS_CARIMBO),
    index=list(MODOS_CARIMBO).index(perfil.modo_carimbo),
    format_func=MODOS_CARIMBO.get,
    help="Vale para o fluxo de preços impressos no catálogo. No fluxo com "
    "tabela separada o preço é sempre adicionado ao lado do código.",
)
perfil.exigir_rs = st.sidebar.toggle(
    "Considerar apenas valores com R$",
    value=perfil.exigir_rs,
    help="Mais seguro. Desligue apenas se o catálogo mostra os preços sem o "
    "símbolo R$ (aí números como 99,90 também serão detectados).",
)
perfil.descricao_na_etiqueta = st.sidebar.toggle(
    "Descrição da peça na etiqueta",
    value=perfil.descricao_na_etiqueta,
    help="No fluxo com tabela separada, escreve o nome da peça na primeira "
    "linha da etiqueta — essencial quando há mais de um código na mesma "
    "foto (ex.: bermuda e camiseta).",
)
perfil.cor_etiqueta = st.sidebar.color_picker(
    "Cor da etiqueta de preço", value=perfil.cor_etiqueta,
    help="Cor de fundo da etiqueta no modo “adicionar”. O texto fica branco "
    "ou preto automaticamente, conforme o contraste.",
)

with st.sidebar.expander("Limites para alerta"):
    perfil.valor_minimo = st.number_input(
        "Alertar se preço original abaixo de (R$)", value=float(perfil.valor_minimo), step=1.0
    )
    perfil.valor_maximo = st.number_input(
        "Alertar se preço original acima de (R$)", value=float(perfil.valor_maximo), step=10.0
    )

# ----- logo do grupo de compras (fica salvo para as próximas vezes)
PASTA_LOGOS = Path(__file__).parent / "logos"


def _caminho_logo() -> Path:
    nome_seguro = "".join(c if c.isalnum() else "_" for c in perfil.nome) or "logo"
    return PASTA_LOGOS / f"{nome_seguro}.png"


with st.sidebar.expander("🏷️ Logo do seu grupo"):
    logo_enviado = st.file_uploader(
        "Imagem do logo (PNG ou JPG)", type=["png", "jpg", "jpeg"], key="logo_upload"
    )
    if logo_enviado is not None:
        PASTA_LOGOS.mkdir(exist_ok=True)
        _caminho_logo().write_bytes(logo_enviado.getvalue())
        st.success("Logo salvo — será usado automaticamente nas próximas vezes.")
    logo_bytes = _caminho_logo().read_bytes() if _caminho_logo().exists() else None
    if logo_bytes:
        st.image(logo_bytes, width=120)
        perfil.usar_logo = st.toggle("Inserir o logo no PDF gerado", value=perfil.usar_logo)
        perfil.logo_posicao = st.selectbox(
            "Posição", list(POSICOES_LOGO),
            index=list(POSICOES_LOGO).index(perfil.logo_posicao),
            format_func=POSICOES_LOGO.get,
        )
        perfil.logo_largura = st.slider(
            "Tamanho (% da largura da página)", 5, 50, int(perfil.logo_largura)
        )
        perfil.logo_todas_paginas = st.toggle(
            "Em todas as páginas (desligado = só na primeira)",
            value=perfil.logo_todas_paginas,
        )
    else:
        st.caption("Envie o logo uma vez; ele fica salvo para as próximas vezes.")


def _aplicar_logo(pdf: bytes) -> bytes:
    if logo_bytes and perfil.usar_logo:
        return inserir_logo(
            pdf, logo_bytes,
            posicao=perfil.logo_posicao,
            largura_frac=perfil.logo_largura / 100,
            todas_as_paginas=perfil.logo_todas_paginas,
        )
    return pdf


COR_ETIQUETA_RGB = hex_para_rgb(perfil.cor_etiqueta)

if st.sidebar.button("💾 Salvar perfil da marca", use_container_width=True):
    if not perfil.nome or perfil.nome == "Nova marca":
        st.sidebar.error("Dê um nome para a marca antes de salvar.")
    else:
        perfis[perfil.nome] = perfil
        repo.salvar(perfis)
        st.sidebar.success(f"Perfil “{perfil.nome}” salvo.")

# ---------------------------------------------------------------- Fluxo
st.title("Precificador de Catálogos")

fluxo = st.radio(
    "Como vem o preço desta marca?",
    ["📄 Preços impressos no próprio catálogo", "📄+📊 Catálogo + tabela de preços separada"],
    horizontal=True,
)

FLUXO_UM = fluxo.startswith("📄 ")


def _tabela_para_itens(tabela: pd.DataFrame, precos) -> list[ItemCarimbo]:
    return [
        ItemCarimbo(
            pagina=precos[int(row["id"])].pagina,
            bbox=precos[int(row["id"])].bbox,
            novo_valor=float(row["Novo preço (R$)"]),
            tinha_rs=precos[int(row["id"])].tinha_rs,
        )
        for _, row in tabela.iterrows()
        if row["Incluir"]
    ]


def _botao_download(resultado: bytes, nome: str) -> None:
    st.download_button(
        "⬇️ Baixar PDF precificado",
        data=resultado,
        file_name=nome,
        mime="application/pdf",
        type="primary",
    )


# ================================================================ FLUXO 1
if FLUXO_UM:
    st.caption(
        "1️⃣ Envie o PDF do catálogo · 2️⃣ Confira os preços detectados · "
        "3️⃣ Ajuste o que precisar · 4️⃣ Baixe o PDF precificado"
    )

    arquivo = st.file_uploader("PDF do catálogo", type=["pdf"])
    if arquivo is None:
        st.info("Envie um catálogo em PDF para começar.")
        st.stop()

    pdf_bytes = arquivo.getvalue()

    chave_extracao = (arquivo.name, len(pdf_bytes), perfil.exigir_rs,
                      perfil.valor_minimo, perfil.valor_maximo)
    if st.session_state.get("chave_extracao") != chave_extracao:
        with st.spinner("Lendo o catálogo e procurando os preços..."):
            precos, avisos = extrair_precos(
                pdf_bytes,
                exigir_rs=perfil.exigir_rs,
                valor_minimo=perfil.valor_minimo,
                valor_maximo=perfil.valor_maximo,
            )
        st.session_state.chave_extracao = chave_extracao
        st.session_state.precos = precos
        st.session_state.avisos = avisos
        st.session_state.pop("tabela_editada", None)

    precos = st.session_state.precos
    avisos = st.session_state.avisos

    for aviso in avisos:
        st.warning(aviso, icon="⚠️")

    if not precos:
        st.error(
            "Nenhum preço foi detectado neste PDF. Se o catálogo é escaneado "
            "(imagem), o texto não pode ser lido automaticamente. Se os preços "
            "aparecem sem o símbolo R$, desligue a opção “Considerar apenas "
            "valores com R$” na barra lateral. Se os preços vêm numa tabela "
            "separada, troque o fluxo lá em cima para “Catálogo + tabela”."
        )
        st.stop()

    st.subheader("2️⃣ Confira e ajuste os preços")

    linhas = []
    for i, p in enumerate(precos):
        novo = calcular_preco(p.valor, perfil.multiplicador, perfil.arredondamento)
        linhas.append({
            "id": i,
            "Incluir": True,
            "Página": p.pagina + 1,
            "Preço no catálogo": p.valor,
            "Novo preço (R$)": novo,
            "Alerta": "; ".join(p.avisos) if p.avisos else "",
        })
    base = pd.DataFrame(linhas)

    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Preços detectados", len(precos))
    col_m2.metric("Páginas do catálogo", int(base["Página"].max()))
    n_alertas = int((base["Alerta"] != "").sum())
    col_m3.metric("Itens com alerta", n_alertas)

    if n_alertas:
        st.warning(
            f"{n_alertas} item(ns) com alerta — confira as linhas marcadas na "
            "coluna “Alerta” antes de gerar o PDF.",
            icon="🚨",
        )

    st.caption(
        "A coluna **Novo preço** já vem calculada com o multiplicador "
        f"×{perfil.multiplicador:.2f} — edite direto na tabela os itens que fogem "
        "da regra. Desmarque **Incluir** para deixar um item com o preço original."
    )

    tabela = st.data_editor(
        base,
        key="tabela_editada",
        hide_index=True,
        use_container_width=True,
        column_config={
            "id": None,
            "Incluir": st.column_config.CheckboxColumn("Incluir"),
            "Página": st.column_config.NumberColumn("Página", disabled=True),
            "Preço no catálogo": st.column_config.NumberColumn(
                "Preço no catálogo (R$)", format="%.2f", disabled=True
            ),
            "Novo preço (R$)": st.column_config.NumberColumn(
                "Novo preço (R$)", format="%.2f", min_value=0.0
            ),
            "Alerta": st.column_config.TextColumn("Alerta", disabled=True),
        },
        num_rows="fixed",
    )

    st.subheader("3️⃣ Pré-visualização")
    paginas_disponiveis = sorted(tabela["Página"].unique())
    pagina_escolhida = st.selectbox(
        "Página", paginas_disponiveis, format_func=lambda p: f"Página {p}"
    )

    tabela_pagina = tabela[tabela["Página"] == pagina_escolhida]
    itens_da_pagina = _tabela_para_itens(tabela_pagina, precos)

    col_antes, col_depois = st.columns(2)
    with col_antes:
        st.markdown("**Original** (preços detectados em vermelho)")
        destaques = [precos[int(r["id"])].bbox for _, r in tabela_pagina.iterrows()]
        st.image(imagem_pagina(pdf_bytes, pagina_escolhida - 1, destaques=destaques))
    with col_depois:
        st.markdown("**Precificado**")
        pdf_previa = _aplicar_logo(carimbar(
            pdf_bytes, itens_da_pagina, modo=perfil.modo_carimbo,
            cor_etiqueta=COR_ETIQUETA_RGB,
        ))
        st.image(imagem_pagina(pdf_previa, pagina_escolhida - 1))

    st.subheader("4️⃣ Gerar o PDF precificado")
    if st.button("✅ Gerar PDF precificado", type="primary"):
        itens = _tabela_para_itens(tabela, precos)
        with st.spinner("Carimbando os preços..."):
            resultado = _aplicar_logo(carimbar(
                pdf_bytes, itens, modo=perfil.modo_carimbo,
                cor_etiqueta=COR_ETIQUETA_RGB,
            ))
        st.session_state.resultado = resultado
        st.session_state.resultado_nome = arquivo.name.replace(".pdf", "") + "_precificado.pdf"
        total = sum(i.novo_valor for i in itens)
        st.success(
            f"Pronto! {len(itens)} preço(s) carimbado(s). "
            f"Soma dos novos preços: {formatar_brl(total)}."
        )

    if "resultado" in st.session_state:
        _botao_download(st.session_state.resultado, st.session_state.resultado_nome)

# ================================================================ FLUXO 2
else:
    st.caption(
        "1️⃣ Envie o catálogo (fotos com códigos) e a tabela de preços · "
        "2️⃣ Confira os códigos e valores · 3️⃣ Ajuste o que precisar · "
        "4️⃣ Baixe o PDF com os preços ao lado dos códigos"
    )

    col_up1, col_up2 = st.columns(2)
    with col_up1:
        arq_catalogo = st.file_uploader("Catálogo (PDF com fotos e códigos)", type=["pdf"])
    with col_up2:
        arq_tabela = st.file_uploader(
            "Tabela de preços (Excel, CSV ou PDF)", type=["xlsx", "xls", "csv", "pdf"]
        )

    if arq_catalogo is None or arq_tabela is None:
        st.info("Envie os dois arquivos para começar.")
        st.stop()

    pdf_bytes = arq_catalogo.getvalue()
    tabela_bytes = arq_tabela.getvalue()

    # ----- lê a tabela de preços
    if arq_tabela.name.lower().endswith(".pdf"):
        linhas_tabela, avisos_tabela = ler_tabela_pdf(tabela_bytes)
    else:
        try:
            df_bruto = ler_planilha(tabela_bytes, arq_tabela.name)
        except Exception as e:
            st.error(f"Não consegui ler a planilha: {e}")
            st.stop()
        chute_cod, chute_precos = adivinhar_colunas(df_bruto)
        colunas = list(df_bruto.columns)
        st.markdown("**Qual coluna é o quê?** (confira a pré-visualização)")
        col_a, col_b, col_c = st.columns([1, 1, 2])
        with col_a:
            col_codigo = st.selectbox(
                "Coluna do código", colunas,
                index=colunas.index(chute_cod) if chute_cod in colunas else 0,
            )
        with col_b:
            cols_preco = st.multiselect(
                "Coluna(s) de preço", colunas,
                default=[c for c in chute_precos if c != col_codigo],
                help="Se a tabela tem um preço por faixa de tamanho, "
                "selecione todas as colunas de preço.",
            )
        with col_c:
            st.dataframe(df_bruto.head(5), use_container_width=True, hide_index=True)
        if not cols_preco:
            st.error("Selecione pelo menos uma coluna de preço.")
            st.stop()
        if col_codigo in cols_preco:
            st.error("A coluna do código não pode ser também coluna de preço.")
            st.stop()
        linhas_tabela, avisos_tabela = extrair_linhas(df_bruto, col_codigo, cols_preco)

    for aviso in avisos_tabela:
        st.warning(aviso, icon="⚠️")

    if not linhas_tabela:
        st.error(
            "Não consegui extrair nenhum par código + preço da tabela. "
            "Confira se escolheu as colunas certas (ou, no caso de PDF, se a "
            "tabela tem texto legível)."
        )
        st.stop()

    # ----- localiza os códigos no catálogo (com cache por arquivos)
    codigos = [l.codigo for l in linhas_tabela]
    chave_loc = (arq_catalogo.name, len(pdf_bytes), tuple(codigos))
    if st.session_state.get("chave_loc") != chave_loc:
        with st.spinner("Procurando os códigos no catálogo..."):
            ocorrencias, avisos_loc = localizar_codigos(pdf_bytes, codigos)
        st.session_state.chave_loc = chave_loc
        st.session_state.ocorrencias = ocorrencias
        st.session_state.avisos_loc = avisos_loc
        st.session_state.pop("tabela_codigos", None)

    ocorrencias = st.session_state.ocorrencias
    for aviso in st.session_state.avisos_loc:
        st.warning(aviso, icon="⚠️")

    # ----- tabela de conferência (uma linha por código + faixa de tamanho)
    st.subheader("2️⃣ Confira os códigos e os preços")

    linhas_ui = []
    for linha in linhas_tabela:
        ocs = ocorrencias.get(linha.codigo, [])
        alerta = ""
        if not ocs:
            alerta = "não encontrado no catálogo"
        elif len(ocs) > 1:
            alerta = f"aparece {len(ocs)}× no catálogo (todas serão precificadas)"
        for pt in linha.precos:
            novo = calcular_preco(pt.valor, perfil.multiplicador, perfil.arredondamento)
            linhas_ui.append({
                "Incluir": bool(ocs),
                "Código": linha.codigo,
                "Tamanho": pt.rotulo or "—",
                "Descrição": linha.descricao,
                "Preço na tabela": pt.valor,
                "Novo preço (R$)": novo,
                "Páginas": ", ".join(str(o.pagina + 1) for o in ocs) or "—",
                "Alerta": alerta,
            })
    base = pd.DataFrame(linhas_ui)

    n_nao_achados = sum(1 for l in linhas_tabela if not ocorrencias.get(l.codigo))
    col_m1, col_m2, col_m3 = st.columns(3)
    col_m1.metric("Códigos na tabela", len(linhas_tabela))
    col_m2.metric("Encontrados no catálogo", len(linhas_tabela) - n_nao_achados)
    col_m3.metric("Não encontrados", n_nao_achados)

    if n_nao_achados:
        st.warning(
            f"{n_nao_achados} código(s) da tabela não foram localizados no "
            "catálogo — essas peças precisam ser conferidas manualmente. "
            "Veja a coluna “Alerta”.",
            icon="🚨",
        )

    st.caption(
        "O **Novo preço** já vem calculado com o multiplicador "
        f"×{perfil.multiplicador:.2f} sobre o preço da tabela — edite os itens "
        "que fogem da regra. Desmarque **Incluir** para não carimbar um item."
    )

    tabela_ui = st.data_editor(
        base,
        key="tabela_codigos",
        hide_index=True,
        use_container_width=True,
        column_config={
            "Incluir": st.column_config.CheckboxColumn("Incluir"),
            "Código": st.column_config.TextColumn("Código", disabled=True),
            "Tamanho": st.column_config.TextColumn("Tamanho", disabled=True),
            "Descrição": st.column_config.TextColumn("Descrição", disabled=True),
            "Preço na tabela": st.column_config.NumberColumn(
                "Preço na tabela (R$)", format="%.2f", disabled=True
            ),
            "Novo preço (R$)": st.column_config.NumberColumn(
                "Novo preço (R$)", format="%.2f", min_value=0.0
            ),
            "Páginas": st.column_config.TextColumn("Páginas", disabled=True),
            "Alerta": st.column_config.TextColumn("Alerta", disabled=True),
        },
        num_rows="fixed",
    )

    def _itens_fluxo2(df: pd.DataFrame, apenas_pagina: int | None = None) -> list[ItemCarimbo]:
        """Agrupa as linhas incluídas por código e monta uma etiqueta por
        ocorrência no catálogo: descrição da peça (opcional) + uma linha
        de preço por faixa de tamanho."""
        por_codigo: dict[str, dict] = {}
        for _, row in df.iterrows():
            if not row["Incluir"]:
                continue
            info = por_codigo.setdefault(
                row["Código"], {"descricao": str(row["Descrição"] or ""), "precos": []}
            )
            info["precos"].append((str(row["Tamanho"]), float(row["Novo preço (R$)"])))
        itens = []
        for codigo, info in por_codigo.items():
            linhas_etiqueta = linhas_da_etiqueta(
                info["descricao"] if perfil.descricao_na_etiqueta else "",
                info["precos"],
            )
            for oc in ocorrencias.get(codigo, []):
                if apenas_pagina is not None and oc.pagina != apenas_pagina:
                    continue
                itens.append(ItemCarimbo(
                    pagina=oc.pagina,
                    bbox=oc.bbox,
                    novo_valor=0.0,
                    tinha_rs=True,
                    linhas_etiqueta=linhas_etiqueta,
                ))
        return itens

    # ----- pré-visualização
    st.subheader("3️⃣ Pré-visualização")
    paginas_com_codigo = sorted({
        o.pagina + 1 for ocs in ocorrencias.values() for o in ocs
    })
    if not paginas_com_codigo:
        st.error(
            "Nenhum código da tabela foi localizado no catálogo. Se o catálogo "
            "é escaneado (imagem), o texto não pode ser lido automaticamente."
        )
        st.stop()

    pagina_escolhida = st.selectbox(
        "Página", paginas_com_codigo, format_func=lambda p: f"Página {p}"
    )
    itens_previa = _itens_fluxo2(tabela_ui, apenas_pagina=pagina_escolhida - 1)

    col_antes, col_depois = st.columns(2)
    with col_antes:
        st.markdown("**Original** (códigos localizados em vermelho)")
        destaques = [o.bbox for ocs in ocorrencias.values() for o in ocs
                     if o.pagina == pagina_escolhida - 1]
        st.image(imagem_pagina(pdf_bytes, pagina_escolhida - 1, destaques=destaques))
    with col_depois:
        st.markdown("**Precificado** (preço ao lado do código)")
        pdf_previa = _aplicar_logo(carimbar(
            pdf_bytes, itens_previa, modo="adicionar", cor_etiqueta=COR_ETIQUETA_RGB,
        ))
        st.image(imagem_pagina(pdf_previa, pagina_escolhida - 1))

    # ----- gerar
    st.subheader("4️⃣ Gerar o PDF precificado")
    if st.button("✅ Gerar PDF precificado", type="primary"):
        itens = _itens_fluxo2(tabela_ui)
        with st.spinner("Carimbando os preços..."):
            resultado = _aplicar_logo(carimbar(
                pdf_bytes, itens, modo="adicionar", cor_etiqueta=COR_ETIQUETA_RGB,
            ))
        st.session_state.resultado2 = resultado
        st.session_state.resultado2_nome = (
            arq_catalogo.name.replace(".pdf", "") + "_precificado.pdf"
        )
        st.success(f"Pronto! {len(itens)} carimbo(s) aplicado(s).")

    if "resultado2" in st.session_state:
        _botao_download(st.session_state.resultado2, st.session_state.resultado2_nome)
