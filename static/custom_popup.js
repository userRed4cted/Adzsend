// =============================================================================
// CUSTOM POPUP SYSTEM
// =============================================================================
// Replaces browser alert() and confirm() with styled custom popups

// Simple HTML sanitizer to prevent XSS - allows safe tags only
function sanitizeHtml(html) {
    if (typeof html !== 'string') return '';

    // Create a temporary element
    const temp = document.createElement('div');
    temp.innerHTML = html;

    // Remove dangerous elements
    const dangerous = temp.querySelectorAll('script, iframe, object, embed, form, input, button, link, meta, style');
    dangerous.forEach(el => el.remove());

    // Remove dangerous attributes from all elements
    const allElements = temp.querySelectorAll('*');
    allElements.forEach(el => {
        // Remove event handlers and dangerous attributes
        const attrs = [...el.attributes];
        attrs.forEach(attr => {
            const name = attr.name.toLowerCase();
            if (name.startsWith('on') || name === 'href' && attr.value.toLowerCase().startsWith('javascript:') ||
                name === 'src' && !attr.value.match(/^(https?:\/\/|\/|data:image\/)/i)) {
                el.removeAttribute(attr.name);
            }
        });
    });

    return temp.innerHTML;
}

let currentPopup = null;
let popupResolve = null;
let tokenUpdateCallback = null;
let tokenDebounceTimer = null; // Track debounce timer for cleanup
let isTokenPopupOpen = false; // Track if token popup is open (to prevent click-off closing)

// Create popup overlay and structure
function initCustomPopup() {
    // Check if already initialized
    if (document.getElementById('custom-popup-overlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'custom-popup-overlay';
    overlay.className = 'custom-popup-overlay';

    overlay.innerHTML = `
        <div class="custom-popup" id="custom-popup">
            <button class="custom-popup-close" id="custom-popup-close">&times;</button>
            <h2 class="custom-popup-title" id="custom-popup-title"></h2>
            <p class="custom-popup-text" id="custom-popup-text"></p>
            <div class="custom-popup-content" id="custom-popup-content" style="display: none;"></div>
            <div id="custom-popup-token-section" style="display: none;">
                <div class="custom-popup-status" id="custom-popup-token-status">Enter a token.</div>
                <input type="text" class="custom-popup-input" id="custom-popup-token-input" placeholder="Account token">
            </div>
            <button class="custom-popup-btn" id="custom-popup-btn">Ok</button>
        </div>
    `;

    document.body.appendChild(overlay);

    // Event listeners
    const closeBtn = document.getElementById('custom-popup-close');
    const actionBtn = document.getElementById('custom-popup-btn');

    closeBtn.addEventListener('click', () => {
        // X button always works (resets token popup state)
        isTokenPopupOpen = false;
        closePopup(false);
    });
    actionBtn.addEventListener('click', () => closePopup(true));

    // Click outside to close (disabled for token popup)
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay && !isTokenPopupOpen) {
            closePopup(false);
        }
    });

    // ESC key to close (disabled for token popup)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && currentPopup && !isTokenPopupOpen) {
            closePopup(false);
        }
    });
}

// Show custom popup
function showCustomPopup(title, message, buttonText = 'Ok', options = {}) {
    return new Promise((resolve) => {
        initCustomPopup();

        // If a popup is already showing, close it first and resolve its promise
        if (currentPopup && popupResolve) {
            const prevResolve = popupResolve;
            popupResolve = null;
            currentPopup = null;
            prevResolve(false);
        }

        const overlay = document.getElementById('custom-popup-overlay');
        const closeBtn = document.getElementById('custom-popup-close');
        const titleEl = document.getElementById('custom-popup-title');
        const textEl = document.getElementById('custom-popup-text');
        const btnEl = document.getElementById('custom-popup-btn');
        const contentEl = document.getElementById('custom-popup-content');
        const tokenSection = document.getElementById('custom-popup-token-section');

        // Ensure overlay is reset before showing new popup
        overlay.classList.remove('active');

        // Reset token popup state
        isTokenPopupOpen = false;

        // Reset visibility
        contentEl.style.display = 'none';
        contentEl.innerHTML = '';
        tokenSection.style.display = 'none';
        btnEl.style.display = 'block';
        closeBtn.style.display = 'block';

        // Support HTML content if allowHtml is true
        if (options.allowHtml) {
            titleEl.textContent = title;  // Title is always plain text
            textEl.innerHTML = sanitizeHtml(message);   // Message sanitized for safety
            textEl.style.display = message ? 'block' : 'none';

            // Add event listeners for collapsible sections after HTML is inserted
            setTimeout(() => {
                const resultHeaders = textEl.querySelectorAll('.result-header');
                resultHeaders.forEach(header => {
                    header.addEventListener('click', function() {
                        this.parentElement.classList.toggle('collapsed');
                    });
                });
            }, 0);
        } else {
            titleEl.textContent = title;
            textEl.textContent = message;
            textEl.style.display = message ? 'block' : 'none';
        }

        // Hide title if empty
        titleEl.style.display = title ? 'block' : 'none';

        // Support scrollable content box
        if (options.contentHtml) {
            contentEl.innerHTML = sanitizeHtml(options.contentHtml);
            contentEl.style.display = 'block';
        }

        // Hide button if specified and remove content margin
        if (options.hideButton) {
            btnEl.style.display = 'none';
            contentEl.style.marginBottom = '0';
        } else {
            btnEl.textContent = buttonText;
            contentEl.style.marginBottom = '1rem';
        }

        currentPopup = overlay;
        popupResolve = resolve;

        // Show with animation (use requestAnimationFrame to ensure DOM is ready)
        requestAnimationFrame(() => {
            overlay.classList.add('active');
        });
    });
}

// Close popup
function closePopup(result) {
    const overlay = document.getElementById('custom-popup-overlay');
    if (!overlay) return;

    // Clear any pending debounce timer
    if (tokenDebounceTimer) {
        clearTimeout(tokenDebounceTimer);
        tokenDebounceTimer = null;
    }

    // Prevent double-closing
    if (!overlay.classList.contains('active')) {
        // Still resolve if there's a pending promise
        if (popupResolve) {
            popupResolve(result);
            popupResolve = null;
        }
        currentPopup = null;
        return;
    }

    overlay.classList.remove('active');

    // Reset token section
    const tokenSection = document.getElementById('custom-popup-token-section');
    const tokenInput = document.getElementById('custom-popup-token-input');
    const tokenStatus = document.getElementById('custom-popup-token-status');
    if (tokenSection) tokenSection.style.display = 'none';
    if (tokenInput) tokenInput.value = '';
    if (tokenStatus) {
        tokenStatus.textContent = 'Enter a token.';
        tokenStatus.style.color = '#991a35';
    }

    // Call token update callback if closing without success
    if (tokenUpdateCallback && !result) {
        tokenUpdateCallback(false);
        tokenUpdateCallback = null;
    }

    if (popupResolve) {
        popupResolve(result);
        popupResolve = null;
    }

    currentPopup = null;
}

// Alert replacement (returns Promise that resolves when closed)
function customAlert(title, message, options = {}) {
    return showCustomPopup(title, message, 'Ok', options);
}

// Confirm replacement (returns Promise that resolves to true/false)
function customConfirm(title, message, buttonText = 'Ok', options = {}) {
    return showCustomPopup(title, message, buttonText, options);
}

// Token update popup for invalid/changed tokens
function showTokenUpdatePopup(accountInfo, onClose) {
    return new Promise((resolve) => {
        initCustomPopup();

        const overlay = document.getElementById('custom-popup-overlay');
        const closeBtn = document.getElementById('custom-popup-close');
        const titleEl = document.getElementById('custom-popup-title');
        const textEl = document.getElementById('custom-popup-text');
        const btnEl = document.getElementById('custom-popup-btn');
        const contentEl = document.getElementById('custom-popup-content');
        const tokenSection = document.getElementById('custom-popup-token-section');
        const tokenInput = document.getElementById('custom-popup-token-input');
        const tokenStatus = document.getElementById('custom-popup-token-status');

        // Reset
        contentEl.style.display = 'none';
        contentEl.innerHTML = '';

        // Set content
        titleEl.textContent = 'Discord account token';
        textEl.textContent = `The account token of ${accountInfo.username || 'Unknown'} (${accountInfo.discord_id || 'Unknown'}) has changed. To continue using this account, update the token.`;

        // Show token section, hide main button (keep X button visible)
        tokenSection.style.display = 'block';
        btnEl.style.display = 'none';

        // Mark token popup as open (prevents click-off closing)
        isTokenPopupOpen = true;

        // Store callback for when popup closes
        tokenUpdateCallback = onClose;

        currentPopup = overlay;
        popupResolve = resolve;

        // Clear any previous debounce timer
        if (tokenDebounceTimer) {
            clearTimeout(tokenDebounceTimer);
            tokenDebounceTimer = null;
        }

        // Token input handler with debounce
        const handleTokenInput = async () => {
            // Get fresh reference to input
            const currentInput = document.getElementById('custom-popup-token-input');
            const currentStatus = document.getElementById('custom-popup-token-status');
            if (!currentInput || !currentStatus) return;

            const token = currentInput.value.trim();

            if (!token) {
                currentStatus.textContent = 'Enter a token.';
                currentStatus.style.color = '#991a35';
                return;
            }

            // Check for quotation marks
            if (token.includes('"') || token.includes("'")) {
                currentStatus.textContent = 'Remove quotation marks.';
                currentStatus.style.color = '#991a35';
                return;
            }

            currentStatus.textContent = 'Verifying token.';
            currentStatus.style.color = '#81828A';

            try {
                const response = await fetch('/api/linked-accounts/update-token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': window.csrfToken || ''
                    },
                    body: JSON.stringify({
                        account_id: accountInfo.account_id,
                        token: token
                    })
                });

                const data = await response.json();

                if (data.success) {
                    currentStatus.textContent = 'Success.';
                    currentStatus.style.color = '#15d8bc';

                    // Close popup after short delay
                    setTimeout(() => {
                        isTokenPopupOpen = false;
                        if (tokenUpdateCallback) {
                            tokenUpdateCallback(true);
                            tokenUpdateCallback = null;
                        }
                        closePopup(true);
                    }, 500);
                } else {
                    // Ensure period at end of error message
                    const errorMsg = data.error || 'Invalid token';
                    currentStatus.textContent = errorMsg.endsWith('.') ? errorMsg : errorMsg + '.';
                    currentStatus.style.color = '#991a35';
                }
            } catch (error) {
                currentStatus.textContent = 'Network error.';
                currentStatus.style.color = '#991a35';
            }
        };

        // Get fresh token input and set up listener
        const freshTokenInput = document.getElementById('custom-popup-token-input');
        freshTokenInput.value = '';

        // Remove old listeners by cloning
        const newInput = freshTokenInput.cloneNode(true);
        freshTokenInput.parentNode.replaceChild(newInput, freshTokenInput);

        // Add input listener with debounce
        newInput.addEventListener('input', () => {
            clearTimeout(tokenDebounceTimer);
            tokenDebounceTimer = setTimeout(handleTokenInput, 500);
        });

        // Reset status
        const freshStatus = document.getElementById('custom-popup-token-status');
        freshStatus.textContent = 'Enter a token.';
        freshStatus.style.color = '#991a35';

        // Show popup
        overlay.classList.add('active');

        // Focus input
        setTimeout(() => newInput.focus(), 100);
    });
}

// Show suspended account popup
function showSuspendedAccountPopup(accountInfo) {
    const username = accountInfo.username || 'Unknown';
    const discordId = accountInfo.discord_id || 'Unknown';

    return new Promise((resolve) => {
        showCustomPopup(
            'Whoops, no action is required',
            `It seems ${username} (${discordId}) is unavailable, this can be due to moderation actions against your account, account deletion, etc. Your account has been unlinked, feel free to link a new account!`,
            'Link another account'
        ).then(() => {
            // Open settings and navigate to Discord accounts page
            if (typeof openSettings === 'function') {
                openSettings();
                setTimeout(() => {
                    const discordAccountsBtn = document.querySelector('[data-settings-page="discord-accounts"]');
                    if (discordAccountsBtn) {
                        discordAccountsBtn.click();
                    }
                }, 100);
            }
            resolve();
        });
    });
}

// Show user suspension popup (when Adzsend account is suspended)
function showSuspendPopup() {
    initCustomPopup();

    const overlay = document.getElementById('custom-popup-overlay');
    const popup = document.getElementById('custom-popup');
    const closeBtn = document.getElementById('custom-popup-close');
    const titleEl = document.getElementById('custom-popup-title');
    const textEl = document.getElementById('custom-popup-text');
    const btnEl = document.getElementById('custom-popup-btn');
    const contentEl = document.getElementById('custom-popup-content');
    const tokenSection = document.getElementById('custom-popup-token-section');

    // Reset
    contentEl.style.display = 'none';
    contentEl.innerHTML = '';
    tokenSection.style.display = 'none';

    // Set content
    titleEl.textContent = 'Account suspended';
    titleEl.style.display = 'block';
    textEl.textContent = 'Your account has been suspended, if you want to appeal or believe this was a mistake, contact support.';
    textEl.style.display = 'block';
    btnEl.textContent = 'Resolve';
    btnEl.style.display = 'block';

    // Override close behavior - just close popup and return to analytics
    const handleClose = () => {
        overlay.classList.remove('active');
        currentPopup = null;
        // Force back to analytics tab
        const analyticsBtn = document.querySelector('[data-page="analytics"]');
        if (analyticsBtn) analyticsBtn.click();
    };

    // Remove old listeners by cloning
    const newCloseBtn = closeBtn.cloneNode(true);
    closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
    newCloseBtn.addEventListener('click', handleClose);

    // Click outside closes popup
    const handleOverlayClick = (e) => {
        if (e.target === overlay) {
            handleClose();
        }
    };
    overlay.removeEventListener('click', handleOverlayClick);
    overlay.addEventListener('click', handleOverlayClick);

    // Button redirects to support page
    const newBtn = btnEl.cloneNode(true);
    btnEl.parentNode.replaceChild(newBtn, btnEl);
    newBtn.textContent = 'Resolve';
    newBtn.addEventListener('click', () => {
        window.location.href = '/support';
    });

    // ESC key closes popup
    const handleEsc = (e) => {
        if (e.key === 'Escape' && overlay.classList.contains('active')) {
            handleClose();
        }
    };
    document.addEventListener('keydown', handleEsc);

    // Show popup
    overlay.classList.add('active');
    currentPopup = overlay;
}

// Check if bridge is connected, show popup if not
// Returns true if bridge is connected, false otherwise
async function checkBridgeConnected() {
    try {
        const response = await fetch('/api/bridge/status');
        const data = await response.json();

        if (data.success && data.is_online) {
            return true;
        }

        // Bridge not connected - show popup
        const result = await showCustomPopup(
            'Adzsend Bridge',
            'In order to send messages, Adzsend Bridge must be connected.',
            'View'
        );

        if (result) {
            // User clicked View - go to settings/bridge page
            if (typeof openSettings === 'function') {
                openSettings();
                setTimeout(() => {
                    const bridgeBtn = document.querySelector('[data-settings-page="bridge"]');
                    if (bridgeBtn) {
                        bridgeBtn.click();
                    }
                }, 100);
            }
        }

        return false;
    } catch (error) {
        console.error('Error checking bridge status:', error);
        // If we can't check, assume not connected
        await customAlert('Error', 'Unable to check bridge status. Please try again.');
        return false;
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCustomPopup);
} else {
    initCustomPopup();
}
