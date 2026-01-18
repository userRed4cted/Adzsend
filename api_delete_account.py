# API endpoint for user account deletion
# This will be imported in app.py

def delete_user_account(user_id):
    """
    Completely delete a user and all their data from the database.
    Returns (success: bool, error: str or None)
    """
    import sqlite3
    from config import DATABASE_PATH

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # Delete from all tables where user data exists
        tables_to_delete = [
            ('users', 'id'),
            ('discord_accounts', 'user_id'),
            ('user_settings', 'user_id'),
            ('user_sessions', 'user_id'),
            ('verification_codes', 'user_id'),
            ('teams', 'owner_id'),
            ('team_members', 'user_id'),
            ('team_invitations', 'user_id'),
            ('team_invitations', 'inviter_id'),
            ('purchases', 'user_id'),
            ('subscriptions', 'user_id'),
            ('usage_tracking', 'user_id'),
            ('discord_oauth', 'user_id'),
        ]

        for table, column in tables_to_delete:
            try:
                cursor.execute(f'DELETE FROM {table} WHERE {column} = ?', (user_id,))
            except sqlite3.OperationalError:
                # Table might not exist, continue
                pass

        conn.commit()
        conn.close()

        return True, None

    except Exception as e:
        print(f"[DELETE ACCOUNT] Error deleting user {user_id}: {str(e)}")
        return False, str(e)
