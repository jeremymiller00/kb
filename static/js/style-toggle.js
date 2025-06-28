// Style toggle functionality for Knowledge Base UI
document.addEventListener('DOMContentLoaded', function() {
    const STORAGE_KEY = 'kb-theme-preference';
    const RETRO_THEME = 'retro';
    const MODERN_THEME = 'modern';
    
    // Get current theme from localStorage or default to retro
    function getCurrentTheme() {
        return localStorage.getItem(STORAGE_KEY) || RETRO_THEME;
    }
    
    // Save theme preference
    function saveTheme(theme) {
        localStorage.setItem(STORAGE_KEY, theme);
    }
    
    // Apply theme by updating the stylesheet link
    function applyTheme(theme) {
        const linkElement = document.getElementById('theme-stylesheet');
        if (linkElement) {
            const stylePath = theme === MODERN_THEME 
                ? '/static/styles/modern.css' 
                : '/static/styles/retro_terminal.css';
            linkElement.href = stylePath;
        }
        
        // Update body class for any theme-specific styling
        document.body.className = document.body.className
            .replace(/theme-\w+/g, '') + ` theme-${theme}`;
    }
    
    // Toggle between themes
    function toggleTheme() {
        const currentTheme = getCurrentTheme();
        const newTheme = currentTheme === RETRO_THEME ? MODERN_THEME : RETRO_THEME;
        
        saveTheme(newTheme);
        applyTheme(newTheme);
        updateToggleButton(newTheme);
        
        // Add smooth transition effect
        document.body.style.transition = 'all 0.3s ease';
        setTimeout(() => {
            document.body.style.transition = '';
        }, 300);
    }
    
    // Update toggle button text and icon
    function updateToggleButton(theme) {
        const toggleButton = document.getElementById('style-toggle-btn');
        if (toggleButton) {
            if (theme === MODERN_THEME) {
                toggleButton.innerHTML = '🖥️ Switch to Retro';
                toggleButton.title = 'Switch to retro terminal theme';
            } else {
                toggleButton.innerHTML = '✨ Switch to Modern';
                toggleButton.title = 'Switch to modern sleek theme';
            }
        }
    }
    
    // Initialize theme on page load
    function initializeTheme() {
        const currentTheme = getCurrentTheme();
        applyTheme(currentTheme);
        updateToggleButton(currentTheme);
    }
    
    // Create and add toggle button to the page
    function createToggleButton() {
        const toggleButton = document.createElement('button');
        toggleButton.id = 'style-toggle-btn';
        toggleButton.className = 'style-toggle';
        toggleButton.onclick = toggleTheme;
        toggleButton.setAttribute('aria-label', 'Toggle theme');
        
        // Insert at the beginning of body
        document.body.insertBefore(toggleButton, document.body.firstChild);
        
        return toggleButton;
    }
    
    // Initialize everything
    let toggleButton = document.getElementById('style-toggle-btn');
    if (!toggleButton) {
        toggleButton = createToggleButton();
    }
    
    initializeTheme();
    
    // Add keyboard shortcut (Ctrl/Cmd + Shift + T)
    document.addEventListener('keydown', function(e) {
        if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
            e.preventDefault();
            toggleTheme();
        }
    });
});