"""Models for the intentionally imperfect order-management application."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass
class Product:
    sku: str
    name: str
    price: Decimal
    stock: int


@dataclass
class CartLine:
    sku: str
    name: str
    unit_price: Decimal
    quantity: int


@dataclass
class OrderResult:
    order_id: int | None
    status: str
    total: Decimal
