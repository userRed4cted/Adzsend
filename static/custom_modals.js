// ==============================================
// CUSTOM MODAL SYSTEM
// ==============================================
// Replaces browser alert() and confirm() with styled modals

(function() {
    // Create modal HTML and inject into page
    const modalHTML = `
        <div class="custom-modal-overlay" id="custom-alert-modal">
            <div class="custom-modal-box">
                <div class="custom-modal-icon" id="custom-alert-icon" style="display: none; text-align: center; margin-bottom: 16px;"></div>
                <div class="custom-modal-header" id="custom-alert-title">Notice</div>
                <div class="custom-modal-content" id="custom-alert-message"></div>
                <div class="custom-modal-actions">
                    <button class="custom-modal-btn primary" id="custom-alert-ok">OK</button>
                </div>
            </div>
        </div>
        <div class="custom-modal-overlay" id="custom-confirm-modal">
            <div class="custom-modal-box">
                <div class="custom-modal-header" id="custom-confirm-title">Confirm</div>
                <div class="custom-modal-content" id="custom-confirm-message"></div>
                <div class="custom-modal-actions">
                    <button class="custom-modal-btn secondary" id="custom-confirm-cancel">Cancel</button>
                    <button class="custom-modal-btn primary" id="custom-confirm-ok">Confirm</button>
                </div>
            </div>
        </div>
    `;

    const modalStyles = `
        <style>
            .custom-modal-overlay {
                display: none;
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.7);
                z-index: 10000;
                justify-content: center;
                align-items: center;
                backdrop-filter: blur(4px);
            }
            .custom-modal-overlay.active {
                display: flex;
            }
            .custom-modal-box {
                background: #1a1a1d;
                border-radius: 12px;
                padding: 24px;
                max-width: 450px;
                width: 90%;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
                border: 1px solid #2a2a30;
            }
            .custom-modal-header {
                color: #fff;
                font-size: 18px;
                font-weight: 600;
                margin-bottom: 16px;
            }
            .custom-modal-content {
                color: #e0e0e0;
                font-size: 14px;
                line-height: 1.6;
                margin-bottom: 24px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            .custom-modal-actions {
                display: flex;
                justify-content: center;
                gap: 0;
            }
            .custom-modal-btn {
                flex: 1;
                max-width: 200px;
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: all 0.2s;
            }
            .custom-modal-actions .custom-modal-btn:first-child:not(:last-child) {
                border-radius: 6px 0 0 6px;
            }
            .custom-modal-actions .custom-modal-btn:last-child:not(:first-child) {
                border-radius: 0 6px 6px 0;
            }
            .custom-modal-actions .custom-modal-btn:only-child {
                border-radius: 6px;
                max-width: 400px;
            }
            .custom-modal-btn.primary {
                background: linear-gradient(to bottom, #15d8bc, #006e59);
                border: none;
                color: #121215;
                font-weight: 600;
            }
            .custom-modal-btn.primary:hover {
                background: linear-gradient(to bottom, #10b89e, #004e40);
            }
            .custom-modal-btn.secondary {
                background: linear-gradient(to bottom, #3a3a4d, #2a2a3d);
                border: none;
                color: #ffffff;
            }
            .custom-modal-btn.secondary:hover {
                background: linear-gradient(to bottom, #4a4a5d, #3a3a4d);
            }
            .custom-modal-btn.danger {
                background: linear-gradient(to bottom, #991a35, #3b0b15);
                border: none;
                color: #ffffff;
            }
            .custom-modal-btn.danger:hover {
                background: linear-gradient(to bottom, #7a152b, #2d0810);
            }
        </style>
    `;

    // Inject styles and HTML when DOM is ready
    function injectModals() {
        if (!document.getElementById('custom-alert-modal')) {
            document.head.insertAdjacentHTML('beforeend', modalStyles);
            document.body.insertAdjacentHTML('beforeend', modalHTML);
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', injectModals);
    } else {
        injectModals();
    }

    // Alert function - returns a Promise
    // Options: { icon: 'success' | 'error' | 'warning' | 'none' }
    window.showAlert = function(message, title = 'Notice', options = {}) {
        return new Promise((resolve) => {
            injectModals();
            const modal = document.getElementById('custom-alert-modal');
            const titleEl = document.getElementById('custom-alert-title');
            const messageEl = document.getElementById('custom-alert-message');
            const iconEl = document.getElementById('custom-alert-icon');
            const okBtn = document.getElementById('custom-alert-ok');

            titleEl.textContent = title;
            messageEl.textContent = message;

            // Handle icon display
            const iconType = options.icon || 'none';
            if (iconType === 'success') {
                iconEl.innerHTML = '<img src="/static/tick.png" width="48" height="48" style="filter: sepia(1) saturate(5) hue-rotate(130deg) brightness(0.9);">';
                iconEl.style.display = 'block';
            } else if (iconType === 'error') {
                iconEl.innerHTML = '<span style="font-size: 48px; color: #991a35; font-weight: 300; line-height: 1;">✕</span>';
                iconEl.style.display = 'block';
            } else if (iconType === 'warning') {
                iconEl.innerHTML = '<svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#FFC107" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';
                iconEl.style.display = 'block';
            } else {
                iconEl.style.display = 'none';
                iconEl.innerHTML = '';
            }

            modal.classList.add('active');

            function handleOk() {
                modal.classList.remove('active');
                okBtn.removeEventListener('click', handleOk);
                resolve();
            }

            okBtn.addEventListener('click', handleOk);
        });
    };

    // Confirm function - returns a Promise that resolves to true/false
    window.showConfirm = function(message, title = 'Confirm', options = {}) {
        return new Promise((resolve) => {
            injectModals();
            const modal = document.getElementById('custom-confirm-modal');
            const titleEl = document.getElementById('custom-confirm-title');
            const messageEl = document.getElementById('custom-confirm-message');
            const okBtn = document.getElementById('custom-confirm-ok');
            const cancelBtn = document.getElementById('custom-confirm-cancel');

            titleEl.textContent = title;
            messageEl.textContent = message;

            // Set button text
            okBtn.textContent = options.confirmText || 'Confirm';
            cancelBtn.textContent = options.cancelText || 'Cancel';

            // Set danger style if specified
            if (options.danger) {
                okBtn.classList.remove('primary');
                okBtn.classList.add('danger');
            } else {
                okBtn.classList.remove('danger');
                okBtn.classList.add('primary');
            }

            modal.classList.add('active');

            function handleOk() {
                modal.classList.remove('active');
                cleanup();
                resolve(true);
            }

            function handleCancel() {
                modal.classList.remove('active');
                cleanup();
                resolve(false);
            }

            function cleanup() {
                okBtn.removeEventListener('click', handleOk);
                cancelBtn.removeEventListener('click', handleCancel);
            }

            okBtn.addEventListener('click', handleOk);
            cancelBtn.addEventListener('click', handleCancel);
        });
    };
})();
