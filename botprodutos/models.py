"""Modelo de dados comum a todas as fontes de ofertas."""

from dataclasses import dataclass, field


@dataclass
class Deal:
    id: str            # identificador único (fonte + id externo), usado no dedupe
    title: str
    url: str           # link da oferta (loja ou página da comunidade)
    source: str        # "promobit", "pelando", "mercadolivre"...
    price: float | None = None
    old_price: float | None = None
    store: str | None = None
    image: str | None = None
    coupon: str | None = None
    hot_score: int | None = None  # temperatura/likes na comunidade de origem

    @property
    def discount_pct(self) -> float | None:
        if self.price and self.old_price and self.old_price > self.price:
            return round(100 * (1 - self.price / self.old_price), 1)
        return None
