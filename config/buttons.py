# ==============================================
# BUTTON STYLES CONFIGURATION
# ==============================================
# This file contains all button styles used across the website.
# Each button has its actual CSS values extracted from styles.css
#
# IMPORTANT: requires_confirmation = True means the button will show
# a confirmation dialog before performing the action (e.g., "Are you sure?")
# ==============================================

BUTTONS = {
    # ==========================================
    # LOGIN BUTTON (navbar - when not logged in)
    # ==========================================
    # Used in: Navbar (when user is not logged in)
    # CSS class: .auth-btn.login-btn
    'login': {
        'background': 'transparent',
        'color': '#ffffff',
        'border': '2px solid #ffffff',
        'border_radius': '6px',
        'padding': '0.6rem 1.5rem',
        'font_weight': '700',
        'font_size': '0.95rem',
        'hover_background': 'rgba(255, 255, 255, 0.1)',
        'hover_border_color': '#ffffff',
        'requires_confirmation': False,
    },

    # ==========================================
    # SIGNUP BUTTON (navbar - when not logged in)
    # ==========================================
    # Used in: Navbar (when user is not logged in)
    # CSS class: .auth-btn.signup-btn
    'signup': {
        'background': '#335FFF',  # var(--primary)
        'color': '#ffffff',
        'border': '2px solid #335FFF',
        'border_radius': '6px',
        'padding': '0.6rem 1.5rem',
        'font_weight': '700',
        'font_size': '0.95rem',
        'hover_background': '#4575FF',  # var(--primary-light)
        'hover_border_color': '#4575FF',
        'requires_confirmation': False,
    },

    # ==========================================
    # VIEW PRICING BUTTON (homepage hero section)
    # ==========================================
    # Used in: Homepage hero section
    # CSS class: .view-pricing-btn
    'view_pricing': {
        'background': 'linear-gradient(to bottom, #15d8bc, #006e59)',
        'color': '#ffffff',
        'border': '2px solid #15d8bc',
        'border_radius': '8px',
        'padding': '0.75rem 2rem',
        'font_weight': '700',
        'font_size': '1rem',
        'letter_spacing': '0.5px',
        'hover_transform': 'scale(1.015)',
        'requires_confirmation': False,
    },

    # ==========================================
    # DELETE ACCOUNT BUTTON (settings page)
    # ==========================================
    # Used in: Settings page - Account section
    # CSS class: .delete-account-btn
    'delete_account': {
        'background': 'linear-gradient(to bottom, #991a35, #3b0b15)',
        'color': '#ffffff',
        'border': 'none',
        'border_radius': '6px',
        'padding': '0.75rem 1.5rem',
        'font_weight': '600',
        'font_size': '0.95rem',
        'hover_background': 'linear-gradient(to bottom, #7a152b, #2d0810)',
        'hover_transform': 'scale(1.02)',
        'requires_confirmation': True,  # Shows "Are you sure?" dialog
    },

    # ==========================================
    # SEND MESSAGE BUTTON (personal panel)
    # ==========================================
    # Used in: Personal Panel - Message sending panel
    # CSS class: .send-button
    'send_message': {
        'background': '#335FFF',  # var(--primary)
        'color': '#ffffff',
        'border': 'none',
        'border_radius': '8px',
        'padding': '0.75rem 2rem',
        'font_weight': '700',
        'hover_transform': 'scale(1.015)',
        'requires_confirmation': True,  # Shows confirmation before sending
    },

    # ==========================================
    # PRIMARY BUTTON (general use)
    # ==========================================
    # Used in: Various places - submit buttons, CTA buttons
    # CSS class: .submit-btn, .clear-all-btn, .return-panel-btn
    'primary': {
        'background': '#335FFF',
        'color': '#ffffff',
        'border': 'none',
        'border_radius': '8px',
        'padding': '1rem 2rem',
        'font_weight': '700',
        'font_size': '1rem',
        'letter_spacing': '0.5px',
        'hover_transform': 'scale(1.015)',
        'requires_confirmation': False,
    },

    # ==========================================
    # PURCHASE BUTTON (purchase page plan cards)
    # ==========================================
    # Used in: Purchase page - Plan cards
    # CSS class: .purchase-btn
    'purchase': {
        'background': 'transparent',
        'color': '#ffffff',
        'border': '2px solid #ffffff',
        'border_radius': '6px',
        'padding': '0.75rem 1.5rem',
        'font_weight': '700',
        'font_size': '1rem',
        'hover_background': 'rgba(255, 255, 255, 0.1)',
        'hover_border_color': '#ffffff',
        'requires_confirmation': False,
    },

    # ==========================================
    # LOGOUT BUTTON (various locations)
    # ==========================================
    # Used in: Settings page, some panel areas
    # CSS class: .logout-btn, .logout-btn-settings
    'logout': {
        'background': 'rgba(153, 26, 53, 0.2)',
        'color': '#ffffff',
        'border': '2px solid #991a35',
        'border_radius': '8px',
        'padding': '0.75rem 1.5rem',
        'font_weight': '600',
        'font_size': '0.95rem',
        'letter_spacing': '0.5px',
        'box_shadow': '0 0 15px rgba(153, 26, 53, 0.4)',
        'hover_transform': 'scale(1.015)',
        'requires_confirmation': False,
    },

    # ==========================================
    # MODE TOGGLE BUTTON (purchase page)
    # ==========================================
    # Used in: Purchase page - Personal/Business toggle
    # CSS class: .mode-btn
    'mode_toggle': {
        'background': '#1a1a1d',
        'color': '#ffffff',
        'border': '2px solid transparent',
        'border_radius': '8px',
        'padding': '0.75rem 2rem',
        'font_weight': '600',
        'font_size': '1rem',
        'hover_background': '#212227',
        'hover_border_color': 'rgba(51, 95, 255, 0.3)',
        'active_background': 'rgba(51, 95, 255, 0.15)',
        'active_border_color': '#335FFF',
        'active_color': '#335FFF',
        'requires_confirmation': False,
    },

    # ==========================================
    # HELP BUTTON (login/signup pages)
    # ==========================================
    # Used in: Login/Signup forms - "How do I get my token?"
    # CSS class: .help-btn
    'help': {
        'background': 'none',
        'color': '#72767d',
        'border': 'none',
        'padding': '0.5rem',
        'font_size': '0.9rem',
        'font_weight': '400',
        'hover_color': '#335FFF',
        'hover_text_decoration': 'underline',
        'requires_confirmation': False,
    },

    # ==========================================
    # CLEAR ALL BUTTON (personal panel)
    # ==========================================
    # Used in: Personal Panel - Clear selected channels
    # CSS class: .clear-all-btn
    'clear_all': {
        'background': '#335FFF',
        'color': '#ffffff',
        'border': 'none',
        'border_radius': '8px',
        'padding': '1rem 2rem',
        'font_weight': '700',
        'font_size': '1rem',
        'letter_spacing': '0.5px',
        'hover_transform': 'scale(1.015)',
        'requires_confirmation': False,
    },
}
