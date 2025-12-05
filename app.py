from flask import Flask, render_template
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

FINNISH_WEEKDAYS = [
    "Maanantai",
    "Tiistai",
    "Keskiviikko",
    "Torstai",
    "Perjantai",
    "Lauantai",
    "Sunnuntai",
]

def scrape_iss(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    meals = []
    
    # Find the English section by looking for the h2 element with text starting with "Week"
    english_section = soup.find('h2', class_='lunch-menu__title multiple js-lunch-menu-toggle', text=lambda t: t and t.startswith('Week'))
    if english_section:
        # Get the parent article of the English section
        english_menu = english_section.find_next('article', class_='lunch-menu')
        if english_menu:
            # Get the current day of the week (0=Monday, 6=Sunday)
            current_day_index = datetime.now().weekday()
            if current_day_index < 5:  # Only consider weekdays
                meal_days = english_menu.find_all('div', class_='lunch-menu__day')
                current_day = meal_days[current_day_index]
                meal_items = current_day.find_all('p')
                for item in meal_items:
                    meal_text = item.get_text(strip=True)
                    if not meal_text:
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
    finnish_weekday = FINNISH_WEEKDAYS[current_weekday_index]
    try:
        response = requests.get(
            "https://www.nest-restaurant.fi/",
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
        if not section_name.startswith(finnish_weekday):
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
    except Exception as e:
        print(f"Error scraping Compass: {e}")
        return [{'name': 'Menu temporarily unavailable'}]

@app.route('/')
def index():
    restaurants = [
        {
            'name': 'ISS FG by ISS',
            'scraper': scrape_iss,
            'url': 'https://fg.ravintolapalvelut.iss.fi/'
        },
        {
            'name': 'Nest by Nest Restaurant',
            'scraper': scrape_nest,
            'url': None
        },
        {
            'name': 'Cafe Keilalahti by Compass Group',
            'scraper': scrape_compass,
            'url': 'https://www.compass-group.fi/menuapi/feed/rss/current-day?costNumber=3283&language=en'
        }
    ]

    menus = []
    restaurant_names = []
    for restaurant in restaurants:
        scraper = restaurant['scraper']
        url = restaurant.get('url')
        menu = scraper(url) if url else scraper()
        menus.append(menu)
        restaurant_names.append(restaurant['name'])

    current_weekday = datetime.today().strftime('%A')
    current_date = datetime.now().strftime('%d.%m.%Y')

    return render_template(
        'index.html',
        menus=menus,
        restaurant_names=restaurant_names,
        current_weekday=current_weekday,
        current_date=current_date,
        zip=zip,
    )

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)