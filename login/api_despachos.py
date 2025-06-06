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
    'host': '192.168.9.134',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3308,
    'charset': 'utf8mb4',
    'autocommit': False,
}

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
    'direccion_sucursal': 'Dirección Sucursal'
}

def normalize_tiquete(tiquete_value):
    if tiquete_value is None:
        return None
    # Convertir a string, quitar espacios en blanco al inicio/final, y convertir a minúsculas
    return str(tiquete_value).strip().lower()

def normalize_value(value):
    """Normaliza valores para comparación (maneja None, espacios, etc.)"""
    if value is None:
        return None
    return str(value).strip()

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

def compare_records(db_record, api_item):
    """
    Compara un registro de la BD con un item de la API
    Retorna (has_changes, changes_list)
    """
    # Campos a comparar (excluimos id, tiquete, guid, metadata, estado_novedad, novedad)
    fields_to_compare = [
        'fecha_despacho', 'orden', 'consecutivo_cercafe', 'guia',
        'peso_caliente', 'peso_frio', 'rendimiento_caliente', 'rendimiento_frio',
        'merma', 'clasificacion', 'mm_grasa', 'fecha_hora_sacrificio',
        'cliente', 'es_desposte_traslado', 'tipo_despacho', 'es_retoma',
        'sucursal', 'direccion_sucursal'
    ]
    
    changes = []
    
    # db_record es una tupla, necesitamos mapear a índices
    # Orden de campos en la consulta SELECT:
    field_indices = {
        'id': 0, 'fecha_despacho': 1, 'orden': 2, 'consecutivo_cercafe': 3,
        'tiquete': 4, 'guia': 5, 'peso_caliente': 6, 'peso_frio': 7,
        'rendimiento_caliente': 8, 'rendimiento_frio': 9, 'merma': 10,
        'clasificacion': 11, 'mm_grasa': 12, 'fecha_hora_sacrificio': 13,
        'cliente': 14, 'es_desposte_traslado': 15, 'tipo_despacho': 16,
        'es_retoma': 17, 'sucursal': 18, 'direccion_sucursal': 19
    }
    
    for field in fields_to_compare:
        db_value = normalize_value(db_record[field_indices[field]])
        api_value = normalize_value(api_item.get(field))
        
        if db_value != api_value:
            field_display_name = FIELD_NAMES.get(field, field)
            change_msg = f"cambió {field_display_name} de '{db_value}' por '{api_value}'"
            changes.append(change_msg)
    
    return len(changes) > 0, changes

# Función para insertar/actualizar datos en la base de datos
def insert_or_update_data_to_db(data_from_api):
    if not data_from_api:
        print("No hay datos de la API para procesar.")
        return

    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # 1. Obtener todos los registros existentes de la base de datos
        select_query = """
            SELECT id, fecha_despacho, orden, consecutivo_cercafe, tiquete, guia,
                   peso_caliente, peso_frio, rendimiento_caliente, rendimiento_frio,
                   merma, clasificacion, mm_grasa, fecha_hora_sacrificio, cliente,
                   es_desposte_traslado, tipo_despacho, es_retoma, sucursal,
                   direccion_sucursal
            FROM despacho_detalle 
            WHERE tiquete IS NOT NULL
        """
        
        cursor.execute(select_query)
        existing_records = cursor.fetchall()
        
        # Crear un diccionario para búsqueda rápida por tiquete normalizado
        existing_records_dict = {}
        for record in existing_records:
            tiquete_normalized = normalize_tiquete(record[4])  # tiquete está en índice 4
            if tiquete_normalized:
                existing_records_dict[tiquete_normalized] = record

        print(f"Encontrados {len(existing_records_dict)} registros existentes en la base de datos.")

        # Queries para insertar y actualizar
        insert_query = """
            INSERT INTO despacho_detalle (
                fecha_despacho, orden, consecutivo_cercafe, tiquete, guia,
                peso_caliente, peso_frio, rendimiento_caliente, rendimiento_frio,
                merma, clasificacion, mm_grasa, fecha_hora_sacrificio, cliente,
                es_desposte_traslado, estado_novedad, tipo_despacho, es_retoma, sucursal,
                direccion_sucursal, guid, metadata
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, CURRENT_TIMESTAMP
            )
        """

        update_query = """
            UPDATE despacho_detalle SET
                fecha_despacho = %s, orden = %s, consecutivo_cercafe = %s, guia = %s,
                peso_caliente = %s, peso_frio = %s, rendimiento_caliente = %s, 
                rendimiento_frio = %s, merma = %s, clasificacion = %s, mm_grasa = %s,
                fecha_hora_sacrificio = %s, cliente = %s, es_desposte_traslado = %s,
                tipo_despacho = %s, es_retoma = %s, sucursal = %s, direccion_sucursal = %s,
                estado_novedad = %s, novedad = %s, metadata = CURRENT_TIMESTAMP
            WHERE id = %s
        """

        new_records_to_insert = []
        records_to_update = []
        skipped_count = 0
        processed_api_tiquetes_for_this_run = set()

        print(f"Procesando {len(data_from_api)} ítems de la API...")
        
        for index, item in enumerate(data_from_api):
            api_tiquete_raw = item.get('tiquete')
            api_tiquete_normalized = normalize_tiquete(api_tiquete_raw)

            if api_tiquete_normalized is None or not api_tiquete_normalized:
                skipped_count += 1
                continue

            # Evitar duplicados en la misma ejecución
            if api_tiquete_normalized in processed_api_tiquetes_for_this_run:
                skipped_count += 1
                continue
            
            processed_api_tiquetes_for_this_run.add(api_tiquete_normalized)

            if api_tiquete_normalized in existing_records_dict:
                # Registro existe, verificar si hay cambios
                existing_record = existing_records_dict[api_tiquete_normalized]
                has_changes, changes_list = compare_records(existing_record, item)
                
                if has_changes:
                    # Preparar datos para actualización
                    novedad_text = "; ".join(changes_list)
                    update_values = (
                        item.get('fecha_despacho'), item.get('orden'), 
                        item.get('consecutivo_cercafe'), item.get('guia'),
                        item.get('peso_caliente'), item.get('peso_frio'),
                        item.get('rendimiento_caliente'), item.get('rendimiento_frio'),
                        item.get('merma'), item.get('clasificacion'), item.get('mm_grasa'),
                        item.get('fecha_hora_sacrificio'), item.get('cliente'),
                        item.get('es_desposte_traslado'), item.get('tipo_despacho'),
                        item.get('es_retoma'), item.get('sucursal'),
                        item.get('direccion_sucursal'), 'actualizado', novedad_text,
                        existing_record[0]  # ID del registro
                    )
                    records_to_update.append(update_values)
                else:
                    # No hay cambios, no hacer nada
                    skipped_count += 1
            else:
                # Registro nuevo, preparar para inserción
                guid_value = str(uuid.uuid4())
                insert_values = (
                    item.get('fecha_despacho'), item.get('orden'), 
                    item.get('consecutivo_cercafe'), api_tiquete_raw, item.get('guia'),
                    item.get('peso_caliente'), item.get('peso_frio'),
                    item.get('rendimiento_caliente'), item.get('rendimiento_frio'),
                    item.get('merma'), item.get('clasificacion'), item.get('mm_grasa'),
                    item.get('fecha_hora_sacrificio'), item.get('cliente'),
                    item.get('es_desposte_traslado'), 'nuevo', item.get('tipo_despacho'),
                    item.get('es_retoma'), item.get('sucursal'),
                    item.get('direccion_sucursal'), guid_value
                )
                new_records_to_insert.append(insert_values)

        # Ejecutar inserciones
        if new_records_to_insert:
            print(f"Insertando {len(new_records_to_insert)} nuevos registros...")
            cursor.executemany(insert_query, new_records_to_insert)
            print(f"Se insertaron {len(new_records_to_insert)} nuevos registros exitosamente.")

        # Ejecutar actualizaciones
        if records_to_update:
            print(f"Actualizando {len(records_to_update)} registros existentes...")
            cursor.executemany(update_query, records_to_update)
            print(f"Se actualizaron {len(records_to_update)} registros exitosamente.")

        # Confirmar cambios
        connection.commit()

        if skipped_count > 0:
            print(f"Se omitieron {skipped_count} registros (sin cambios o duplicados).")

        print(f"Resumen: {len(new_records_to_insert)} nuevos, {len(records_to_update)} actualizados, {skipped_count} omitidos.")

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
        insert_or_update_data_to_db(data)
    else:
        print("No se obtuvieron datos de la API o la respuesta fue vacía.")

if __name__ == "__main__":
    main()