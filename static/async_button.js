// =============================================================================
// ASYNC BUTTON HANDLER - Centralized button click management
// =============================================================================
// Prevents double-clicks, handles loading states, and queues management
// Included via: {% include 'partials/base_scripts.html' %}
//
// =============================================================================
// SETUP GUIDE - How to protect new async buttons
// =============================================================================
//
// STEP 1: Add the check and start at the beginning of your async function
// STEP 2: Add endOperation in a finally block
//
// BASIC PATTERN:
// --------------
//   async function myHandler() {
//       if (AsyncButton.isProcessing('my_unique_id')) return;
//       AsyncButton.startOperation('my_unique_id');
//
//       try {
//           // ... your async code (fetch, API calls, etc.)
//       } finally {
//           AsyncButton.endOperation('my_unique_id');
//       }
//   }
//
// WITH DYNAMIC ID (for lists/items):
// ----------------------------------
//   async function deleteItem(itemId) {
//       const operationId = `delete_item_${itemId}`;
//       if (AsyncButton.isProcessing(operationId)) return;
//       AsyncButton.startOperation(operationId);
//
//       try {
//           await fetch(`/api/delete/${itemId}`, { method: 'POST' });
//       } finally {
//           AsyncButton.endOperation(operationId);
//       }
//   }
//
// WITH CONFIRMATION DIALOG:
// -------------------------
//   async function deleteWithConfirm(id) {
//       const operationId = `delete_${id}`;
//       if (AsyncButton.isProcessing(operationId)) return;
//
//       const confirmed = await customConfirm('Delete?', 'Are you sure?');
//       if (!confirmed) return;
//
//       AsyncButton.startOperation(operationId);  // Start AFTER confirm
//       try {
//           await fetch('/api/delete', { method: 'POST' });
//       } finally {
//           AsyncButton.endOperation(operationId);
//       }
//   }
//
// OPERATION ID NAMING CONVENTIONS:
// --------------------------------
//   - Use snake_case: 'save_settings', 'delete_account'
//   - For dynamic IDs: `action_${uniqueId}` e.g. 'remove_member_12345'
//   - Keep IDs descriptive and unique per action type
//
// =============================================================================

const AsyncButton = (function() {
    // Track which buttons are currently processing
    const processingButtons = new Set();

    // Track buttons by custom ID for named operations
    const namedOperations = new Map();

    /**
     * Wrap an async button click handler to prevent double-clicks
     * @param {HTMLElement|string} buttonOrId - Button element or selector
     * @param {Function} asyncHandler - Async function to run on click
     * @param {Object} options - Configuration options
     * @param {string} options.loadingText - Text to show while loading (optional)
     * @param {boolean} options.disableOnProcess - Disable button while processing (default: true)
     * @param {string} options.operationId - Unique ID for this operation type (prevents same operation from multiple sources)
     * @param {Function} options.onCancel - Function to call if clicked while processing (for cancellable operations)
     */
    function wrap(buttonOrId, asyncHandler, options = {}) {
        const button = typeof buttonOrId === 'string'
            ? document.querySelector(buttonOrId)
            : buttonOrId;

        if (!button) {
            console.warn('AsyncButton: Button not found', buttonOrId);
            return null;
        }

        const {
            loadingText = null,
            disableOnProcess = true,
            operationId = null,
            onCancel = null
        } = options;

        // Store original content for restoration
        const originalContent = button.innerHTML;
        const originalDisabled = button.disabled;

        // Create the wrapped handler
        const wrappedHandler = async function(event) {
            // Check if this specific button is already processing
            if (processingButtons.has(button)) {
                // If there's a cancel handler, call it
                if (onCancel) {
                    await onCancel();
                }
                return;
            }

            // Check if this operation type is already running (from any source)
            if (operationId && namedOperations.has(operationId)) {
                if (onCancel) {
                    await onCancel();
                }
                return;
            }

            // Mark as processing
            processingButtons.add(button);
            if (operationId) {
                namedOperations.set(operationId, button);
            }

            // Apply loading state
            if (disableOnProcess) {
                button.disabled = true;
            }
            if (loadingText) {
                button.innerHTML = loadingText;
            }

            try {
                // Run the actual handler
                await asyncHandler.call(this, event);
            } catch (error) {
                console.error('AsyncButton: Handler error', error);
            } finally {
                // Restore button state
                processingButtons.delete(button);
                if (operationId) {
                    namedOperations.delete(operationId);
                }

                // Only restore if not explicitly changed by handler
                if (disableOnProcess && button.disabled) {
                    button.disabled = originalDisabled;
                }
                if (loadingText && button.innerHTML === loadingText) {
                    button.innerHTML = originalContent;
                }
            }
        };

        // Remove existing listeners and add new one
        button._asyncHandler = wrappedHandler;
        button.addEventListener('click', wrappedHandler);

        // Return control object
        return {
            button,
            isProcessing: () => processingButtons.has(button),
            forceRelease: () => {
                processingButtons.delete(button);
                if (operationId) {
                    namedOperations.delete(operationId);
                }
                button.disabled = originalDisabled;
                button.innerHTML = originalContent;
            },
            setLoading: (text) => {
                button.innerHTML = text;
            },
            restore: () => {
                button.innerHTML = originalContent;
                button.disabled = originalDisabled;
            },
            unwrap: () => {
                button.removeEventListener('click', wrappedHandler);
                delete button._asyncHandler;
            }
        };
    }

    /**
     * Check if a button or operation is currently processing
     * @param {HTMLElement|string} buttonOrOperationId - Button element or operation ID
     */
    function isProcessing(buttonOrOperationId) {
        if (typeof buttonOrOperationId === 'string') {
            // Check by operation ID first
            if (namedOperations.has(buttonOrOperationId)) {
                return true;
            }
            // Then try as selector
            const button = document.querySelector(buttonOrOperationId);
            return button ? processingButtons.has(button) : false;
        }
        return processingButtons.has(buttonOrOperationId);
    }

    /**
     * Manually mark an operation as started (for complex multi-step operations)
     * @param {string} operationId - Unique operation identifier
     */
    function startOperation(operationId) {
        namedOperations.set(operationId, true);
    }

    /**
     * Manually mark an operation as complete
     * @param {string} operationId - Unique operation identifier
     */
    function endOperation(operationId) {
        namedOperations.delete(operationId);
    }

    /**
     * Create loading dots HTML (matches website style)
     */
    function loadingDots() {
        return '<div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>';
    }

    /**
     * Create loading text with dots
     * @param {string} text - Text to show before dots
     */
    function loadingWithText(text) {
        return `<span>${text}</span> ${loadingDots()}`;
    }

    // Public API
    return {
        wrap,
        isProcessing,
        startOperation,
        endOperation,
        loadingDots,
        loadingWithText
    };
})();

// Also expose globally for inline handlers
window.AsyncButton = AsyncButton;
