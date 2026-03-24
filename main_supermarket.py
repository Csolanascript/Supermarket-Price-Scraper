import os
import pandas as pd
import cloudscraper
import time
import sys
from datetime import datetime
from dotenv import load_dotenv, set_key
from requests.utils import dict_from_cookiejar

# Imports de tus módulos locales
from excel_data import export_excel
from supermarket.mercadona import gestion_mercadona
from supermarket.carrefour import gestion_carrefour
from supermarket.dia import gestion_dia

# URLs de referencia
URL_REF_CARREFOUR = "https://www.carrefour.es/cloud-api/categories-api/v1/categories/menu/"
URL_REF_DIA = "https://www.dia.es/api/v1/plp-insight/initial_analytics/charcuteria-y-quesos/jamon-cocido-lacon-fiambres-y-mortadela/c/L2001?navigation=L2001"

# Listas de favoritos (puedes seguir añadiendo IDs aquí)
LIST_IDS_FAVORITES_MERCADONA = ["4749", "4193", "4954", "4957"] # ... (abreviado por brevedad)
LIST_IDS_FAVORITES_CARREFOUR = []
LIST_IDS_FAVORITES_DIA = []

def peticion_con_retries(scraper, url, headers, nombre_super):
    """
    Gestiona peticiones con reintentos ante errores 403.
    Retorna la respuesta si es 200, de lo contrario None tras agotar intentos.
    """
    max_intentos = 5
    espera = 20

    for intento in range(1, max_intentos + 1):
        try:
            res = scraper.get(url, headers=headers, timeout=15)
            
            if res.status_code == 200:
                return res
            
            if res.status_code == 403:
                print(f"⚠️ [Intento {intento}/{max_intentos}] {nombre_super} bloqueó el acceso (403).")
                if intento < max_intentos:
                    print(f"   Esperando {espera} segundos para reintentar...")
                    time.sleep(espera)
                else:
                    print(f"❌ Se agotaron los {max_intentos} intentos para {nombre_super}.")
            else:
                print(f"⚠️ {nombre_super} devolvió error {res.status_code}. No se puede continuar automáticamente.")
                return None

        except Exception as e:
            print(f"❌ Error de conexión en {nombre_super}: {e}")
            if intento < max_intentos: time.sleep(espera)
            
    return None

def actualizar_cookies_automaticamente(ruta_env):
    """Obtiene cookies frescas y las guarda en el archivo .env"""
    print("🔄 Iniciando actualización automática de cookies...")
    scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'es-ES,es;q=0.9'
    }

    exito_c = False
    exito_d = False

    # Carrefour
    res_c = peticion_con_retries(scraper, URL_REF_CARREFOUR, headers, "Carrefour")
    if res_c:
        cookies = dict_from_cookiejar(scraper.cookies)
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        set_key(ruta_env, "COOKIE_CARREFOUR", cookie_str)
        print("✅ COOKIE_CARREFOUR actualizada.")
        exito_c = True

    # DIA
    res_d = peticion_con_retries(scraper, URL_REF_DIA, headers, "DIA")
    if res_d:
        cookies = dict_from_cookiejar(scraper.cookies)
        cookie_str = "; ".join([f"{k}={v}" for k, v in cookies.items()])
        set_key(ruta_env, "COOKIE_DIA", cookie_str)
        print("✅ COOKIE_DIA actualizada.")
        exito_d = True

    return exito_c, exito_d

def check_favortites_products(df):
    if df.empty: return df
    df['Favorito'] = False
    all_favs = LIST_IDS_FAVORITES_MERCADONA + LIST_IDS_FAVORITES_CARREFOUR + LIST_IDS_FAVORITES_DIA
    df.loc[df['Id'].isin(all_favs), 'Favorito'] = True
    return df

def checkConditions(ruta_env, ruta):
    if not os.path.exists(ruta): os.makedirs(ruta)
    if not os.path.exists(ruta_env):
        with open(ruta_env, 'w') as f: f.write("COOKIE_CARREFOUR=''\nCOOKIE_DIA=''\n")
    load_dotenv(override=True)
    return True

if __name__ == "__main__":
    ahora = datetime.now()
    nombrecarpeta = ahora.strftime("%Y-%m-%d_%H-%M-%S")
    ruta_export = os.path.join(os.getcwd(), "export", nombrecarpeta)
    ruta_env = os.path.join(os.getcwd(), ".env")

    # 1. Actualización con reintentos
    exito_c, exito_d = actualizar_cookies_automaticamente(ruta_env)

    # 2. Salida controlada si todo falla
    if not exito_c and not exito_d:
        print("\n🚫 ERROR CRÍTICO: No se han podido obtener cookies tras 5 intentos.")
        print("Es posible que Cloudflare haya bloqueado tu IP. Abortando ejecución.")
        sys.exit(1)

    # 3. Ejecución principal
    if checkConditions(ruta_env, ruta_export):
        dfs = []

        if exito_d:
            print("\n" + "-"*20 + " DIA " + "-"*20)
            dfs.append(gestion_dia(ruta_export))

        if exito_c:
            print("\n" + "-"*20 + " CARREFOUR " + "-"*20)
            dfs.append(gestion_carrefour(ruta_export))

        print("\n" + "-"*20 + " MERCADONA " + "-"*20)
        dfs.append(gestion_mercadona(ruta_export))

        # Unir y exportar final
        valid_dfs = [d for d in dfs if not d.empty]
        if valid_dfs:
            df_total = pd.concat(valid_dfs, ignore_index=True)
            df_total = check_favortites_products(df_total)
            export_excel(df_total, ruta_export, "products_all", "Productos_Global")
            print(f"\n✅ Proceso completado con éxito en: {ruta_export}")
        else:
            print("\n❌ No se recuperó información de ningún supermercado.")