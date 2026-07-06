# Contexto do repositório

Automação para o grupo de compra coletiva de roupas de bebê/infantil
(vendas via WhatsApp). O trabalho está dividido em **dois projetos que
evoluem em paralelo** — mudanças em um não devem quebrar o outro.

## Projeto 1 — `precificador_catalogo/` (precificação, Python)

App web local (Streamlit + PyMuPDF) que precifica catálogos PDF das marcas.
Status: funcional, validado com duas marcas reais (UP BABY e tabela com
blocos lado a lado).

- Fluxo 1: preços impressos no catálogo → detecta e substitui (redação real).
- Fluxo 2: catálogo + tabela separada (Excel/CSV/PDF) → localiza códigos e
  carimba etiqueta com preço(s) por faixa de tamanho, com desvio de colisão.
- Perfis por marca em `perfis.json` (multiplicador, arredondamento, cor da
  etiqueta, logo). Logo salvo em `logos/` (ambos fora do git).
- Testes: `python3 -m pytest precificador_catalogo/tests/`.

## Projeto 2 — `catalogo_web/` (catálogo web interativo, funcional)

Página web gerada a partir das precificações do Projeto 1: o cliente
navega no catálogo, toca no ➕ da peça, escolhe o tamanho, monta a
"sacolinha" e envia o pedido pronto pelo WhatsApp da vendedora (link
`wa.me` com refs, tamanhos, preços e total). É a "Opção B" do brainstorm.

- `catalogo_web/gerador.py` monta um zip (index.html autocontido +
  paginas/*.jpg) a partir dos dados do Projeto 1; `template.html` é a
  página (vanilla JS, mobile-first, sem dependências externas).
- Integração: seção "5️⃣ Catálogo web interativo" no fluxo 2 do app do
  Projeto 1 (import opcional — se `catalogo_web/` faltar, o app segue).
- Publicação: usuária arrasta a pasta descompactada em
  https://app.netlify.com/drop e manda o link nos grupos.
- `noindex` + link não listado; sacolinha em localStorage.
- Nunca expor o preço de custo do catálogo — somente o preço de venda.
- Testes: `python3 -m pytest catalogo_web/tests/`.

## Observações gerais

- Idioma do produto e da documentação: português (pt-BR).
- Usuária final não é técnica: priorizar simplicidade de uso e redução de
  erro (alertas, conferência antes de gerar).
- `precificacao_if/` é um projeto antigo não relacionado — não mexer.
