import requests
import pymysql
from datetime import datetime

# Configuración de la API
API_URL = "https://api.controlfrigo.com/api/v1/beneficios"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

# Configuración de la base de datos 
#### PRUEBAS ##########
# DB_CONFIG = {
#     'host': '192.168.9.134',
#     'user': 'DEV_USER',
#     'password': 'DEV-USER12345',
#     'database': 'prod_carnica',
#     'port': 3308,
#     'charset': 'utf8mb4',
#     'autocommit': True,
# }
##### PRODUCCION  ####
DB_CONFIG = {
    'host': '192.168.9.41',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3306,
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
        return None  # Retorna None pero no imprime error aquí

# Función para obtener el ID propietario y el NIT propietario desde el ID de la granja
def obtener_id_propietario(id_granja, cursor):
    if id_granja is None:
        return None, None
    
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
        return None, None

# Función para insertar novedad en tabla de control
def insertar_novedad(cursor, tiquete, tipo_novedad, descripcion, datos_originales):
    """
    Inserta una novedad en la tabla de control cuando hay problemas con los datos
    """
    query_novedad = """
    INSERT INTO beneficio_novedades (
        tiquete, 
        tipo_novedad, 
        descripcion, 
        datos_json, 
        estado, 
        fecha_registro
    ) VALUES (%s, %s, %s, %s, 'PENDIENTE', NOW())
    """
    
    # Convertir los datos originales a JSON string para almacenar
    import json
    datos_json = json.dumps(datos_originales, default=str, ensure_ascii=False)
    
    cursor.execute(query_novedad, (tiquete, tipo_novedad, descripcion, datos_json))
    print(f"NOVEDAD REGISTRADA - Tiquete: {tiquete}, Tipo: {tipo_novedad}, Descripción: {descripcion}")

# Función para crear la tabla de novedades si no existe
def crear_tabla_novedades_si_no_existe(cursor):
    """
    Crea la tabla de novedades si no existe
    """
    query_create_table = """
    CREATE TABLE IF NOT EXISTS beneficio_novedades (
        id INT AUTO_INCREMENT PRIMARY KEY,
        tiquete VARCHAR(50) NOT NULL,
        tipo_novedad VARCHAR(100) NOT NULL,
        descripcion TEXT,
        datos_json JSON,
        estado ENUM('PENDIENTE', 'REVISADO', 'RESUELTO') DEFAULT 'PENDIENTE',
        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        fecha_resolucion TIMESTAMP NULL,
        observaciones TEXT,
        INDEX idx_tiquete (tiquete),
        INDEX idx_estado (estado),
        INDEX idx_fecha_registro (fecha_registro)
    )
    """
    cursor.execute(query_create_table)

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
   
# Función para insertar datos en la base de datos (CORREGIDA)
def insertar_datos(datos):
    connection = pymysql.connect(**DB_CONFIG)
    try:
        with connection.cursor() as cursor:
            # Crear tabla de novedades si no existe
            crear_tabla_novedades_si_no_existe(cursor)
            
            registros_procesados = 0
            registros_con_novedades = 0
            registros_insertados = 0
            registros_actualizados = 0
            registros_omitidos_procesados = 0
            
            for registro in datos:
                tiquete = registro['tiquete']
                estado = registro['estado']
                tiene_novedades_criticas = False  # Flag para saber si hay problemas reales
                
                # Obtener el id_granja a partir del nombre de la granja
                id_granja = obtener_id_granja(cursor, registro['granja'])
                if id_granja is None:
                    tiene_novedades_criticas = True
                    insertar_novedad(
                        cursor, 
                        tiquete, 
                        'GRANJA_NO_ENCONTRADA',
                        f"No se encontró id_granja para la granja: {registro['granja']}", 
                        registro
                    )
                    # Usar valores por defecto o NULL
                    id_granja = None
                
                # Obtener ID propietario y NIT propietario
                id_propietario, nit_propietario = obtener_id_propietario(id_granja, cursor)
                if not id_propietario or not nit_propietario:
                    tiene_novedades_criticas = True
                    insertar_novedad(
                        cursor, 
                        tiquete, 
                        'PROPIETARIO_NO_ENCONTRADO',
                        f"No se encontró propietario para la granja con ID {id_granja}", 
                        registro
                    )
                    # Usar valores por defecto
                    id_propietario = None
                    nit_propietario = None
                
                # Si hay novedades críticas (datos faltantes), saltamos este registro
                if tiene_novedades_criticas:
                    registros_con_novedades += 1
                    print(f"⚠️  Tiquete {tiquete} saltado por novedades críticas")
                    continue
                
                # Verificar si el tiquete ya existe y obtener su estado
                query_check = """
                SELECT COUNT(*), 
                       (SELECT estado_frigorifico FROM beneficio WHERE tiquete = %s LIMIT 1) AS estado_frigorifico 
                FROM beneficio 
                WHERE tiquete = %s
                """
                cursor.execute(query_check, (tiquete, tiquete))
                result = cursor.fetchone()
                
                if result is None:
                    insertar_novedad(
                        cursor, 
                        tiquete, 
                        'ERROR_CONSULTA_TIQUETE',
                        f"Error al consultar información del tiquete {tiquete}", 
                        registro
                    )
                    registros_con_novedades += 1
                    continue
                
                count, estado_actual = result

                # PROCESAR EL REGISTRO SOLO SI NO HAY PROBLEMAS CRÍTICOS
                try:
                    if count == 0:
                        # Insertar registro nuevo
                        query_insert = """
                        INSERT INTO beneficio (
                            id_frigorifico, fecha_recepcion, consecutivo_cercafe, orden_beneficio, lote, 
                            nit_propietario, id_propietario, id_granja, tiquete, fecha_hora_beneficio, 
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
                        print(f"✅ Registro con tiquete {tiquete} insertado correctamente.")
                        registros_procesados += 1
                        registros_insertados += 1
                        
                    else:
                        # Verificar si está en estado PROCESADOS antes de actualizar
                        if estado_actual == "PROCESADOS":
                            registros_omitidos_procesados += 1
                            print(f"ℹ️  Tiquete {tiquete} en estado PROCESADOS - se omite actualización")
                            continue  # No actualizar registros en estado PROCESADOS
                        
                        # Actualizar registro existente
                        query_update = """
                        UPDATE beneficio SET
                            id_frigorifico = 6,
                            fecha_recepcion = %s,
                            consecutivo_cercafe = %s,
                            orden_beneficio = %s,
                            lote = %s,
                            nit_propietario = %s,
                            id_propietario = %s,
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
                        print(f"🔄 Registro con tiquete {tiquete} actualizado correctamente.")
                        registros_procesados += 1
                        registros_actualizados += 1
                
                except Exception as e:
                    insertar_novedad(
                        cursor, 
                        tiquete, 
                        'ERROR_INSERT_UPDATE',
                        f"Error al insertar/actualizar registro: {str(e)}", 
                        registro
                    )
                    registros_con_novedades += 1
                    print(f"❌ Error procesando tiquete {tiquete}: {str(e)}")
                
            print(f"\n📊 RESUMEN DEL PROCESO:")
            print(f"   Total registros procesados exitosamente: {registros_procesados}")
            print(f"   - Registros insertados: {registros_insertados}")
            print(f"   - Registros actualizados: {registros_actualizados}")
            print(f"   - Registros omitidos (estado PROCESADOS): {registros_omitidos_procesados}")
            print(f"   Registros con novedades (problemas): {registros_con_novedades}")
            if registros_con_novedades > 0:
                print(f"   ⚠️  Revisar tabla 'beneficio_novedades' para detalles de problemas encontrados")
                
        connection.commit()
    except Exception as e:
        print(f"❌ Error general al procesar datos: {e}")
        connection.rollback()
    finally:
        connection.close()

# Función principal
def main():
    # Configurar rango de fechas (hoy)
    today = datetime.now().strftime("%Y-%m-%d")
    datos = obtener_datos_api(start_date='2025-06-01', end_date=today)
    if datos:
        insertar_datos(datos)
    else:
        print("No se obtuvieron datos de la API.") 

if __name__ == "__main__":
    main()