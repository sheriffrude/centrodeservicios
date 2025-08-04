import requests
import pymysql
from datetime import datetime, timedelta
import traceback
import sys
import logging

# --- CONFIGURACIÓN ---

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DB_CONFIG = {
    'host': '192.168.9.134',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica', # Base de datos por defecto
    'port': 3308,
    'charset': 'utf8mb4',
    'autocommit': True,
    'cursorclass': pymysql.cursors.DictCursor
}

API_URL = "https://api.controlfrigo.com/api/v1/recepcion/ordenes"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"


# --- FUNCIONES DE OBTENCIÓN DE DATOS (Optimizadas para recibir un cursor) ---

def fetch_data_from_api(start_date, end_date):
    """Consume la API para obtener las órdenes de recepción en un rango de fechas."""
    # La API espera el formato YYYY-MM-DD, pero para rangos de tiempo,
    # a menudo se usa YYYY-MM-DDTHH:MM:SS. Ajustamos al formato que acepte la API.
    # Usaremos el formato completo para precisión.
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')
    
    headers = {'Key': API_KEY}
    # Asumimos que la API acepta el formato de fecha y hora ISO 8601
    params = {'startDate': start_str, 'endDate': end_str}
    
    logging.info(f"Consultando API desde {start_str} hasta {end_str}")
    
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
    """Obtiene datos de despacho usando un cursor existente."""
    if not consecutivo_cercafe: return {'regic': None, 'frigorifico': None, 'granja': None}
    query = "SELECT regic, frigorifico, granja FROM prodsostenible.despachoLotesGranjas WHERE consecutivo_cercafe = %s LIMIT 1"
    cursor.execute(query, (consecutivo_cercafe,))
    return cursor.fetchone() or {'regic': None, 'frigorifico': None, 'granja': None}

def get_tipo_corte_id(cursor):
    """Obtiene el ID del tipo de corte usando un cursor existente."""
    current_time_str = datetime.now().strftime("%H:%M")
    query = "SELECT id FROM dhc.p_tipo_corte WHERE tipo_corte = %s LIMIT 1"
    cursor.execute(query, (current_time_str,))
    result = cursor.fetchone()
    return result['id'] if result else None

def get_id_propietario(cursor, nit_propietario):
    """Obtiene el ID del propietario usando un cursor existente."""
    if not nit_propietario: return None
    query = "SELECT id FROM dhc.razon_social WHERE ID_tributaria = %s LIMIT 1"
    cursor.execute(query, (nit_propietario,))
    result = cursor.fetchone()
    return result['id'] if result else None

# --- FUNCIONES PRINCIPALES DE PROCESAMIENTO ---

def sync_and_audit_data(data_from_api):
    """
    Inserta o actualiza registros en la tabla de auditoría.
    Retorna un conjunto de 'consecutivo_cercafe' que fueron procesados.
    """
    if not data_from_api:
        logging.info("No hay datos de la API para procesar.")
        return set()

    consecutivos_procesados = set()
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            id_tipo_corte = get_tipo_corte_id(cursor)

            for record in data_from_api:
                consecutivo = record.get('consecutivo_cercafe')
                orden = record.get('orden')

                if not consecutivo or not orden:
                    logging.warning(f"Registro API omitido por falta de 'consecutivo_cercafe' u 'orden': {record}")
                    continue

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

                query = """
                INSERT INTO auditoria_recepcion (
                    fecha_recepcion, consecutivo_cercafe, orden_recepcion, nit_propietario,
                    id_propietario, id_granja, cerdos_recibidos, peso_total, ingreso_qr,
                    registro_ic, id_frigorifico, placa, ica, tipo_corte
                ) VALUES (
                    %(fecha_recepcion)s, %(consecutivo_cercafe)s, %(orden_recepcion)s, %(nit_propietario)s,
                    %(id_propietario)s, %(id_granja)s, %(cerdos_recibidos)s, %(peso_total)s, %(ingreso_qr)s,
                    %(registro_ic)s, %(id_frigorifico)s, %(placa)s, %(ica)s, %(tipo_corte)s
                )
                ON DUPLICATE KEY UPDATE
                    fecha_recepcion = VALUES(fecha_recepcion), nit_propietario = VALUES(nit_propietario),
                    id_propietario = VALUES(id_propietario), id_granja = VALUES(id_granja),
                    cerdos_recibidos = VALUES(cerdos_recibidos), peso_total = VALUES(peso_total),
                    ingreso_qr = VALUES(ingreso_qr), registro_ic = VALUES(registro_ic),
                    id_frigorifico = VALUES(id_frigorifico), placa = VALUES(placa),
                    ica = VALUES(ica), tipo_corte = VALUES(tipo_corte);
                """
                cursor.execute(query, record_data)
                consecutivos_procesados.add(consecutivo)
        
        logging.info(f"Se procesaron (INSERT/UPDATE) {len(consecutivos_procesados)} consecutivos en 'auditoria_recepcion'.")

    except Exception as e:
        logging.error(f"Error durante la sincronización con la BD de auditoría: {e}")
        traceback.print_exc()
    finally:
        if connection:
            connection.close()
    
    return consecutivos_procesados

def validate_and_update_orders(consecutivos_a_validar, data_from_api):
    """Valida órdenes y actualiza su estado, incluyendo la lógica de 'muertos_transporte'."""
    if not consecutivos_a_validar:
        logging.info("No hay consecutivos para validar.")
        return

    logging.info(f"Iniciando validación para {len(consecutivos_a_validar)} consecutivos.")
    
    # Agrupamos los datos de la API para no tener que recorrerla en cada iteración
    consecutivos_api_agrupados = {}
    for record in data_from_api:
        consecutivo = record.get('consecutivo_cercafe')
        if consecutivo not in consecutivos_api_agrupados:
            consecutivos_api_agrupados[consecutivo] = {'cantidad_total': 0, 'nit_propietario': None}
        consecutivos_api_agrupados[consecutivo]['cantidad_total'] += record.get('cantidad', 0)
        consecutivos_api_agrupados[consecutivo]['nit_propietario'] = record.get('nit_propietario')

    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            for consecutivo in consecutivos_a_validar:
                
                # 1. Obtener total despachado y granja desde prodsostenible
                cursor.execute(
                    "SELECT SUM(cerdosDespachados) as total, granja FROM prodsostenible.despachoLotesGranjas WHERE consecutivo_cercafe = %s GROUP BY granja",
                    (consecutivo,)
                )
                despacho_info = cursor.fetchone()

                if not despacho_info:
                    novedad = "No hay registros en despachoLotesGranjas."
                    cursor.execute("UPDATE auditoria_recepcion SET orden = 'ABIERTA', novedad_orden = %s WHERE consecutivo_cercafe = %s", (novedad, consecutivo))
                    logging.warning(f"VALIDACIÓN: Consecutivo {consecutivo} - Estado: ABIERTA. Motivo: {novedad}")
                    continue
                
                total_cerdos_despachados_bd = int(despacho_info['total'] or 0)
                id_granja_bd = despacho_info['granja']

                # 2. Obtener muertos en transporte desde data360
                cursor.execute(
                    "SELECT muertos_transporte FROM data360.llegada_animales WHERE consecutivo_cercafe = %s LIMIT 1",
                    (consecutivo,)
                )
                llegada_info = cursor.fetchone()
                muertos_transporte = int(llegada_info['muertos_transporte'] or 0) if llegada_info else 0
                
                # 3. Obtener NIT asociado a la granja
                cursor.execute(
                    "SELECT E.ID_tributaria as nit FROM dhc.granjas C JOIN dhc.razon_social E ON C.RAZON_SOCIAL = E.ID WHERE C.ID = %s",
                    (id_granja_bd,)
                )
                nit_result = cursor.fetchone()
                nit_asociado_bd = nit_result['nit'] if nit_result else None
                
                # 4. Lógica de validación
                api_info = consecutivos_api_agrupados.get(consecutivo, {'cantidad_total': 0, 'nit_propietario': None})
                cantidad_recibida_api = api_info['cantidad_total']
                nit_propietario_api = api_info['nit_propietario']

                orden_status = 'CERRADA'
                novedad_orden = "S/N"

                # Validación de cantidad
                if cantidad_recibida_api != total_cerdos_despachados_bd:
                    if (cantidad_recibida_api + muertos_transporte) == total_cerdos_despachados_bd:
                        orden_status = 'CERRADA NOVEDAD'
                        novedad_orden = f"API {cantidad_recibida_api}, BD {total_cerdos_despachados_bd}, Muertos transporte: {muertos_transporte}"
                    else:
                        orden_status = 'ABIERTA'
                        novedad_orden = f"Cantidad API ({cantidad_recibida_api}) vs BD ({total_cerdos_despachados_bd}) no coincide. Muertos: {muertos_transporte}."
                
                # Validación de propietario (solo si la orden sigue cerrada)
                if orden_status == 'CERRADA':
                    if not nit_asociado_bd:
                        orden_status = 'ABIERTA'
                        novedad_orden = f"No se encontró NIT asociado para la granja ID ({id_granja_bd})."
                    elif nit_propietario_api != nit_asociado_bd:
                        orden_status = 'ABIERTA'
                        novedad_orden = f"Propietario API ({nit_propietario_api}) vs NIT asociado BD ({nit_asociado_bd}) no coincide."

                # 5. Actualizar estado final
                cursor.execute("UPDATE auditoria_recepcion SET orden = %s, novedad_orden = %s WHERE consecutivo_cercafe = %s", (orden_status, novedad_orden, consecutivo))
                logging.info(f"VALIDACIÓN: Consecutivo {consecutivo} - Estado: {orden_status}. Motivo: {novedad_orden}")

    except Exception as e:
        logging.error(f"Error durante la validación de órdenes: {e}")
        traceback.print_exc()
    finally:
        if connection:
            connection.close()


def get_date_range_for_execution(tipo_corte):
    """Calcula el rango de fecha y hora según el tipo de corte."""
    now = datetime.now()
    if tipo_corte == 'parcial':
        # De hoy a las 9:30 AM hasta la hora actual (5:00 PM)
        start_date = now.replace(hour=9, minute=30, second=0, microsecond=0)
        end_date = now
        return start_date, end_date
    elif tipo_corte == 'final':
        # Del día anterior a las 5:00 PM hasta hoy a las 9:30 AM
        end_date = now.replace(hour=9, minute=30, second=0, microsecond=0)
        ayer = now - timedelta(days=1)
        start_date = ayer.replace(hour=17, minute=0, second=0, microsecond=0)
        return start_date, end_date
    else:
        return None, None

def main():
    """Función principal que orquesta el proceso."""
    if len(sys.argv) < 2 or sys.argv[1] not in ['parcial', 'final']:
        print("Error: Debes especificar el tipo de ejecución.")
        print("Uso: python tu_script.py [parcial|final]")
        sys.exit(1)

    tipo_corte = sys.argv[1]
    logging.info(f"--- INICIANDO PROCESO DE AUDITORÍA - TIPO: {tipo_corte.upper()} ---")

    start_date, end_date = get_date_range_for_execution(tipo_corte)
    if not start_date or not end_date:
        logging.error("Tipo de corte inválido. Proceso abortado.")
        return

    try:
        api_data = fetch_data_from_api(start_date, end_date)
        if not api_data:
            logging.info("No se encontraron datos en la API para el rango de tiempo especificado. Proceso finalizado.")
            return

        consecutivos_procesados = sync_and_audit_data(api_data)
        
        # Siempre validar todos los consecutivos que se acaban de insertar/actualizar.
        validate_and_update_orders(consecutivos_procesados, api_data)

        logging.info(f"--- PROCESO {tipo_corte.upper()} COMPLETADO EXITOSAMENTE ---")

    except Exception as e:
        logging.error(f"ERROR INESPERADO EN MAIN: {type(e).__name__} - {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()