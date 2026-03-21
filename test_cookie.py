import cloudscraper
import os
from dotenv import load_dotenv

load_dotenv()
scraper = cloudscraper.create_scraper() # Crea un cliente que salta protecciones
cookie = os.getenv('COOKIE_CARREFOUR')

headers = {
    'User-Agent': 'TU_USER_AGENT_DE_CHROME_REAL',
    'Cookie': cookie
}

r = scraper.get("https://www.carrefour.es/cloud-api/categories-api/v1/categories/menu/", headers=headers)
print(f"Resultado con CloudScraper: {r.status_code}")