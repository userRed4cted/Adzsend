// =============================================================================
// CENTRALIZED SCALE MANAGER - Lightweight viewport info provider
// =============================================================================
// Provides CSS variables for viewport dimensions. No zoom/transform applied.
// Content stays full-width at all resolutions.

(function() {
    const BASE_WIDTH = 1920;
    let rafId = null;

    function update() {
        const w = window.innerWidth;
        const h = window.innerHeight;
        const s = document.documentElement.style;
        s.setProperty('--scale-factor', w / BASE_WIDTH);
        s.setProperty('--vw', w + 'px');
        s.setProperty('--vh', h + 'px');
    }

    function onResize() {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
            update();
            rafId = null;
        });
    }

    // Initialize
    update();
    window.addEventListener('resize', onResize, { passive: true });
})();
