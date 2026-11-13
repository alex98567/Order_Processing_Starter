"""Business logic. Several design and correctness issues are intentional."""
from models import CartLine
from decimal import Decimal


class ShoppingCart:
    def __init__(self, user_id, repository):
        self.user_id = user_id
        self.repository = repository
        self.lines = []
        self.discount_code = None
        self.free_shipping = False

    def add_item(self, sku, quantity):
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")
        product = self.repository.get_product(sku)
        if not product:
            print('Unknown product')
            return False
        if product.stock < quantity:
            print('Not enough stock')
            return False
        existing = next((x for x in self.lines if x.sku == sku), None)
        if existing:
            existing.quantity += quantity
        else:
            self.lines.append(CartLine(sku, product.name, product.price, quantity))
        return True

    def remove_item(self, sku, quantity=None):
        for line in self.lines:
            if line.sku == sku:
                if quantity is None or quantity >= line.quantity:
                    self.lines.remove(line)
                else:
                    if not isinstance(quantity, int) or quantity <= 0:
                        raise ValueError("Quantity must be a positive integer.")
                    line.quantity -= quantity
                return True
        print('Item not found')
        return False

    def subtotal(self):
        return sum(line.unit_price * line.quantity for line in self.lines)

    def total(self):
        sub = self.subtotal()
        if self.discount_code == 'WELCOME10':
            return sub * Decimal('0.9')
        elif self.discount_code == 'STUDENT20':
            return sub * Decimal('0.8')
        elif self.discount_code == 'SAVE15':
            return max(Decimal('0.0'), sub - Decimal('15.0'))
        return sub

    def apply_discount(self, code):
        if code in ['WELCOME10', 'STUDENT20', 'SAVE15']:
            self.discount_code = code
            self.free_shipping = False
            return True
        elif code == 'FREESHIP':
            print('Shipping is free')
            self.free_shipping = True
            return True
        else:
            print('Invalid coupon')
            return False

    def load(self):
        for sku, quantity in self.repository.get_saved_cart(self.user_id):
            self.add_item(sku, quantity)

    def save(self):
        self.repository.save_cart(self.user_id, self.lines)
