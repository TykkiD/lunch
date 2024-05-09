import pytesseract
from PIL import Image
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from datetime import datetime, timedelta
import os

finnish_weekdays = {
    'Monday': 'Maanantai',
    'Tuesday': 'Tiistai',
    'Wednesday': 'Keskiviikko',
    'Thursday': 'Torstai',
    'Friday': 'Perjantai',
    'Saturday': 'Lauantai',
    'Sunday': 'Sunnuntai'
}
finnish_weekday = finnish_weekdays.get(datetime.today().strftime('%A'))

today = datetime.today()
week = today.isocalendar()[1]
day_month = today.strftime("%-d.%-m")
# this weeks monday 9am
monday_9am = today.replace(hour=9, minute=0, second=0, microsecond=0) - timedelta(days=today.weekday())

taste_lunch_url = 'https://www.tasteravintolat.fi/fi/taste-buffet-lunch-porvoo'
taste_day_night_url = 'https://www.tasteravintolat.fi/fi/taste-day-night-club-porvoo'

def create_cache_file():
    with open('cache.txt', 'w') as file:
        file.write(f"{today},{week}")

def check_cache_file():
    try:
        with open('cache.txt', 'r') as file:
            cache_data = file.read().strip().split(',')
            cache_date = datetime.strptime(cache_data[0], '%Y-%m-%d %H:%M:%S.%f')
            cache_week = int(cache_data[1])
            if cache_week != week or cache_date < monday_9am:
                create_cache_file()
                return True
            return False
    except FileNotFoundError:
        create_cache_file()
    except Exception as e:
        print("Error reading cache file:", e)

def get_image(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        img = soup.select('#img_comp-lltgfoul img') or soup.select('#img_comp-lp9rmpan img')
        if img:
            img_url = img[0].get('src')
            if img_url:
                png_index = img_url.find('.png')
                img_url = img_url[:png_index + 4]
                img_response = requests.get(img_url)
                img_response.raise_for_status()
                print("Image fetched successfully")
                return Image.open(BytesIO(img_response.content))
        print("No image URL found")
    except Exception as e:
        print(f"Error: {e}")
    return None

def extract_text_from_image(img):
    # Perform OCR using PyTesseract
    width, height = img.size
    left_img = img.crop((0, 380, width / 2 - 50, 1560))
    right_img = img.crop((width / 2.2, 380, width, 1300))

    left_text = pytesseract.image_to_string(left_img, lang='fin')
    right_text = pytesseract.image_to_string(right_img, lang='fin')

    text = """LOUNAASEEN KUULUU TUMMAPAAHDETTUA KAHVIA
PORVOON PAAHTIMOLTA"""

    right_text = right_text.replace(text, '')

    # left_img.show()
    # right_img.show()

    return left_text, right_text

def sort_days(text):
    # Define the start and end positions of each day's text
    day_positions = {
        "MAANANTAI": ["MAANANTAI", "KESKIVIIKKO"],
        "TIISTAI": ["TIISTAI", "TORSTAI"],
        "KESKIVIIKKO": ["KESKIVIIKKO", "PERJANTAI"],
        "TORSTAI": ["TORSTAI", None],
        "PERJANTAI": ["PERJANTAI", "TIISTAI"]
    }

    # Extract text for each day
    days_text = {}
    for day, (start, end) in day_positions.items():
        start_pos = text.find(start)
        end_pos = text.find(end) if end is not None else None
        day_text = text[start_pos:end_pos].strip().split('\n')
        # Filter out empty strings
        day_text = [line.capitalize() for line in day_text if line.strip()]
        # Capitalize only the last word of each line
        modified_day_text = []
        for line in day_text:
            words = line.strip().split()
            if words:
                words[-1] = words[-1].upper()
                modified_day_text.append(' '.join(words))
        days_text[day] = modified_day_text


    return days_text.values()

def get_menu_from_image(*urls):
    if check_cache_file() or not os.path.exists('all_menus.txt'):
        all_menus = {}
        for url in urls:
            try:
                image = get_image(url)
                if image:
                    left_text, right_text = extract_text_from_image(image)
                    text = left_text + right_text
                    all_days = sort_days(text)
                    # Remove empty lists from all_days
                    all_days = [day for day in all_days if day]
                    if all_days:  # Only add non-empty lists to all_menus
                        all_menus[url.split("/")[-1]] = all_days
            except Exception as e:
                print(f"Error processing image from {url}: {e}")
        print(all_menus)
        with open('all_menus.txt', 'w') as file:
            file.write(str(all_menus))
    else:
        with open('all_menus.txt', 'r') as file:
            all_menus = eval(file.read())
    return all_menus

def get_all_menus():
    return get_menu_from_image(taste_lunch_url, taste_day_night_url)

def get_today():
    menus_of_today = []
    all_menus = get_menu_from_image(taste_lunch_url, taste_day_night_url)
    for url, menu in all_menus.items(): 
        for todays_menu in menu: 
            menus_date = todays_menu[0].split()[1]
            menu_weekday = todays_menu[0].split()[0]
            if menus_date == day_month  or menus_date == day_month + '.':
                menus_of_today.append(todays_menu)
            elif menu_weekday == finnish_weekday:
                menus_of_today.append([todays_menu[0], 'Tuskin mitään ruokaa'])
    return menus_of_today

# if __name__ == "__main__":
#     main()
if __name__ == "__main__":
    app.run(debug=True)