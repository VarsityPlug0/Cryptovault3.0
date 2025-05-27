// Theme handling functionality
document.addEventListener('DOMContentLoaded', () => {
    console.log('Theme script loaded');
    
    // Get the theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    console.log('Theme toggle button:', themeToggle);
    
    if (!themeToggle) {
        console.error('Theme toggle button not found!');
        return;
    }
    
    const themeIcon = themeToggle.querySelector('i');
    console.log('Theme icon:', themeIcon);
    
    // Get the current theme from localStorage or default to 'light'
    const currentTheme = localStorage.getItem('theme') || 'light';
    console.log('Current theme:', currentTheme);
    
    // Set initial theme
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);
    
    // Theme toggle click handler
    themeToggle.addEventListener('click', () => {
        console.log('Theme toggle clicked');
        
        // Get current theme
        const currentTheme = document.documentElement.getAttribute('data-theme');
        console.log('Current theme before toggle:', currentTheme);
        
        // Toggle theme
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        console.log('New theme:', newTheme);
        
        // Update theme
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update icon
        updateThemeIcon(newTheme);
    });
    
    // Function to update theme icon
    function updateThemeIcon(theme) {
        console.log('Updating theme icon for theme:', theme);
        if (theme === 'dark') {
            themeIcon.classList.remove('bi-sun-fill');
            themeIcon.classList.add('bi-moon-fill');
        } else {
            themeIcon.classList.remove('bi-moon-fill');
            themeIcon.classList.add('bi-sun-fill');
        }
    }
}); 