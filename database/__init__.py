# Database Package
# All database models and operations

from .models import (
    get_db, init_db, get_user_by_discord_id, get_user_by_adzsend_id, get_user_by_id, update_user_token,
    set_subscription, get_active_subscription, can_send_message,
    record_successful_send, get_plan_status, update_user_session,
    validate_user_session, save_user_data, get_user_data,
    get_all_users_for_admin, get_user_admin_details, ban_user, unban_user,
    flag_user, unflag_user, delete_user_account_admin,
    get_decrypted_token, delete_user, delete_user_by_email, update_user_profile,
    get_business_team_by_owner, get_business_team_by_member, get_team_members,
    get_team_member_stats, update_team_member_info, get_team_member_count,
    add_team_member, remove_team_member, remove_team_member_by_adzsend_id, update_team_message,
    create_business_team, is_business_plan_owner, is_business_team_member,
    cancel_subscription, activate_free_plan, get_business_plan_status, increment_business_usage,
    get_team_invitations, accept_team_invitation, deny_team_invitation,
    clear_all_invitations, leave_team, get_current_team_for_member,
    remove_team_member_from_list, auto_deny_pending_invitations,
    # Email authentication functions
    get_user_by_email, create_user_with_email, create_verification_code,
    verify_code, get_resend_status, resend_verification_code, clear_rate_limit,
    is_code_rate_limited, update_user_email, has_active_verification_code,
    # Discord OAuth account linking functions
    save_discord_oauth, get_discord_oauth_status, get_discord_oauth_info,
    complete_discord_link, unlink_discord_oauth, is_discord_linked,
    get_user_by_internal_id, full_unlink_discord_account, update_discord_profile,
    # Admin functions
    get_purchase_history,
    # Team member analytics functions
    get_member_analytics, get_member_daily_stats, get_member_join_date,
    record_daily_stat,
    # Personal analytics functions
    get_personal_daily_stats,
    get_personal_analytics_summary,
    # Linked Discord accounts functions
    add_linked_discord_account, get_linked_discord_accounts, get_linked_discord_account_count,
    get_linked_discord_account_by_id, unlink_discord_account,
    update_linked_discord_account_profile, mark_linked_account_invalid, mark_linked_account_valid,
    search_linked_discord_accounts,
    # Per-Discord-account channel storage
    save_discord_account_channels, get_discord_account_channels, clear_user_channel_selections,
    # Sent message verification
    log_sent_message, check_sent_message, cleanup_old_sent_messages,
    # Bridge connection functions
    generate_bridge_secret_key, verify_bridge_secret_key, validate_bridge_secret_key,
    create_or_get_bridge_connection, get_bridge_connection, get_bridge_connection_by_adzsend_id,
    regenerate_bridge_secret_key, set_bridge_online, set_bridge_offline,
    is_bridge_online, get_bridge_status,
    # Stripe integration functions
    update_user_stripe_customer_id, update_user_stripe_subscription_id,
    get_user_by_stripe_customer_id, extend_subscription_by_stripe_subscription_id,
    # Scheduled plan change functions (for downgrades)
    set_scheduled_plan_change, get_scheduled_plan_change, clear_scheduled_plan_change
)
