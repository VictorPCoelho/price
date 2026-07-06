# Catálogo Web Interativo 🛍️ (Projeto 2)

Transforma o catálogo precificado (Projeto 1) numa **página web** em que o
cliente:

1. Navega pelas páginas do catálogo (com os preços de venda já carimbados);
2. Toca no **➕** da peça que gostou;
3. Escolhe o tamanho e adiciona à **sacolinha**;
4. Aperta **"Enviar pedido pelo WhatsApp"** → abre o WhatsApp da vendedora
   com a mensagem pronta: referências, tamanhos, preços e total.

## Como gerar

Não se usa esta pasta diretamente: no app do Projeto 1
(`precificador_catalogo`), fluxo **"Catálogo + tabela de preços separada"**,
após conferir os preços, use a seção **"5️⃣ Catálogo web interativo"**:
informe o WhatsApp (com DDD) e o nome do catálogo, clique em **Gerar
catálogo web** e baixe o `.zip`.

## Como publicar (grátis)

1. Descompacte o `.zip` baixado.
2. Acesse **https://app.netlify.com/drop** (conta gratuita).
3. **Arraste a pasta inteira** para a página. Em segundos sai um link
   (ex.: `https://algumacoisa.netlify.app`).
4. Mande esse link nos grupos de WhatsApp. Só acessa quem tiver o link.

Alternativa: GitHub Pages (subir os arquivos num repositório e ativar
Settings → Pages).

## O que tem dentro do zip

```
index.html            # a página completa (funciona offline, sem serviços externos)
paginas/pagina-NN.jpg # as páginas do catálogo em imagem
LEIA-ME.txt           # instruções de publicação resumidas
```

## Decisões de segurança

- Somente **preços de venda** entram no site — o preço de custo do
  catálogo da marca nunca sai do Projeto 1.
- `<meta name="robots" content="noindex">`: o link não aparece em
  buscadores; funciona como link não listado.
- A sacolinha fica no `localStorage` do celular do cliente (nada é
  enviado a servidor nenhum — o pedido vai direto pro WhatsApp).

## Testes

```bash
python3 -m pytest catalogo_web/tests/
```
