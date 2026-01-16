// =============================================================================
// CUSTOM POPUP SYSTEM
// =============================================================================
// Replaces browser alert() and confirm() with styled custom popups

let currentPopup = null;
let popupResolve = null;
let tokenUpdateCallback = null;

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
                <div class="custom-popup-status" id="custom-popup-token-status">Enter a token</div>
                <input type="text" class="custom-popup-input" id="custom-popup-token-input" placeholder="Account token">
            </div>
            <button class="custom-popup-btn" id="custom-popup-btn">Ok</button>
        </div>
    `;

    document.body.appendChild(overlay);

    // Event listeners
    const closeBtn = document.getElementById('custom-popup-close');
    const actionBtn = document.getElementById('custom-popup-btn');

    closeBtn.addEventListener('click', () => closePopup(false));
    actionBtn.addEventListener('click', () => closePopup(true));

    // Click outside to close
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) {
            closePopup(false);
        }
    });

    // ESC key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && currentPopup) {
            closePopup(false);
        }
    });
}

// Show custom popup
function showCustomPopup(title, message, buttonText = 'Ok', options = {}) {
    return new Promise((resolve) => {
        initCustomPopup();

        const overlay = document.getElementById('custom-popup-overlay');
        const titleEl = document.getElementById('custom-popup-title');
        const textEl = document.getElementById('custom-popup-text');
        const btnEl = document.getElementById('custom-popup-btn');
        const contentEl = document.getElementById('custom-popup-content');
        const tokenSection = document.getElementById('custom-popup-token-section');

        // Reset visibility
        contentEl.style.display = 'none';
        contentEl.innerHTML = '';
        tokenSection.style.display = 'none';
        btnEl.style.display = 'block';

        // Support HTML content if allowHtml is true
        if (options.allowHtml) {
            titleEl.textContent = title;  // Title is always plain text
            textEl.innerHTML = message;   // Message can be HTML
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
            contentEl.innerHTML = options.contentHtml;
            contentEl.style.display = 'block';
        }

        // Hide button if specified
        if (options.hideButton) {
            btnEl.style.display = 'none';
        } else {
            btnEl.textContent = buttonText;
        }

        currentPopup = overlay;
        popupResolve = resolve;

        // Show with animation
        overlay.classList.add('active');
    });
}

// Close popup
function closePopup(result) {
    const overlay = document.getElementById('custom-popup-overlay');
    if (!overlay) return;

    overlay.classList.remove('active');

    // Reset token section
    const tokenSection = document.getElementById('custom-popup-token-section');
    const tokenInput = document.getElementById('custom-popup-token-input');
    const tokenStatus = document.getElementById('custom-popup-token-status');
    if (tokenSection) tokenSection.style.display = 'none';
    if (tokenInput) tokenInput.value = '';
    if (tokenStatus) {
        tokenStatus.textContent = 'Enter a token';
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
        textEl.textContent = `The account token of ${accountInfo.username} (${accountInfo.discord_id}) has changed, please update it if you want to continue using it below.`;

        // Show token section, hide button
        tokenSection.style.display = 'block';
        btnEl.style.display = 'none';
        tokenInput.value = '';
        tokenStatus.textContent = 'Enter a token';
        tokenStatus.style.color = '#991a35';

        // Store callback for when popup closes
        tokenUpdateCallback = onClose;

        currentPopup = overlay;
        popupResolve = resolve;

        // Token input handler with debounce
        let debounceTimer = null;
        const handleTokenInput = async () => {
            const token = tokenInput.value.trim();

            if (!token) {
                tokenStatus.textContent = 'Enter a token';
                tokenStatus.style.color = '#991a35';
                return;
            }

            // Check for quotation marks
            if (token.includes('"') || token.includes("'")) {
                tokenStatus.textContent = 'Remove quotation marks';
                tokenStatus.style.color = '#991a35';
                return;
            }

            tokenStatus.textContent = 'Verifying...';
            tokenStatus.style.color = '#81828A';

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
                    tokenStatus.textContent = 'Token updated!';
                    tokenStatus.style.color = '#15d8bc';

                    // Close popup after short delay
                    setTimeout(() => {
                        if (tokenUpdateCallback) {
                            tokenUpdateCallback(true);
                            tokenUpdateCallback = null;
                        }
                        closePopup(true);
                    }, 500);
                } else {
                    tokenStatus.textContent = data.error || 'Invalid token';
                    tokenStatus.style.color = '#991a35';
                }
            } catch (error) {
                tokenStatus.textContent = 'Network error';
                tokenStatus.style.color = '#991a35';
            }
        };

        // Remove old listener and add new one
        const newInput = tokenInput.cloneNode(true);
        tokenInput.parentNode.replaceChild(newInput, tokenInput);
        newInput.addEventListener('input', () => {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(handleTokenInput, 500);
        });

        // Show popup
        overlay.classList.add('active');

        // Focus input
        setTimeout(() => newInput.focus(), 100);
    });
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCustomPopup);
} else {
    initCustomPopup();
}
