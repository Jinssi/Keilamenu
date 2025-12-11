import os
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Feature toggles
FEATURE_LANGUAGE_SELECTOR = os.getenv('FEATURE_LANGUAGE_SELECTOR', 'false').lower() == 'true'
FEATURE_RATINGS = os.getenv('FEATURE_RATINGS', 'false').lower() == 'true'

from services.translator import (
    translate_menu, 
    parse_accept_language, 
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE
)
from services.database import (
    init_db,
    add_rating,
    get_ratings_summary,
    get_top_pick
)

app = Flask(__name__)

# Restaurant ID mapping for database operations
RESTAURANT_IDS = {
    'ISS FG by ISS': 'iss',
    'Nest by Nest Restaurant': 'nest',
    'Cafe Keilalahti by Compass Group': 'compass'
}

ENGLISH_WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

def scrape_iss(url):
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    meals = []
    
    # Find the English section by looking for the h2 element with text starting with "Week"
    english_section = soup.find('h2', class_='lunch-menu__title multiple js-lunch-menu-toggle', string=lambda t: t and t.startswith('Week'))
    if english_section:
        # Get the parent article of the English section
        english_menu = english_section.find_next('article', class_='lunch-menu')
        if english_menu:
            current_day_index = datetime.now().weekday()
            current_day_name = ENGLISH_WEEKDAYS[current_day_index].lower() if current_day_index < 7 else None
            
            if current_day_index >= 5:  # Weekend
                return meals
            
            # Find the correct day section by matching day name in header
            meal_days = english_menu.find_all('div', class_='lunch-menu__day')
            target_day = None
            
            for day_div in meal_days:
                # Look for day header (h3 or strong element containing day name)
                day_header = day_div.find(['h3', 'strong', 'b'])
                if day_header:
                    header_text = day_header.get_text(strip=True).lower()
                    if current_day_name in header_text:
                        target_day = day_div
                        break
            
            # Fallback to index-based if name matching fails
            if not target_day and current_day_index < len(meal_days):
                target_day = meal_days[current_day_index]
            
            # SPECIAL CASE: If it's Friday and we couldn't find Friday section,
            # look for Friday data embedded in Thursday's section (data corruption recovery)
            search_within_previous_day = False
            if not target_day and current_day_index == 4:  # Friday
                # Try to find Thursday's section and extract Friday from it
                for day_div in meal_days:
                    day_header = day_div.find(['h3', 'strong', 'b'])
                    if day_header and 'thursday' in day_header.get_text(strip=True).lower():
                        target_day = day_div
                        search_within_previous_day = True
                        break
                # Or use index 3 (Thursday) as fallback
                if not target_day and len(meal_days) > 3:
                    target_day = meal_days[3]
                    search_within_previous_day = True
            
            if target_day:
                meal_items = target_day.find_all('p')
                collecting = not search_within_previous_day  # Start collecting immediately unless searching for embedded day
                
                for item in meal_items:
                    meal_text = item.get_text(strip=True)
                    if not meal_text:
                        continue
                    
                    # If searching within previous day's section for current day's data
                    if search_within_previous_day:
                        # Start collecting when we see current day's name
                        if current_day_name in meal_text.lower():
                            collecting = True
                            continue  # Skip the day header line itself
                        if not collecting:
                            continue
                    
                    # Stop if we hit the next day's header
                    next_day_index = current_day_index + 1
                    if next_day_index < 5:  # There's a next weekday
                        next_day_name = ENGLISH_WEEKDAYS[next_day_index].lower()
                        if next_day_name in meal_text.lower():
                            break
                    
                    # Also stop if we hit a different day header (general case)
                    text_lower = meal_text.lower()
                    is_day_header = any(day.lower() in text_lower and len(meal_text) < 20 
                                       for day in ENGLISH_WEEKDAYS[:5])
                    if is_day_header and current_day_name not in text_lower:
                        if not search_within_previous_day:
                            break
                        continue

                    if ':' in meal_text:
                        label_raw, description_raw = meal_text.split(':', 1)
                        label = label_raw.strip() or 'Main'
                        description = description_raw.strip()
                    else:
                        label = 'Main'
                        description = meal_text.strip()

                    if not description:
                        description = label

                    meals.append({
                        'label': label,
                        'description': description,
                    })
    return meals

def scrape_nest():
    current_weekday_index = datetime.today().weekday()
    english_weekday = ENGLISH_WEEKDAYS[current_weekday_index]
    try:
        response = requests.get(
            "https://www.nest-restaurant.fi/en",
            timeout=12,
        )
        response.raise_for_status()
    except requests.RequestException:
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    menu_container = soup.select_one('[data-hook="menu.container"]')
    if not menu_container:
        return []

    sections = menu_container.select('[data-hook="section.container"]')
    meals = []
    for section in sections:
        name_el = section.select_one('[data-hook="section.name"]')
        if not name_el:
            continue
        section_name = name_el.get_text(strip=True)
        if not section_name.startswith(english_weekday):
            continue

        for item in section.select('[data-hook="item.container"]'):
            title_el = item.select_one('[data-hook="item.name"]')
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            description_el = item.select_one('[data-hook="item.description"]')
            description = description_el.get_text(" ", strip=True) if description_el else ''
            description = re.sub(r"\s+", " ", description).strip()

            combined = f"{title}: {description}" if description else title
            label, desc = (part.strip() for part in combined.split(':', 1)) if ':' in combined else (combined.strip(), '')
            meals.append({'label': label, 'description': desc})
        break

    return meals

def scrape_compass(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        meals = []
        # Find the item tag in the RSS feed
        item = soup.find('item')
        if item:
            # Find the description tag within the item
            description = item.find('description')
            if description:
                # Get the description content as is
                description_content = description.get_text().strip()
                # Remove text before "€:" using regex
                description_content = re.sub(r'^.*?€:', '', description_content, flags=re.DOTALL).strip()
                # Replace multiple <br> tags with a single newline
                description_content = re.sub(r'(<br\s*/?>\s*)+', '\n', description_content)
                # Split the description content by newlines and append each line as a separate meal entry
                for line in description_content.split('\n'):
                    line = line.strip()
                    if line:
                        meals.append({'name': line})
        return meals
    except requests.RequestException as e:
        print(f"Error scraping Compass: {e}")
        return [{'name': 'Menu temporarily unavailable'}]

@app.route('/')
def index():
    # Get user's preferred language from header or query param
    lang = request.args.get('lang')
    if not lang:
        lang = parse_accept_language(request.headers.get('Accept-Language', ''))
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE

    restaurants = [
        {
            'name': 'ISS FG by ISS',
            'id': 'iss',
            'scraper': scrape_iss,
            'url': 'https://fg.ravintolapalvelut.iss.fi/'
        },
        {
            'name': 'Nest by Nest Restaurant',
            'id': 'nest',
            'scraper': scrape_nest,
            'url': None
        },
        {
            'name': 'Cafe Keilalahti by Compass Group',
            'id': 'compass',
            'scraper': scrape_compass,
            'url': 'https://www.compass-group.fi/menuapi/feed/rss/current-day?costNumber=3283&language=en'
        }
    ]

    menus = []
    restaurant_names = []
    restaurant_ids = []
    all_ratings = {}
    
    for restaurant in restaurants:
        scraper = restaurant['scraper']
        url = restaurant.get('url')
        menu = scraper(url) if url else scraper()
        
        # Translate menu if needed
        if lang != DEFAULT_LANGUAGE:
            menu = translate_menu(menu, lang)
        
        menus.append(menu)
        restaurant_names.append(restaurant['name'])
        restaurant_ids.append(restaurant['id'])
        
        # Get ratings for this restaurant
        all_ratings[restaurant['id']] = get_ratings_summary(restaurant['id'])

    # Get today's top pick
    top_pick = get_top_pick()

    current_weekday = datetime.today().strftime('%A')
    current_date = datetime.now().strftime('%d.%m.%Y')

    return render_template(
        'index.html',
        menus=menus,
        restaurant_names=restaurant_names,
        restaurant_ids=restaurant_ids,
        ratings=all_ratings,
        top_pick=top_pick,
        current_weekday=current_weekday,
        current_date=current_date,
        current_lang=lang,
        supported_languages=SUPPORTED_LANGUAGES,
        feature_language_selector=FEATURE_LANGUAGE_SELECTOR,
        feature_ratings=FEATURE_RATINGS,
        zip=zip,
    )


@app.route('/api/rate', methods=['POST'])
def rate_meal():
    """
    Submit a rating for a meal.
    Expects JSON: {"restaurant_id": "iss", "meal_name": "Chicken Tikka", "rating": 1}
    rating: 1 for thumbs up, -1 for thumbs down
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    restaurant_id = data.get('restaurant_id')
    meal_name = data.get('meal_name')
    rating = data.get('rating')
    
    if not all([restaurant_id, meal_name, rating is not None]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    if rating not in (-1, 1):
        return jsonify({'error': 'Rating must be 1 or -1'}), 400
    
    if restaurant_id not in ['iss', 'nest', 'compass']:
        return jsonify({'error': 'Invalid restaurant_id'}), 400
    
    success = add_rating(restaurant_id, meal_name, rating)
    if success:
        # Return updated ratings for this restaurant
        updated_ratings = get_ratings_summary(restaurant_id)
        return jsonify({
            'success': True,
            'ratings': updated_ratings.get(meal_name, {'up': 0, 'down': 0, 'score': 0})
        })
    else:
        return jsonify({'error': 'Database not available'}), 503


@app.route('/api/ratings/<restaurant_id>')
def get_restaurant_ratings(restaurant_id):
    """Get all ratings for a restaurant."""
    if restaurant_id not in ['iss', 'nest', 'compass']:
        return jsonify({'error': 'Invalid restaurant_id'}), 400
    
    ratings = get_ratings_summary(restaurant_id)
    return jsonify(ratings)


@app.route('/api/top-pick')
def api_top_pick():
    """Get today's top-rated meal."""
    top = get_top_pick()
    if top:
        return jsonify(top)
    return jsonify({'message': 'No ratings yet today'}), 404

if __name__ == '__main__':
    import os
    # Initialize database on startup
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)