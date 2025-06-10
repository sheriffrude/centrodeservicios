from datetime import datetime, timedelta, date
from decimal import Decimal
import requests
import mysql.connector
from mysql.connector import Error
import uuid
import json # Para pretty print en depuración

# Configuración de la API
API_URL = "https://api.controlfrigo.com/api/v1/despachos/detallado"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

##### PRODUCCION  ####
DB_CONFIG = {
    'host': '192.168.9.41',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3306,
}

##### PRUEBAS ####
# DB_CONFIG = {
#     'host': '192.168.9.134',
#     'user': 'DEV_USER',
#     'password': 'DEV-USER12345',
#     'database': 'prod_carnica',
#     'port': 3308,
#     'charset': 'utf8mb4',
#     'autocommit': False,
# }

# Mapeo de nombres de campos para mensajes más legibles
FIELD_NAMES = {
    'fecha_despacho': 'Fecha de Despacho',
    'orden': 'Orden',
    'consecutivo_cercafe': 'Consecutivo Cercafe',
    'guia': 'Guía',
    'peso_caliente': 'Peso Caliente',
    'peso_frio': 'Peso Frío',
    'rendimiento_caliente': 'Rendimiento Caliente',
    'rendimiento_frio': 'Rendimiento Frío',
    'merma': 'Merma',
    'clasificacion': 'Clasificación',
    'mm_grasa': 'MM Grasa',
    'fecha_hora_sacrificio': 'Fecha Hora Sacrificio',
    'cliente': 'Cliente',
    'es_desposte_traslado': 'Es Desposte Traslado',
    'tipo_despacho': 'Tipo Despacho',
    'es_retoma': 'Es Retoma',
    'sucursal': 'Sucursal',
    'direccion_sucursal': 'Dirección Sucursal',
    'estado': 'Estado'
}

# Mapeo de campos API a campos BD (cuando los nombres difieren)
API_TO_DB_MAPPING = {
    'expendio': 'sucursal',
    'direccion_expendio': 'direccion_sucursal'
}

def normalize_tiquete(tiquete_value):
    """Normaliza el valor del tiquete para comparación (quita espacios, convierte a minúsculas, maneja None)."""
    if tiquete_value is None:
        return None
    return str(tiquete_value).strip().lower()

def get_api_value(api_item, field_name):
    """
    Obtiene el valor de un campo de la API, considerando el mapeo de nombres.
    """
    api_field_name = field_name
    for api_key, db_key in API_TO_DB_MAPPING.items():
        if db_key == field_name:
            api_field_name = api_key
            break
            
    value = api_item.get(api_field_name)
    
    # Manejo específico para el campo 'estado' si viene como booleano
    if api_field_name == 'estado' and isinstance(value, bool):
         return 'ACTIVO' if value else 'INACTIVO'
         
    # Convertir valores vacíos o que solo contienen espacios en None para consistencia
    if isinstance(value, str) and not value.strip():
        return None

    return value

def obtener_datos_api(start_date, end_date):
    headers = {'Key': API_KEY}
    params = {'startDate': start_date, 'endDate': end_date}
    print(f"Consultando API desde {start_date} hasta {end_date}...")
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        print(f"API respondió con estado: {response.status_code}")
        data = response.json()
        print(f"API devolvió {len(data)} registros.")
        return data
    except requests.exceptions.HTTPError as http_err:
        print(f"Error HTTP al consultar la API: {http_err}")
        if 'response' in locals():
             print(f"Respuesta de la API: {response.text}")
    except requests.exceptions.Timeout:
         print(f"Tiempo de espera agotado al consultar la API después de 60 segundos.")
    except requests.exceptions.RequestException as req_err:
        print(f"Error genérico al consultar la API: {req_err}")
    except json.JSONDecodeError:
        print(f"Error al decodificar JSON de la respuesta de la API. Respuesta: {response.text if 'response' in locals() else 'N/A'}")
    return []

# --- NUEVA FUNCIÓN AUXILIAR ---
def normalize_for_comparison(value):
    """Normaliza un valor para hacer una comparación robusta."""
    if value is None:
        return None
    # Si es un objeto de fecha/hora, convertir a string en formato ISO
    if isinstance(value, (datetime, date)):
        return value.isoformat(sep=' ', timespec='seconds')
    # Si es un Decimal (de la BD), convertir a float para comparar con el JSON
    if isinstance(value, Decimal):
        return float(value)
    # Si es un booleano (de la BD, tipo TINYINT(1)), convertirlo a string '1' o '0'
    if isinstance(value, bool):
        return '1' if value else '0'
    # Para el resto, convertir a string para una comparación genérica
    # Esto ayuda a igualar '1' con 1, o 'true' con True si no se manejó antes.
    return str(value)

# --- FUNCIÓN CORREGIDA Y COMPLETADA ---
def compare_records(db_record, api_item):
    """
    Compara un registro de la BD con un item de la API para identificar cambios.
    Retorna (has_changes, changes_list).
    """
    fields_to_compare = [
        'fecha_despacho', 'orden', 'consecutivo_cercafe', 'guia',
        'peso_caliente', 'peso_frio', 'rendimiento_caliente', 'rendimiento_frio',
        'merma', 'clasificacion', 'mm_grasa', 'fecha_hora_sacrificio',
        'cliente', 'es_desposte_traslado', 'tipo_despacho', 'es_retoma',
        'sucursal', 'direccion_sucursal', 'estado'
    ]
    
    changes = []
    
    # El SELECT debe traer los campos en este orden EXACTO:
    field_indices = {
        'id': 0, 'fecha_despacho': 1, 'orden': 2, 'consecutivo_cercafe': 3,
        'tiquete': 4, 'guia': 5, 'peso_caliente': 6, 'peso_frio': 7,
        'rendimiento_caliente': 8, 'rendimiento_frio': 9, 'merma': 10,
        'clasificacion': 11, 'mm_grasa': 12, 'fecha_hora_sacrificio': 13,
        'cliente': 14, 'es_desposte_traslado': 15, 'tipo_despacho': 16,
        'es_retoma': 17, 'sucursal': 18, 'direccion_sucursal': 19,
        'estado': 20
    }
    
    for field in fields_to_compare:
        db_value = db_record[field_indices.get(field)]
        api_value = get_api_value(api_item, field)

        # Normalizamos ambos valores para una comparación justa
        db_value_norm = normalize_for_comparison(db_value)
        api_value_norm = normalize_for_comparison(api_value)
        
        # El campo booleano 'es_desposte_traslado' o similares pueden venir como 0/1 de la BD
        # y True/False del API. La normalización a string ('0'/'1') ayuda.
        # Si el API da 'True' o 'False' como texto, hay que ajustarlo.
        # Asumimos que get_api_value ya lo maneja bien.
        
        # Manejo especial para booleanos de la API que pueden no ser strings '1'/'0'
        if isinstance(api_value, bool):
             api_value_norm = '1' if api_value else '0'

        if db_value_norm != api_value_norm:
            field_display_name = FIELD_NAMES.get(field, field)
            change_message = (
                f"{field_display_name} cambió de '{db_value or 'N/A'}' a '{api_value or 'N/A'}'."
            )
            changes.append(change_message)
            
    return len(changes) > 0, changes

# --- FUNCIÓN CORREGIDA Y COMPLETADA ---
def insert_or_update_data_to_db(data_from_api):
    if not data_from_api:
        print("No hay datos de la API para procesar.")
        return

    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        select_query = """
            SELECT id, fecha_despacho, orden, consecutivo_cercafe, tiquete, guia,
                   peso_caliente, peso_frio, rendimiento_caliente, rendimiento_frio,
                   merma, clasificacion, mm_grasa, fecha_hora_sacrificio, cliente,
                   es_desposte_traslado, tipo_despacho, es_retoma, sucursal,
                   direccion_sucursal, estado
            FROM despacho_detalle 
            WHERE tiquete IS NOT NULL
        """
        cursor.execute(select_query)
        existing_records = cursor.fetchall()
        
        existing_records_dict = {
            normalize_tiquete(rec[4]): rec for rec in existing_records if normalize_tiquete(rec[4])
        }

        print(f"Encontrados {len(existing_records_dict)} registros existentes en la base de datos con tiquete.")

        # --- CORRECCIÓN EN INSERT QUERY ---
        # Añadido el campo 'novedad' a la lista y a los VALUES
        insert_query = """
            INSERT INTO despacho_detalle (
                fecha_despacho, orden, consecutivo_cercafe, tiquete, guia,
                peso_caliente, peso_frio, rendimiento_caliente, rendimiento_frio,
                merma, clasificacion, mm_grasa, fecha_hora_sacrificio, cliente,
                es_desposte_traslado, tipo_despacho, es_retoma, sucursal,
                direccion_sucursal, estado, estado_novedad, novedad, guid, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, CURRENT_TIMESTAMP
            )
        """

        update_query = """
            UPDATE despacho_detalle SET
                fecha_despacho = %s, orden = %s, consecutivo_cercafe = %s, guia = %s,
                peso_caliente = %s, peso_frio = %s, rendimiento_caliente = %s, 
                rendimiento_frio = %s, merma = %s, clasificacion = %s, mm_grasa = %s,
                fecha_hora_sacrificio = %s, cliente = %s, es_desposte_traslado = %s,
                tipo_despacho = %s, es_retoma = %s, sucursal = %s, direccion_sucursal = %s,
                estado = %s, estado_novedad = %s, novedad = %s, metadata = CURRENT_TIMESTAMP
            WHERE id = %s
        """

        new_records_to_insert_params = []
        records_to_update_params = []
        skipped_unchanged_count = 0
        skipped_no_tiquete_count = 0
        skipped_duplicate_api_tiquete = 0
        processed_api_tiquetes_for_this_run = set()

        print(f"Procesando {len(data_from_api)} ítems de la API...")
        
        for item in data_from_api:
            api_tiquete_raw = item.get('tiquete')
            api_tiquete_normalized = normalize_tiquete(api_tiquete_raw)

            if not api_tiquete_normalized:
                skipped_no_tiquete_count += 1
                continue

            if api_tiquete_normalized in processed_api_tiquetes_for_this_run:
                skipped_duplicate_api_tiquete += 1
                continue
            
            processed_api_tiquetes_for_this_run.add(api_tiquete_normalized)

            existing_record = existing_records_dict.get(api_tiquete_normalized)
            
            if existing_record:
                # El registro existe, verificar si hay cambios
                has_changes, changes_list = compare_records(existing_record, item)
                
                if has_changes:
                    novedad_text = "; ".join(changes_list)
                    db_id = existing_record[0] # ID es el primer campo

                    update_values = (
                        get_api_value(item, 'fecha_despacho'), get_api_value(item, 'orden'), 
                        get_api_value(item, 'consecutivo_cercafe'), get_api_value(item, 'guia'),
                        get_api_value(item, 'peso_caliente'), get_api_value(item, 'peso_frio'),
                        get_api_value(item, 'rendimiento_caliente'), get_api_value(item, 'rendimiento_frio'),
                        get_api_value(item, 'merma'), get_api_value(item, 'clasificacion'),
                        get_api_value(item, 'mm_grasa'), get_api_value(item, 'fecha_hora_sacrificio'),
                        get_api_value(item, 'cliente'), get_api_value(item, 'es_desposte_traslado'),
                        get_api_value(item, 'tipo_despacho'), get_api_value(item, 'es_retoma'), 
                        get_api_value(item, 'sucursal'), get_api_value(item, 'direccion_sucursal'),
                        get_api_value(item, 'estado'), 'actualizado', novedad_text, db_id
                    )
                    records_to_update_params.append(update_values)
                    print(f"TIQUETE {api_tiquete_normalized}: Preparado para ACTUALIZAR. Cambios: {novedad_text}")
                else:
                    skipped_unchanged_count += 1
            else:
                # El registro no existe, preparar para inserción
                guid_value = str(uuid.uuid4())
                
                # --- CORRECCIÓN EN EL ORDEN Y NÚMERO DE VALORES ---
                # El orden debe coincidir EXACTAMENTE con el INSERT INTO ...
                insert_values = (
                    get_api_value(item, 'fecha_despacho'), get_api_value(item, 'orden'),
                    get_api_value(item, 'consecutivo_cercafe'), api_tiquete_raw,
                    get_api_value(item, 'guia'), get_api_value(item, 'peso_caliente'),
                    get_api_value(item, 'peso_frio'), get_api_value(item, 'rendimiento_caliente'),
                    get_api_value(item, 'rendimiento_frio'), get_api_value(item, 'merma'),
                    get_api_value(item, 'clasificacion'), get_api_value(item, 'mm_grasa'),
                    get_api_value(item, 'fecha_hora_sacrificio'), get_api_value(item, 'cliente'),
                    get_api_value(item, 'es_desposte_traslado'), get_api_value(item, 'tipo_despacho'),
                    get_api_value(item, 'es_retoma'), get_api_value(item, 'sucursal'),
                    get_api_value(item, 'direccion_sucursal'), get_api_value(item, 'estado'),
                    'nuevo',        # estado_novedad
                    None,           # novedad (es nuevo, no hay cambios)
                    guid_value      # guid
                )
                new_records_to_insert_params.append(insert_values)
                print(f"TIQUETE {api_tiquete_normalized}: Preparado para INSERTAR como nuevo.")

        if new_records_to_insert_params:
            print(f"Insertando {len(new_records_to_insert_params)} nuevos registros...")
            cursor.executemany(insert_query, new_records_to_insert_params)
        
        if records_to_update_params:
            print(f"Actualizando {len(records_to_update_params)} registros existentes que cambiaron...")
            cursor.executemany(update_query, records_to_update_params)
            
        connection.commit()
        print("\n--- RESUMEN DEL PROCESO ---")
        print(f"  - Registros de API procesados: {len(data_from_api)}")
        print(f"  - Nuevos registros insertados: {len(new_records_to_insert_params)}")
        print(f"  - Registros existentes actualizados: {len(records_to_update_params)}")
        print(f"  - Registros existentes sin cambios (omitidos): {skipped_unchanged_count}")
        print(f"  - Registros de API omitidos (sin tiquete): {skipped_no_tiquete_count}")
        print(f"  - Registros de API omitidos (tiquete duplicado): {skipped_duplicate_api_tiquete}")
        
    except Error as e:
        print(f"Error al interactuar con la base de datos: {e}")
        if connection and connection.is_connected():
            connection.rollback()
            print("Rollback realizado.")
    finally:
        if cursor:
            cursor.close()
        if connection and connection.is_connected():
            connection.close()
            print("Conexión a la base de datos cerrada.")

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    start_date = '2025-01-01'
    end_date = today

    data = obtener_datos_api(start_date, end_date)

    if data:
        insert_or_update_data_to_db(data)
    else:
        print("No se obtuvieron datos de la API o la respuesta estaba vacía.")

if __name__ == "__main__":
    main()