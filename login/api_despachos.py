from datetime import datetime, timedelta
import requests
import mysql.connector
from mysql.connector import Error
import uuid
import json # Para pretty print en depuración

# Configuración de la API
API_URL = "https://api.controlfrigo.com/api/v1/despachos/detallado"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

# Configuración de la base de datos
DB_CONFIG = {
    'host': '192.168.9.41',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': False,
}

def normalize_tiquete(tiquete_value):
    """Normaliza un valor de tiquete a un string, minúsculas y sin espacios extra."""
    if tiquete_value is None:
        return None
    # Convertir a string, quitar espacios en blanco al inicio/final, y convertir a minúsculas
    return str(tiquete_value).strip().lower()

# Función para obtener los datos de la API
def obtener_datos_api(start_date, end_date):
    headers = {
        'Key': API_KEY,
    }
    params = {
        'startDate': start_date,
        'endDate': end_date,
    }
    print(f"Consultando API desde {start_date} hasta {end_date}...")
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP al consultar la API: {http_err}, {response.text if 'response' in locals() else 'No response text'}")
    except requests.exceptions.RequestException as req_err:
        print(f"Error genérico al consultar la API: {req_err}")
    return []

# Función para insertar datos en la base de datos
def insert_data_to_db(data_from_api):
    if not data_from_api:
        print("No hay datos de la API para procesar.")
        return

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 1. Obtener y normalizar todos los tiquetes existentes de la base de datos
        cursor.execute("SELECT tiquete FROM despacho_detalle WHERE tiquete IS NOT NULL") # No es necesario CAST aquí si normalizamos en Python
        existing_tiquetes_raw = cursor.fetchall()
        
        existing_tiquetes = {normalize_tiquete(row[0]) for row in existing_tiquetes_raw}
        # Eliminar posible None del set si algún tiquete era NULL y normalize_tiquete devolvió None
        existing_tiquetes.discard(None)

        print(f"Encontrados {len(existing_tiquetes)} tiquetes existentes normalizados en la base de datos.")
        # --- INICIO BLOQUE DE DEPURACIÓN ---
        # Descomenta las siguientes líneas para ver una muestra de tiquetes existentes y de la API
        # print("Muestra de primeros 5 tiquetes existentes (normalizados):")
        # for i, t in enumerate(list(existing_tiquetes)[:5]):
        #     print(f"  BD Tiquete {i+1}: '{t}' (tipo: {type(t)})")
        # --- FIN BLOQUE DE DEPURACIÓN ---

        insert_query = """
            INSERT INTO despacho_detalle (
                fecha_despacho, orden, consecutivo_cercafe, tiquete, guia,
                peso_caliente, peso_frio, rendimiento_caliente, rendimiento_frio,
                merma, clasificacion, mm_grasa, fecha_hora_sacrificio, cliente,
                es_desposte_traslado, estado, tipo_despacho, es_retoma, expendio,
                direccion_expendio, guid, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, CURRENT_TIMESTAMP
            )
        """ # Corregido: 21 placeholders para 21 columnas (guid es el 21)

        new_records_to_insert = []
        skipped_count = 0
        processed_api_tiquetes_for_this_run = set()

        print(f"Procesando {len(data_from_api)} ítems de la API...")
        for index, item in enumerate(data_from_api):
            api_tiquete_raw = item.get('tiquete')
            api_tiquete_normalized = normalize_tiquete(api_tiquete_raw)

            # --- INICIO BLOQUE DE DEPURACIÓN ---
            # Descomenta esta sección para ver la comparación para cada tiquete de la API
            # if index < 5 or index > len(data_from_api) - 6 : # Muestra los primeros 5 y últimos 5
            #     is_in_db = api_tiquete_normalized in existing_tiquetes
            #     print(f"Ítem API {index}: Raw='{api_tiquete_raw}', Norm='{api_tiquete_normalized}' (Tipo Norm: {type(api_tiquete_normalized)}). En BD (norm)?: {is_in_db}")
            #     if is_in_db:
            #         # Si dice que está en BD pero luego se inserta, es un problema.
            #         # Si dice que NO está en BD pero debería estar, también es un problema.
            #         # Buscar manualmente api_tiquete_normalized en la lista de existing_tiquetes impresos antes.
            #         pass
            # --- FIN BLOQUE DE DEPURACIÓN ---

            if api_tiquete_normalized is None or not api_tiquete_normalized: # Si es None o cadena vacía
                # print(f"Ítem {index}: Tiquete normalizado es None o vacío. Omitiendo. Raw: '{api_tiquete_raw}'")
                skipped_count += 1
                continue

            if api_tiquete_normalized not in existing_tiquetes:
                if api_tiquete_normalized not in processed_api_tiquetes_for_this_run:
                    guid_value = str(uuid.uuid4())
                    values = (
                        item.get('fecha_despacho'), item.get('orden'), item.get('consecutivo_cercafe'),
                        api_tiquete_raw, # Insertar el valor original de la API
                        item.get('guia'), item.get('peso_caliente'), item.get('peso_frio'),
                        item.get('rendimiento_caliente'), item.get('rendimiento_frio'), item.get('merma'),
                        item.get('clasificacion'), item.get('mm_grasa'), item.get('fecha_hora_sacrificio'),
                        item.get('cliente'), item.get('es_desposte_traslado'), item.get('estado'),
                        item.get('tipo_despacho'), item.get('es_retoma'), item.get('expendio'),
                        item.get('direccion_expendio'), guid_value
                    )
                    new_records_to_insert.append(values)
                    processed_api_tiquetes_for_this_run.add(api_tiquete_normalized)
                else:
                    # print(f"Ítem {index}: Tiquete '{api_tiquete_normalized}' duplicado dentro de esta llamada API. Omitiendo.")
                    skipped_count += 1
            else:
                # print(f"Ítem {index}: Tiquete '{api_tiquete_normalized}' ya existe en la BD (normalizado). Omitiendo.")
                skipped_count += 1

        if new_records_to_insert:
            print(f"Intentando insertar {len(new_records_to_insert)} nuevas filas.")
            cursor.executemany(insert_query, new_records_to_insert)
            connection.commit()
            print(f"Se insertaron {cursor.rowcount} nuevas filas exitosamente.") # Usar cursor.rowcount para executemany
        else:
            print("No hay nuevos registros para insertar.")

        if skipped_count > 0:
            print(f"Se omitieron {skipped_count} registros.")

    except Error as e:
        print(f"Error al interactuar con la base de datos: {e}")
        if connection and connection.is_connected():
            connection.rollback()
    except Exception as ex:
        print(f"Ocurrió un error inesperado: {ex}")
        if connection and connection.is_connected():
            connection.rollback()
    finally:
        if connection and connection.is_connected():
            if cursor:
                cursor.close()
            connection.close()
            print("Conexión a la base de datos cerrada.")

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    start_date = yesterday
    end_date = today

    data = obtener_datos_api(start_date, end_date)

    if data:
        print(f"API devolvió {len(data)} registros.")
        # --- INICIO BLOQUE DE DEPURACIÓN ---
        # Descomenta para ver el primer ítem de la API y verificar 'tiquete'
        # if data:
        #     print("Ejemplo del primer ítem de la API:")
        #     print(json.dumps(data[0], indent=2, ensure_ascii=False))
        # --- FIN BLOQUE DE DEPURACIÓN ---
        insert_data_to_db(data)
    else:
        print("No se obtuvieron datos de la API o la respuesta fue vacía.")

if __name__ == "__main__":
    main()