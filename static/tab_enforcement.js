// Single-tab enforcement using BroadcastChannel API
(function() {
    // Generate a unique tab ID for this tab
    const tabId = Date.now() + '-' + Math.random();

    // Create a broadcast channel for tab communication
    const channel = new BroadcastChannel('tab_enforcement_channel');

    // Flag to track if this tab is the active one
    let isActiveTab = false;

    // Flag to prevent recursive alerts
    let alertShown = false;

    // Send a message to check if any other tabs are actually alive
    function checkForActiveTabs() {
        return new Promise((resolve) => {
            let gotResponse = false;

            const responseHandler = (event) => {
                if (event.data.type === 'tab_alive_response' && event.data.tabId !== tabId) {
                    gotResponse = true;
                }
            };

            channel.addEventListener('message', responseHandler);

            channel.postMessage({
                type: 'tab_alive_check',
                tabId: tabId
            });

            // Wait 300ms for responses
            setTimeout(() => {
                channel.removeEventListener('message', responseHandler);
                resolve(gotResponse);
            }, 300);
        });
    }

    // Handle messages from other tabs
    channel.onmessage = (event) => {
        const data = event.data;

        if (data.type === 'tab_alive_check' && data.tabId !== tabId && isActiveTab) {
            // Another tab is checking if we're alive - respond
            channel.postMessage({
                type: 'tab_alive_response',
                tabId: tabId
            });
        } else if (data.type === 'tab_open' && data.tabId !== tabId) {
            // Another tab is being opened
            if (isActiveTab && !alertShown) {
                // This tab is active, notify the new tab to close
                channel.postMessage({
                    type: 'close_request',
                    tabId: tabId,
                    timestamp: Date.now()
                });
            }
        } else if (data.type === 'close_request' && data.tabId !== tabId) {
            // This tab is being asked to close by another active tab
            if (!alertShown && !isActiveTab) {
                alertShown = true;
                alert('Only one active session is allowed. This tab will be logged out.');
                window.location.href = '/logout';
            }
        }
    };

    // Initialize on page load
    async function initialize() {
        // First, check if there are any ACTUALLY alive tabs
        const hasActiveTabs = await checkForActiveTabs();

        if (!hasActiveTabs) {
            // No other tabs responded - we can be the active tab
            // Clean up any stale localStorage data
            localStorage.removeItem('active_tab_id');
            localStorage.removeItem('active_tab_timestamp');

            localStorage.setItem('active_tab_id', tabId);
            localStorage.setItem('active_tab_timestamp', Date.now().toString());
            isActiveTab = true;

            // Update timestamp periodically to show we're alive
            setInterval(() => {
                if (isActiveTab) {
                    localStorage.setItem('active_tab_timestamp', Date.now().toString());
                }
            }, 2000);
        } else {
            // There's an active tab - announce ourselves and wait for response
            channel.postMessage({
                type: 'tab_open',
                tabId: tabId,
                timestamp: Date.now()
            });

            // If we don't get closed within 500ms, something is wrong
            setTimeout(() => {
                if (!alertShown) {
                    alertShown = true;
                    alert('Only one active session is allowed. This tab will be logged out.');
                    window.location.href = '/logout';
                }
            }, 500);
        }
    }

    // Clean up when tab is closed
    window.addEventListener('beforeunload', () => {
        const currentActiveTab = localStorage.getItem('active_tab_id');

        if (currentActiveTab === tabId) {
            localStorage.removeItem('active_tab_id');
            localStorage.removeItem('active_tab_timestamp');
        }

        channel.close();
    });

    // Also clean up on visibility change (helps with mobile/tab switching)
    document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'hidden' && isActiveTab) {
            // Update timestamp when tab goes hidden
            localStorage.setItem('active_tab_timestamp', Date.now().toString());
        }
    });

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();
