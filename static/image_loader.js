// =============================================================================
// CENTRALIZED IMAGE LOADER
// =============================================================================
// Automatically handles image loading failures and retries for all images
// across the entire site, including dynamically added images.

// Configuration
const IMAGE_LOADER_CONFIG = {
    MAX_RETRIES: 100,
    RETRY_DELAY: 10
};

// Track retry attempts for each image using WeakMap (automatic garbage collection)
const imageRetryMap = new WeakMap();

/**
 * Handle image load error with retry logic
 */
function handleImageError(img) {
    // Skip if no src
    if (!img.src) return;

    // Get current retry count for this image
    let retryCount = imageRetryMap.get(img) || 0;

    // Check if we've exceeded max retries
    if (retryCount >= IMAGE_LOADER_CONFIG.MAX_RETRIES) {
        console.warn(`Image failed to load after ${IMAGE_LOADER_CONFIG.MAX_RETRIES} attempts:`, img.src);
        return;
    }

    // Increment retry count
    retryCount++;
    imageRetryMap.set(img, retryCount);

    // Retry loading the image after delay
    setTimeout(() => {
        // Double-check image still exists in DOM before retrying
        if (!img.isConnected) return;

        const originalSrc = img.src;
        img.src = ''; // Clear src to force reload
        img.src = originalSrc; // Reload
    }, IMAGE_LOADER_CONFIG.RETRY_DELAY);
}

/**
 * Handle successful image load
 */
function handleImageLoad(img) {
    // Reset retry count on successful load
    imageRetryMap.delete(img);
}

/**
 * Attach listeners to an image element
 */
function attachImageListeners(img) {
    // Skip if already has listeners (prevent duplicate listeners)
    if (img.dataset.imageLoaderAttached) return;

    // Mark as having listeners attached
    img.dataset.imageLoaderAttached = 'true';

    // Attach error handler
    img.addEventListener('error', function() {
        handleImageError(this);
    });

    // Attach load handler
    img.addEventListener('load', function() {
        handleImageLoad(this);
    });

    // Check current state of the image
    if (img.complete) {
        // Image already finished loading (or failed)
        if (img.naturalWidth === 0 && img.src) {
            // Failed to load - retry
            handleImageError(img);
        }
    }
}

/**
 * Initialize image loader for all current images
 */
function initImageLoader() {
    const images = document.querySelectorAll('img');
    images.forEach(img => attachImageListeners(img));
}

/**
 * Watch for dynamically added images
 */
function watchForNewImages() {
    const observer = new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType === 1) {
                    if (node.tagName === 'IMG') {
                        attachImageListeners(node);
                    } else if (node.querySelectorAll) {
                        const images = node.querySelectorAll('img');
                        images.forEach(img => attachImageListeners(img));
                    }
                }
            }
        }
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        initImageLoader();
        watchForNewImages();
    }, { once: true });
} else {
    initImageLoader();
    watchForNewImages();
}
