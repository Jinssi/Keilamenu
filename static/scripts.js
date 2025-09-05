document.addEventListener('DOMContentLoaded', function() {
    var cookiesButton = document.getElementById('cookies-button');
    var cookiesNote = document.getElementById('cookies-note');
    
    // Enhanced keyboard accessibility for cookie notice
    function dismissCookieNotice() {
        cookiesNote.style.display = 'none';
        cookiesNote.setAttribute('aria-hidden', 'true');
        
        // Focus management - move focus to main content after dismissal
        var mainContent = document.getElementById('main-content');
        if (mainContent) {
            mainContent.focus();
        }
    }
    
    // Click event handler
    cookiesButton.addEventListener('click', dismissCookieNotice);
    
    // Keyboard event handler for accessibility
    cookiesButton.addEventListener('keydown', function(event) {
        if (event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            dismissCookieNotice();
        }
    });
    
    // Handle escape key to dismiss cookie notice
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape' && cookiesNote.style.display !== 'none') {
            dismissCookieNotice();
        }
    });
    
    // Skip link functionality
    var skipLink = document.querySelector('.skip-link');
    if (skipLink) {
        skipLink.addEventListener('click', function(event) {
            event.preventDefault();
            var target = document.querySelector(skipLink.getAttribute('href'));
            if (target) {
                target.focus();
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    }
    
    // Ensure proper focus management for menu sections
    var menuSections = document.querySelectorAll('.menu');
    menuSections.forEach(function(section, index) {
        // Make sections focusable for keyboard navigation
        section.setAttribute('tabindex', '0');
        
        // Add keyboard navigation between menu sections
        section.addEventListener('keydown', function(event) {
            var currentIndex = Array.from(menuSections).indexOf(section);
            
            switch(event.key) {
                case 'ArrowRight':
                case 'ArrowDown':
                    event.preventDefault();
                    var nextIndex = (currentIndex + 1) % menuSections.length;
                    menuSections[nextIndex].focus();
                    break;
                    
                case 'ArrowLeft':
                case 'ArrowUp':
                    event.preventDefault();
                    var prevIndex = currentIndex === 0 ? menuSections.length - 1 : currentIndex - 1;
                    menuSections[prevIndex].focus();
                    break;
                    
                case 'Home':
                    event.preventDefault();
                    menuSections[0].focus();
                    break;
                    
                case 'End':
                    event.preventDefault();
                    menuSections[menuSections.length - 1].focus();
                    break;
            }
        });
    });
    
    // Announce page load completion to screen readers
    var pageStatus = document.createElement('div');
    pageStatus.setAttribute('aria-live', 'polite');
    pageStatus.setAttribute('aria-atomic', 'true');
    pageStatus.className = 'sr-only';
    pageStatus.textContent = 'Page loaded. Lunch menus for ' + menuSections.length + ' restaurants are available.';
    document.body.appendChild(pageStatus);
    
    // Add screen reader only class for announcements
    var style = document.createElement('style');
    style.textContent = `
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
    `;
    document.head.appendChild(style);
});