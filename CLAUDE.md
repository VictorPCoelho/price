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

## Projeto 2 — catálogo web interativo (upgrade, a iniciar)

Página web gerada a partir das precificações do Projeto 1: o cliente
navega no catálogo, toca na peça que gostou, monta uma "sacolinha" e envia
o pedido pronto pelo WhatsApp da vendedora (link `wa.me` com refs,
tamanhos, preços e total). Corresponde à "Opção B" do brainstorm feito na
sessão de criação.

- Diretório previsto: `catalogo_web/` (separado do Projeto 1).
- Insumo: dados que o Projeto 1 já produz (código, página, posição/bbox,
  descrição, preços por tamanho, imagens das páginas).
- Hospedagem alvo: estática e gratuita (GitHub Pages/Netlify), link não
  listado.
- Nunca expor o preço de custo do catálogo — somente o preço de venda.

## Observações gerais

- Idioma do produto e da documentação: português (pt-BR).
- Usuária final não é técnica: priorizar simplicidade de uso e redução de
  erro (alertas, conferência antes de gerar).
- `precificacao_if/` é um projeto antigo não relacionado — não mexer.
