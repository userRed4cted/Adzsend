// Database Wipe Notice
// Shows a dialogue when the database has been reset

(function() {
    // Get current database version from the page
    const currentVersion = window.DB_VERSION || 1;
    const wipeMessage = window.DB_WIPE_MESSAGE || 'The database has been reset. All accounts have been wiped.';

    // Check stored version
    const storedVersion = localStorage.getItem('db_version');

    // If no stored version or stored version is less than current, show notice
    if (!storedVersion || parseInt(storedVersion) < currentVersion) {
        showWipeNotice(wipeMessage, currentVersion);
    }

    function showWipeNotice(message, version) {
        // Create overlay
        const overlay = document.createElement('div');
        overlay.id = 'db-wipe-overlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.85);
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: fadeIn 0.3s ease;
        `;

        // Create dialog box
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: #191A1F;
            border-radius: 12px;
            padding: 2rem;
            max-width: 450px;
            width: 90%;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
            animation: slideIn 0.3s ease;
        `;

        // Warning icon
        const icon = document.createElement('div');
        icon.style.cssText = `
            font-size: 3rem;
            margin-bottom: 1rem;
        `;
        icon.textContent = '⚠️';

        // Title
        const title = document.createElement('h2');
        title.style.cssText = `
            color: #FFC107;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 1rem;
        `;
        title.textContent = 'Database Reset';

        // Message
        const messageEl = document.createElement('p');
        messageEl.style.cssText = `
            color: #ffffff;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        `;
        messageEl.textContent = message;

        // Button
        const button = document.createElement('button');
        button.style.cssText = `
            background: #335FFF;
            color: #ffffff;
            border: none;
            border-radius: 8px;
            padding: 0.75rem 2rem;
            font-size: 1rem;
            font-weight: 700;
            cursor: pointer;
            transition: transform 0.2s ease;
        `;
        button.textContent = 'I Understand';
        button.onmouseover = () => button.style.transform = 'scale(1.05)';
        button.onmouseout = () => button.style.transform = 'scale(1)';
        button.onclick = () => {
            // Save version to localStorage
            localStorage.setItem('db_version', version.toString());
            // Remove overlay with animation
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => overlay.remove(), 300);
        };

        // Add animation styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }
            @keyframes fadeOut {
                from { opacity: 1; }
                to { opacity: 0; }
            }
            @keyframes slideIn {
                from { transform: translateY(-20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        // Assemble dialog
        dialog.appendChild(icon);
        dialog.appendChild(title);
        dialog.appendChild(messageEl);
        dialog.appendChild(button);
        overlay.appendChild(dialog);

        // Add to page
        document.body.appendChild(overlay);
    }
})();
