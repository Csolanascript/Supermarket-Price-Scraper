import cloudscraper
import os
from dotenv import load_dotenv

load_dotenv()
scraper = cloudscraper.create_scraper()

# Configuración de Dia
cookie_dia = os.getenv('COOKIE_DIA')
url_dia = "https://www.dia.es/api/v1/plp-insight/initial_analytics/charcuteria-yquesos/jamon-cocido-lacon-fiambres-ymortadela/c/L2001?navigation=L2001"

headers_dia = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Cookie': cookie_dia,
    'Accept': 'application/json',
    'Accept-Language': 'es-ES,es;q=0.9'
}

response = scraper.get(url_dia, headers=headers_dia)

if response.status_code == 200:
    data = response.json()
    print("Conexión exitosa con Dia")
    # Aquí ya puedes procesar el JSON 'data'
else:
    print(f"Error en Dia: {response.status_code}")