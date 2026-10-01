/**
 * Initialize Government Portal Theme
 * Adds professional government-style decorations
 */

function initGovernmentPortalTheme() {
    // Add tricolor header strip
    const headerStrip = document.createElement('div');
    headerStrip.className = 'govt-header-strip';
    document.body.insertBefore(headerStrip, document.body.firstChild);
    
    // Add footer strip
    const footerStrip = document.createElement('div');
    footerStrip.className = 'govt-footer-strip';
    document.body.appendChild(footerStrip);
    
    // Add subtle pattern
    const pattern = document.createElement('div');
    pattern.className = 'govt-pattern';
    document.body.appendChild(pattern);
    
    // Add corner decorations
    const corners = ['top-left', 'top-right', 'bottom-left', 'bottom-right'];
    corners.forEach(corner => {
        const decoration = document.createElement('div');
        decoration.className = `govt-corner-decoration ${corner}`;
        document.body.appendChild(decoration);
    });
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGovernmentPortalTheme);
} else {
    initGovernmentPortalTheme();
}
