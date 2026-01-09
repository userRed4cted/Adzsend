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
            '30 messages per day',
            '2 channels per server',
            'Personal use',
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

        # GLOW COLOR
        # Element: Glowing border effect around plan card on hover
        # Format: 'rgba(R, G, B, opacity)' where opacity is 0-1
        'glow_color': 'rgba(255, 255, 255, 0.6)',

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
        'price_monthly': 7,
        'price_yearly': 75,

        # FEATURES LIST
        # Element: Bullet points with checkmarks on plan card
        # Each string is one feature line
        'features': [
            '500 message posts per week',
            'Unlimited channel and server selections',
            'Advanced analytics',
            'Post with multiple Discord account',
            'Personal use',
        ],

        # MESSAGE LIMIT
        # How many messages user can send
        # -1 = unlimited, any positive number = that limit
        'message_limit': 500,

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

        # GLOW COLOR
        # Element: Glowing border effect around plan card on hover
        # Format: 'rgba(R, G, B, opacity)' where opacity is 0-1
        'glow_color': 'rgba(255, 255, 255, 0.6)',

        # SAVINGS TEXT (shown when Yearly is selected)
        # Element: Text below price showing savings info
        # If empty/not set: auto-calculates "SAVING $XX (17% OFF) YEARLY"
        # If set: shows your custom text instead
        'savings_text': '$6.25 per month',

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
        'name': 'Max x3 & x5',
        'price_monthly': 15,
        'price_yearly': 160,
        'features': [
            'x3 or x5 (of Pro) message posting',
            'Unlimited channel and server selections',
            'Advanced analytics',
            'Post with multiple Discord account',
            'Personal use',
        ],
        'message_limit': 1500,  # x5=2500 -1 = unlimited
        'usage_type': 'amount',
        'allowance_period': 'Weekly',
        'glow_color': 'rgba(21, 216, 188, 0.6)',
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
# ONE-TIME PURCHASE PLANS (Single payment, limited duration)
# =============================================================================
# Displayed below subscription plans in the "Personal" section.
# Users pay once and get access for a set number of days.

ONE_TIME_PLANS = {

    # -------------------------------------------------------------------------
    # 1 DAY PASS
    # -------------------------------------------------------------------------
    'plan_1day': {
        # PLAN NAME
        # Element: Title text at top of plan card
        'name': '1 Day',

        # PRICE (one-time payment)
        # Element: Large price number on plan card
        'price': 2.50,

        # FEATURES LIST
        # Element: Bullet points with checkmarks on plan card
        'features': [
            '50 message posts limit',
            'Personal use'
        ],

        # MESSAGE LIMIT
        # How many messages user can send total
        'message_limit': 50,

        # USAGE TYPE
        # 'allowance' = limit resets after period
        # 'amount' = fixed total, never resets
        'usage_type': 'amount',

        # ALLOWANCE PERIOD
        # Set to None for 'amount' type
        # Or 'daily'/'weekly'/'monthly' for 'allowance' type
        'allowance_period': None,

        # DURATION DAYS
        # How many days the plan lasts after purchase
        'duration_days': 1,

        # GLOW COLOR
        # Element: Glowing border effect around plan card on hover
        'glow_color': 'rgba(255, 255, 255, 0.6)',

        # BUTTON TEXT
        # Element: Text on the purchase button
        'button_text': 'Purchase',

        # MAX CHANNELS PER SERVER
        # How many channels user can select from each server
        # -1 = unlimited, any positive number = that limit
        'max_channels_per_server': 2,
    },

    # -------------------------------------------------------------------------
    # 3 DAY PASS
    # -------------------------------------------------------------------------
    'plan_3day': {
        'name': '3 Days',
        'price': 5,
        'features': [
            '50 message posts limit per day',
            'Daily Limit',
            'Personal use'
        ],
        'message_limit': 50,
        'usage_type': 'allowance',
        'allowance_period': 'daily',  # Resets every day
        'duration_days': 3,
        'glow_color': 'rgba(255, 255, 255, 0.6)',
        'button_text': 'Purchase',
        'max_channels_per_server': 2,  # -1 = unlimited
    },

    # -------------------------------------------------------------------------
    # 7 DAY PASS
    # -------------------------------------------------------------------------
    'plan_7day': {
        'name': '7 Days',
        'price': 7.50,
        'features': [
            '70 message posts limit per day',
            'Daily Limit',
            'Personal use'
        ],
        'message_limit': 70,
        'usage_type': 'allowance',
        'allowance_period': 'daily',
        'duration_days': 7,
        'glow_color': 'rgba(21, 216, 188, 0.6)',
        'button_text': 'Purchase',
        'max_channels_per_server': 2,  # -1 = unlimited
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
        'price_yearly': 195,

        # FEATURES LIST
        # Element: Bullet points with checkmarks on plan card
        'features': [
            '5000 message posts per week across all members',
            'Unlimited channel and server selections',
            'Advanced analytics',
            'Team management',
            'Up to 15 team members',
        ],

        # MESSAGE LIMIT
        # Total messages shared across ALL team members
        'message_limit': 5000,

        # USAGE TYPE & PERIOD
        'usage_type': 'allowance',
        'allowance_period': 'weekly',

        # MAX TEAM MEMBERS
        # Maximum number of people who can join this business team
        'max_members': 15,

        # GLOW COLOR
        # Element: Glowing border effect around plan card on hover
        'glow_color': 'rgba(255, 255, 255, 0.6)',

        # SAVINGS TEXT & COLOR (shown when Yearly selected)
        'savings_text': '$16.25 per month',
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
            'Unlimited message posting',
            'Unlimited channel and server selections',
            'Advanced analytics',
            'Team management',
            'Up to 40 team members',
        ],
        'message_limit': -1,  # -1 = unlimited
        'usage_type': 'amount',
        'allowance_period': 'monthly',
        'max_members': 40,
        'glow_color': 'rgba(21, 216, 188, 0.6)',  # Orange-gold glow
        'savings_text': '$24 per month',
        'savings_color': '#15d8bc',
        'button_text': 'Subscribe',
        'max_channels_per_server': -1,  # -1 = unlimited
    },
}
