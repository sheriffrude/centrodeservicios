import requests
import pymysql
from datetime import datetime, timedelta

# Configuración de la API y DB se mantiene igual...
API_URL = "https://api.controlfrigo.com/api/v1/beneficios"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

DB_CONFIG = {
    'host': '192.168.9.134',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3308,
    'charset': 'utf8mb4',
    'autocommit': True,
}

def obtener_datos_api(start_date, end_date):
    headers = {'Key': API_KEY}
    params = {
        'startDate': start_date,
        'endDate': end_date,
    }
    response = requests.get(API_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error al consultar la API: {response.status_code}, {response.text}")
        return []

def obtener_id_granja(cursor, nombre_granja):
    query_granja = """
    SELECT id FROM dhc.homologacion_granjas
    WHERE NOMBRE_FRIGOTUN = %s
    LIMIT 1
    """
    cursor.execute(query_granja, (nombre_granja,))
    result = cursor.fetchone()
    return result[0] if result else None

def obtener_id_propietario(id_granja, cursor):
    query_propietario = """
    SELECT rs.ID, rs.ID_TRIBUTARIA 
    FROM dhc.granjas g
    JOIN dhc.razon_social rs ON g.RAZON_SOCIAL = rs.ID
    WHERE g.ID = %s
    """
    cursor.execute(query_propietario, (id_granja,))
    result = cursor.fetchone()
    return (result[0], result[1]) if result else (None, None)

def obtener_cerdos_recibidos(cursor, consecutivo_cercafe):
    query = """
    SELECT cerdos_recibidos 
    FROM recepcion 
    WHERE consecutivo_cercafe = %s 
    ORDER BY fecha_corte DESC 
    LIMIT 1
    """
    cursor.execute(query, (consecutivo_cercafe,))
    result = cursor.fetchone()
    return int(result[0]) if result else 0

def obtener_cantidad_registros(cursor, consecutivo_cercafe):
    query = """
    SELECT COUNT(*) 
    FROM auditoria_beneficio 
    WHERE consecutivo_cercafe = %s
    """
    cursor.execute(query, (consecutivo_cercafe,))
    result = cursor.fetchone()
    return int(result[0]) if result else 0

def validar_y_actualizar_estado(cursor, consecutivo_cercafe, registros_a_insertar=0):
    """
    Valida y actualiza el estado de una orden considerando los registros que se van a insertar
    """
    cerdos_recibidos = obtener_cerdos_recibidos(cursor, consecutivo_cercafe)
    cantidad_registros = obtener_cantidad_registros(cursor, consecutivo_cercafe) + registros_a_insertar
    
    if cerdos_recibidos == cantidad_registros:
        orden = "CERRADA"
        novedad_orden = "Validación exitosa"
    else:
        orden = "ABIERTA"
        novedad_orden = f"Faltan {cerdos_recibidos - cantidad_registros} registros para cerrar la orden"
    
    # Actualizar el estado en la base de datos
    query_update = """
    UPDATE auditoria_beneficio 
    SET orden = %s, novedad_orden = %s 
    WHERE consecutivo_cercafe = %s
    """
    cursor.execute(query_update, (orden, novedad_orden, consecutivo_cercafe))
    
    return orden, novedad_orden

def insertar_datos(datos):
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            # Agrupar registros por consecutivo_cercafe
            registros_por_consecutivo = {}
            for registro in datos:
                consecutivo = registro['consecutivo_cercafe']
                if consecutivo not in registros_por_consecutivo:
                    registros_por_consecutivo[consecutivo] = []
                registros_por_consecutivo[consecutivo].append(registro)
            
            # Procesar cada grupo de registros
            for consecutivo_cercafe, registros_grupo in registros_por_consecutivo.items():
                nuevos_registros = 0
                for registro in registros_grupo:
                    tiquete = registro['tiquete']
                    estado = registro['estado']
                    
                    # Obtener id_granja
                    id_granja = obtener_id_granja(cursor, registro['granja'])
                    if id_granja is None:
                        print(f"Saltando registro con tiquete {tiquete}: no se encontró id_granja")
                        continue
                    
                    # Obtener datos del propietario
                    id_propietario, nit_propietario = obtener_id_propietario(id_granja, cursor)
                    if not id_propietario or not nit_propietario:
                        continue
                    
                    # Verificar si el tiquete existe
                    query_check = """
                    SELECT COUNT(*), 
                           (SELECT estado_frigorifico FROM auditoria_beneficio WHERE tiquete = %s LIMIT 1) AS estado_frigorifico 
                    FROM auditoria_beneficio 
                    WHERE tiquete = %s
                    """
                    cursor.execute(query_check, (tiquete, tiquete))
                    result = cursor.fetchone()
                    count = result[0] if result else 0
                    estado_actual = result[1] if result and len(result) > 1 else None
                    
                    if count == 0:
                        nuevos_registros += 1
                        
                    # Validar y obtener el estado actualizado de la orden
                    orden, novedad_orden = validar_y_actualizar_estado(
                        cursor, 
                        consecutivo_cercafe, 
                        nuevos_registros
                    )
                    
                    if count == 0:
                        # Insertar nuevo registro
                        query_insert = """
                        INSERT INTO auditoria_beneficio2 (
                            id_frigorifico, fecha_recepcion, consecutivo_cercafe, orden_beneficio, lote, 
                            nit_propietario, id_propietario, id_granja, tiquete, fecha_hora_beneficio, 
                            fecha_hora_peso_caliente, peso_pie, peso_caliente, clasificacion, 
                            clasificacion_seurop, mm_grasa, porcentaje_magro, 
                            rendimiento_caliente, estado_frigorifico, orden, novedad_orden, metadata
                        ) VALUES (
                           %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                        )
                        """
                        cursor.execute(query_insert, (
                            6, registro['fecha_recepcion'], registro['consecutivo_cercafe'],
                            registro['orden'], registro['lote'], nit_propietario,
                            id_propietario, id_granja, registro['tiquete'],
                            registro['fecha_hora_sacrificio'], registro['fecha_hora_peso_caliente'],
                            registro['peso_pie'], registro['peso_caliente'],
                            registro['clasificacion'], registro['clasificacion_seurop'],
                            registro['mm_grasa'], registro['porcentaje_magro'],
                            registro['rendimiento_caliente'], registro['estado'],
                            orden, novedad_orden
                        ))
                        print(f"Registro con tiquete {tiquete} insertado correctamente.")
                    elif estado_actual != "PROCESADOS":
                        # Actualizar registro existente
                        query_update = """
                        UPDATE auditoria_beneficio SET
                            id_frigorifico = 6,
                            fecha_recepcion = %s,
                            consecutivo_cercafe = %s,
                            orden_beneficio = %s,
                            lote = %s,
                            nit_propietario = %s,
                            id_granja = %s,
                            fecha_hora_beneficio = %s,
                            fecha_hora_peso_caliente = %s,
                            peso_pie = %s,
                            peso_caliente = %s,
                            clasificacion = %s,
                            clasificacion_seurop = %s,
                            mm_grasa = %s,
                            porcentaje_magro = %s,
                            rendimiento_caliente = %s,
                            estado_frigorifico = %s,
                            orden = %s,
                            novedad_orden = %s,
                            metadata = NOW()
                        WHERE tiquete = %s
                        """
                        cursor.execute(query_update, (
                            registro['fecha_recepcion'], registro['consecutivo_cercafe'],
                            registro['orden'], registro['lote'], nit_propietario,
                            id_granja, registro['fecha_hora_sacrificio'],
                            registro['fecha_hora_peso_caliente'], registro['peso_pie'],
                            registro['peso_caliente'], registro['clasificacion'],
                            registro['clasificacion_seurop'], registro['mm_grasa'],
                            registro['porcentaje_magro'], registro['rendimiento_caliente'],
                            estado, orden, novedad_orden, tiquete
                        ))
                        print(f"Registro con tiquete {tiquete} actualizado correctamente.")
                
                # Actualizar estado final de la orden completa
                validar_y_actualizar_estado(cursor, consecutivo_cercafe)
    finally:
        connection.close()

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    datos = obtener_datos_api(start_date=yesterday, end_date=today)
    if datos:
        insertar_datos(datos)
    else:
        print("No se obtuvieron datos de la API.")

if __name__ == "__main__":
    main()