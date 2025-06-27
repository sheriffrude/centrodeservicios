import requests
import pymysql
from datetime import datetime, timedelta

# Configuración sin cambios...
API_URL = "https://api.controlfrigo.com/api/v1/beneficios"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

#### PRUEBAS ##########
DB_CONFIG = {
    'host': '192.168.9.134',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3308,
    'charset': 'utf8mb4',
    'autocommit': True,
}
##### PRODUCCION  ####
# DB_CONFIG = {
#     'host': '192.168.9.41',
#     'user': 'DEV_USER',
#     'password': 'DEV-USER12345',
#     'database': 'prod_carnica',
#     'port': 3306,
# }
# --- FUNCIONES DE OBTENCIÓN DE DATOS (API, GRANJA, PROPIETARIO) SIN CAMBIOS ---

def obtener_datos_api(start_date, end_date):
    headers = {'Key': API_KEY}
    params = {'startDate': start_date, 'endDate': end_date}
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status() # Lanza un error para códigos 4xx/5xx
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al consultar la API: {e}")
        return []

def obtener_id_granja(cursor, nombre_granja):
    query = "SELECT id FROM dhc.homologacion_granjas WHERE NOMBRE_FRIGOTUN = %s LIMIT 1"
    cursor.execute(query, (nombre_granja,))
    result = cursor.fetchone()
    return result[0] if result else None

def obtener_id_propietario(id_granja, cursor):
    query = """
    SELECT rs.ID, rs.ID_TRIBUTARIA FROM dhc.granjas g
    JOIN dhc.razon_social rs ON g.RAZON_SOCIAL = rs.ID WHERE g.ID = %s
    """
    cursor.execute(query, (id_granja,))
    result = cursor.fetchone()
    return (result[0], result[1]) if result else (None, None)

def obtener_cantidad_registros(cursor, consecutivo_cercafe):
    """Cuenta cuántos tiquetes existen para un consecutivo en auditoria_beneficio."""
    query = "SELECT COUNT(*) FROM auditoria_beneficio WHERE consecutivo_cercafe = %s"
    cursor.execute(query, (consecutivo_cercafe,))
    result = cursor.fetchone()
    return int(result[0]) if result else 0

# --- INICIO DE LA FUNCIÓN CORREGIDA ---

def obtener_detalle_recepcion(cursor, consecutivo_cercafe):
    """
    Obtiene el desglose de cerdos recibidos por cada orden de beneficio
    para un mismo consecutivo.
    """
    # MODIFICADO: Se cambió 'orden_beneficio' por 'orden' para que coincida con el nombre de columna en la tabla 'recepcion'.
    query = """
    SELECT orden, cerdos_recibidos 
    FROM recepcion 
    WHERE consecutivo_cercafe = %s
    """
    cursor.execute(query, (consecutivo_cercafe,))
    # Devuelve una lista de diccionarios, ej: [{'orden': '60240', 'cantidad': 31}, ...]
    return [{'orden': row[0], 'cantidad': int(row[1])} for row in cursor.fetchall()]

# --- FIN DE LA FUNCIÓN CORREGIDA ---

def validar_y_actualizar_estado(cursor, consecutivo_cercafe):
    """
    Valida y actualiza el estado usando el desglose de órdenes.
    """
    # 1. Obtener el desglose y calcular el total esperado
    detalle_recepcion = obtener_detalle_recepcion(cursor, consecutivo_cercafe)
    total_cerdos_recibidos = sum(item['cantidad'] for item in detalle_recepcion)

    # 2. Obtener la cantidad de tiquetes ya registrados en la auditoría
    cantidad_registros_actuales = obtener_cantidad_registros(cursor, consecutivo_cercafe)
    
    # 3. Construir el mensaje de diagnóstico detallado
    detalle_str = ", ".join([f"Orden {item['orden']}: {item['cantidad']} registros" for item in detalle_recepcion])
    if not detalle_str:
        detalle_str = "No hay registros en la tabla de recepción."

    # 4. Determinar el estado y la novedad de la orden
    if total_cerdos_recibidos > 0 and total_cerdos_recibidos == cantidad_registros_actuales:
        orden = "CERRADA"
        novedad_orden = f"Validación exitosa. Total: {cantidad_registros_actuales}/{total_cerdos_recibidos} ({detalle_str})"
    else:
        orden = "ABIERTA"
        faltantes = total_cerdos_recibidos - cantidad_registros_actuales
        novedad_orden = f"Faltan {faltantes} registros. Total: {cantidad_registros_actuales}/{total_cerdos_recibidos} ({detalle_str})"

    # 5. Actualizar TODOS los registros de ese consecutivo con el estado y novedad calculados
    query_update = """
    UPDATE auditoria_beneficio 
    SET orden = %s, novedad_orden = %s 
    WHERE consecutivo_cercafe = %s
    """
    cursor.execute(query_update, (orden, novedad_orden, consecutivo_cercafe))
    print(f"Estado para consecutivo {consecutivo_cercafe} actualizado: {orden} - {novedad_orden}")

def insertar_datos(datos):
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            registros_por_consecutivo = {}
            for registro in datos:
                consecutivo = registro.get('consecutivo_cercafe')
                if consecutivo:
                    if consecutivo not in registros_por_consecutivo:
                        registros_por_consecutivo[consecutivo] = []
                    registros_por_consecutivo[consecutivo].append(registro)

            for consecutivo_cercafe, registros_grupo in registros_por_consecutivo.items():
                for registro in registros_grupo:
                    tiquete = registro['tiquete']
                    
                    id_granja = obtener_id_granja(cursor, registro['granja'])
                    if id_granja is None:
                        print(f"Saltando tiquete {tiquete}: no se encontró id_granja para '{registro['granja']}'")
                        continue
                    
                    id_propietario, nit_propietario = obtener_id_propietario(id_granja, cursor)
                    if not id_propietario:
                        print(f"Saltando tiquete {tiquete}: no se encontró propietario para id_granja {id_granja}")
                        continue
                    
                    query_check = "SELECT estado_frigorifico FROM auditoria_beneficio WHERE tiquete = %s"
                    cursor.execute(query_check, (tiquete,))
                    result = cursor.fetchone()
                    
                    if not result:
                        query_insert = """
                        INSERT INTO auditoria_beneficio (
                            id_frigorifico, fecha_recepcion, consecutivo_cercafe, orden_beneficio, lote, 
                            nit_propietario, id_propietario, id_granja, tiquete, fecha_hora_beneficio, 
                            fecha_hora_peso_caliente, peso_pie, peso_caliente, clasificacion, 
                            clasificacion_seurop, mm_grasa, porcentaje_magro, 
                            rendimiento_caliente, estado_frigorifico, metadata
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                        """
                        cursor.execute(query_insert, (
                            6, registro['fecha_recepcion'], registro['consecutivo_cercafe'],
                            registro['orden'], registro['lote'], nit_propietario,
                            id_propietario, id_granja, registro['tiquete'],
                            registro['fecha_hora_sacrificio'], registro['fecha_hora_peso_caliente'],
                            registro['peso_pie'], registro['peso_caliente'],
                            registro['clasificacion'], registro['clasificacion_seurop'],
                            registro['mm_grasa'], registro['porcentaje_magro'],
                            registro['rendimiento_caliente'], registro['estado']
                        ))
                        print(f"Tiquete {tiquete} (consecutivo {consecutivo_cercafe}) insertado.")
                    elif result[0] != "PROCESADOS":
                        query_update = """
                        UPDATE auditoria_beneficio SET
                            estado_frigorifico = %s, metadata = NOW()
                        WHERE tiquete = %s
                        """
                        cursor.execute(query_update, (registro['estado'], tiquete))
                        print(f"Tiquete {tiquete} (consecutivo {consecutivo_cercafe}) actualizado.")
                
                validar_y_actualizar_estado(cursor, consecutivo_cercafe)
    finally:
        connection.close()

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    datos = obtener_datos_api(start_date='2025-06-03', end_date='2025-06-04')
    if datos:
        insertar_datos(datos)
    else:
        print("No se obtuvieron datos de la API para el rango de fechas.")

if __name__ == "__main__":
    main()