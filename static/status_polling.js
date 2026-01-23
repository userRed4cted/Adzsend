/**
 * Real-time status polling for Borz Marketing Panel
 * Polls the server every 5 seconds to check for status changes
 * (ban status, team membership changes, etc.)
 */

(function() {
    // Store initial state
    let lastStatus = null;
    let pollIntervalId = null;
    const POLL_INTERVAL = 5000; // 5 seconds

    async function checkStatus() {
        try {
            const response = await fetch('/api/status-check');
            if (!response.ok) {
                if (response.status === 401) {
                    // User not logged in - redirect to home
                    window.location.href = '/home';
                    return;
                }
                return;
            }

            const data = await response.json();
            if (!data.success) return;

            // If this is the first check, store the status
            if (lastStatus === null) {
                lastStatus = {
                    is_banned: data.is_banned,
                    is_team_member: data.is_team_member,
                    is_owner: data.is_owner,
                    has_plan: data.has_plan
                };
                return;
            }

            // Check for changes and reload if needed
            let shouldReload = false;

            // Ban status changed
            if (lastStatus.is_banned !== data.is_banned) {
                shouldReload = true;
            }

            // Team membership changed
            if (lastStatus.is_team_member !== data.is_team_member) {
                shouldReload = true;
            }

            // Owner status changed
            if (lastStatus.is_owner !== data.is_owner) {
                shouldReload = true;
            }

            // Plan status changed
            if (lastStatus.has_plan !== data.has_plan) {
                shouldReload = true;
            }

            if (shouldReload) {
                window.location.reload();
            }

            // Update last status
            lastStatus = {
                is_banned: data.is_banned,
                is_team_member: data.is_team_member,
                is_owner: data.is_owner,
                has_plan: data.has_plan
            };

        } catch (error) {
            console.error('Status check error:', error);
        }
    }

    // Start polling when page loads
    document.addEventListener('DOMContentLoaded', function() {
        // Initial check after 1 second
        setTimeout(checkStatus, 1000);

        // Then poll every 5 seconds
        pollIntervalId = setInterval(checkStatus, POLL_INTERVAL);
    });

    // Also check when page becomes visible again (user switches back to tab)
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            checkStatus();
        }
    });

    // Cleanup interval on page unload to prevent memory leaks
    window.addEventListener('beforeunload', function() {
        if (pollIntervalId) {
            clearInterval(pollIntervalId);
            pollIntervalId = null;
        }
    });
})();
