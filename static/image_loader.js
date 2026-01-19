// =============================================================================
// CENTRALIZED IMAGE LOADER
// =============================================================================
// Automatically handles image loading failures and retries for all images
// across the entire site, including dynamically added images.

// Configuration
const IMAGE_LOADER_CONFIG = {
    MAX_RETRIES: 100,      // Maximum retry attempts per image
    RETRY_DELAY: 10        // Delay between retries in milliseconds
};

// Track retry attempts for each image using WeakMap (automatic garbage collection)
const imageRetryMap = new WeakMap();

/**
 * Handle image load error with retry logic
 */
function handleImageError(img) {
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

    // Attach error handler (passive for better performance)
    img.addEventListener('error', function() {
        handleImageError(this);
    }, { passive: true });

    // Attach load handler (passive for better performance)
    img.addEventListener('load', function() {
        handleImageLoad(this);
    }, { passive: true });

    // If image already failed to load, trigger retry immediately
    if (img.complete && img.naturalWidth === 0) {
        handleImageError(img);
    }
}

/**
 * Initialize image loader for all current images
 */
function initImageLoader() {
    // Get all images on the page
    const images = document.querySelectorAll('img');

    // Use requestAnimationFrame to avoid blocking the main thread
    requestAnimationFrame(() => {
        images.forEach(img => attachImageListeners(img));
    });
}

/**
 * Watch for dynamically added images
 */
function watchForNewImages() {
    // Batch processing for better performance
    let pendingImages = new Set();
    let rafId = null;

    function processPendingImages() {
        pendingImages.forEach(img => attachImageListeners(img));
        pendingImages.clear();
        rafId = null;
    }

    // Create a MutationObserver to watch for new images
    const observer = new MutationObserver((mutations) => {
        // Collect all new images
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                // If the node is an image
                if (node.nodeType === 1) { // Element node
                    if (node.tagName === 'IMG') {
                        pendingImages.add(node);
                    }
                    // If the node contains images
                    else if (node.querySelectorAll) {
                        const images = node.querySelectorAll('img');
                        images.forEach(img => pendingImages.add(img));
                    }
                }
            }
        }

        // Process images in next animation frame (debounced)
        if (pendingImages.size > 0 && !rafId) {
            rafId = requestAnimationFrame(processPendingImages);
        }
    });

    // Start observing the document body for changes
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
    // DOM already loaded
    initImageLoader();
    watchForNewImages();
}
