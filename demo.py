"""Run using synthetic data only. Not executed on import."""
from repository import StoreRepository
from cart import ShoppingCart
from payments import FakePaymentGateway
from checkout import CheckoutService
from setup_db import initialize


def main():
    initialize()
    repo = StoreRepository()
    cart = ShoppingCart('demo-user', repo)
    cart.add_item('MOU-01', 2)
    cart.apply_discount('WELCOME10')
    result = CheckoutService(repo, FakePaymentGateway()).checkout(cart, 'TEST_TOKEN', 'demo-request-1')
    print('Order result:', result)


if __name__ == '__main__':
    main()
