import requests
import pymysql
from datetime import datetime, timedelta
import logging

# --- CONFIGURACIÓN ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Se asume que ambas bases de datos (prod_carnica y data360) son accesibles
# con la misma conexión. Si no es así, se necesitaría una segunda configuración.
# DB_CONFIG = {
#     'host': '192.168.9.134',
#     'user': 'DEV_USER',
#     'password': 'DEV-USER12345',
#     'database': 'prod_carnica', # Base de datos por defecto
#     'port': 3308,
#     'charset': 'utf8mb4',
#     'autocommit': True,
#     'cursorclass': pymysql.cursors.DictCursor
# }
##### PRODUCCION  ####
DB_CONFIG = {
    'host': '192.168.9.41',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3306,
    'charset': 'utf8mb4',
    'autocommit': True,
    'cursorclass': pymysql.cursors.DictCursor
}

API_URL = "https://api.controlfrigo.com/api/v1/recepcion/ordenes"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

# --- FUNCIONES DE OBTENCIÓN DE DATOS (Sin cambios) ---

def fetch_data_from_api(start_date, end_date):
    """Consume la API para obtener las órdenes de recepción en un rango de fechas."""
    headers = {'Key': API_KEY}
    params = {'startDate': start_date, 'endDate': end_date}
    logging.info(f"Consultando API desde {start_date} hasta {end_date}")
    
    try:
        response = requests.get(API_URL, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        logging.info(f"Se recibieron {len(data)} registros de la API.")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error al consultar la API: {e}")
        return []

def get_registro_ic_and_frigorifico(cursor, consecutivo_cercafe):
    """Obtiene el registro IC, frigorífico y granja de la tabla de despachos."""
    query = """
    SELECT regic, frigorifico, granja
    FROM prodsostenible.despachoLotesGranjas
    WHERE consecutivo_cercafe = %s
    LIMIT 1
    """
    cursor.execute(query, (consecutivo_cercafe,))
    result = cursor.fetchone()
    return result if result else {'regic': None, 'frigorifico': None, 'granja': None}

def get_tipo_corte_id(cursor):
    """Obtiene el ID del tipo de corte basado en la hora actual."""
    current_time = datetime.now().strftime("%H:%M")
    query = "SELECT id FROM dhc.p_tipo_corte WHERE tipo_corte = %s LIMIT 1"
    cursor.execute(query, (current_time,))
    result = cursor.fetchone()
    return result['id'] if result else None

def get_id_propietario(cursor, nit_propietario):
    """Obtiene el ID del propietario basado en el NIT."""
    if not nit_propietario:
        return None
    query = "SELECT id FROM dhc.razon_social WHERE ID_tributaria = %s LIMIT 1"
    cursor.execute(query, (nit_propietario,))
    result = cursor.fetchone()
    return result['id'] if result else None

# --- FUNCIONES PRINCIPALES DE PROCESAMIENTO (sync_api_data_to_db sin cambios) ---

def sync_api_data_to_db(data_from_api):
    """
    Sincroniza los datos de la API con la base de datos.
    - Inserta registros nuevos.
    - Actualiza registros existentes si han cambiado.
    - Ignora registros sin cambios.
    Retorna un conjunto de 'consecutivo_cercafe' que fueron modificados.
    """
    if not data_from_api:
        logging.info("No hay datos de la API para procesar.")
        return set()

    consecutivos_afectados = set()
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            id_tipo_corte = get_tipo_corte_id(cursor)

            for record in data_from_api:
                consecutivo = record.get('consecutivo_cercafe')
                orden = record.get('orden')

                if not consecutivo or not orden:
                    logging.warning(f"Registro de API omitido por falta de 'consecutivo_cercafe' u 'orden': {record}")
                    continue

                cursor.execute(
                    "SELECT * FROM recepcion WHERE consecutivo_cercafe = %s AND orden_recepcion = %s",
                    (consecutivo, orden)
                )
                db_record = cursor.fetchone()

                despacho_info = get_registro_ic_and_frigorifico(cursor, consecutivo)
                id_propietario_db = get_id_propietario(cursor, record.get('nit_propietario'))
                
                record_data = {
                    'fecha_recepcion': record.get('fecha_recepcion'),
                    'consecutivo_cercafe': consecutivo,
                    'orden_recepcion': orden,
                    'nit_propietario': record.get('nit_propietario'),
                    'id_propietario': id_propietario_db,
                    'id_granja': despacho_info['granja'], 
                    'cerdos_recibidos': record.get('cantidad'),
                    'peso_total': record.get('peso_total'),
                    'ingreso_qr': "SI" if record.get('placa') else "NO",
                    'registro_ic': despacho_info['regic'],
                    'id_frigorifico': despacho_info['frigorifico'],
                    'placa': record.get('placa'),
                    'ica': record.get('ica'),
                    'tipo_corte': id_tipo_corte
                }

                if db_record is None:
                    sql_keys = ', '.join(f"`{k}`" for k in record_data.keys())
                    sql_values = ', '.join(['%s'] * len(record_data))
                    query = f"INSERT INTO recepcion ({sql_keys}) VALUES ({sql_values})"
                    
                    cursor.execute(query, list(record_data.values()))
                    consecutivos_afectados.add(consecutivo)
                    logging.info(f"NUEVO REGISTRO: Insertado orden {orden} para consecutivo {consecutivo}.")
                else:
                    db_values = {k: str(v) if v is not None else None for k, v in db_record.items()}
                    api_values = {k: str(v) if v is not None else None for k, v in record_data.items()}
                    
                    fields_to_compare = [
                        'cerdos_recibidos', 'peso_total', 'placa', 
                        'id_granja', 'id_propietario', 'registro_ic'
                    ]
                    
                    has_changed = any(api_values.get(f) != db_values.get(f) for f in fields_to_compare)

                    if has_changed:
                        update_query = """
                        UPDATE recepcion SET
                            fecha_recepcion=%s, nit_propietario=%s, id_propietario=%s, id_granja=%s,
                            cerdos_recibidos=%s, peso_total=%s, ingreso_qr=%s, registro_ic=%s,
                            id_frigorifico=%s, placa=%s, ica=%s, tipo_corte=%s
                        WHERE consecutivo_cercafe = %s AND orden_recepcion = %s
                        """
                        cursor.execute(update_query, (
                            record_data['fecha_recepcion'], record_data['nit_propietario'], record_data['id_propietario'], record_data['id_granja'],
                            record_data['cerdos_recibidos'], record_data['peso_total'], record_data['ingreso_qr'], record_data['registro_ic'],
                            record_data['id_frigorifico'], record_data['placa'], record_data['ica'], record_data['tipo_corte'],
                            consecutivo, orden
                        ))
                        consecutivos_afectados.add(consecutivo)
                        logging.info(f"REGISTRO ACTUALIZADO: Orden {orden} para consecutivo {consecutivo} ha cambiado.")
                    else:
                        logging.debug(f"SIN CAMBIOS: Orden {orden} para consecutivo {consecutivo} ya está sincronizado.")
    except Exception as e:
        logging.error(f"Error durante la sincronización con la BD: {e}")
        return set()
    finally:
        if connection:
            connection.close()
    return consecutivos_afectados

# ==============================================================================
# FUNCIÓN CORREGIDA Y MEJORADA
# ==============================================================================
def validate_and_update_orders(api_data, consecutivos_a_validar):
    """
    Valida las órdenes comparando datos de API, despachos y llegada de animales.
    Acumula las novedades para una validación más completa antes de actualizar.
   """
    if not consecutivos_a_validar:
        logging.info("No hay consecutivos nuevos o actualizados para validar.")
        return

    logging.info(f"Iniciando validación para {len(consecutivos_a_validar)} consecutivos.")

    connection = None
    try:
            connection = pymysql.connect(**DB_CONFIG)
            with connection.cursor() as cursor:
                    consecutivos_agrupados = {record['consecutivo_cercafe']: record for record in api_data}

                    for consecutivo_cercafe in consecutivos_a_validar:
                            api_record = consecutivos_agrupados.get(consecutivo_cercafe)
                            if not api_record:
                                    logging.warning(f"No se encontraron datos de la API para el consecutivo {consecutivo_cercafe}. Saltando...")
                                    continue

                            # Obtener total de cerdos despachados desde `prodsostenible`
                            cursor.execute(
                                    "SELECT SUM(cerdosDespachados) AS total_despachado FROM prodsostenible.despachoLotesGranjas WHERE consecutivo_cercafe = %s",
                                    (consecutivo_cercafe,)
                            )
                            sum_result = cursor.fetchone()
                            total_cerdos_despachados_bd = int(sum_result['total_despachado'] or 0)

                            # OBTENER MUERTOS EN TRANSPORTE desde `data360`
                            cursor.execute(
                                    "SELECT muertos_transporte FROM data360.llegada_animales WHERE consecutivo_cercafe = %s LIMIT 1",
                                    (consecutivo_cercafe,)
                            )
                            llegada_animales_info = cursor.fetchone()
                            muertos_transporte = int(llegada_animales_info['muertos_transporte'] or 0) if llegada_animales_info else 0
                            
                            # Obtener información de la granja (para validación de NIT)
                            cursor.execute(
                                    "SELECT granja FROM prodsostenible.despachoLotesGranjas WHERE consecutivo_cercafe = %s LIMIT 1",
                                    (consecutivo_cercafe,)
                            )
                            despacho_info = cursor.fetchone()

                            # Iniciar lógica de validación
                            novedades = []
                            final_status = 'CERRADA'

                            if not despacho_info:
                                    novedades.append("No hay registros en despachoLotesGranjas.")
                                    final_status = 'ABIERTA'
                            else:
                                    # Validaciones de cantidad de cerdos
                                    cantidad_total_api = sum(r.get('cantidad', 0) for r in api_data if r.get('consecutivo_cercafe') == consecutivo_cercafe)
                                    if (cantidad_total_api + muertos_transporte) != total_cerdos_despachados_bd:
                                            novedades.append(f"Cantidad API ({cantidad_total_api}) vs BD ({total_cerdos_despachados_bd}) no coincide. Muertos: {muertos_transporte}.")
                                            final_status = 'ABIERTA'
                                    elif muertos_transporte > 0:
                                            # Si la cantidad coincide gracias a los muertos, el estado es CERRADA NOVEDAD
                                            novedades.append(f"Cantidad ajustada por {muertos_transporte} muertos en transporte.")
                                            final_status = 'CERRADA NOVEDAD'

                                    # Validaciones de propietario
                                    granja_id_bd = despacho_info['granja']
                                    cursor.execute(
                                            "SELECT E.ID_tributaria AS Nit_asociado FROM dhc.granjas C JOIN dhc.razon_social E ON C.RAZON_SOCIAL = E.ID WHERE C.ID = %s",
                                            (granja_id_bd,)
                                    )
                                    nit_result = cursor.fetchone()
                                    nit_asociado = nit_result['Nit_asociado'] if nit_result else None
                                    
                                    propietario_api = api_record.get('nit_propietario')
                                    if nit_asociado and propietario_api != nit_asociado:
                                            novedades.append(f"Propietario API ({propietario_api}) vs NIT asociado BD ({nit_asociado}) no coincide.")
                                            final_status = 'ABIERTA'
                                    elif not nit_asociado:
                                            novedades.append(f"No se encontró NIT asociado para la granja ID ({granja_id_bd}).")
                                            final_status = 'ABIERTA'
                            
                            # Determinar la novedad final y actualizar
                            final_novedad = "S/N"
                            if novedades:
                                    final_novedad = " ".join(novedades)
                                    if final_status == 'CERRADA':
                                            final_status = 'CERRADA NOVEDAD'

                            update_query = "UPDATE recepcion SET orden = %s, novedad_orden = %s WHERE consecutivo_cercafe = %s"
                            cursor.execute(update_query, (final_status, final_novedad, consecutivo_cercafe))
                            logging.info(f"VALIDACIÓN: Consecutivo {consecutivo_cercafe} - Estado: {final_status}. Motivo: {final_novedad}")

    except Exception as e:
            logging.error(f"Error durante la validación de órdenes: {e}")
    finally:
            if connection:
                    connection.close()


def main():
   
    logging.info("--- INICIANDO PROCESO DE SINCRONIZACIÓN ---")
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
    
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")

    try:
       
        api_data = fetch_data_from_api(start_date, end_date)
        
        if not api_data:
            logging.info("No se recibieron datos de la API. Finalizando proceso.")
            return

        consecutivos_modificados = sync_api_data_to_db(api_data)
        
        logging.info("Buscando órdenes 'ABIERTA' existentes para re-validar...")
        consecutivos_abiertos = set()
        connection = pymysql.connect(**DB_CONFIG)
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT DISTINCT consecutivo_cercafe FROM recepcion 
                    WHERE orden = 'ABIERTA' AND fecha_recepcion BETWEEN %s AND %s
                """
                cursor.execute(query, (start_date + " 00:00:00", end_date + " 23:59:59"))
                results = cursor.fetchall()
                for row in results:
                    consecutivos_abiertos.add(row['consecutivo_cercafe'])
        finally:
            connection.close()
        
        logging.info(f"Se encontraron {len(consecutivos_abiertos)} consecutivos abiertos para re-validar.")
       
        consecutivos_a_validar = consecutivos_modificados.union(consecutivos_abiertos)
        
        validate_and_update_orders(api_data, consecutivos_a_validar)
        
        logging.info("--- PROCESO COMPLETADO EXITOSAMENTE ---")

    except Exception as e:
        logging.error(f"Ocurrió un error fatal en el proceso principal: {e}")

if __name__ == "__main__":
    main()