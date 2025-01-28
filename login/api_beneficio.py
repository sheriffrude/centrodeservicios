import requests
import pymysql
from datetime import datetime

# Configuración de la API
API_URL = "https://api.controlfrigo.com/api/v1/beneficios"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

# Configuración de la base de datos
DB_CONFIG = {
    'host': '192.168.9.134',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3308,
    'charset': 'utf8mb4',
    'autocommit': True,
}

# Función para obtener los datos de la API
def obtener_datos_api(start_date, end_date):
    headers = {
    'Key': API_KEY,
    }

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

# Función para obtener el id de la granja
def obtener_id_granja(cursor, nombre_granja):
    query_granja = """
    SELECT id FROM dhc.homologacion_granjas
    WHERE NOMBRE_FRIGOTUN = %s
    LIMIT 1
    """
    cursor.execute(query_granja, (nombre_granja,))
    result = cursor.fetchone()
    if result:
        return result[0]  # Retorna el id_granja
    else:
        print(f"No se encontró un id_granja para la granja: {nombre_granja}")
        return None
# Función para obtener el ID propietario y el NIT propietario desde el ID de la granja
def obtener_id_propietario(id_granja, cursor):
    query_propietario = """
    SELECT rs.ID, rs.ID_TRIBUTARIA 
    FROM dhc.granjas g
    JOIN dhc.razon_social rs ON g.RAZON_SOCIAL = rs.ID
    WHERE g.ID = %s
    """
    cursor.execute(query_propietario, (id_granja,))
    result = cursor.fetchone()
    if result:
        return result[0], result[1]  # Retornar ID propietario e ID tributaria
    else:
        print(f"No se encontró propietario para la granja con ID {id_granja}.")
        return None, None
    
current_time = datetime.now().strftime("%H:%M")
def get_tipo_corte_id(current_time):
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    # Consultamos el id correspondiente al tipo_corte
    query = """
    SELECT id
    FROM dhc.p_tipo_corte
    WHERE tipo_corte = %s
    LIMIT 1
    """
    cursor.execute(query, (current_time,))
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return result[0] if result else None
   
# Función para insertar datos en la base de datos
def insertar_datos(datos):
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            for registro in datos:
                tiquete = registro['tiquete']
                estado = registro['estado']
                
                # Obtener el id_granja a partir del nombre de la granja
                id_granja = obtener_id_granja(cursor, registro['granja'])
                if id_granja is None:
                    print(f"Saltando registro con tiquete {tiquete} porque no se encontró id_granja.")
                    continue  # Saltar al siguiente registro si no se encuentra el id_granja
                
                # Verificar si el tiquete ya existe y obtener su estado
                query_check = """
                SELECT COUNT(*), 
                       (SELECT estado_frigorifico FROM beneficio WHERE tiquete = %s LIMIT 1) AS estado_frigorifico 
                FROM beneficio 
                WHERE tiquete = %s
                """
                cursor.execute(query_check, (tiquete, tiquete))
                result = cursor.fetchone()
                
                # Verificar si result no es None
                if result is None:
                    print(f"No se encontró información para el tiquete {tiquete}.")
                    continue  # Saltar al siguiente registro
                
                count, estado_actual = result

                 # Obtener ID propietario y NIT propietario
                id_propietario, nit_propietario = obtener_id_propietario(id_granja, cursor)
                if not id_propietario or not nit_propietario:
                    continue  # Si no hay datos del propietario, saltar al siguiente registro

                
                if count == 0:
                    # Insertar registro si no existe
                    query_insert = """
                    INSERT INTO beneficio (
                        id_frigorifico,fecha_recepcion, consecutivo_cercafe, orden_beneficio, lote, 
                        nit_propietario,id_propietario, id_granja, tiquete, fecha_hora_beneficio, 
                        fecha_hora_peso_caliente, peso_pie, peso_caliente, clasificacion, 
                        clasificacion_seurop, mm_grasa, porcentaje_magro, 
                        rendimiento_caliente, estado_frigorifico, metadata
                    ) VALUES (
                       %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                    )
                    """
                    cursor.execute(query_insert, (
                        6,
                        registro['fecha_recepcion'],
                        registro['consecutivo_cercafe'],
                        registro['orden'],
                        registro['lote'],
                        nit_propietario,
                        id_propietario, 
                        id_granja,  
                        registro['tiquete'],
                        registro['fecha_hora_sacrificio'],
                        registro['fecha_hora_peso_caliente'],
                        registro['peso_pie'],
                        registro['peso_caliente'],
                        registro['clasificacion'],
                        registro['clasificacion_seurop'],
                        registro['mm_grasa'],
                        registro['porcentaje_magro'],
                        registro['rendimiento_caliente'],
                        registro['estado'],
                    ))
                    print(f"Registro con tiquete {tiquete} insertado correctamente.")
                else:
                    # Si el tiquete existe, verificar el estado
                    if estado_actual != "PROCESADOS":
                        # Actualizar registro si el estado no es "PROCESADOS"
                        query_update = """
                        UPDATE beneficio SET
                            id_frigorifico = 6,
                            fecha_recepcion = %s,
                            consecutivo_cercafe = %s,
                            orden_beneficio = %s,
                            lote = %s,
                            nit_propietario = %s,
                            id_propietario  = %s,
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
                            metadata = NOW()
                        WHERE tiquete = %s
                        """
                        cursor.execute(query_update, (
                            registro['fecha_recepcion'],
                            registro['consecutivo_cercafe'],
                            registro['orden'],
                            registro['lote'],
                            nit_propietario,
                            id_propietario, 
                            id_granja,
                            registro['fecha_hora_sacrificio'],
                            registro['fecha_hora_peso_caliente'],
                            registro['peso_pie'],
                            registro['peso_caliente'],
                            registro['clasificacion'],
                            registro['clasificacion_seurop'],
                            registro['mm_grasa'],
                            registro['porcentaje_magro'],
                            registro['rendimiento_caliente'],
                            registro['estado'],
                            tiquete
                        ))
                        print(f"Registro con tiquete {tiquete} actualizado correctamente.")
                    else:
                        print(f"El tiquete {tiquete} ya existe y está en estado 'PROCESADOS'. No se actualizará.")
        connection.commit()
    except Exception as e:
        print(f"Error al insertar/actualizar datos en la base de datos: {e}")
    finally:
        connection.close()

# Función principal
def main():
    # Configurar rango de fechas (hoy)
    today = datetime.now().strftime("%Y-%m-%d")
    datos = obtener_datos_api(start_date=today, end_date=today)
    if datos:
        insertar_datos(datos)
    else:
        print("No se obtuvieron datos de la API.")

if __name__ == "__main__":
    main()
