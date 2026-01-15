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

    // Add account cards
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

    const avatarUrl = '/static/discordlogo.png';
    const isDisabled = !canLinkMoreAccounts;

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

    // Check if there's pending link data
    if (pendingLinkAccount) {
        card.style.opacity = '1';
        card.style.cursor = 'default';
        card.style.pointerEvents = 'auto';
        // Show token input instead
        card.innerHTML = `
            <div class="team-current-avatar" style="background: #1A1A1E;">
                <img src="${getDiscordAvatarUrl(pendingLinkAccount.discord_id, pendingLinkAccount.avatar)}" alt="${pendingLinkAccount.username}">
            </div>
            <div class="team-current-info" style="flex-direction: column; align-items: flex-start; gap: 0.5rem;">
                <span class="team-current-id">${escapeHtml(pendingLinkAccount.username)}</span>
                <input type="text" class="search-input" placeholder="Account token" id="discord-token-input" style="width: 100%; margin: 0;">
                <span class="team-current-id" id="discord-token-status" style="font-size: 0.8rem;"></span>
            </div>
            <button class="team-leave-btn" onclick="verifyAndLinkToken(event)">Link</button>
        `;
    } else if (!isDisabled) {
        card.addEventListener('click', initiateAccountLink);
    }

    return card;
}

// Create account card for list view
function createAccountCardList(account) {
    const card = document.createElement('div');
    card.className = 'team-current-profile';

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
    // Open OAuth in popup
    const popup = window.open('/discord/link-account', 'discord_oauth', 'width=500,height=700');

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

            alert('OAuth failed: ' + (event.data.error || 'Unknown error'));
        }
    });
}

// Verify and link token
async function verifyAndLinkToken(event) {
    event.stopPropagation();

    const tokenInput = document.getElementById('discord-token-input');
    const statusDiv = document.getElementById('discord-token-status');
    const token = tokenInput ? tokenInput.value.trim() : '';

    if (!token) {
        if (statusDiv) {
            statusDiv.textContent = 'Please enter a token';
            statusDiv.style.color = '#f04747';
        }
        return;
    }

    if (statusDiv) {
        statusDiv.textContent = 'Verifying...';
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

        if (data.success && data.valid) {
            if (statusDiv) {
                statusDiv.textContent = 'Account linked!';
                statusDiv.style.color = '#43b581';
            }

            // Clear pending data
            pendingLinkAccount = null;

            // Reload accounts after short delay
            setTimeout(() => {
                loadDiscordAccounts();
            }, 1000);
        } else {
            if (statusDiv) {
                statusDiv.textContent = data.error || 'Incorrect account token';
                statusDiv.style.color = '#f04747';
            }
        }
    } catch (error) {
        console.error('Error verifying token:', error);
        if (statusDiv) {
            statusDiv.textContent = 'Verification failed';
            statusDiv.style.color = '#f04747';
        }
    }
}

// Unlink Discord account
async function unlinkDiscordAccount(accountId, event) {
    event.stopPropagation();

    if (!confirm('Are you sure you want to unlink this Discord account?')) {
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
            alert('Failed to unlink account: ' + (data.error || 'Unknown error'));
        }
    } catch (error) {
        console.error('Error unlinking account:', error);
        alert('Failed to unlink account');
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
