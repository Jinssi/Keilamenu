document.addEventListener('DOMContentLoaded', function() {
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
    
    // Initialize new features
    initializeDailyTheme();
    initializeSearch();
    initializeFavorites();
    initializeChefsPicks();
    initializeFoodIcons();
    initializeDietaryTags();
    
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

// Daily theme functionality
function initializeDailyTheme() {
    const themes = [
        { emoji: '🥗', text: 'Green Monday' },
        { emoji: '🍜', text: 'Soup Tuesday' },
        { emoji: '🌮', text: 'World Wednesday' },
        { emoji: '🍖', text: 'Protein Thursday' },
        { emoji: '🍰', text: 'Sweet Friday' },
        { emoji: '🍳', text: 'Brunch Saturday' },
        { emoji: '🥘', text: 'Family Sunday' }
    ];
    
    const today = new Date().getDay();
    const theme = themes[today];
    
    document.getElementById('theme-emoji').textContent = theme.emoji;
    document.getElementById('theme-text').textContent = theme.text;
}

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('search-input');
    searchInput.addEventListener('input', function(e) {
        const query = e.target.value.toLowerCase();
        const mealRows = document.querySelectorAll('.mealrow');
        
        mealRows.forEach(row => {
            const mealText = row.getAttribute('data-meal');
            if (mealText && mealText.toLowerCase().includes(query)) {
                row.style.display = 'flex';
            } else {
                row.style.display = 'none';
            }
        });
    });
}

// Menu toggle functionality
function toggleMenu(index) {
    const mealList = document.getElementById('meal-list-' + index);
    const toggleBtn = mealList.previousElementSibling.querySelector('.menu-toggle');
    
    if (mealList.classList.contains('collapsed')) {
        mealList.classList.remove('collapsed');
        mealList.classList.add('expanded');
        toggleBtn.textContent = '▲';
        toggleBtn.classList.remove('collapsed');
    } else {
        mealList.classList.remove('expanded');
        mealList.classList.add('collapsed');
        toggleBtn.textContent = '▼';
        toggleBtn.classList.add('collapsed');
    }
}

// Favorites functionality
function initializeFavorites() {
    const favorites = JSON.parse(localStorage.getItem('menu-favorites') || '[]');
    
    // Update favorite buttons based on stored data
    document.querySelectorAll('.favorite-btn').forEach(btn => {
        const mealName = btn.parentElement.getAttribute('data-meal');
        if (favorites.includes(mealName)) {
            btn.textContent = '❤️';
            btn.classList.add('favorited');
        }
    });
}

function toggleFavorite(btn) {
    const mealName = btn.parentElement.getAttribute('data-meal');
    const favorites = JSON.parse(localStorage.getItem('menu-favorites') || '[]');
    
    if (btn.classList.contains('favorited')) {
        // Remove from favorites
        const index = favorites.indexOf(mealName);
        if (index > -1) {
            favorites.splice(index, 1);
        }
        btn.textContent = '♡';
        btn.classList.remove('favorited');
    } else {
        // Add to favorites
        favorites.push(mealName);
        btn.textContent = '❤️';
        btn.classList.add('favorited');
    }
    
    localStorage.setItem('menu-favorites', JSON.stringify(favorites));
}

// Chef's picks functionality
function initializeChefsPicks() {
    const restaurants = document.querySelectorAll('.menu');
    const today = new Date().toDateString();
    const storedDate = localStorage.getItem('chefs-pick-date');
    
    // Check if we need to select new chef's picks for today
    if (storedDate !== today) {
        const newPicks = [];
        
        restaurants.forEach((restaurant, index) => {
            const mealRows = restaurant.querySelectorAll('.mealrow[data-meal]');
            if (mealRows.length > 0) {
                const randomIndex = Math.floor(Math.random() * mealRows.length);
                newPicks.push({ restaurant: index, meal: randomIndex });
            }
        });
        
        localStorage.setItem('chefs-picks', JSON.stringify(newPicks));
        localStorage.setItem('chefs-pick-date', today);
    }
    
    // Apply chef's picks
    const picks = JSON.parse(localStorage.getItem('chefs-picks') || '[]');
    picks.forEach(pick => {
        const restaurant = restaurants[pick.restaurant];
        if (restaurant) {
            const mealRows = restaurant.querySelectorAll('.mealrow[data-meal]');
            if (mealRows[pick.meal]) {
                mealRows[pick.meal].classList.add('chefs-pick');
            }
        }
    });
}

// Food icons functionality
function initializeFoodIcons() {
    const foodKeywords = {
        '🍲': ['soup', 'broth', 'stew'],
        '🍛': ['curry', 'rice', 'bowl'],
        '🥗': ['salad', 'greens', 'lettuce'],
        '🍖': ['meat', 'beef', 'pork', 'lamb'],
        '🐟': ['fish', 'salmon', 'tuna', 'seafood'],
        '🍗': ['chicken', 'poultry', 'wings'],
        '🍝': ['pasta', 'spaghetti', 'noodles'],
        '🍕': ['pizza'],
        '🥪': ['sandwich', 'burger', 'wrap'],
        '🍰': ['cake', 'dessert', 'sweet'],
        '🥤': ['drink', 'beverage', 'juice']
    };
    
    document.querySelectorAll('.meal-icon').forEach(icon => {
        const mealText = icon.parentElement.getAttribute('data-meal').toLowerCase();
        let foundIcon = '🍽️'; // Default icon
        
        for (const [emoji, keywords] of Object.entries(foodKeywords)) {
            if (keywords.some(keyword => mealText.includes(keyword))) {
                foundIcon = emoji;
                break;
            }
        }
        
        icon.textContent = foundIcon;
    });
}

// Dietary tags functionality
function initializeDietaryTags() {
    document.querySelectorAll('.mealrow[data-meal]').forEach(row => {
        const mealText = row.getAttribute('data-meal').toLowerCase();
        const tagsContainer = row.querySelector('.meal-tags');
        
        // Check for dietary indicators
        if (mealText.includes('vegan') || mealText.includes('v+')) {
            const tag = document.createElement('span');
            tag.className = 'dietary-tag vegan';
            tag.textContent = 'Vegan';
            tagsContainer.appendChild(tag);
        } else if (mealText.includes('vegetarian') || mealText.includes('v')) {
            const tag = document.createElement('span');
            tag.className = 'dietary-tag vegetarian';
            tag.textContent = 'Vegetarian';
            tagsContainer.appendChild(tag);
        }
        
        if (mealText.includes('gluten-free') || mealText.includes('gf')) {
            const tag = document.createElement('span');
            tag.className = 'dietary-tag gluten-free';
            tag.textContent = 'Gluten-Free';
            tagsContainer.appendChild(tag);
        }
    });
}