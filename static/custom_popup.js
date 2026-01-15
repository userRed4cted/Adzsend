// =============================================================================
// CUSTOM POPUP SYSTEM
// =============================================================================
// Replaces browser alert() and confirm() with styled custom popups

let currentPopup = null;
let popupResolve = null;

// Create popup overlay and structure
function initCustomPopup() {
    // Check if already initialized
    if (document.getElementById('custom-popup-overlay')) return;

    const overlay = document.createElement('div');
    overlay.id = 'custom-popup-overlay';
    overlay.className = 'custom-popup-overlay';

    overlay.innerHTML = `
        <div class="custom-popup" id="custom-popup">
            <button class="custom-popup-close" id="custom-popup-close">×</button>
            <h2 class="custom-popup-title" id="custom-popup-title"></h2>
            <p class="custom-popup-text" id="custom-popup-text"></p>
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
function showCustomPopup(title, message, buttonText = 'Ok') {
    return new Promise((resolve) => {
        initCustomPopup();

        const overlay = document.getElementById('custom-popup-overlay');
        const titleEl = document.getElementById('custom-popup-title');
        const textEl = document.getElementById('custom-popup-text');
        const btnEl = document.getElementById('custom-popup-btn');

        titleEl.textContent = title;
        textEl.textContent = message;
        btnEl.textContent = buttonText;

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

    if (popupResolve) {
        popupResolve(result);
        popupResolve = null;
    }

    currentPopup = null;
}

// Alert replacement (returns Promise that resolves when closed)
function customAlert(title, message) {
    return showCustomPopup(title, message, 'Ok');
}

// Confirm replacement (returns Promise that resolves to true/false)
function customConfirm(title, message, buttonText = 'Ok') {
    return showCustomPopup(title, message, buttonText);
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCustomPopup);
} else {
    initCustomPopup();
}
