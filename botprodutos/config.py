"""Filtros e limites do bot — ajuste aqui o comportamento das postagens."""

# Desconto mínimo (%) para uma oferta com preço "de/por" ser postada.
# Ofertas sem old_price conhecido passam pelo filtro de hot_score abaixo.
MIN_DISCOUNT_PCT = 30

# Temperatura mínima na comunidade de origem (Promobit/Pelando) para
# postar uma oferta que não tem desconto calculável.
MIN_HOT_SCORE = 100

# Acima deste desconto a oferta é marcada como possível BUG DE PREÇO,
# com aviso de que o pedido pode ser cancelado pela loja.
BUG_DISCOUNT_PCT = 70

# Máximo de posts por execução, para não inundar o canal.
MAX_POSTS_PER_RUN = 5

# Se não-vazio, só posta ofertas cujo título contém uma destas palavras
# (case-insensitive). Vazio = posta tudo que passar nos filtros acima.
KEYWORDS: list[str] = []

# Palavras que bloqueiam a oferta mesmo que passe nos outros filtros.
BLOCKED_WORDS: list[str] = []

# Quantos IDs de ofertas já postadas manter no data/seen.json.
SEEN_MAX_IDS = 2000
