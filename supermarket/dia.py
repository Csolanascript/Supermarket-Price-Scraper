import cloudscraper
import os
from datetime import *
import pandas as pd
import time
from dotenv import load_dotenv
# Asumo que estas funciones vienen de tus archivos locales
from excel_data import export_excel 

# --- CONFIGURACIÓN ---
# Creamos el scraper a nivel global para reutilizar la sesión
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

URL_CATEGORY_DIA = "https://www.dia.es/api/v1/plp-insight/initial_analytics/charcuteria-y-quesos/jamon-cocido-lacon-fiambres-y-mortadela/c/L2001?navigation=L2001"
URL_PRODUCTS_BY_CATEGORY_DIA = "https://www.dia.es/api/v1/plp-back/reduced"

# Mantenemos tus headers pero asegúrate de que el User-Agent coincida con el que usaste para sacar la Cookie
HEADERS_REQUEST_DIA = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': "es-ES,es;q=0.9",
    'Cookie': os.getenv('COOKIE_DIA'), # La cargamos directamente aquí
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Sec-Ch-Ua-Platform': '"Windows"',
}

def gestion_dia(ruta):
    tiempo_inicio_dia = time.time()

    # 1. Obtener IDs de categorías
    list_categories = get_ids_categorys_dia()
    
    if not list_categories:
        print("No se pudieron obtener las categorías. Revisa la COOKIE_DIA.")
        return pd.DataFrame()

    # 2. Obtener productos
    df_dia = get_products_by_category_dia(list_categories, ruta)

    duracion_total_dia = time.time() - tiempo_inicio_dia
    minutos_dia = int(duracion_total_dia // 60)
    segundos_dia = int(duracion_total_dia % 60)

    print(f"La ejecución de DIA ha tomado: {minutos_dia} min y {segundos_dia} seg")
    return df_dia


def get_products_by_category_dia(list_categories, ruta):
    df_products = pd.DataFrame()
    
    for index, stringCategoria in enumerate(list_categories):
        print(f"{index+1}/{len(list_categories)} - Procesando categoría: {stringCategoria}")
        
        # En la API de Dia, el ID de categoría suele ir como parámetro o parte de la URL
        url = f"{URL_PRODUCTS_BY_CATEGORY_DIA}/{stringCategoria}"

        try:
            # CAMBIO: Usamos scraper.get en lugar de requests.get
            response = scraper.get(url, headers=HEADERS_REQUEST_DIA, timeout=10)
            
            if response.status_code == 200:
                list_products = response.json()
                
                if "plp_items" in list_products and list_products["plp_items"]:
                    df_productos = pd.json_normalize(list_products["plp_items"], sep="_")
                    
                    # Transformaciones de datos
                    df_productos['url'] = 'https://www.dia.es' + df_productos['url']
                    df_productos['image'] = 'https://www.dia.es' + df_productos['image']
                    df_productos['categoria'] = stringCategoria
                    df_productos['supermercado'] = "Dia"
                    
                    # Mapeo de columnas
                    renamed_columns = {
                        'object_id': 'Id', 
                        'display_name': 'Nombre',
                        'prices_price': 'Precio',
                        'prices_price_per_unit': 'Precio Pack',
                        'prices_measure_unit': 'Formato',
                        'categoria': 'Categoria',
                        'supermercado': 'Supermercado',
                        'url': 'Url', 
                        'image': 'Url_imagen'
                    }
                    
                    # Filtrar solo las que existen para evitar errores
                    cols_to_use = [c for c in renamed_columns.keys() if c in df_productos.columns]
                    df_final = df_productos[cols_to_use].rename(columns=renamed_columns)
                    
                    df_products = pd.concat([df_products, df_final], ignore_index=True)
                else:
                    print(f"Sin productos en: {stringCategoria}")
            else:
                print(f"Error {response.status_code} en categoría {stringCategoria}")
                
        except Exception as e:
            print(f"ERROR en {stringCategoria}: {e}")


    # Export Excel (función externa que ya tienes)
    try:
        export_excel(df_products, os.path.join(ruta,""), "products_dia_", "Productos_Dia")
    except NameError:
        print("Aviso: Función export_excel no definida, se omite el guardado.")
    
    return df_products

def get_ids_categorys_dia():
    try:
        # CAMBIO: Usamos scraper.get
        response = scraper.get(URL_CATEGORY_DIA, headers=HEADERS_REQUEST_DIA)
        if response.status_code != 200:
            print(f"Error al obtener categorías: {response.status_code}")
            return []
            
        list_category_dia = response.json()
        info = list_category_dia['menu_analytics']
        
        data = procesar_nodo(info)
        df_resultado = pd.DataFrame(data, columns=['id', 'parameter', 'path'])
        df_resultado = df_resultado[df_resultado['parameter'].notna()]

        # Extraer los IDs de las categorías (ajusta según la estructura real de 'path')
        category_ids = df_resultado["path"].explode().dropna().unique().tolist()
        return category_ids

    except Exception as e:
        print(f"ERROR - La cookie ha caducado o hay un problema de conexión: {e}")
        return []

def procesar_nodo(nodo, parent_path=""):
    data = []
    for key, value in nodo.items():
        path = f"{parent_path}/{key}" if parent_path else key
        parameter = value.get('parameter', None)
        path_list = value.get('path', None)
        data.append((key, parameter, path_list))
        children = value.get('children', {})
        if children:
            data.extend(procesar_nodo(children, parent_path=path))
        elif 'children' in value:
            data.append(('', None, path))
    return data