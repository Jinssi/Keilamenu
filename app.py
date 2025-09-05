from flask import Flask, render_template
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

app = Flask(__name__)

def scrape_iss(url):
    try:
        response = requests.get(url, timeout=10)
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
                    if len(meal_days) > current_day_index:
                        current_day = meal_days[current_day_index]
                        meal_items = current_day.find_all('p')
                        for item in meal_items:
                            meal_text = item.get_text(strip=True)
                            if meal_text:
                                # Split the text at the colon and keep the part after it
                                meal_name = meal_text.split(' : ', 1)[-1].strip()
                                meals.append({'name': meal_name})
        return meals
    except Exception as e:
        print(f"Error scraping ISS: {e}")
        return [{'name': 'Menu temporarily unavailable'}]

def scrape_sodexo(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        meals = []
        
        # Get the current weekday (0=Monday, 1=Tuesday, ..., 4=Friday)
        current_weekday = datetime.today().weekday()
        
        # Only consider weekdays (Monday to Friday)
        if current_weekday < 5:
            # Find the div with id="tabs-X" where X is the current weekday
            tabs_div = soup.find('div', id=f'tabs-{current_weekday}')
            if tabs_div:
                # Find all div elements with class="mealrow"
                mealrows = tabs_div.find_all('div', class_='mealrow')
                for mealrow in mealrows:
                    # Find the div with class="meal-wrapper" within each mealrow
                    meal_wrapper = mealrow.find('div', class_='meal-wrapper')
                    if meal_wrapper:
                        # Find all p elements with class="meal-name" within the meal-wrapper
                        meal_names = meal_wrapper.find_all('p', class_='meal-name')
                        for meal_name in meal_names:
                            meals.append({'name': meal_name.get_text(strip=True)})
        return meals
    except Exception as e:
        print(f"Error scraping Sodexo: {e}")
        return [{'name': 'Menu temporarily unavailable'}]

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
    urls = [
        'https://fg.ravintolapalvelut.iss.fi/',
        'https://www.sodexo.fi/en/restaurants/ravintola-foodhub-ab',
        'https://www.compass-group.fi/menuapi/feed/rss/current-day?costNumber=3283&language=en'
    ]
    menus = []
    for url in urls:
        try:
            if 'sodexo' in url:
                menus.append(scrape_sodexo(url))
            elif 'iss' in url:
                menus.append(scrape_iss(url))
            elif 'compass-group' in url:
                menus.append(scrape_compass(url))
        except Exception as e:
            print(f"Error processing {url}: {e}")
            menus.append([{'name': 'Menu temporarily unavailable'}])
    
    restaurant_names = ['FG by ISS', 'FoodHub by Sodexo', 'Keila Cafe by Compass Group']
    
    # Get the current weekday name
    current_weekday = datetime.today().strftime('%A')
    current_date = datetime.now().strftime('%d.%m.%Y')
    
    return render_template('index.html', menus=menus, restaurant_names=restaurant_names, current_weekday=current_weekday, current_date=current_date, zip=zip)

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)