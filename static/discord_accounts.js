// =============================================================================
// DISCORD ACCOUNTS MANAGEMENT
// =============================================================================

let allDiscordAccounts = [];
let accountLimit = 3;
let currentAccountCount = 0;
let canLinkMoreAccounts = true;
let pendingLinkAccount = null; // Store pending account data after OAuth

// Initialize Discord accounts page
async function initDiscordAccountsPage() {
    // Set up search listener
    const searchInput = document.getElementById('discord-accounts-search-input');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(handleDiscordAccountsSearch, 300));
    }

    // Load accounts
    await loadDiscordAccounts();
}

// Load all Discord accounts
async function loadDiscordAccounts() {
    try {
        const response = await fetch('/api/linked-accounts');
        const data = await response.json();

        if (data.success) {
            allDiscordAccounts = data.accounts || [];
            accountLimit = data.limit || 3;
            currentAccountCount = data.count || 0;
            canLinkMoreAccounts = data.can_link || false;
            renderDiscordAccounts(allDiscordAccounts);
        } else {
            console.error('Failed to load Discord accounts:', data.error);
        }
    } catch (error) {
        console.error('Error loading Discord accounts:', error);
    } finally {
        // ALWAYS hide loading and show content, success or fail
        const loadingEl = document.getElementById('discord-accounts-loading');
        const contentEl = document.getElementById('discord-accounts-content');
        if (loadingEl) loadingEl.style.display = 'none';
        if (contentEl) {
            contentEl.style.opacity = '1';
            contentEl.style.pointerEvents = 'auto';
        }
    }
}

// Render Discord accounts
function renderDiscordAccounts(accounts) {
    const container = document.getElementById('discord-accounts-list-view');
    if (!container) return;

    container.innerHTML = '';

    // Always add "Link Account" card (disabled if at limit)
    const linkCard = createLinkAccountCardList();
    container.appendChild(linkCard);

    // If there's a pending link, add the pending card right after
    if (pendingLinkAccount) {
        const pendingCard = createPendingLinkCard();
        container.appendChild(pendingCard);
    }

    // Add linked account cards
    accounts.forEach(account => {
        const card = createAccountCardList(account);
        container.appendChild(card);
    });
}

// Create "Link Account" card for list view
function createLinkAccountCardList() {
    const card = document.createElement('div');
    card.className = 'team-current-profile';
    card.style.position = 'relative';
    card.style.marginBottom = '8px';
    card.style.display = 'flex';
    card.style.background = '#121215';
    card.style.border = '1px solid #222225';
    card.style.borderRadius = '6px';
    card.style.padding = '13px';

    const avatarUrl = '/static/discordlogo.png';
    const isDisabled = !canLinkMoreAccounts || pendingLinkAccount !== null;

    // Apply disabled styling
    if (isDisabled) {
        card.style.opacity = '0.5';
        card.style.cursor = 'not-allowed';
        card.style.pointerEvents = 'none';
    } else {
        card.style.cursor = 'pointer';
    }

    card.innerHTML = `
        <div class="team-current-avatar" style="background: #1A1A1E;">
            <img src="${avatarUrl}" alt="Discord" style="width: 100%; height: 100%; object-fit: contain; padding: 6px;">
        </div>
        <div class="team-current-info">
            <span class="team-current-id">Link a Discord account</span>
            <span class="team-current-id" style="color: #81828A; font-size: 0.85rem;">(${currentAccountCount}/${accountLimit} Linked)</span>
        </div>
    `;

    if (!isDisabled) {
        card.addEventListener('click', initiateAccountLink);
    }

    return card;
}

// Create pending link card (shown when OAuth completed but waiting for token)
function createPendingLinkCard() {
    const card = document.createElement('div');
    card.className = 'team-current-profile';
    card.style.cursor = 'default';
    card.style.marginBottom = '8px';
    card.style.display = 'flex';
    card.style.background = '#121215';
    card.style.border = '1px solid #222225';
    card.style.borderRadius = '6px';
    card.style.padding = '13px';

    card.innerHTML = `
        <div class="team-current-avatar" style="background: #1A1A1E; position: relative;">
            <img src="${getDiscordAvatarUrl(pendingLinkAccount.discord_id, pendingLinkAccount.avatar)}" alt="${pendingLinkAccount.username}">
        </div>
        <div class="team-current-info" style="display: flex; flex-direction: column; align-items: flex-start; gap: 0.25rem; flex: 1;">
            <span class="team-current-id" style="color: #dcddde;">${escapeHtml(pendingLinkAccount.username)}</span>
            <span class="team-current-id" style="color: #81828A; font-size: 0.85rem;">${pendingLinkAccount.discord_id}</span>
        </div>
        <div style="display: flex; flex-direction: column; gap: 0.25rem; flex: 1; max-width: 250px;">
            <span class="team-current-id" id="discord-token-status" style="font-size: 0.75rem; color: #991a35; min-height: 1rem;">Enter a token</span>
            <input type="text" class="search-input" placeholder="Account token" id="discord-token-input" style="width: 100%; margin: 0;">
        </div>
    `;

    // Add input listener for auto-verification
    setTimeout(() => {
        const input = document.getElementById('discord-token-input');
        if (input) {
            input.addEventListener('input', debounce(autoVerifyToken, 500));
        }
    }, 0);

    return card;
}

// Create account card for list view
function createAccountCardList(account) {
    const card = document.createElement('div');
    card.className = 'team-current-profile';
    card.style.marginBottom = '8px';
    card.style.display = 'flex';
    card.style.background = '#121215';
    card.style.border = '1px solid #222225';
    card.style.borderRadius = '6px';
    card.style.padding = '13px';

    const avatarUrl = getDiscordAvatarUrl(account.discord_id, account.avatar);
    const decorationHtml = account.avatar_decoration
        ? `<img src="https://cdn.discordapp.com/avatar-decoration-presets/${account.avatar_decoration}.png" alt="Decoration" style="position: absolute; top: -4px; left: -4px; width: calc(100% + 8px); height: calc(100% + 8px); pointer-events: none;">`
        : '';

    card.innerHTML = `
        <div class="team-current-avatar" style="background: #1A1A1E; position: relative;">
            <img src="${avatarUrl}" alt="${escapeHtml(account.username)}">
            ${decorationHtml}
        </div>
        <div class="team-current-info">
            <span class="team-current-id" style="color: #dcddde;">${escapeHtml(account.username)}</span>
            <span class="team-current-id" style="color: #81828A; font-size: 0.85rem;">${account.discord_id}</span>
        </div>
        <button class="team-leave-btn" onclick="unlinkDiscordAccount(${account.id}, event)">Unlink</button>
    `;

    return card;
}

// Get Discord avatar URL
function getDiscordAvatarUrl(discordId, avatarHash) {
    if (!avatarHash) {
        const defaultAvatarIndex = parseInt(discordId) % 5;
        return `https://cdn.discordapp.com/embed/avatars/${defaultAvatarIndex}.png`;
    }
    return `https://cdn.discordapp.com/avatars/${discordId}/${avatarHash}.png?size=128`;
}

// Fetch pending account data from API
async function fetchPendingAccount() {
    try {
        const response = await fetch('/api/linked-accounts/pending');
        const data = await response.json();

        if (data.success && data.pending) {
            pendingLinkAccount = data.pending;
        } else {
            pendingLinkAccount = null;
        }
    } catch (error) {
        console.error('Error fetching pending account:', error);
        pendingLinkAccount = null;
    }
}

// Initiate account linking
async function initiateAccountLink() {
    // Check if we're on mobile - use different approach
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);

    if (isMobile) {
        // On mobile, open in same window and use session storage to track return
        sessionStorage.setItem('discord_link_return', 'settings');
        window.location.href = '/discord/link-account';
        return;
    }

    // Desktop: Open OAuth in popup
    const popup = window.open('/discord/link-account', 'discord_oauth', 'width=500,height=700');

    // Check if popup was blocked
    if (!popup || popup.closed || typeof popup.closed === 'undefined') {
        // Popup blocked - fallback to same window
        customAlert('Popup Blocked', 'Your browser blocked the popup. Redirecting to complete OAuth...').then(() => {
            sessionStorage.setItem('discord_link_return', 'settings');
            window.location.href = '/discord/link-account';
        });
        return;
    }

    // Listen for messages from the popup
    window.addEventListener('message', async function handleOAuthMessage(event) {
        // Verify origin
        if (event.origin !== window.location.origin) return;

        if (event.data.type === 'oauth_success') {
            // Remove listener
            window.removeEventListener('message', handleOAuthMessage);

            // Fetch pending account data
            await fetchPendingAccount();

            // Reload accounts list to show token input
            await loadDiscordAccounts();
        } else if (event.data.type === 'oauth_error') {
            // Remove listener
            window.removeEventListener('message', handleOAuthMessage);

            customAlert('OAuth Failed', event.data.error || 'Unknown error');
        }
    });
}

// Auto-verify and link token (called on input with debounce)
async function autoVerifyToken() {
    const tokenInput = document.getElementById('discord-token-input');
    const statusDiv = document.getElementById('discord-token-status');
    let token = tokenInput ? tokenInput.value.trim() : '';

    if (!token) {
        if (statusDiv) {
            statusDiv.textContent = 'Enter a token';
            statusDiv.style.color = '#991a35'; // Delete button top gradient color
        }
        return;
    }

    // Check for quotation marks anywhere in token and show error
    if (token.includes('"') || token.includes("'")) {
        if (statusDiv) {
            statusDiv.textContent = 'Remove quotation marks';
            statusDiv.style.color = '#991a35';
        }
        return;
    }

    if (statusDiv) {
        statusDiv.textContent = 'Verifying';
        statusDiv.style.color = '#81828A';
    }

    try {
        const response = await fetch('/api/linked-accounts/verify-token', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.csrfToken || ''
            },
            body: JSON.stringify({ token })
        });

        const data = await response.json();

        console.log('Verify token response:', response.status, data);

        if (data.success && data.valid) {
            // Clear pending data
            pendingLinkAccount = null;

            // Reload accounts immediately to update the UI
            await loadDiscordAccounts();

            // Dispatch custom event to notify dashboard/other pages to refresh
            // This allows the dashboard to update without page reload
            window.dispatchEvent(new CustomEvent('discord-account-linked', {
                detail: { account: data.account }
            }));

            // Show success popup
            await customAlert('WooHoo! Account linked', 'Your Discord account has been successfully linked.');
        } else {
            if (statusDiv) {
                // Check if it's a CSRF error
                if (response.status === 403 || (data.error && data.error.toLowerCase().includes('csrf'))) {
                    statusDiv.textContent = 'Invalid CSRF token';
                    statusDiv.style.color = '#991a35';
                } else if (data.error) {
                    // Show the actual error message from the API
                    statusDiv.textContent = data.error;
                    statusDiv.style.color = '#991a35';
                } else {
                    statusDiv.textContent = 'Incorrect token';
                    statusDiv.style.color = '#991a35';
                }
            }
        }
    } catch (error) {
        console.error('Error verifying token:', error);
        if (statusDiv) {
            statusDiv.textContent = 'Network error: ' + error.message;
            statusDiv.style.color = '#991a35';
        }
    }
}

// Unlink Discord account
async function unlinkDiscordAccount(accountId, event) {
    event.stopPropagation();

    const confirmed = await customConfirm('Unlink Account', 'Are you sure you want to unlink this Discord account?', 'Unlink');
    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/api/linked-accounts/${accountId}/unlink`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': window.csrfToken || ''
            }
        });

        const data = await response.json();

        if (data.success) {
            // Reload accounts
            await loadDiscordAccounts();
        } else {
            customAlert('Unlink Failed', data.error || 'Unknown error');
        }
    } catch (error) {
        console.error('Error unlinking account:', error);
        customAlert('Unlink Failed', 'Failed to unlink account');
    }
}

// Handle Discord accounts search
async function handleDiscordAccountsSearch(event) {
    const query = event.target.value.trim();

    if (!query) {
        // Show all accounts
        renderDiscordAccounts(allDiscordAccounts);
        return;
    }

    try {
        const response = await fetch(`/api/linked-accounts/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();

        if (data.success) {
            renderDiscordAccounts(data.accounts);
        } else {
            console.error('Search failed:', data.error);
        }
    } catch (error) {
        console.error('Error searching accounts:', error);
    }
}

// Check for pending link and set up token input
async function checkPendingLink() {
    // Check if there's pending account data on page load
    await fetchPendingAccount();

    if (pendingLinkAccount) {
        // Re-render accounts to show token input
        await loadDiscordAccounts();
    }
}

// Utility: Debounce function
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Utility: Escape HTML
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when settings page is opened
document.addEventListener('DOMContentLoaded', () => {
    // Check for pending link on page load
    checkPendingLink();
});
