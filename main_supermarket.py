import os
import pandas as pd
import cloudscraper
import time
from datetime import datetime
from dotenv import load_dotenv, set_key
from requests.utils import dict_from_cookiejar

# Imports de tus módulos locales
from excel_data import export_excel
from supermarket.mercadona import gestion_mercadona
from supermarket.carrefour import gestion_carrefour
from supermarket.dia import gestion_dia

# URLs de referencia para actualización de cookies
URL_REF_CARREFOUR = "https://www.carrefour.es/cloud-api/categories-api/v1/categories/menu/"
URL_REF_DIA = "https://www.dia.es/api/v1/plp-insight/initial_analytics/charcuteria-y-quesos/jamon-cocido-lacon-fiambres-y-mortadela/c/L2001?navigation=L2001"

LIST_IDS_FAVORITES_PRODUCTS_MERCADONA = [
    "4749", "4193", "4954", "4957", "19733", "35343", "17382", "86190", "23575", "5044", 
    "26029", "5325", "13577", "6261", "6250", "6245", "60722", "22836", "16883", "15430",
    "11801", "67658", "11178", "13594", "2794", "4523", "2792", "25926", "2787", "3682", 
    "3680", "2778", "2784", "2781", "25183", "25184", "25353", "25182", "30006", "4570", 
    "3976", "8122", "35884", "2870", "15611", "86074", "53141", "59124", "59071", "50385", 
    "50927", "51234", "51223", "61261", "61231", "18018", "18107", "16616", "16416", "7313", 
    "86047", "7032", "16043", "13603", "10381", "20727", "10199", "40732", "40180", "71380", 
    "43011", "43347", "43496", "16805", "49173", "49619", "47818", "49750", "83886", "80942", "21358"
]

LIST_IDS_FAVORITES_PRODUCTS_CARREFOUR = []
LIST_IDS_FAVORITES_PRODUCTS_DIA = []

def actualizar_cookies_automaticamente(ruta_env):
    """Obtiene cookies frescas y las guarda en el archivo .env"""
    print("🔄 Intentando actualizar cookies automáticamente...")
    scraper = cloudscraper.create_scraper()
    
    # Cabeceras genéricas para simular navegador real
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-ES,es;q=0.9'
    }

    # Actualizar Carrefour
    try:
        res = scraper.get(URL_REF_CARREFOUR, headers=headers, timeout=10)
        if res.status_code == 200:
            cookies = dict_from_cookiejar(scraper.cookies)
            cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
            set_key(ruta_env, "COOKIE_CARREFOUR", cookie_str)
            print("✅ COOKIE_CARREFOUR actualizada.")
        else:
            print(f"⚠️ Carrefour devolvió estado {res.status_code}")
    except Exception as e:
        print(f"❌ Error actualizando Carrefour: {e}")

    # Actualizar DIA
    try:
        res_dia = scraper.get(URL_REF_DIA, headers=headers, timeout=10)
        if res_dia.status_code == 200:
            cookies_dia = dict_from_cookiejar(scraper.cookies)
            cookie_dia_str = "; ".join([f"{k}={v}" for k, v in cookies_dia.items()])
            set_key(ruta_env, "COOKIE_DIA", cookie_dia_str)
            print("✅ COOKIE_DIA actualizada.")
        else:
            print(f"⚠️ DIA devolvió estado {res_dia.status_code}")
    except Exception as e:
        print(f"❌ Error actualizando DIA: {e}")

def check_favortites_products(df_supermercados):
    if df_supermercados.empty:
        return df_supermercados
    df_supermercados['Favorito'] = False
    df_supermercados.loc[df_supermercados['Id'].isin(LIST_IDS_FAVORITES_PRODUCTS_MERCADONA), 'Favorito'] = True
    df_supermercados.loc[df_supermercados['Id'].isin(LIST_IDS_FAVORITES_PRODUCTS_CARREFOUR), 'Favorito'] = True
    df_supermercados.loc[df_supermercados['Id'].isin(LIST_IDS_FAVORITES_PRODUCTS_DIA), 'Favorito'] = True
    return df_supermercados

def checkConditions(ruta_env, ruta):
    if not os.path.exists(ruta):
        os.makedirs(ruta) # Crear carpeta si no existe
        print(f"Carpeta '{ruta}' creada.")
    
    if not os.path.exists(ruta_env):
        # Crear un .env básico si no existe
        with open(ruta_env, 'w') as f:
            f.write("COOKIE_CARREFOUR=''\nCOOKIE_DIA=''\n")
        print("Archivo .env creado. Reintentando actualización...")

    load_dotenv(override=True) # Cargar/Recargar variables del .env
    
    if os.getenv('COOKIE_CARREFOUR') in [None, '', 'TU_COOKIE_CARREFOUR']:
        print("Falta COOKIE_CARREFOUR en el archivo .env.")
        return False
    
    if os.getenv('COOKIE_DIA') in [None, '', 'TU_COOKIE_DIA']:
        print("Falta COOKIE_DIA en el archivo .env.")
        return False
        
    return True

if __name__ == "__main__":
    ruta_actual = os.getcwd()
    ruta_export = os.path.join(ruta_actual, "export")
    ruta_env = os.path.join(ruta_actual, ".env")

    # 1. Automatización: Intentar conseguir cookies antes de validar
    actualizar_cookies_automaticamente(ruta_env)

    # 2. Validar y ejecutar
    if checkConditions(ruta_env, ruta_export):
        print("\n--- INICIANDO SCRAPER DE SUPERMERCADOS ---")
        
        print("\n------------------------------------CARREFOUR------------------------------------")
        df_carrefour = gestion_carrefour(ruta_export)

        print("\n------------------------------------DIA------------------------------------")
        df_dia = gestion_dia(ruta_export)

        print("\n------------------------------------MERCADONA------------------------------------")
        df_mercadona = gestion_mercadona(ruta_export)

        # Unir resultados
        dfs = []
        if not df_carrefour.empty: dfs.append(df_carrefour)
        if not df_dia.empty: dfs.append(df_dia)
        if not df_mercadona.empty: dfs.append(df_mercadona)

        if dfs:
            df_supermercados = pd.concat(dfs, ignore_index=True)
            df_supermercados = check_favortites_products(df_supermercados)
            export_excel(df_supermercados, ruta_export, "products", "Productos")
            print(f"\n✅ Proceso finalizado. Archivo guardado en {ruta_export}")
        else:
            print("\n❌ No se obtuvieron datos de ningún supermercado.")
    else:
        print("\n❌ No se cumplen las condiciones para ejecutar el script.")