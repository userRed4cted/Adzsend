# =============================================================================
# PRICING PLANS CONFIGURATION
# =============================================================================
# This file controls all pricing plans displayed on the Purchase page.
# Each setting is documented with what it does and which UI element it affects.
#
# COLOR FORMATS:
#   - Hex: '#15d8bc', '#ffffff', '#335FFF'
#   - RGBA: 'rgba(21, 216, 188, 0.6)' - last value is transparency (0-1)
#
# PRICE FORMATS:
#   - Whole numbers: 7, 15, 30 (displays as $7, $15, $30)
#   - Decimals: 2.50, 7.99 (displays as $2.50, $7.99)
# =============================================================================


# =============================================================================
# PLAN HIERARCHY (for upgrade/downgrade detection)
# =============================================================================
# Higher tier = higher number. Used to determine if a plan change is an
# upgrade (immediate switch) or downgrade (scheduled at period end).
# Personal and Business plans are separate hierarchies.
#
# Hierarchy (tier is primary, billing period is secondary):
#   Pro Monthly < Pro Yearly < Max Monthly < Max Yearly
#   Startup Monthly < Startup Yearly < Premium Monthly < Premium Yearly
#
# Personal plans: plan_free (0) < plan_1/Pro (1) < plan_2/Max (2)
# Business plans: team_plan_1/Startup (1) < team_plan_2/Premium (2)
PLAN_TIERS = {
    'plan_free': 0,
    'plan_1': 1,      # Pro
    'plan_2': 2,      # Max
    'team_plan_1': 1,  # Startup
    'team_plan_2': 2,  # Premium
}

# Billing period hierarchy (yearly > monthly within same tier)
BILLING_PERIOD_VALUE = {
    'monthly': 0,
    'yearly': 1,
}


def is_upgrade(current_plan_id, new_plan_id, current_billing_period=None, new_billing_period=None):
    """Determine if changing from current_plan to new_plan is an upgrade.

    Returns True if upgrade (immediate switch), False if downgrade (scheduled).
    Cross-category changes (personal <-> business) are always treated as upgrades
    (immediate switch with payment).

    Hierarchy: Tier is primary, billing period is secondary.
    - Pro Monthly < Pro Yearly < Max Monthly < Max Yearly
    - Changing to higher tier = upgrade (regardless of billing period)
    - Changing to lower tier = downgrade (regardless of billing period)
    - Same tier, monthly to yearly = upgrade
    - Same tier, yearly to monthly = downgrade
    """
    if not current_plan_id or current_plan_id == 'plan_free':
        return True  # From free to anything is an upgrade

    current_is_business = current_plan_id.startswith('team_')
    new_is_business = new_plan_id.startswith('team_')

    # Cross-category change (personal <-> business) = immediate switch
    if current_is_business != new_is_business:
        return True

    current_tier = PLAN_TIERS.get(current_plan_id, 0)
    new_tier = PLAN_TIERS.get(new_plan_id, 0)

    # Different tier - tier takes precedence
    if new_tier != current_tier:
        return new_tier > current_tier

    # Same tier - compare billing periods
    if current_billing_period and new_billing_period:
        current_period_value = BILLING_PERIOD_VALUE.get(current_billing_period, 0)
        new_period_value = BILLING_PERIOD_VALUE.get(new_billing_period, 0)
        # Same plan same period = not an upgrade (no change needed)
        if current_period_value == new_period_value:
            return False  # Will be caught as "same plan" elsewhere
        return new_period_value > current_period_value

    # No billing period info provided - fall back to tier comparison only
    return new_tier > current_tier


# =============================================================================
# SUBSCRIPTION PLANS (Monthly/Yearly recurring)
# =============================================================================
# Displayed in the "Personal" section of the Purchase page.
# Users pay monthly or yearly and get recurring access.

SUBSCRIPTION_PLANS = {

    # -------------------------------------------------------------------------
    # FREE PLAN
    # -------------------------------------------------------------------------
    'plan_free': {
        # PLAN NAME
        # Element: Title text at top of plan card
        'name': 'Free',

        # FEATURES LIST
        # Element: Bullet points with checkmarks on plan card
        # Each string is one feature line
        'features': [
            '30 messages posts per day',
            '2 channels per server',
            'Personal panel',
        ],

        # MESSAGE LIMIT
        # How many messages user can send
        # -1 = unlimited, any positive number = that limit
        'message_limit': 30,

        # USAGE TYPE
        # 'allowance' = limit resets after period (daily/weekly/monthly)
        # 'amount' = fixed total, never resets
        'usage_type': 'allowance',

        # ALLOWANCE PERIOD (only used if usage_type is 'allowance')
        # 'daily' = resets every day
        # 'weekly' = resets every week
        # 'monthly' = resets every month
        # None = not applicable (for 'amount' type)
        'allowance_period': 'daily',

        # BUTTON TEXT
        # Element: Text on the purchase button at bottom of card
        'button_text': 'Select',

        # FEATURE FLAGS
        # These control additional plan capabilities (no function yet - placeholder for future use)
        'analytics_and_insights': False,
        'multi_discord_accounts': False,
        'multi_variation_message': False,
        'max_channels_per_server': 2,  # -1 = unlimited
    },

    # -------------------------------------------------------------------------
    # REGULAR PLAN
    # -------------------------------------------------------------------------
    'plan_1': {
        # PLAN NAME
        # Element: Title text at top of plan card
        'name': 'Pro',

        # PRICING
        # Element: Large price number on plan card
        # price_monthly: Shown when "Monthly" toggle is selected
        # price_yearly: Shown when "Yearly" toggle is selected (total per year)
        'price_monthly': 8,
        'price_yearly': 72,

        # FEATURES LIST
        # Element: Bullet points with checkmarks on plan card
        # Each string is one feature line
        'features': [
            '800 message posts per week',
            'Unlimited channel and server selections',
            'Advanced analytics',
            'Personal panel',
        ],

        # MESSAGE LIMIT
        # How many messages user can send
        # -1 = unlimited, any positive number = that limit
        'message_limit': 800,

        # USAGE TYPE
        # 'allowance' = limit resets after period (daily/weekly/monthly)
        # 'amount' = fixed total, never resets
        'usage_type': 'allowance',

        # ALLOWANCE PERIOD (only used if usage_type is 'allowance')
        # 'daily' = resets every day
        # 'weekly' = resets every week
        # 'monthly' = resets every month
        # None = not applicable (for 'amount' type)
        'allowance_period': 'weekly',

        # SAVINGS TEXT (shown when Yearly is selected)
        # Element: Text below price showing savings info
        # If empty/not set: auto-calculates "SAVING $XX (17% OFF) YEARLY"
        # If set: shows your custom text instead
        'savings_text': '$6 per month',

        # SAVINGS TEXT COLOR
        # Element: Color of the savings text
        # If empty/not set: uses default CSS color
        'savings_color': '#15d8bc',

        # BUTTON TEXT
        # Element: Text on the purchase button at bottom of card
        'button_text': 'Subscribe',

        # FEATURE FLAGS
        'analytics_and_insights': True,
        'multi_discord_accounts': True,
        'multi_variation_message': True,
        'max_channels_per_server': -1,  # -1 = unlimited
    },

    # -------------------------------------------------------------------------
    # PRO PLAN
    # -------------------------------------------------------------------------
    'plan_2': {
        'name': 'Max',
        'price_monthly': 17.50,
        'price_yearly': 160,
        'features': [
            '3200 message posts per week',
            'Unlimited channel and server selections',
            'Advanced analytics',
            'Personal panel',
        ],
        'message_limit': 3200,  # x4 of pro | -1 = unlimited
        'usage_type': 'amount',
        'allowance_period': 'Weekly',
        'savings_text': '$12.50 per month',
        'savings_color': '#15d8bc',
        'button_text': 'Subscribe',

        # FEATURE FLAGS
        'analytics_and_insights': True,
        'multi_discord_accounts': True,
        'multi_variation_message': True,
        'max_channels_per_server': -1,  # -1 = unlimited
    },
}


# =============================================================================
# BUSINESS PLANS (Team subscriptions)
# =============================================================================
# Displayed in the "Business" section of the Purchase page.
# Includes team management features with multiple members sharing a limit.

BUSINESS_PLANS = {

    # -------------------------------------------------------------------------
    # BUSINESS STARTER
    # -------------------------------------------------------------------------
    'team_plan_1': {
        # PLAN NAME
        # Element: Title text at top of plan card
        'name': 'Startup',

        # PRICING
        # Element: Large price number on plan card
        'price_monthly': 20,
        'price_yearly': 192,

        # FEATURES LIST
        # Element: Bullet points with checkmarks on plan card
        'features': [
            '3200 message posts per week across all members',
            'Unlimited channel and server selections',
            'Advanced analytics',
            'Team management',
            'Up to 3 team members',
            'Team panel for owner and members',
        ],

        # MESSAGE LIMIT
        # Total messages shared across ALL team members
        'message_limit': 3200,

        # USAGE TYPE & PERIOD
        'usage_type': 'allowance',
        'allowance_period': 'weekly',

        # MAX TEAM MEMBERS
        # Maximum number of people who can join this business team
        'max_members': 3,

        # SAVINGS TEXT & COLOR (shown when Yearly selected)
        'savings_text': '$16 per month',
        'savings_color': '#15d8bc',

        # BUTTON TEXT
        # Element: Text on the purchase button
        'button_text': 'Subscribe',

        # MAX CHANNELS PER SERVER
        # How many channels user can select from each server
        # -1 = unlimited, any positive number = that limit
        'max_channels_per_server': -1,
    },

    # -------------------------------------------------------------------------
    # ENTERPRISE PLAN
    # -------------------------------------------------------------------------
    'team_plan_2': {
        'name': 'Premium',
        'price_monthly': 30,
        'price_yearly': 288,
        'features': [
            '7000 message posts per week across all members',
            'Unlimited channel and server selections',
            'Advanced analytics',
            'Team management',
            'Up to 10 team members',
            'Team panel for owner and members',
        ],
        'message_limit': 7000,  # -1 = unlimited
        'usage_type': 'amount',
        'allowance_period': 'monthly',
        'max_members': 10,
        'savings_text': '$24 per month',
        'savings_color': '#15d8bc',
        'button_text': 'Subscribe',
        'max_channels_per_server': -1,  # -1 = unlimited
    },
}
