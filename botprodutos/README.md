# 🤖 Bot de Ofertas

Bot que monitora **Promobit** e **Pelando** a cada 10 minutos, filtra as melhores promoções (e possíveis bugs de preço) e posta automaticamente num **canal do Telegram** — rodando de graça no GitHub Actions, sem servidor.

Quando suas contas de afiliado forem aprovadas, o bot passa a trocar os links automaticamente (basta cadastrar um secret — nenhuma mudança de código).

---

## 🚀 Configuração (uma vez só, ~15 minutos)

### 1. Criar o bot no Telegram

1. No Telegram, procure **@BotFather** e mande `/newbot`.
2. Escolha um nome (ex.: `Ofertas do Victor`) e um username terminado em `bot` (ex.: `ofertasvictor_bot`).
3. O BotFather responde com um **token** parecido com `123456789:AAHdqTcvbXYZ...`. **Copie e guarde** — é o `TELEGRAM_BOT_TOKEN`.

### 2. Criar o canal e adicionar o bot

1. No Telegram: **Novo canal** → dê um nome (ex.: `Promoções do Victor`) → tipo **Público** → escolha um link (ex.: `t.me/promocoesdovictor`).
2. Abra o canal → **Administradores** → **Adicionar administrador** → procure o username do seu bot → adicione com permissão de **postar mensagens**.

### 3. Descobrir o CHAT_ID

Para canal **público** é fácil: o chat_id é `@` + o link do canal.
Exemplo: canal `t.me/promocoesdovictor` → `TELEGRAM_CHAT_ID` = `@promocoesdovictor`

<details>
<summary>Se o canal for privado, clique aqui</summary>

1. Poste qualquer mensagem no canal.
2. Encaminhe essa mensagem para o bot **@userinfobot** — ele mostra o id do canal (um número negativo tipo `-1001234567890`). Esse número é o `TELEGRAM_CHAT_ID`.
</details>

### 4. Cadastrar os secrets no GitHub

1. Nesta página do repositório, vá em **Settings** (aba lá em cima) → menu lateral **Secrets and variables** → **Actions**.
2. Clique em **New repository secret** e crie:

| Name | Value |
|---|---|
| `TELEGRAM_BOT_TOKEN` | o token do BotFather (passo 1) |
| `TELEGRAM_CHAT_ID` | `@seucanal` ou o número (passo 3) |

### 5. Rodar o primeiro teste

1. Aba **Actions** do repositório → workflow **Bot de Ofertas** (menu à esquerda).
2. Se aparecer um aviso pedindo para habilitar workflows, clique em **Enable**.
3. Clique em **Run workflow** → **Run workflow** (botão verde).
4. Em ~1 minuto o run aparece na lista; clique nele para ver os logs. Se tudo deu certo, as primeiras ofertas chegam no seu canal. 🎉

A partir daí o bot roda **sozinho a cada 10 minutos**.

> ⚠️ O GitHub desativa o agendamento se o repositório ficar 60 dias sem nenhum commit. Como o bot commita o histórico de posts a cada rodada, isso não deve acontecer — mas se você pausar o bot por meses, é só rodar manualmente de novo.

---

## ⚙️ Ajustar filtros

Edite o arquivo [`config.py`](config.py):

- `MIN_DISCOUNT_PCT` — desconto mínimo para postar (padrão 30%).
- `MIN_HOT_SCORE` — temperatura mínima no Promobit/Pelando quando não há desconto calculável (padrão 100°).
- `BUG_DISCOUNT_PCT` — acima disso a oferta é marcada como 🚨 possível bug de preço (padrão 70%).
- `MAX_POSTS_PER_RUN` — máximo de posts a cada 10 min (padrão 5).
- `KEYWORDS` — ex.: `["notebook", "ssd", "iphone"]` para postar só esses assuntos.
- `BLOCKED_WORDS` — palavras que bloqueiam a postagem.

## 💰 Ativar afiliados (quando suas contas forem aprovadas)

| Programa | O que fazer |
|---|---|
| **Amazon Associates** | Cadastre o secret `AMAZON_TAG` com seu tag (ex.: `victor-20`). Links da Amazon passam a sair com seu código automaticamente. |
| **Mercado Livre** | Fase 2 — veja instruções em [`sources/mercadolivre.py`](sources/mercadolivre.py). |
| Outros (Awin, Shopee...) | Adicione um converter em [`affiliates.py`](affiliates.py) seguindo o exemplo da Amazon. |

> Dica: cadastre-se nos programas com o link do seu canal do Telegram como "site" — é aceito pela maioria.

## 🧪 Rodar localmente (opcional)

```bash
pip install -r requirements.txt
python main.py --dry-run            # mostra o que seria postado, sem postar
python main.py --source promobit    # testa só uma fonte
python -m unittest discover tests   # testes offline
```

## 📁 Como funciona

```
sources/promobit.py   busca ofertas (RSS → fallback scraping)
sources/pelando.py    idem
main.py               filtra (config.py), deduplica (data/seen.json) e posta
telegram_poster.py    formata e envia para o canal
affiliates.py         troca links por links de afiliado (se configurado)
.github/workflows/ofertas.yml   agenda tudo a cada 10 min no GitHub Actions
```

## ⚖️ Avisos

- Ofertas marcadas como **bug de preço** podem ser canceladas pela loja — o bot já posta com esse aviso.
- Respeite os termos dos programas de afiliados (nada de spam ou cloaking).
- Este bot posta no **Telegram**. Automação não-oficial no WhatsApp viola os termos de uso e derruba o número.
