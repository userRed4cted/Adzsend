# Usage Types Configuration Guide

## Overview
The usage types system controls how message limits are applied and reset for each plan.

## Config File Location
**File to edit:** `config/plans.py`

## Usage Types

### 1. Allowance
**Usage:** `'usage_type': 'allowance'`

The message limit resets after a specified time period. Ideal for subscription plans.

**Required Field:** `'allowance_period'`

**Available Periods:**
- `'daily'` - Resets every day at midnight
- `'weekly'` - Resets every week
- `'monthly'` - Resets every month

**Example:**
```python
'regular': {
    'name': 'Regular',
    'price_monthly': 7,
    'price_yearly': 75,
    'message_limit': 500,
    'usage_type': 'allowance',
    'allowance_period': 'weekly',  # Resets every week
}
```

### 2. Amount
**Usage:** `'usage_type': 'amount'`

Fixed total for the entire plan duration with NO resets. Once used up, no more messages until plan expires or is renewed.

**Required Field:** `'allowance_period': None`

**Example:**
```python
'1day': {
    'name': '1 Day Pass',
    'price': 2.50,
    'message_limit': 50,
    'usage_type': 'amount',
    'allowance_period': None,  # No reset
    'duration_days': 1,
}
```

## Configuration Examples

### Monthly Subscription with Weekly Reset
```python
'pro': {
    'name': 'Pro',
    'price_monthly': 15,
    'price_yearly': 160,
    'message_limit': 5000,
    'usage_type': 'allowance',
    'allowance_period': 'weekly',
}
```

### One-Time Purchase with Fixed Amount
```python
'weekend': {
    'name': '3 Day Pass',
    'price': 5,
    'message_limit': 150,
    'usage_type': 'amount',
    'allowance_period': None,
    'duration_days': 3,
}
```

### Unlimited Plan
```python
'unlimited': {
    'name': 'Unlimited',
    'price_monthly': 25,
    'message_limit': -1,  # -1 means unlimited
    'usage_type': 'allowance',
    'allowance_period': 'monthly',
}
```

## Important Notes

1. **Usage Only Counts Successful Sends** - Failed sends don't count against the limit
2. **Unlimited Plans** - When `message_limit` is `-1`, usage type settings are ignored
3. **One-Time Plans** - Usually use 'amount' type (no reset during plan period)
4. **Subscription Plans** - Usually use 'allowance' type with periodic resets
