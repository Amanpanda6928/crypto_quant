"""
Payment Processing Module for FastAPI Backend
"""

import os
import stripe
from typing import Dict, Optional

# Stripe configuration
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class PaymentService:
    """Payment service for subscription management"""

    def __init__(self):
        self.stripe = stripe

    def create_customer(self, email: str, name: str) -> str:
        """Create Stripe customer"""
        customer = self.stripe.Customer.create(
            email=email,
            name=name
        )
        return customer.id

    def create_subscription(self, customer_id: str, price_id: str) -> Dict:
        """Create subscription"""
        subscription = self.stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"]
        )
        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }

    def cancel_subscription(self, subscription_id: str) -> bool:
        """Cancel subscription"""
        try:
            self.stripe.Subscription.delete(subscription_id)
            return True
        except Exception:
            return False

    def get_customer(self, customer_id: str) -> Optional[Dict]:
        """Get customer details"""
        try:
            customer = self.stripe.Customer.retrieve(customer_id)
            return {
                "id": customer.id,
                "email": customer.email,
                "name": customer.name
            }
        except Exception:
            return None