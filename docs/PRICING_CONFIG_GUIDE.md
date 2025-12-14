# Purchase Page Configuration Guide

## Config File Location
**File to edit:** `config/plans.py`

This file controls all pricing, features, and plan details for the purchase page.

## Configuration Options

### 1. Yearly Discount Percentage
```python
YEARLY_DISCOUNT_PERCENT = 17  # This means 17% off when paying yearly
```
- This applies to ALL subscription plans
- When users toggle to "Yearly", prices are calculated automatically
- Plan cards show savings text when yearly is selected

### 2. Subscription Plans

Each subscription plan has the following configurable options:

```python
SUBSCRIPTION_PLANS = {
    'plan_id': {
        'name': 'Plan Name',           # Display name
        'price_monthly': 9.99,          # Monthly price in dollars
        'price_yearly': 99.99,          # Yearly total price in dollars
        'features': [                   # List of features to display
            'Feature 1',
            'Feature 2',
            'Feature 3'
        ],
        'message_limit': -1,            # -1 for unlimited, or a number for limit
        'usage_type': 'allowance',      # 'allowance' (resets) or 'amount' (fixed total)
        'allowance_period': 'monthly',  # 'daily', 'weekly', 'monthly' (only for allowance type)
        'glow_color': 'rgba(51, 95, 255, 0.6)',  # Glow effect color (RGBA)
        'savings_text': '$8.33 per month',  # Custom text shown when yearly is selected
        'button_text': 'Subscribe'      # Button text
    }
}
```

**Important Notes:**
- `price_monthly`: Regular monthly price
- `price_yearly`: Total yearly price
- `savings_text`: Custom text shown on plan card when yearly billing is selected
- `usage_type`: Controls how message limits work
  - `'allowance'` - Limit resets after the specified period
  - `'amount'` - Fixed total for entire plan duration, no resets
- `allowance_period`: Only used when usage_type is 'allowance'
  - Options: `'daily'`, `'weekly'`, `'monthly'`

### 3. One-Time Purchase Plans

```python
ONE_TIME_PLANS = {
    'plan_id': {
        'name': '1 Day',
        'price': 2.99,                  # One-time price in dollars
        'features': [
            '1 day access',
            '50 messages total'
        ],
        'message_limit': 50,
        'usage_type': 'amount',         # Usually 'amount' for one-time purchases
        'allowance_period': None,       # None for 'amount' type
        'duration_days': 1,             # How many days the plan lasts
        'glow_color': 'rgba(100, 255, 100, 0.6)',
        'button_text': 'Purchase'
    }
}
```

### 4. Business Plans

```python
BUSINESS_PLANS = {
    'plan_id': {
        'name': 'Business Starter',
        'price_monthly': 20,
        'price_yearly': 195,
        'features': [
            '5000 messages per week across all members',
            'Up to 15 team members'
        ],
        'message_limit': 5000,
        'usage_type': 'allowance',
        'allowance_period': 'weekly',
        'max_members': 15,              # Maximum team members (business-specific)
        'glow_color': 'rgba(255, 215, 0, 0.6)',
        'savings_text': '$16.25 per month',
        'button_text': 'Subscribe'
    }
}
```

## Billing Toggle

The purchase page has a simple Monthly/Yearly toggle switch:
- **Monthly**: Shows `price_monthly` with "PER MONTH"
- **Yearly**: Shows `price_yearly` with "PER YEAR" and displays `savings_text`

## Color Guide for Glow Effects

Use RGBA colors for the glow effect:
- `rgba(R, G, B, A)` where:
  - R, G, B are 0-255 (red, green, blue)
  - A is 0-1 (transparency, 0.6 recommended)

Common colors:
- White: `rgba(255, 255, 255, 0.6)`
- Blue: `rgba(51, 95, 255, 0.6)`
- Gold: `rgba(255, 215, 0, 0.6)`
- Purple: `rgba(188, 83, 207, 0.6)`
- Pink: `rgba(218, 83, 207, 0.6)`

## Pricing Format

The purchase page automatically handles both decimal and whole number prices:

**Decimal Prices**:
```python
'price': 2.99   # Displays as: $2.99
```

**Whole Number Prices**:
```python
'price': 5      # Displays as: $5
```

## Tips

1. **Keep feature lists concise** - 2-4 features per plan is ideal
2. **Use clear feature names** - Be specific about what's included
3. **Price format** - Use numbers like `9.99` or `10`, not strings
4. **Test your changes** - Save the file and refresh the purchase page
5. **Usage types** - See [USAGE_TYPES_GUIDE.md](USAGE_TYPES_GUIDE.md) for details
