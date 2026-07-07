"""Testes offline (fixtures embutidas, sem rede)."""

import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import main
from affiliates import rewrite_link
from models import Deal
from sources import pelando, promobit
from telegram_poster import format_caption

RSS_FIXTURE = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>Promobit</title>
<item>
  <title>Notebook Gamer Acer Nitro 5 por R$ 3.499,90</title>
  <link>https://www.promobit.com.br/oferta/notebook-acer-123</link>
  <guid>promo-123</guid>
</item>
</channel></rss>"""

NEXT_DATA_FIXTURE = {
    "props": {
        "pageProps": {
            "offers": [
                {
                    "id": 987,
                    "title": "SSD Kingston 1TB NV2",
                    "slug": "ssd-kingston-987",
                    "price": 299.9,
                    "old_price": 499.9,
                    "store": {"name": "Amazon"},
                    "image": "https://img.example/ssd.jpg",
                    "temperature": 250,
                }
            ]
        }
    }
}


class FakeResp:
    def __init__(self, content):
        self.content = content
        self.text = content.decode() if isinstance(content, bytes) else content


class TestPromobit(unittest.TestCase):
    def test_rss_parsing(self):
        with mock.patch.object(promobit, "get", return_value=FakeResp(RSS_FIXTURE)):
            deals = promobit._from_rss()
        self.assertEqual(len(deals), 1)
        d = deals[0]
        self.assertEqual(d.id, "promobit:promo-123")
        self.assertEqual(d.price, 3499.90)
        self.assertEqual(d.source, "promobit")

    def test_next_data_extraction(self):
        html = (
            "<html><body><script id=\"__NEXT_DATA__\" type=\"application/json\">"
            + json.dumps(NEXT_DATA_FIXTURE)
            + "</script></body></html>"
        )
        with mock.patch.object(promobit, "get", return_value=FakeResp(html.encode())):
            deals = promobit._from_page()
        self.assertEqual(len(deals), 1)
        d = deals[0]
        self.assertEqual(d.title, "SSD Kingston 1TB NV2")
        self.assertEqual(d.old_price, 499.9)
        self.assertEqual(d.store, "Amazon")
        self.assertEqual(d.discount_pct, 40.0)

    def test_parse_price_formats(self):
        self.assertEqual(promobit._parse_price("por R$ 1.234,56"), 1234.56)
        self.assertEqual(promobit._parse_price("R$ 99"), 99.0)
        self.assertIsNone(promobit._parse_price("sem preço"))


class TestPelando(unittest.TestCase):
    def test_next_data_extraction(self):
        data = {"deals": [{"id": 55, "title": "Mouse Logitech", "price": 89.9, "temperature": 300, "slug": "mouse-55"}]}
        html = (
            "<html><body><script id=\"__NEXT_DATA__\" type=\"application/json\">"
            + json.dumps(data)
            + "</script></body></html>"
        )
        with mock.patch.object(pelando, "get", return_value=FakeResp(html.encode())):
            deals = pelando._from_page()
        self.assertEqual(len(deals), 1)
        self.assertEqual(deals[0].id, "pelando:55")
        self.assertEqual(deals[0].hot_score, 300)


class TestFilters(unittest.TestCase):
    def _deal(self, **kw):
        base = dict(id="x:1", title="Produto Teste", url="https://loja.com/p", source="x")
        base.update(kw)
        return Deal(**base)

    def test_discount_filter(self):
        self.assertTrue(main.passes_filters(self._deal(price=50, old_price=100)))
        self.assertFalse(main.passes_filters(self._deal(price=90, old_price=100)))

    def test_hot_score_fallback(self):
        self.assertTrue(main.passes_filters(self._deal(hot_score=config.MIN_HOT_SCORE + 1)))
        self.assertFalse(main.passes_filters(self._deal(hot_score=1)))
        self.assertFalse(main.passes_filters(self._deal()))

    def test_blocked_words(self):
        with mock.patch.object(config, "BLOCKED_WORDS", ["vape"]):
            self.assertFalse(main.passes_filters(self._deal(title="Vape XYZ", price=10, old_price=100)))


class TestCaptionAndAffiliates(unittest.TestCase):
    def test_caption_bug_warning(self):
        d = Deal(id="x:1", title="TV 50\"", url="https://loja.com/tv", source="x", price=100, old_price=1000)
        cap = format_caption(d)
        self.assertIn("BUG DE PREÇO", cap)
        self.assertIn("90% OFF", cap)

    def test_caption_normal(self):
        d = Deal(id="x:2", title="Fone <b>", url="https://loja.com/f", source="x", price=70, old_price=100)
        cap = format_caption(d)
        self.assertNotIn("BUG DE PREÇO", cap)
        self.assertIn("&lt;b&gt;", cap)  # HTML escapado

    def test_affiliate_noop_without_env(self):
        d = Deal(id="x:3", title="t", url="https://www.amazon.com.br/dp/B0ABC", source="x")
        os.environ.pop("AMAZON_TAG", None)
        self.assertEqual(rewrite_link(d), d.url)

    def test_affiliate_amazon_tag(self):
        d = Deal(id="x:4", title="t", url="https://www.amazon.com.br/dp/B0ABC", source="x")
        with mock.patch.dict(os.environ, {"AMAZON_TAG": "meutag-20"}):
            self.assertIn("tag=meutag-20", rewrite_link(d))


if __name__ == "__main__":
    unittest.main()
