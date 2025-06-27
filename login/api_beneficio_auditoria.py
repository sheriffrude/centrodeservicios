import requests
import pymysql
from datetime import datetime, timedelta

# Configuración de la API y DB
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

def obtener_datos_api(start_date, end_date):
    """Obtiene los datos de la API de ControlFrigo."""
    headers = {'Key': API_KEY}
    params = {'startDate': start_date, 'endDate': end_date}
    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al consultar la API: {e}")
        return []

# --- FUNCIÓN CLAVE CORREGIDA ---
def obtener_total_cerdos_esperados(cursor, consecutivo_cercafe):
    """
    Calcula el total de cerdos esperados para un consecutivo.
    1. Para cada 'orden_recepcion' distinta dentro del consecutivo, encuentra su registro más reciente.
    2. Suma la cantidad de cerdos de esos registros más recientes.
    """
    # Se cambió 'orden_beneficio' por 'orden_recepcion' para que coincida con el nombre de la columna en la tabla 'recepcion'
    query = """
    SELECT SUM(cerdos_recibidos)
    FROM (
        SELECT 
            cerdos_recibidos,
            ROW_NUMBER() OVER(PARTITION BY orden_recepcion ORDER BY fecha_corte DESC) as rn
        FROM recepcion
        WHERE consecutivo_cercafe = %s
    ) as ranked_recepciones
    WHERE rn = 1;
    """
    cursor.execute(query, (consecutivo_cercafe,))
    result = cursor.fetchone()
    return int(result[0]) if result and result[0] is not None else 0

def obtener_id_granja(cursor, nombre_granja):
    """Obtiene el ID de una granja desde la tabla de homologación."""
    query = "SELECT id FROM dhc.homologacion_granjas WHERE NOMBRE_FRIGOTUN = %s LIMIT 1"
    cursor.execute(query, (nombre_granja,))
    result = cursor.fetchone()
    return result[0] if result else None

def obtener_id_propietario(id_granja, cursor):
    """Obtiene el ID y NIT del propietario de una granja."""
    query = """
    SELECT rs.ID, rs.ID_TRIBUTARIA 
    FROM dhc.granjas g
    JOIN dhc.razon_social rs ON g.RAZON_SOCIAL = rs.ID
    WHERE g.ID = %s
    """
    cursor.execute(query, (id_granja,))
    result = cursor.fetchone()
    return (result[0], result[1]) if result else (None, None)

def insertar_datos(datos):
    """
    Inserta o actualiza datos, validando el lote completo antes de procesar sus registros.
    """
    if not datos:
        return

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
                
                # --- VALIDACIÓN A NIVEL DE LOTE ---
                total_recibidos_db = obtener_total_cerdos_esperados(cursor, consecutivo_cercafe)
                total_en_api = len(registros_grupo)

                orden_estado = "ABIERTA"
                orden_novedad = ""

                if total_recibidos_db == 0:
                    orden_novedad = f"Error: No se encontró recepción válida para el consecutivo {consecutivo_cercafe}."
                elif total_recibidos_db != total_en_api:
                    faltantes = total_recibidos_db - total_en_api
                    orden_novedad = f"Faltan {faltantes} registros. (Esperados: {total_recibidos_db}, Recibidos en API: {total_en_api})"
                else:
                    orden_estado = "CERRADA"
                    orden_novedad = "Validación exitosa."

                print(f"--- Procesando orden {consecutivo_cercafe} | Estado Determinado: {orden_estado} | Novedad: {orden_novedad} ---")
                
                for registro in registros_grupo:
                    tiquete = registro['tiquete']
                    
                    id_granja, id_propietario, nit_propietario = None, None, None
                    novedad_individual = ""
                    nombre_granja_api = registro.get('granja')
                    if not nombre_granja_api:
                        novedad_individual = "Novedad: Granja no informada en API."
                    else:
                        id_granja = obtener_id_granja(cursor, nombre_granja_api)
                        if id_granja is None:
                            novedad_individual = f"Novedad: Granja '{nombre_granja_api}' no homologada."
                        else:
                            id_propietario, nit_propietario = obtener_id_propietario(id_granja, cursor)
                            if not id_propietario:
                                novedad_individual = f"Novedad: Propietario no encontrado para granja ID {id_granja}."
                    
                    novedad_final_registro = orden_novedad
                    estado_final_registro = orden_estado
                    if novedad_individual:
                        novedad_final_registro = novedad_individual
                        estado_final_registro = "ABIERTA"

                    query_check = "SELECT 1 FROM auditoria_beneficio WHERE tiquete = %s"
                    cursor.execute(query_check, (tiquete,))
                    existe = cursor.fetchone()

                    if not existe:
                        query_insert = """
                        INSERT INTO auditoria_beneficio (
                            id_frigorifico, fecha_recepcion, consecutivo_cercafe, orden_beneficio, lote, 
                            nit_propietario, id_propietario, id_granja, tiquete, fecha_hora_beneficio, 
                            fecha_hora_peso_caliente, peso_pie, peso_caliente, clasificacion, 
                            clasificacion_seurop, mm_grasa, porcentaje_magro, rendimiento_caliente, 
                            estado_frigorifico, orden, novedad_orden, metadata
                        ) VALUES (
                           6, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                        )
                        """
                        params = (
                            registro.get('fecha_recepcion'), consecutivo_cercafe,
                            registro.get('orden'), registro.get('lote'), nit_propietario,
                            id_propietario, id_granja, tiquete,
                            registro.get('fecha_hora_sacrificio'), registro.get('fecha_hora_peso_caliente'),
                            registro.get('peso_pie'), registro.get('peso_caliente'),
                            registro.get('clasificacion'), registro.get('clasificacion_seurop'),
                            registro.get('mm_grasa'), registro.get('porcentaje_magro'),
                            registro.get('rendimiento_caliente'), registro.get('estado'),
                            estado_final_registro, novedad_final_registro
                        )
                        cursor.execute(query_insert, params)
                        print(f"  > Tiquete {tiquete} INSERTADO.")
                    else:
                        query_update = """
                        UPDATE auditoria_beneficio SET
                            fecha_recepcion = %s, orden_beneficio = %s, lote = %s, 
                            nit_propietario = %s, id_propietario = %s, id_granja = %s, fecha_hora_beneficio = %s, 
                            fecha_hora_peso_caliente = %s, peso_pie = %s, peso_caliente = %s, 
                            clasificacion = %s, clasificacion_seurop = %s, mm_grasa = %s, 
                            porcentaje_magro = %s, rendimiento_caliente = %s, estado_frigorifico = %s, 
                            orden = %s, novedad_orden = %s, metadata = NOW()
                        WHERE tiquete = %s AND consecutivo_cercafe = %s
                        """
                        params = (
                            registro.get('fecha_recepcion'), registro.get('orden'), registro.get('lote'),
                            nit_propietario, id_propietario, id_granja,
                            registro.get('fecha_hora_sacrificio'), registro.get('fecha_hora_peso_caliente'),
                            registro.get('peso_pie'), registro.get('peso_caliente'),
                            registro.get('clasificacion'), registro.get('clasificacion_seurop'),
                            registro.get('mm_grasa'), registro.get('porcentaje_magro'),
                            registro.get('rendimiento_caliente'), registro.get('estado'),
                            estado_final_registro, novedad_final_registro, tiquete, consecutivo_cercafe
                        )
                        cursor.execute(query_update, params)
                        print(f"  > Tiquete {tiquete} ACTUALIZADO.")

    except pymysql.MySQLError as e:
        print(f"Error de base de datos: {e}")
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()
            print("Conexión a la base de datos cerrada.")

def main():
    today = datetime.now().strftime("%Y-%m-%d")
    seven_days_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    
    datos = obtener_datos_api(start_date=seven_days_ago, end_date=today)
    
    if datos:
        print(f"Se obtuvieron {len(datos)} registros de la API. Procesando...")
        insertar_datos(datos)
    else:
        print("No se obtuvieron datos de la API o la respuesta estaba vacía.")

if __name__ == "__main__":
    main()