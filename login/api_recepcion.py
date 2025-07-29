import requests
import pymysql
from datetime import datetime, timedelta
import logging

# --- CONFIGURACIÓN ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_CONFIG = {
    'host': '192.168.9.134',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3308,
    'charset': 'utf8mb4',
    'autocommit': True,
    'cursorclass': pymysql.cursors.DictCursor
}

API_URL = "https://api.controlfrigo.com/api/v1/recepcion/ordenes"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

# --- FUNCIONES DE OBTENCIÓN DE DATOS ---

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
        return [] # Retornar lista vacía en caso de error

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

# --- FUNCIONES PRINCIPALES DE PROCESAMIENTO ---

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
# FUNCIÓN CORREGIDA
# ==============================================================================
def validate_and_update_orders(api_data, consecutivos_a_validar):
    """
    Valida las órdenes y actualiza su estado (ABIERTA/CERRADA).
    El problema original era que `SUM(...) GROUP BY ...` creaba múltiples filas
    si los valores de `regic` eran diferentes para un mismo consecutivo, y `fetchone()`
    solo leía la primera fila.

    La solución es separar las consultas:
    1. Una consulta para obtener la SUMA TOTAL de `cerdosDespachados`.
    2. Otra consulta para obtener la información de la granja y el NIT asociado.
    """
    if not consecutivos_a_validar:
        logging.info("No hay consecutivos nuevos o actualizados para validar.")
        return

    logging.info(f"Iniciando validación para {len(consecutivos_a_validar)} consecutivos.")

    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            # Agrupamos los datos de la API una sola vez para eficiencia
            consecutivos_agrupados = {}
            for record in api_data:
                consecutivo = record.get('consecutivo_cercafe')
                if consecutivo not in consecutivos_agrupados:
                    consecutivos_agrupados[consecutivo] = {'ordenes': [], 'cantidad_total': 0, 'propietario_api': None}
                
                consecutivos_agrupados[consecutivo]['ordenes'].append(record.get('orden'))
                consecutivos_agrupados[consecutivo]['cantidad_total'] += record.get('cantidad', 0)
                consecutivos_agrupados[consecutivo]['propietario_api'] = record.get('nit_propietario')

            for consecutivo_cercafe in consecutivos_a_validar:
                datos_agrupados = consecutivos_agrupados.get(consecutivo_cercafe)
                if not datos_agrupados:
                    logging.warning(f"No se encontraron datos de la API para el consecutivo {consecutivo_cercafe} a validar. Saltando...")
                    continue

                # --- INICIO DE LA CORRECCIÓN ---

                # 1. Obtenemos la SUMA TOTAL REAL de cerdos despachados para el consecutivo, sin agrupar.
                #    Esto resuelve el problema principal.
                cursor.execute(
                    "SELECT SUM(cerdosDespachados) AS total_despachado FROM prodsostenible.despachoLotesGranjas WHERE consecutivo_cercafe = %s",
                    (consecutivo_cercafe,)
                )
                sum_result = cursor.fetchone()
                total_cerdos_despachados_bd = sum_result['total_despachado'] if sum_result and sum_result['total_despachado'] is not None else 0

                # 2. Obtenemos la información de la granja (asumimos que es la misma para un mismo consecutivo).
                cursor.execute(
                    "SELECT granja FROM prodsostenible.despachoLotesGranjas WHERE consecutivo_cercafe = %s LIMIT 1",
                    (consecutivo_cercafe,)
                )
                despacho_info = cursor.fetchone()

                # --- FIN DE LA CORRECCIÓN ---

                motivo_abierta = None
                nit_asociado = None

                # Validamos si encontramos al menos un registro de despacho
                if not despacho_info:
                    motivo_abierta = "No hay registros en despachoLotesGranjas."
                else:
                    # Si hay despacho, buscamos el NIT asociado a la granja encontrada
                    granja_id_bd = despacho_info['granja']
                    cursor.execute(
                        """
                        SELECT E.ID_tributaria AS Nit_asociado
                        FROM dhc.granjas C JOIN dhc.razon_social E ON C.RAZON_SOCIAL = E.ID
                        WHERE C.ID = %s
                        """, (granja_id_bd,)
                    )
                    nit_result = cursor.fetchone()
                    nit_asociado = nit_result['Nit_asociado'] if nit_result else None
                    
                    # Ahora realizamos las validaciones con los datos correctos
                    cantidad_total_api = datos_agrupados['cantidad_total']
                    propietario_api = datos_agrupados['propietario_api']

                    # Comparamos la suma total de la API vs la suma total REAL de la BD
                    if cantidad_total_api != total_cerdos_despachados_bd:
                        motivo_abierta = f"Cantidad API ({cantidad_total_api}) vs BD ({int(total_cerdos_despachados_bd)}) no coincide."
                    elif not nit_asociado:
                        motivo_abierta = f"No se encontró NIT asociado para la granja ID ({granja_id_bd})."
                    elif propietario_api != nit_asociado:
                        motivo_abierta = f"Propietario API ({propietario_api}) vs NIT asociado BD ({nit_asociado}) no coincide."

                # Actualizamos el estado de la orden
                orden_status = 'ABIERTA' if motivo_abierta else 'CERRADA'
                novedad_orden = motivo_abierta if motivo_abierta else "S/N"
                
                update_query = "UPDATE recepcion SET orden = %s, novedad_orden = %s WHERE consecutivo_cercafe = %s"
                cursor.execute(update_query, (orden_status, novedad_orden, consecutivo_cercafe))
                
                logging.info(f"VALIDACIÓN: Consecutivo {consecutivo_cercafe} - Estado: {orden_status}. Motivo: {novedad_orden}")

    except Exception as e:
        logging.error(f"Error durante la validación de órdenes: {e}")
    finally:
        if connection:
            connection.close()


def main():
    """
    Función principal que orquesta todo el proceso.
    """
    logging.info("--- INICIANDO PROCESO DE SINCRONIZACIÓN ---")
    today = datetime.now()
    end_date = today.strftime("%Y-%m-%d")
 
    start_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        # 1. Obtener datos frescos de la API
        api_data = fetch_data_from_api(start_date, end_date)
        
        # Si no hay datos de la API, no hay nada que hacer.
        if not api_data:
            logging.info("No se recibieron datos de la API. Finalizando proceso.")
            return

        # 2. Sincronizar datos con la BD (insertar/actualizar)
        consecutivos_modificados = sync_api_data_to_db(api_data)
        
        # 3. Identificar órdenes que ya estaban 'ABIERTA' para re-validarlas
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

        # 4. Unir los consecutivos modificados con los que ya estaban abiertos
        consecutivos_a_validar = consecutivos_modificados.union(consecutivos_abiertos)
        
        # 5. Validar el estado de todas las órdenes relevantes
        validate_and_update_orders(api_data, consecutivos_a_validar)
        
        logging.info("--- PROCESO COMPLETADO EXITOSAMENTE ---")

    except Exception as e:
        logging.error(f"Ocurrió un error fatal en el proceso principal: {e}")

if __name__ == "__main__":
    main()