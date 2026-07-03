# Precificador de Catálogos 👶

Automação para precificar catálogos PDF de roupas de bebê e infantil
(compra coletiva). Em vez de abrir o PDF e escrever o preço peça a peça,
o app calcula o preço de venda com o multiplicador da marca, mostra tudo
numa tabela para conferência/ajuste e gera um novo PDF já precificado.

Suporta os dois jeitos que as marcas mandam preço:

- **Preços impressos no próprio catálogo (1 arquivo)**: o app encontra
  os preços no PDF e escreve o preço de venda no lugar (mesma posição,
  mesma cor de fundo).
- **Catálogo + tabela de preços separada (2 arquivos)**: o catálogo tem
  as fotos com os códigos das peças e a tabela (Excel, CSV ou PDF) traz
  código → valor. O app localiza cada código no catálogo e carimba uma
  etiqueta com o preço de venda ao lado. No final mostra quais códigos
  da tabela não foram encontrados no catálogo, para conferência.

## Como usar

```bash
pip install -r requirements.txt
streamlit run app.py
```

Ou use os atalhos: `./iniciar.sh` (Linux/Mac) ou `iniciar.bat` (Windows).
O app abre no navegador (http://localhost:8501).

### Passo a passo na tela

1. Na barra lateral, escolha a **marca** (ou crie uma nova) e confira o
   multiplicador, o arredondamento e o modo de escrita. Clique em
   **Salvar perfil da marca** para lembrar dessas escolhas na próxima vez.
2. Escolha o fluxo no topo: **preços impressos no catálogo** ou
   **catálogo + tabela separada**.
3. Envie o **PDF do catálogo** (e a **tabela de preços**, no fluxo de
   2 arquivos — se for planilha, confirme qual coluna é o código e qual
   é o preço).
4. Confira a tabela: o novo preço já vem calculado. **Edite direto na
   tabela** os itens que fogem da regra. Itens com **alerta** merecem
   atenção (preço muito alto/baixo, código não encontrado etc.).
5. Veja a **pré-visualização** lado a lado (original × precificado).
6. Clique em **Gerar PDF precificado** e baixe o arquivo.

## Proteções contra erro

- **Página escaneada (imagem)**: o app avisa quais páginas não têm texto
  legível — os preços delas precisam ser conferidos manualmente.
- **Página sem preço detectado**: o app lista as páginas para conferência.
- **Falsos positivos**: por padrão só considera valores com `R$`
  (referências e medidas como `10,23` são ignoradas). Para catálogos sem o
  símbolo, desligue a opção na barra lateral.
- **Preços fora da faixa** (configurável por marca) são sinalizados na
  tabela.
- **Conferência cruzada no fluxo de 2 arquivos**: códigos da tabela que
  não existem no catálogo (e códigos repetidos com preços diferentes)
  são listados para revisão manual.
- **Preço de custo não vaza**: no modo "substituir", o preço original é
  removido de verdade do PDF (não apenas coberto) — copiar o texto do PDF
  final não revela o valor do catálogo.
- **Arredondamento sempre para cima**: a regra de arredondamento nunca
  reduz o preço calculado.

## Perfis por marca

Cada marca tem seu padrão de catálogo, então cada perfil guarda:
multiplicador, regra de arredondamento, modo de carimbo (substituir ou
adicionar ao lado), se exige `R$` e a faixa de preço esperada.
Os perfis ficam no arquivo `perfis.json` (criado ao salvar o primeiro).

## Limitações conhecidas

- **PDFs escaneados** (foto/imagem do catálogo, sem camada de texto) não
  são suportados — o app detecta e avisa, mas a precificação dessas
  páginas continua manual.
- Preços quebrados em duas linhas no PDF podem não ser detectados
  (aparece o aviso de "página sem preço").

## Testes

```bash
python3 -m pytest tests/
```

## Estrutura

```
app.py                    # interface web (Streamlit)
precificador/extracao.py  # encontra preços e códigos (com posição) no PDF
precificador/tabela.py    # lê a tabela de códigos e preços (Excel/CSV/PDF)
precificador/regras.py    # multiplicador, arredondamento, perfis de marca
precificador/carimbo.py   # gera o PDF final com os novos preços
tests/                    # testes dos dois fluxos
```
