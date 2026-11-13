import pytest
from decimal import Decimal
from models import Product, CartLine, OrderResult
from cart import ShoppingCart
from repository import StoreRepository
from checkout import CheckoutService


# --- Mock / In-Memory Repository & Gateway for Testing ---
class MockRepository:
    def __init__(self):
        self.products = {
            "SKU001": Product("SKU001", "Laptop", Decimal("1000.00"), 5),
            "SKU002": Product("SKU002", "Mouse", Decimal("25.00"), 10),
        }
        self.carts = {}
        self.orders = []

    def get_product(self, sku):
        return self.products.get(sku)

    def get_saved_cart(self, user_id):
        return self.carts.get(user_id, [])

    def save_cart(self, user_id, lines):
        self.carts[user_id] = [(line.sku, line.quantity) for line in lines]

    def update_stock(self, sku, quantity):
        if sku in self.products:
            p = self.products[sku]
            self.products[sku] = Product(p.sku, p.name, p.price, p.stock - quantity)

    def save_order(self, user_id, amount, status, request_id):
        order_id = len(self.orders) + 1
        self.orders.append(
            {"id": order_id, "user_id": user_id, "amount": amount, "status": status, "request_id": request_id})
        return order_id


class MockPaymentGateway:
    def __init__(self, should_succeed=True):
        self.should_succeed = should_succeed

    def charge(self, amount, token):
        if self.should_succeed:
            return {"approved": True}
        else:
            return {"approved": False}


@pytest.fixture
def repo():
    return MockRepository()


@pytest.fixture
def cart(repo):
    return ShoppingCart("user123", repo)


# --- Test Suite (12 Unit Tests) ---

def test_add_valid_item(cart):
    success = cart.add_item("SKU002", 2)
    assert success is True
    assert len(cart.lines) == 1
    assert cart.lines[0].quantity == 2


def test_add_invalid_quantity_raises_error(cart):
    with pytest.raises(ValueError):
        cart.add_item("SKU002", 0)
    with pytest.raises(ValueError):
        cart.add_item("SKU002", -3)


def test_remove_item_partial(cart):
    cart.add_item("SKU002", 5)
    cart.remove_item("SKU002", 2)
    assert cart.lines[0].quantity == 3


def test_remove_item_completely(cart):
    cart.add_item("SKU002", 2)
    cart.remove_item("SKU002", 2)
    assert len(cart.lines) == 0


def test_freeship_coupon_does_not_freeze_total(cart):
    cart.add_item("SKU002", 2)  # Subtotal: 50.00
    cart.apply_discount("FREESHIP")
    assert cart.free_shipping is True
    assert cart.total() == Decimal("50.00")

    # Add more items — total should update dynamically, not freeze
    cart.add_item("SKU002", 2)  # Subtotal: 100.00
    assert cart.total() == Decimal("100.00")


def test_percentage_coupon_welcome10(cart):
    cart.add_item("SKU002", 2)  # Subtotal: 50.00
    cart.apply_discount("WELCOME10")
    assert cart.total() == Decimal("45.00")  # 10% off 50


def test_flat_rate_coupon_save15(cart):
    cart.add_item("SKU001", 1)  # Subtotal: 1000.00
    cart.apply_discount("SAVE15")
    assert cart.total() == Decimal("985.00")  # 1000 - 15


def test_decimal_precision(cart):
    cart.add_item("SKU002", 3)  # 3 * 25.00 = 75.00
    assert isinstance(cart.subtotal(), Decimal)
    assert cart.subtotal() == Decimal("75.00")


def test_checkout_success_updates_stock_and_clears_cart(repo, cart):
    cart.add_item("SKU002", 2)
    gateway = MockPaymentGateway(should_succeed=True)
    service = CheckoutService(repo, gateway)

    result = service.checkout(cart, "tok_123", "req_abc")

    assert result.status == "paid"
    assert result.order_id is not None
    # Stock should be decremented from 10 to 8
    assert repo.products["SKU002"].stock == 8
    # Cart should be cleared on success
    assert len(cart.lines) == 0


def test_checkout_declined_preserves_cart_and_stock(repo, cart):
    cart.add_item("SKU002", 2)
    initial_stock = repo.products["SKU002"].stock

    gateway = MockPaymentGateway(should_succeed=False)
    service = CheckoutService(repo, gateway)

    result = service.checkout(cart, "tok_bad", "req_xyz")

    assert result.status == "declined"
    # Stock should NOT change on declined payment
    assert repo.products["SKU002"].stock == initial_stock
    # Cart should NOT be cleared so user doesn't lose items
    assert len(cart.lines) == 1


def test_empty_cart_checkout(repo, cart):
    gateway = MockPaymentGateway(should_succeed=True)
    service = CheckoutService(repo, gateway)

    result = service.checkout(cart, "tok_123", "req_empty")
    assert result.status == "empty"
    assert result.order_id is None


def test_idempotency_request_id_stored(repo, cart):
    cart.add_item("SKU002", 1)
    gateway = MockPaymentGateway(should_succeed=True)
    service = CheckoutService(repo, gateway)

    service.checkout(cart, "tok_123", "unique-request-id-999")

    # Verify request_id was recorded in the order table
    saved_order = repo.orders[0]
    assert saved_order["request_id"] == "unique-request-id-999"