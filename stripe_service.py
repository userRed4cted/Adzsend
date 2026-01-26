# ==============================================
# STRIPE SERVICE - Payment Integration
# ==============================================
# Handles Stripe checkout sessions and webhooks
# ==============================================

import os
import stripe

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Price ID mapping (plan_id -> {monthly: price_id, yearly: price_id})
STRIPE_PRICE_IDS = {
    'plan_1': {
        'monthly': 'price_1SplVrRxJGN3c6Umt3NCrZ2P',
        'yearly': 'price_1SplVrRxJGN3c6UmF6XrmcK9'
    },
    'plan_2': {
        'monthly': 'price_1StiaLRxJGN3c6UmMDXM0jVQ',
        'yearly': 'price_1SticaRxJGN3c6UmslUUC42q'
    },
    'team_plan_1': {
        'monthly': 'price_1SlpsdRxJGN3c6Umi8xxCU3u',
        'yearly': 'price_1SlpsdRxJGN3c6UmCHE7kDjN'
    },
    'team_plan_2': {
        'monthly': 'price_1Slpx4RxJGN3c6UmiQTSnoYm',
        'yearly': 'price_1Slpx4RxJGN3c6UmeiVnwxVH'
    }
}


def get_or_create_customer(user_id, email):
    """Get existing Stripe customer or create new one."""
    from database import get_user_by_id, update_user_stripe_customer_id

    user = get_user_by_id(user_id)
    if not user:
        return None

    # Check if user already has a Stripe customer ID
    stripe_customer_id = user.get('stripe_customer_id')
    if stripe_customer_id:
        try:
            # Verify customer still exists in Stripe
            customer = stripe.Customer.retrieve(stripe_customer_id)
            if not customer.get('deleted'):
                return stripe_customer_id
        except stripe.error.InvalidRequestError:
            # Customer doesn't exist, create new one
            pass

    # Create new customer
    try:
        customer = stripe.Customer.create(
            email=email,
            metadata={'user_id': str(user_id)}
        )
        # Save customer ID to database
        update_user_stripe_customer_id(user_id, customer.id)
        return customer.id
    except Exception:
        return None


def create_checkout_session(user_id, email, plan_id, billing_period, success_url, cancel_url):
    """Create a Stripe Checkout session for subscription."""
    if not STRIPE_SECRET_KEY:
        return None, "Stripe not configured"

    # Validate plan
    if plan_id not in STRIPE_PRICE_IDS:
        return None, "Invalid plan"

    if billing_period not in ['monthly', 'yearly']:
        return None, "Invalid billing period"

    price_id = STRIPE_PRICE_IDS[plan_id][billing_period]

    # Get or create customer
    customer_id = get_or_create_customer(user_id, email)
    if not customer_id:
        return None, "Failed to create customer"

    try:
        session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1
            }],
            mode='subscription',
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'user_id': str(user_id),
                'plan_id': plan_id,
                'billing_period': billing_period
            },
            subscription_data={
                'metadata': {
                    'user_id': str(user_id),
                    'plan_id': plan_id,
                    'billing_period': billing_period
                }
            }
        )
        return session, None
    except stripe.error.StripeError as e:
        return None, str(e)


def create_billing_portal_session(user_id, return_url):
    """Create a Stripe billing portal session for managing subscription."""
    if not STRIPE_SECRET_KEY:
        return None, "Stripe not configured"

    from database import get_user_by_id

    user = get_user_by_id(user_id)
    if not user:
        return None, "User not found"

    stripe_customer_id = user.get('stripe_customer_id')
    if not stripe_customer_id:
        return None, "No billing account found"

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url
        )
        return session, None
    except stripe.error.StripeError as e:
        return None, str(e)


def verify_webhook_signature(payload, sig_header):
    """Verify Stripe webhook signature."""
    if not STRIPE_WEBHOOK_SECRET:
        return None, "Webhook secret not configured"

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
        return event, None
    except ValueError as e:
        return None, f"Invalid payload: {e}"
    except stripe.error.SignatureVerificationError as e:
        return None, f"Invalid signature: {e}"


def handle_checkout_completed(session):
    """Handle successful checkout - activate subscription."""
    from database import set_subscription, get_user_by_id
    from config.plans import SUBSCRIPTION_PLANS, BUSINESS_PLANS

    user_id = session.get('metadata', {}).get('user_id')
    plan_id = session.get('metadata', {}).get('plan_id')
    billing_period = session.get('metadata', {}).get('billing_period')
    subscription_id = session.get('subscription')

    if not all([user_id, plan_id, billing_period]):
        return False

    user_id = int(user_id)

    # Determine plan type and get config
    if plan_id.startswith('team_'):
        plan_type = 'business'
        plan_config = BUSINESS_PLANS.get(plan_id)
    else:
        plan_type = 'subscription'
        plan_config = SUBSCRIPTION_PLANS.get(plan_id)

    if not plan_config:
        return False

    # Store subscription ID
    from database import update_user_stripe_subscription_id
    update_user_stripe_subscription_id(user_id, subscription_id)

    # Activate subscription
    success = set_subscription(user_id, plan_type, plan_id, plan_config, billing_period)
    if success:
        # If it's a business plan, create a business team
        if plan_type == 'business':
            from database import create_business_team, get_active_subscription, auto_deny_pending_invitations
            subscription = get_active_subscription(user_id)
            if subscription:
                max_members = plan_config.get('max_members', 3)
                create_business_team(user_id, subscription['id'], max_members)
                # Auto-deny any pending team invitations since user is now a business owner
                auto_deny_pending_invitations(user_id)

    return success


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation - downgrade to free."""
    from database import cancel_subscription, get_user_by_stripe_customer_id

    customer_id = subscription.get('customer')
    if not customer_id:
        return False

    user = get_user_by_stripe_customer_id(customer_id)
    if not user:
        return False

    # Cancel subscription (downgrades to free)
    success = cancel_subscription(user['id'])
    return success


def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment - extend subscription if renewal."""
    # This handles subscription renewals
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return True  # Not a subscription invoice

    # For renewals, Stripe automatically extends the subscription
    # Our subscription dates are calculated from creation, so we need to update end_date
    from database import extend_subscription_by_stripe_subscription_id

    billing_reason = invoice.get('billing_reason')
    if billing_reason == 'subscription_cycle':
        # This is a renewal
        extend_subscription_by_stripe_subscription_id(subscription_id)

    return True


def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment - cancel subscription immediately (no retries)."""
    from database import cancel_subscription, get_user_by_stripe_customer_id

    subscription_id = invoice.get('subscription')
    customer_id = invoice.get('customer')

    if not subscription_id:
        return True  # Not a subscription invoice

    # Get user by customer ID
    user = get_user_by_stripe_customer_id(customer_id)
    if not user:
        return False

    # Cancel the subscription in Stripe (this will trigger customer.subscription.deleted webhook)
    try:
        stripe.Subscription.cancel(subscription_id)
    except stripe.error.StripeError:
        # Still cancel locally even if Stripe API fails
        cancel_subscription(user['id'])

    return True


def get_customer_invoices(user_id, limit=10):
    """Get invoices for a user from Stripe."""
    if not STRIPE_SECRET_KEY:
        return [], "Stripe not configured"

    from database import get_user_by_id

    user = get_user_by_id(user_id)
    if not user:
        return [], "User not found"

    stripe_customer_id = user.get('stripe_customer_id')
    if not stripe_customer_id:
        return [], None  # No error, just no invoices

    try:
        invoices = stripe.Invoice.list(
            customer=stripe_customer_id,
            limit=limit
        )

        invoice_list = []
        for inv in invoices.data:
            # Only include paid invoices
            if inv.status == 'paid':
                invoice_list.append({
                    'id': inv.id,
                    'date': inv.created,  # Unix timestamp
                    'amount': inv.amount_paid / 100,  # Convert cents to dollars
                    'status': inv.status,
                    'invoice_url': inv.hosted_invoice_url,  # URL to view invoice
                    'invoice_pdf': inv.invoice_pdf,  # URL to download PDF
                    'description': inv.lines.data[0].description if inv.lines.data else 'Subscription'
                })

        return invoice_list, None
    except stripe.error.StripeError as e:
        return [], str(e)
