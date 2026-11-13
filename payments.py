"""Simulator only: do not use real cards or connect a payment gateway."""
import time


class FakePaymentGateway:
    def __init__(self, should_approve=True, delay=0):
        self.should_approve = should_approve
        self.delay = delay
        self.calls = []

    def charge(self, amount, payment_token):
        time.sleep(self.delay)
        self.calls.append((amount, payment_token))
        return {'approved': self.should_approve, 'transaction_id': 'TEST-001' if self.should_approve else None}
