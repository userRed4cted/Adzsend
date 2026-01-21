// Single-tab enforcement using BroadcastChannel API
// New tabs take over - old tabs get logged out
(function() {
    // Generate a unique tab ID for this tab
    const tabId = Date.now() + '-' + Math.random();

    // Create a broadcast channel for tab communication
    const channel = new BroadcastChannel('tab_enforcement_channel');

    // Flag to track if this tab is the active one
    let isActiveTab = false;

    // Flag to prevent recursive alerts
    let alertShown = false;

    // Handle messages from other tabs
    channel.onmessage = (event) => {
        const data = event.data;

        if (data.type === 'new_tab_takeover' && data.tabId !== tabId) {
            // A new tab is taking over - this old tab should log out
            if (isActiveTab && !alertShown) {
                alertShown = true;
                isActiveTab = false;
                localStorage.removeItem('active_tab_id');
                localStorage.removeItem('active_tab_timestamp');
                alert('You have logged in from another tab. This tab will be logged out.');
                window.location.href = '/logout';
            }
        }
    };

    // Initialize on page load
    function initialize() {
        // This new tab takes over as the active tab
        // Notify any old tabs to log out
        channel.postMessage({
            type: 'new_tab_takeover',
            tabId: tabId,
            timestamp: Date.now()
        });

        // Small delay to ensure message is sent before we set ourselves as active
        setTimeout(() => {
            localStorage.setItem('active_tab_id', tabId);
            localStorage.setItem('active_tab_timestamp', Date.now().toString());
            isActiveTab = true;

            // Update timestamp periodically to show we're alive
            setInterval(() => {
                if (isActiveTab) {
                    localStorage.setItem('active_tab_timestamp', Date.now().toString());
                }
            }, 2000);
        }, 100);
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

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();
