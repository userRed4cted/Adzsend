# API endpoint for user account deletion
# This will be imported in app.py

def delete_user_account(user_id):
    """
    Completely delete a user and all their data from the database.
    Also cancels any active Stripe subscriptions and deletes the Stripe customer.
    Returns (success: bool, error: str or None)
    """
    import sqlite3
    import os
    from database.models import DATABASE

    try:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get user's Stripe subscription ID and customer ID before deleting
        cursor.execute('SELECT stripe_subscription_id, stripe_customer_id FROM users WHERE id = ?', (user_id,))
        user_row = cursor.fetchone()

        stripe_subscription_id = user_row['stripe_subscription_id'] if user_row else None
        stripe_customer_id = user_row['stripe_customer_id'] if user_row else None

        # Cancel Stripe subscription and delete customer if exists
        if os.getenv('STRIPE_SECRET_KEY'):
            try:
                import stripe
                stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

                # Cancel subscription first (if exists)
                if stripe_subscription_id:
                    try:
                        stripe.Subscription.cancel(stripe_subscription_id)
                    except stripe.error.InvalidRequestError:
                        # Subscription might already be cancelled
                        pass

                # Delete the Stripe customer entirely (this also cancels any remaining subscriptions)
                # Since account deletion is permanent, we fully remove the customer from Stripe
                if stripe_customer_id:
                    try:
                        stripe.Customer.delete(stripe_customer_id)
                    except stripe.error.InvalidRequestError:
                        # Customer might already be deleted
                        pass
            except Exception:
                # Continue with deletion even if Stripe operations fail
                pass

        # Delete from all tables where user data exists
        tables_to_delete = [
            ('linked_discord_accounts', 'user_id'),
            ('discord_account_channels', 'user_id'),
            ('user_data', 'user_id'),
            ('usage', 'user_id'),
            ('subscriptions', 'user_id'),
            ('business_team_members', 'user_id'),
            ('bridge_connections', 'user_id'),
            ('verification_codes', 'email'),  # Need to get email first
            ('auth_rate_limits', 'email'),
        ]

        # Get email for verification_codes deletion
        cursor.execute('SELECT email FROM users WHERE id = ?', (user_id,))
        email_row = cursor.fetchone()
        user_email = email_row['email'] if email_row else None

        # Delete user's business team if they own one
        cursor.execute('SELECT id FROM business_teams WHERE owner_user_id = ?', (user_id,))
        team = cursor.fetchone()
        if team:
            team_id = team['id']
            cursor.execute('DELETE FROM business_team_members WHERE team_id = ?', (team_id,))
            cursor.execute('DELETE FROM business_teams WHERE id = ?', (team_id,))

        # Delete from tables with user_id
        for table, column in tables_to_delete:
            try:
                if column == 'email' and user_email:
                    cursor.execute(f'DELETE FROM {table} WHERE {column} = ?', (user_email.lower(),))
                elif column != 'email':
                    cursor.execute(f'DELETE FROM {table} WHERE {column} = ?', (user_id,))
            except sqlite3.OperationalError:
                # Table might not exist, continue
                pass

        # Finally delete the user
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

        conn.commit()

        # VACUUM to permanently remove deleted data
        cursor.execute('VACUUM')

        conn.close()

        return True, None

    except Exception as e:
        return False, str(e)
