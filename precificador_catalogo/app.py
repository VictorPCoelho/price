"""Precificador de Catálogos — app web para precificar catálogos PDF de roupas.

Fluxo: enviar o PDF → conferir os preços detectados → ajustar o que precisar
→ baixar o PDF já precificado.

Para rodar:  streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from precificador.carimbo import ItemCarimbo, carimbar, imagem_pagina
from precificador.extracao import extrair_precos
from precificador.regras import (
    ARREDONDAMENTOS,
    MODOS_CARIMBO,
    PerfilMarca,
    RepositorioPerfis,
    calcular_preco,
    formatar_brl,
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
)
perfil.exigir_rs = st.sidebar.toggle(
    "Considerar apenas valores com R$",
    value=perfil.exigir_rs,
    help="Mais seguro. Desligue apenas se o catálogo mostra os preços sem o "
    "símbolo R$ (aí números como 99,90 também serão detectados).",
)
with st.sidebar.expander("Limites para alerta"):
    perfil.valor_minimo = st.number_input(
        "Alertar se preço original abaixo de (R$)", value=float(perfil.valor_minimo), step=1.0
    )
    perfil.valor_maximo = st.number_input(
        "Alertar se preço original acima de (R$)", value=float(perfil.valor_maximo), step=10.0
    )

if st.sidebar.button("💾 Salvar perfil da marca", use_container_width=True):
    if not perfil.nome or perfil.nome == "Nova marca":
        st.sidebar.error("Dê um nome para a marca antes de salvar.")
    else:
        perfis[perfil.nome] = perfil
        repo.salvar(perfis)
        st.sidebar.success(f"Perfil “{perfil.nome}” salvo.")

# ---------------------------------------------------------------- Upload
st.title("Precificador de Catálogos")
st.caption(
    "1️⃣ Envie o PDF do catálogo · 2️⃣ Confira os preços detectados · "
    "3️⃣ Ajuste o que precisar · 4️⃣ Baixe o PDF precificado"
)

arquivo = st.file_uploader("PDF do catálogo", type=["pdf"])
if arquivo is None:
    st.info("Envie um catálogo em PDF para começar.")
    st.stop()

pdf_bytes = arquivo.getvalue()

# Re-extrai quando muda o arquivo ou a config de extração.
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
        "valores com R$” na barra lateral."
    )
    st.stop()

# ---------------------------------------------------------------- Tabela de revisão
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
    disabled=False,
    num_rows="fixed",
)

# ---------------------------------------------------------------- Pré-visualização
st.subheader("3️⃣ Pré-visualização")
paginas_disponiveis = sorted(tabela["Página"].unique())
pagina_escolhida = st.selectbox(
    "Página", paginas_disponiveis,
    format_func=lambda p: f"Página {p}",
)

itens_da_pagina = [
    ItemCarimbo(
        pagina=precos[int(row["id"])].pagina,
        bbox=precos[int(row["id"])].bbox,
        novo_valor=float(row["Novo preço (R$)"]),
        tinha_rs=precos[int(row["id"])].tinha_rs,
    )
    for _, row in tabela.iterrows()
    if row["Incluir"] and row["Página"] == pagina_escolhida
]

col_antes, col_depois = st.columns(2)
with col_antes:
    st.markdown("**Original** (preços detectados em vermelho)")
    destaques = [precos[int(r["id"])].bbox for _, r in tabela.iterrows()
                 if r["Página"] == pagina_escolhida]
    st.image(imagem_pagina(pdf_bytes, pagina_escolhida - 1, destaques=destaques))
with col_depois:
    st.markdown("**Precificado**")
    pdf_previa = carimbar(pdf_bytes, itens_da_pagina, modo=perfil.modo_carimbo)
    st.image(imagem_pagina(pdf_previa, pagina_escolhida - 1))

# ---------------------------------------------------------------- Gerar PDF
st.subheader("4️⃣ Gerar o PDF precificado")

if st.button("✅ Gerar PDF precificado", type="primary"):
    itens = [
        ItemCarimbo(
            pagina=precos[int(row["id"])].pagina,
            bbox=precos[int(row["id"])].bbox,
            novo_valor=float(row["Novo preço (R$)"]),
            tinha_rs=precos[int(row["id"])].tinha_rs,
        )
        for _, row in tabela.iterrows()
        if row["Incluir"]
    ]
    with st.spinner("Carimbando os preços..."):
        resultado = carimbar(pdf_bytes, itens, modo=perfil.modo_carimbo)
    st.session_state.resultado = resultado
    st.session_state.resultado_nome = arquivo.name.replace(".pdf", "") + "_precificado.pdf"
    total = sum(i.novo_valor for i in itens)
    st.success(
        f"Pronto! {len(itens)} preço(s) carimbado(s). "
        f"Soma dos novos preços: {formatar_brl(total)}."
    )

if "resultado" in st.session_state:
    st.download_button(
        "⬇️ Baixar PDF precificado",
        data=st.session_state.resultado,
        file_name=st.session_state.resultado_nome,
        mime="application/pdf",
        type="primary",
    )
