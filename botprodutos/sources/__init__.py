"""Registro das fontes de ofertas. Para adicionar uma fonte nova,
crie um módulo com fetch() -> list[Deal] e registre aqui."""

from sources import mercadolivre, pelando, promobit

SOURCES = {
    "promobit": promobit.fetch,
    "pelando": pelando.fetch,
    "mercadolivre": mercadolivre.fetch,
}
