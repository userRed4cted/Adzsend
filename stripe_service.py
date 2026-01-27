# ==============================================
# STRIPE SERVICE - Payment Integration
# ==============================================
# Handles Stripe checkout sessions and webhooks
# ==============================================

import os
import logging
import time
import stripe

# Set up logging for webhook debugging (WARNING level for production)
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# Stripe configuration
# Uses restricted API key with permissions: Customers (Write), Checkout Sessions (Write),
# Subscriptions (Write), Customer Portal (Write), Invoices (Read)
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET', '')

# Development mode - set to True to use test price IDs, False for live
# Can also be controlled via STRIPE_TEST_MODE env variable
STRIPE_TEST_MODE = os.getenv('STRIPE_TEST_MODE', 'false').lower() == 'true'

# Initialize Stripe
stripe.api_key = STRIPE_SECRET_KEY

# Live Price IDs (production)
LIVE_PRICE_IDS = {
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

# Test Price IDs (development)
TEST_PRICE_IDS = {
    'plan_1': {  # Pro
        'monthly': 'price_1Stvp0RxJGN3c6UmDsEHwg9x',
        'yearly': 'price_1StvpmRxJGN3c6Umb8sBJdal'
    },
    'plan_2': {  # Max
        'monthly': 'price_1StvqGRxJGN3c6Umrpp353Gd',
        'yearly': 'price_1StvqdRxJGN3c6UmikRq1XuS'
    },
    'team_plan_1': {  # Startup
        'monthly': 'price_1StvtQRxJGN3c6UmnkbcTcv8',
        'yearly': 'price_1StvthRxJGN3c6UmAuRP9lgF'
    },
    'team_plan_2': {  # Premium
        'monthly': 'price_1StvsBRxJGN3c6Um8bzhO271',
        'yearly': 'price_1StvsdRxJGN3c6Um63TFEHda'
    }
}

# Select price IDs based on mode
STRIPE_PRICE_IDS = TEST_PRICE_IDS if STRIPE_TEST_MODE else LIVE_PRICE_IDS

# Customer Portal URLs (static fallback when dynamic session creation fails)
LIVE_PORTAL_URL = 'https://billing.stripe.com/p/login/fZu8wRfFA1EW7kc00'
TEST_PORTAL_URL = 'https://billing.stripe.com/p/login/test_fZu8wRfFA1EW7sxbII7kc00'

# Select portal URL based on mode
STRIPE_PORTAL_URL = TEST_PORTAL_URL if STRIPE_TEST_MODE else LIVE_PORTAL_URL


def get_portal_url():
    """Get the appropriate customer portal URL based on test/live mode."""
    return STRIPE_PORTAL_URL


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
    """Create a Stripe Checkout session for NEW subscription (user has no active subscription).

    For users with existing subscriptions, use handle_plan_change() instead.
    """
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
            # Let Stripe automatically select optimal payment methods based on customer location
            # This is the modern best practice (2025+) - Stripe handles payment method availability
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


def handle_plan_change(user_id, new_plan_id, new_billing_period):
    """Handle plan upgrades and downgrades for existing subscribers.

    UPGRADE (higher tier plan or same tier monthly->yearly):
    - Immediately switch to new plan
    - Prorate: credit unused time from old plan, charge difference for new plan
    - User pays the difference immediately

    DOWNGRADE (lower tier plan or same tier yearly->monthly):
    - Schedule change for end of current billing period
    - User keeps current plan until period ends
    - No immediate payment - new plan starts at next billing cycle
    - User can cancel scheduled downgrade before period ends

    Hierarchy: Tier is primary, billing period is secondary.
    - Pro Monthly < Pro Yearly < Max Monthly < Max Yearly

    Returns:
        (success: bool, result: dict or error_message: str)
        result dict contains: {'action': 'upgrade'|'downgrade', 'effective_date': timestamp or None}
    """
    if not STRIPE_SECRET_KEY:
        return False, "Stripe not configured"

    from database import get_user_by_id, get_active_subscription
    from config.plans import is_upgrade, SUBSCRIPTION_PLANS, BUSINESS_PLANS

    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"

    subscription_data = get_active_subscription(user_id)
    if not subscription_data:
        return False, "No active subscription found"

    current_plan_id = subscription_data.get('plan_id')
    current_billing_period = subscription_data.get('billing_period')
    stripe_subscription_id = user.get('stripe_subscription_id')

    if not stripe_subscription_id:
        return False, "No Stripe subscription found"

    # Check if trying to switch to exact same plan and billing period
    if current_plan_id == new_plan_id and current_billing_period == new_billing_period:
        return False, "You are already on this plan"

    # Validate new plan
    if new_plan_id not in STRIPE_PRICE_IDS:
        return False, "Invalid plan"

    if new_billing_period not in ['monthly', 'yearly']:
        return False, "Invalid billing period"

    new_price_id = STRIPE_PRICE_IDS[new_plan_id][new_billing_period]

    try:
        # Get current subscription from Stripe
        current_subscription = stripe.Subscription.retrieve(stripe_subscription_id)

        if current_subscription.status not in ['active', 'trialing']:
            return False, "Subscription is not active"

        # Determine if this is an upgrade or downgrade
        # Pass both plan IDs and billing periods for accurate comparison
        if is_upgrade(current_plan_id, new_plan_id, current_billing_period, new_billing_period):
            # UPGRADE: Immediate switch with proration
            return _handle_upgrade(user_id, current_subscription, new_plan_id, new_price_id, new_billing_period, current_plan_id)
        else:
            # DOWNGRADE: Schedule for end of period
            return _handle_downgrade(user_id, current_subscription, new_plan_id, new_price_id, new_billing_period, current_plan_id)

    except stripe.error.StripeError as e:
        return False, str(e)


def _handle_upgrade(user_id, current_subscription, new_plan_id, new_price_id, billing_period, current_plan_id=None):
    """Handle upgrade by redirecting to Stripe Checkout for full payment.

    NO proration - user pays full price for new plan.
    Old subscription is cancelled only AFTER checkout completes successfully.
    This prevents abuse where user could get upgraded without paying.
    """
    from database import clear_scheduled_plan_change

    try:
        # Clear any pending scheduled downgrade first
        clear_scheduled_plan_change(user_id)

        # Cancel any existing schedule on this subscription (but NOT the subscription itself)
        if current_subscription.schedule:
            try:
                stripe.SubscriptionSchedule.release(current_subscription.schedule)
            except stripe.error.StripeError:
                pass  # Schedule might not exist or already released

        # Return checkout URL - the actual upgrade happens in handle_checkout_completed webhook
        # which will cancel the old subscription after payment succeeds
        return True, {
            'action': 'upgrade',
            'requires_checkout': True,
            'plan_id': new_plan_id,
            'billing_period': billing_period
        }

    except stripe.error.StripeError as e:
        return False, str(e)


def _handle_downgrade(user_id, current_subscription, new_plan_id, new_price_id, billing_period, current_plan_id=None):
    """Handle scheduled downgrade at end of billing period.

    Uses Stripe's pending_update feature to schedule the price change
    for the next billing cycle without immediate proration.

    Note: Channel selections are NOT cleared here - they will be cleared when
    the downgrade actually takes effect via handle_subscription_updated webhook.
    """
    from database import set_scheduled_plan_change

    try:
        subscription_id = current_subscription['id']

        # Get subscription items
        try:
            items_data = current_subscription['items']
            items_list = items_data['data']
        except (KeyError, TypeError):
            return False, "Invalid subscription structure - no items found"

        if not items_list:
            return False, "Invalid subscription structure - no items found"
        current_item = items_list[0]
        current_item_id = current_item['id']

        # Get effective_date from subscription items (Stripe API 2025-03-31+)
        # This is when the downgrade will take effect (end of current billing period)
        effective_date = get_current_period_end_from_subscription(current_subscription)

        # Cancel any existing schedule first
        try:
            existing_schedule = current_subscription.get('schedule')
            if existing_schedule:
                try:
                    stripe.SubscriptionSchedule.release(existing_schedule)
                except stripe.error.StripeError:
                    pass
        except (KeyError, TypeError):
            pass

        # Use Subscription.modify with proration_behavior='none' to change at next billing cycle
        # This changes the subscription but doesn't charge until next cycle
        updated_subscription = stripe.Subscription.modify(
            subscription_id,
            items=[{
                'id': current_item_id,
                'price': new_price_id,
            }],
            proration_behavior='none',  # No proration - change takes effect at next billing
            metadata={
                'user_id': str(user_id),
                'plan_id': new_plan_id,
                'billing_period': billing_period,
                'pending_downgrade': 'true'
            }
        )

        # Store scheduled change in our database for UI display
        if effective_date:
            set_scheduled_plan_change(user_id, new_plan_id, billing_period, effective_date)

        return True, {
            'action': 'downgrade',
            'effective_date': effective_date
        }

    except stripe.error.StripeError as e:
        return False, str(e)


def cancel_scheduled_downgrade(user_id):
    """Cancel a scheduled downgrade and revert to the original plan.

    Since we use Subscription.modify with proration_behavior='none' for downgrades,
    we need to look up the original plan from our database and revert to it.

    Returns:
        (success: bool, error_message: str or None)
    """
    if not STRIPE_SECRET_KEY:
        return False, "Stripe not configured"

    from database import get_user_by_id, clear_scheduled_plan_change, get_scheduled_plan_change, get_active_subscription

    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"

    stripe_subscription_id = user.get('stripe_subscription_id')
    if not stripe_subscription_id:
        return False, "No subscription found"

    try:
        # Get the scheduled change to know what we're reverting from
        scheduled_change = get_scheduled_plan_change(user_id)
        if not scheduled_change:
            return False, "No scheduled downgrade found"

        # Get the current active subscription from our database (this has the ORIGINAL plan)
        active_sub = get_active_subscription(user_id)
        if not active_sub:
            return False, "No active subscription found"

        original_plan_id = active_sub.get('plan_id')
        original_billing_period = active_sub.get('billing_period')

        if not original_plan_id or original_plan_id not in STRIPE_PRICE_IDS:
            return False, "Could not determine original plan"

        original_price_id = STRIPE_PRICE_IDS[original_plan_id].get(original_billing_period)
        if not original_price_id:
            return False, "Could not determine original price"

        # Get current subscription from Stripe
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)

        # Get subscription items
        items_data = subscription['items']
        items_list = items_data['data']
        if not items_list:
            return False, "Invalid subscription structure"
        current_item_id = items_list[0]['id']

        # Revert to original price (no proration since we're undoing the downgrade)
        stripe.Subscription.modify(
            stripe_subscription_id,
            items=[{
                'id': current_item_id,
                'price': original_price_id,
            }],
            proration_behavior='none',
            metadata={
                'user_id': str(user_id),
                'plan_id': original_plan_id,
                'billing_period': original_billing_period,
                'pending_downgrade': None  # Clear the pending downgrade flag
            }
        )

        # Clear from our database
        clear_scheduled_plan_change(user_id)

        return True, None

    except stripe.error.StripeError as e:
        return False, str(e)


def get_scheduled_plan_change(user_id):
    """Get any scheduled plan change for a user.

    Returns:
        dict with keys: plan_id, billing_period, effective_date
        or None if no scheduled change
    """
    from database import get_scheduled_plan_change as db_get_scheduled

    return db_get_scheduled(user_id)


def cancel_subscription_at_period_end(user_id):
    """Cancel subscription at the end of the current billing period.

    The user keeps their plan until the period ends, then goes to free tier.
    Uses Stripe's cancel_at_period_end feature.

    IMPORTANT: This also clears any pending downgrade - cancel overrides downgrade.
    The subscription will cancel at period end, not downgrade.

    Returns:
        (success: bool, error_message: str or None)
    """
    if not STRIPE_SECRET_KEY:
        return False, "Stripe not configured"

    from database import get_user_by_id, clear_scheduled_plan_change, get_active_subscription

    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"

    stripe_subscription_id = user.get('stripe_subscription_id')
    if not stripe_subscription_id:
        return False, "No subscription found"

    try:
        # First, get current subscription to find the original price (before any pending downgrade)
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        metadata = subscription.get('metadata', {})

        # If there's a pending downgrade, we need to revert the price first
        # then set cancel_at_period_end
        if metadata.get('pending_downgrade') == 'true':

            # Get the original plan from our database
            active_sub = get_active_subscription(user_id)
            if active_sub:
                original_plan_id = active_sub.get('plan_id')
                original_billing_period = active_sub.get('billing_period')

                if original_plan_id and original_plan_id in STRIPE_PRICE_IDS:
                    original_price_id = STRIPE_PRICE_IDS[original_plan_id].get(original_billing_period)

                    if original_price_id:
                        # Get current item ID
                        items_data = subscription.get('items', {})
                        items_list = items_data.get('data', [])
                        if items_list:
                            current_item_id = items_list[0]['id']

                            # Revert to original price and set cancel_at_period_end in one call
                            subscription = stripe.Subscription.modify(
                                stripe_subscription_id,
                                items=[{'id': current_item_id, 'price': original_price_id}],
                                proration_behavior='none',
                                cancel_at_period_end=True,
                                metadata={
                                    'user_id': str(user_id),
                                    'plan_id': original_plan_id,
                                    'billing_period': original_billing_period,
                                    'pending_downgrade': ''  # Clear the flag
                                }
                            )
                            # Clear scheduled change from our database
                            clear_scheduled_plan_change(user_id)
                            return True, None

        # No pending downgrade, just set cancel_at_period_end
        subscription = stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True
        )

        # Clear any scheduled change from our database (just in case)
        clear_scheduled_plan_change(user_id)

        return True, None

    except stripe.error.StripeError as e:
        return False, str(e)


def reactivate_subscription(user_id):
    """Reactivate a subscription that was set to cancel at period end.

    Undoes the cancel_at_period_end, so the subscription continues normally.

    Returns:
        (success: bool, error_message: str or None)
    """
    if not STRIPE_SECRET_KEY:
        return False, "Stripe not configured"

    from database import get_user_by_id

    user = get_user_by_id(user_id)
    if not user:
        return False, "User not found"

    stripe_subscription_id = user.get('stripe_subscription_id')
    if not stripe_subscription_id:
        return False, "No subscription found"

    try:
        # Set cancel_at_period_end to false
        # This reactivates the subscription so it will renew normally
        subscription = stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=False
        )

        return True, None

    except stripe.error.StripeError as e:
        return False, str(e)


def get_current_period_end_from_subscription(subscription):
    """Extract current_period_end from subscription items (Stripe API 2025-03-31+).

    In Stripe API version 2025-03-31 and later, current_period_start and current_period_end
    have moved from the Subscription object to Subscription Item objects.

    Args:
        subscription: Stripe Subscription object (dict-like)

    Returns:
        int (Unix timestamp) or None if not found
    """
    try:
        # Try to get from subscription items (new API 2025-03-31+)
        items = subscription.get('items', {})
        items_data = items.get('data', [])
        if items_data:
            first_item = items_data[0]
            # current_period_end is now on the item level
            period_end = first_item.get('current_period_end')
            if period_end:
                return period_end

        # Fallback: try subscription-level (older API versions)
        period_end = getattr(subscription, 'current_period_end', None)
        if period_end:
            return period_end

        # Last resort: calculate from billing_cycle_anchor
        billing_anchor = subscription.get('billing_cycle_anchor')
        if billing_anchor:
            # Get interval from plan
            items = subscription.get('items', {})
            items_data = items.get('data', [])
            if items_data:
                price = items_data[0].get('price', {})
                recurring = price.get('recurring', {})
                interval = recurring.get('interval', 'month')
                interval_count = recurring.get('interval_count', 1)

                now = int(time.time())

                if interval == 'year':
                    seconds_per_period = 365 * 24 * 60 * 60 * interval_count
                else:  # month
                    seconds_per_period = 30 * 24 * 60 * 60 * interval_count

                # Calculate periods since anchor
                elapsed = now - billing_anchor
                periods_elapsed = elapsed // seconds_per_period
                next_period_end = billing_anchor + (periods_elapsed + 1) * seconds_per_period
                return next_period_end

        return None
    except Exception:
        return None


def get_subscription_status(user_id):
    """Get current subscription status from Stripe.

    Returns:
        dict with keys:
        - is_active: bool
        - cancel_at_period_end: bool (True if scheduled to cancel)
        - current_period_end: int (Unix timestamp)
        - status: str (Stripe status: active, canceled, etc.)
        Or None if no subscription found
    """
    if not STRIPE_SECRET_KEY:
        return None

    from database import get_user_by_id

    user = get_user_by_id(user_id)
    if not user:
        return None

    stripe_subscription_id = user.get('stripe_subscription_id')
    if not stripe_subscription_id:
        return None

    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)

        # Use getattr with defaults to handle missing attributes safely
        cancel_at_period_end = getattr(subscription, 'cancel_at_period_end', False)
        status = getattr(subscription, 'status', 'unknown')

        # Get current_period_end from subscription items (Stripe API 2025-03-31+)
        current_period_end = get_current_period_end_from_subscription(subscription)

        return {
            'is_active': status in ['active', 'trialing'],
            'cancel_at_period_end': cancel_at_period_end,
            'current_period_end': current_period_end,
            'status': status
        }

    except stripe.error.StripeError:
        return None
    except Exception:
        return None


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
    """Handle successful checkout - activate subscription.

    This function:
    1. Cancels any existing Stripe subscription (only after new one is purchased)
    2. Resets channel selections if switching to a different plan tier
    3. Activates the new subscription in our database

    Note: checkout.session.completed only fires when payment succeeds,
    so no need to verify subscription status.
    """
    from database import (set_subscription, get_user_by_id, get_active_subscription,
                          update_user_stripe_subscription_id, clear_user_channel_selections)
    from config.plans import SUBSCRIPTION_PLANS, BUSINESS_PLANS

    user_id = session.get('metadata', {}).get('user_id')
    plan_id = session.get('metadata', {}).get('plan_id')
    billing_period = session.get('metadata', {}).get('billing_period')
    new_subscription_id = session.get('subscription')

    if not all([user_id, plan_id, billing_period, new_subscription_id]):
        logger.error(f"[Webhook] checkout.session.completed missing metadata: user_id={user_id}, plan_id={plan_id}")
        return False

    # Safe type conversion
    try:
        user_id = int(user_id)
    except (ValueError, TypeError):
        logger.error(f"[Webhook] Invalid user_id format: {user_id}")
        return False

    user = get_user_by_id(user_id)
    if not user:
        logger.error(f"[Webhook] User not found: {user_id}")
        return False

    # Idempotency check - if this subscription is already stored for user, skip
    # This prevents duplicate processing from webhook retries
    if user.get('stripe_subscription_id') == new_subscription_id:
        return True  # Already processed, return success

    # Check if user is switching plan types (not just billing period)
    # If so, reset their channel selections due to different limits
    current_subscription = get_active_subscription(user_id)
    if current_subscription:
        current_plan_id = current_subscription.get('plan_id')
        if current_plan_id and current_plan_id != plan_id:
            clear_user_channel_selections(user_id)

    # Cancel old Stripe subscription if exists (user can only have 1 active subscription)
    old_subscription_id = user.get('stripe_subscription_id')
    if old_subscription_id and old_subscription_id != new_subscription_id:
        try:
            stripe.Subscription.cancel(old_subscription_id)
        except stripe.error.StripeError:
            pass  # Old subscription might already be cancelled

    # Determine plan type and get config
    if plan_id.startswith('team_'):
        plan_type = 'business'
        plan_config = BUSINESS_PLANS.get(plan_id)
    else:
        plan_type = 'subscription'
        plan_config = SUBSCRIPTION_PLANS.get(plan_id)

    if not plan_config:
        logger.error(f"[Webhook] Plan config not found: {plan_id}")
        return False

    # Store new subscription ID and activate
    update_user_stripe_subscription_id(user_id, new_subscription_id)
    success = set_subscription(user_id, plan_type, plan_id, plan_config, billing_period)

    if success and plan_type == 'business':
        from database import create_business_team, auto_deny_pending_invitations
        subscription = get_active_subscription(user_id)
        if subscription:
            max_members = plan_config.get('max_members', 3)
            create_business_team(user_id, subscription['id'], max_members)
            auto_deny_pending_invitations(user_id)

    if not success:
        logger.error(f"[Webhook] Failed to activate subscription for user {user_id}")

    return success


def handle_subscription_deleted(subscription):
    """Handle subscription cancellation - downgrade to free.

    Important: Only downgrade if the deleted subscription is the user's current one.
    This prevents issues when switching plans (old subscription deleted, new one active).
    """
    from database import cancel_subscription, get_user_by_stripe_customer_id, clear_scheduled_plan_change, clear_user_channel_selections

    customer_id = subscription.get('customer')
    deleted_subscription_id = subscription.get('id')

    if not customer_id:
        return False

    user = get_user_by_stripe_customer_id(customer_id)
    if not user:
        return False

    # Only downgrade if this is the user's current subscription
    # If user has a different subscription ID, they switched plans and shouldn't be downgraded
    current_subscription_id = user.get('stripe_subscription_id')
    if current_subscription_id and current_subscription_id != deleted_subscription_id:
        return True  # User switched plans, don't downgrade

    # Clear scheduled plan changes and channel selections
    clear_scheduled_plan_change(user['id'])
    clear_user_channel_selections(user['id'])

    # Cancel subscription (downgrades to free)
    return cancel_subscription(user['id'])


def handle_subscription_updated(subscription):
    """Handle subscription updates - particularly scheduled downgrades taking effect.

    This webhook fires when:
    - A scheduled downgrade takes effect (plan changes at period end)
    - Subscription is modified (upgrade already handled in handle_plan_change)
    - Other subscription changes

    We check if the plan has changed and update our database accordingly.
    IMPORTANT: If metadata contains 'pending_downgrade': 'true', we DO NOT update
    the database - the downgrade hasn't taken effect yet.
    """
    from database import (get_user_by_stripe_customer_id, get_active_subscription,
                          set_subscription, clear_scheduled_plan_change, clear_user_channel_selections)
    from config.plans import SUBSCRIPTION_PLANS, BUSINESS_PLANS

    customer_id = subscription.get('customer')
    subscription_id = subscription.get('id')
    metadata = subscription.get('metadata', {})

    if not customer_id:
        return False

    # Check if this is a pending downgrade - if so, don't update the database yet
    # The downgrade will take effect at the next billing cycle
    if metadata.get('pending_downgrade') == 'true':
        return True  # Acknowledge but don't update database

    user = get_user_by_stripe_customer_id(customer_id)
    if not user:
        return False

    # Only process if this is the user's current subscription
    current_subscription_id = user.get('stripe_subscription_id')
    if current_subscription_id != subscription_id:
        return True  # Not the current subscription, ignore

    # Get the current plan from the subscription
    if not subscription.get('items') or not subscription['items'].get('data'):
        return False

    current_item = subscription['items']['data'][0]
    price_id = current_item.get('price', {}).get('id')

    if not price_id:
        return False

    # Find which plan this price ID corresponds to
    new_plan_id = None
    billing_period = None

    for plan_id, periods in STRIPE_PRICE_IDS.items():
        for period, pid in periods.items():
            if pid == price_id:
                new_plan_id = plan_id
                billing_period = period
                break
        if new_plan_id:
            break

    if not new_plan_id:
        return False  # Unknown price ID

    # Check if this is different from our current database record
    current_sub = get_active_subscription(user['id'])
    current_plan_id = current_sub.get('plan_id') if current_sub else None

    if current_sub and current_plan_id == new_plan_id:
        # Same plan, no update needed (might just be a renewal or other update)
        return True

    # Plan has changed - this is likely a scheduled downgrade taking effect
    # Clear channel selections since plan limits may differ
    if current_plan_id and current_plan_id != new_plan_id:
        clear_user_channel_selections(user['id'])

    # Update our database
    if new_plan_id.startswith('team_'):
        plan_type = 'business'
        plan_config = BUSINESS_PLANS.get(new_plan_id)
    else:
        plan_type = 'subscription'
        plan_config = SUBSCRIPTION_PLANS.get(new_plan_id)

    if not plan_config:
        return False

    # Clear the scheduled change since it has now taken effect
    clear_scheduled_plan_change(user['id'])

    # Update subscription in database
    success = set_subscription(user['id'], plan_type, new_plan_id, plan_config, billing_period)

    # Handle business plan team creation if upgrading to business
    if success and plan_type == 'business':
        from database import create_business_team, get_active_subscription as get_sub, auto_deny_pending_invitations
        subscription_record = get_sub(user['id'])
        if subscription_record:
            max_members = plan_config.get('max_members', 3)
            create_business_team(user['id'], subscription_record['id'], max_members)
            auto_deny_pending_invitations(user['id'])

    return success


def handle_invoice_payment_succeeded(invoice):
    """Handle successful invoice payment - extend subscription if renewal.

    Also handles pending downgrades taking effect when the new billing cycle starts.
    """
    subscription_id = invoice.get('subscription')
    if not subscription_id:
        return True  # Not a subscription invoice

    from database import (extend_subscription_by_stripe_subscription_id,
                          get_user_by_stripe_customer_id, set_subscription,
                          clear_scheduled_plan_change, clear_user_channel_selections)
    from config.plans import SUBSCRIPTION_PLANS, BUSINESS_PLANS

    billing_reason = invoice.get('billing_reason')

    if billing_reason == 'subscription_cycle':
        # This is a renewal - check if there's a pending downgrade that should take effect
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            metadata = subscription.get('metadata', {})

            if metadata.get('pending_downgrade') == 'true':
                # Downgrade is now taking effect - update database
                customer_id = subscription.get('customer')
                user = get_user_by_stripe_customer_id(customer_id)

                if user:
                    new_plan_id = metadata.get('plan_id')
                    new_billing_period = metadata.get('billing_period')

                    if new_plan_id:
                        # Update database with new plan
                        if new_plan_id.startswith('team_'):
                            plan_type = 'business'
                            plan_config = BUSINESS_PLANS.get(new_plan_id)
                        else:
                            plan_type = 'subscription'
                            plan_config = SUBSCRIPTION_PLANS.get(new_plan_id)

                        if plan_config:
                            # Clear channel selections since limits may differ
                            clear_user_channel_selections(user['id'])
                            # Update the subscription in our database
                            set_subscription(user['id'], plan_type, new_plan_id, plan_config, new_billing_period)
                            # Clear the scheduled change
                            clear_scheduled_plan_change(user['id'])

                        # Clear the pending_downgrade flag in Stripe
                        stripe.Subscription.modify(
                            subscription_id,
                            metadata={
                                'user_id': str(user['id']),
                                'plan_id': new_plan_id,
                                'billing_period': new_billing_period,
                                'pending_downgrade': ''  # Clear the flag
                            }
                        )
            else:
                # Normal renewal - extend subscription
                extend_subscription_by_stripe_subscription_id(subscription_id)
        except stripe.error.StripeError:
            # Still extend subscription on error
            extend_subscription_by_stripe_subscription_id(subscription_id)

    return True


def handle_invoice_payment_failed(invoice):
    """Handle failed invoice payment - cancel subscription immediately (no retries)."""
    from database import cancel_subscription, get_user_by_stripe_customer_id, clear_user_channel_selections

    subscription_id = invoice.get('subscription')
    customer_id = invoice.get('customer')

    if not subscription_id:
        return True  # Not a subscription invoice

    user = get_user_by_stripe_customer_id(customer_id)
    if not user:
        return False

    # Cancel the subscription in Stripe (this will trigger customer.subscription.deleted webhook)
    # The deleted webhook will handle clearing channels, but we also clear here as a safety net
    try:
        stripe.Subscription.cancel(subscription_id)
    except stripe.error.StripeError:
        # Stripe API failed - cancel locally and clear channels
        clear_user_channel_selections(user['id'])
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
