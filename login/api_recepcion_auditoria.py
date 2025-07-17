import requests
import pymysql
from datetime import datetime, timedelta
import traceback

# --- CONFIGURACIÓN (sin cambios) ---
# Configuración de la base de datos 
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
API_URL = "https://api.controlfrigo.com/api/v1/recepcion/ordenes"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

# --- FUNCIONES DE OBTENCIÓN DE DATOS (sin cambios) ---
def fetch_data_from_api(start_date, end_date):
    # ... (código sin cambios)
    print(f"Llamando a la API con startDate={start_date}, endDate={end_date}")
    headers = {'Key': API_KEY}
    params = {'startDate': start_date, 'endDate': end_date}
    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

def get_registro_ic_and_frigorifico(consecutivo_cercafe):
    # ... (código sin cambios)
    if not consecutivo_cercafe: return None, None, None
    connection = pymysql.connect(**DB_CONFIG)
    with connection.cursor() as cursor:
        query = "SELECT regic, frigorifico, granja FROM prodsostenible.despacholotesgranjas WHERE consecutivo_cercafe = %s LIMIT 1"
        cursor.execute(query, (consecutivo_cercafe,))
        result = cursor.fetchone()
    connection.close()
    return result if result else (None, None, None)

def get_tipo_corte_id(current_time_str):
    # ... (código sin cambios)
    connection = pymysql.connect(**DB_CONFIG)
    with connection.cursor() as cursor:
        query = "SELECT id FROM dhc.p_tipo_corte WHERE tipo_corte = %s LIMIT 1"
        cursor.execute(query, (current_time_str,))
        result = cursor.fetchone()
    connection.close()
    return result[0] if result else None

def get_id_propietario(nit_propietario):
    # ... (código sin cambios)
    if not nit_propietario: return None
    connection = pymysql.connect(**DB_CONFIG)
    with connection.cursor() as cursor:
        query = "SELECT id FROM dhc.razon_social WHERE ID_tributaria = %s LIMIT 1"
        cursor.execute(query, (nit_propietario,))
        result = cursor.fetchone()
    connection.close()
    return result[0] if result else None


# --- LÓGICA PRINCIPAL DE LA BASE DE DATOS (MODIFICADA) ---

def insert_data_into_db(data):
    """Inserta o actualiza registros, permitiendo valores nulos para datos no encontrados."""
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        query = """
        INSERT INTO auditoria_recepcion (
            fecha_recepcion, consecutivo_cercafe, orden_recepcion, nit_propietario,
            id_propietario, id_granja, cerdos_recibidos, peso_total, ingreso_qr,
            registro_ic, id_frigorifico, placa, ica, tipo_corte
        ) VALUES (
            %(fecha_recepcion)s, %(consecutivo_cercafe)s, %(orden_recepcion)s, %(nit_propietario)s,
            %(id_propietario)s, %(id_granja)s, %(cantidad)s, %(peso_total)s, %(ingreso_qr)s,
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
        
        print("\nProcesando registros para insertar/actualizar en la BD...")
        for i, record in enumerate(data):
            print(f"--- Procesando Registro de API #{i+1} ---")
            
            if 'orden' not in record or record['orden'] is None:
                print(f"ADVERTENCIA: Saltando registro para consecutivo {record.get('consecutivo_cercafe')} por falta del campo 'orden'.")
                continue
            
            # Enriquecimiento y mapeo
            record['orden_recepcion'] = record['orden']
            record['ingreso_qr'] = "SI" if record.get('placa') else "NO"
            
            consecutivo = record.get('consecutivo_cercafe')
            nit = record.get('nit_propietario')
            
            # Búsquedas externas
            registro_ic, id_frigorifico, id_granja = get_registro_ic_and_frigorifico(consecutivo)
            record['registro_ic'] = registro_ic
            record['id_frigorifico'] = id_frigorifico
            record['id_granja'] = id_granja
            
            record['id_propietario'] = get_id_propietario(nit)
            record['tipo_corte'] = get_tipo_corte_id(datetime.now().strftime("%H:%M"))
            
            print(f"  > Datos finales para la query: {record}")
            
            # YA NO OMITIMOS. INSERTAMOS CON LOS DATOS QUE TENGAMOS.
            # La validación se hará en el siguiente paso.
            cursor.execute(query, record)
            print(f"  > Registro #{i+1} ejecutado en la BD (INSERT/UPDATE).")

        connection.commit()
        print("\nCommit realizado en la base de datos.")

    finally:
        if connection and connection.open:
            connection.close()
            print("Conexión a la base de datos (insert_data_into_db) cerrada.")


def validate_and_update_orders(data):
    """Valida las órdenes y actualiza su estado, marcando errores de datos como novedad."""
    connection = None
    try:
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()

        update_query = """
        UPDATE prod_carnica.auditoria_recepcion
        SET orden = %s, novedad_orden = %s
        WHERE consecutivo_cercafe = %s
        """
        
        processed_consecutivos = set()
        
        print("\nValidando y actualizando estado de órdenes...")
        for record in data:
            consecutivo_cercafe = record.get('consecutivo_cercafe')
            if not consecutivo_cercafe or consecutivo_cercafe in processed_consecutivos:
                continue
            
            print(f"--- Validando Consecutivo: {consecutivo_cercafe} ---")
            processed_consecutivos.add(consecutivo_cercafe)

            # Re-obtenemos los datos enriquecidos directamente de la BD después del INSERT/UPDATE
            # para tener la versión más actualizada y consistente.
            cursor.execute("SELECT id_granja, nit_propietario FROM auditoria_recepcion WHERE consecutivo_cercafe = %s LIMIT 1", (consecutivo_cercafe,))
            db_record = cursor.fetchone()
            if not db_record:
                print(f"  > ERROR: No se encontró el registro para el consecutivo {consecutivo_cercafe} en la BD para validar.")
                continue
            
            id_granja_db, nit_propietario_db = db_record

            motivo_abierta = None

            # **** NUEVA LÓGICA DE VALIDACIÓN ****
            # 1. Validar si la información básica (enriquecida) existe.
            if id_granja_db is None:
                motivo_abierta = f"Datos de despacho no encontrados para consecutivo {consecutivo_cercafe}."
            # Puedes agregar más validaciones de datos faltantes aquí
            # elif registro_ic_db is None:
            #     motivo_abierta = "Falta registro IC."
            
            # 2. Si los datos básicos existen, proceder con las validaciones de negocio.
            if not motivo_abierta:
                # Obtener datos de despacho para comparar
                cursor.execute("SELECT cerdosDespachados, granja FROM prodsostenible.despacholotesgranjas WHERE consecutivo_cercafe = %s", (consecutivo_cercafe,))
                results_despacho = cursor.fetchall()
                
                # Obtener NIT asociado a la granja
                cursor.execute("SELECT E.ID_tributaria FROM dhc.granjas C JOIN dhc.razon_social E ON C.RAZON_SOCIAL = E.ID WHERE C.ID = %s", (id_granja_db,))
                nit_result = cursor.fetchone()
                nit_asociado = nit_result[0] if nit_result else None
                
                total_cerdos_despachados = sum(row[0] for row in results_despacho)
                
                cursor.execute("SELECT SUM(cerdos_recibidos) FROM prod_carnica.auditoria_recepcion WHERE consecutivo_cercafe = %s", (consecutivo_cercafe,))
                total_recibido_db = cursor.fetchone()[0] or 0

                if total_recibido_db != total_cerdos_despachados:
                    motivo_abierta = f"Cerdos recibidos ({total_recibido_db}) no coinciden con despachados ({total_cerdos_despachados})."
                elif not nit_asociado or nit_propietario_db != nit_asociado:
                    motivo_abierta = f"El propietario ({nit_propietario_db}) no coincide con el Nit asociado a la granja ({nit_asociado})."
            
            # Asignar estado final
            if motivo_abierta:
                orden_status = 'ABIERTA'
                novedad_orden = motivo_abierta
                print(f"  > Estado: ABIERTA. Motivo: {motivo_abierta}")
            else:
                orden_status = 'CERRADA'
                novedad_orden = "S/N"
                print("  > Estado: CERRADA. Sin novedades.")

            cursor.execute(update_query, (orden_status, novedad_orden, consecutivo_cercafe))

        connection.commit()
        print("\nCommit de validación de órdenes realizado.")

    finally:
        if connection and connection.open:
            connection.close()
            print("Conexión a la base de datos (validate_and_update_orders) cerrada.")

# --- PUNTO DE ENTRADA DEL SCRIPT (sin cambios) ---
def main():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = yesterday
    end_date = today

    try:
        data = fetch_data_from_api(start_date, end_date)
        if not data:
            print("No se encontraron nuevos datos en la API.")
            return

        print(f"Se encontraron {len(data)} registros en la API. Iniciando proceso.")
        insert_data_into_db(data)
        validate_and_update_orders(data)
        print("\n--- Proceso completado exitosamente ---")

    except requests.exceptions.RequestException as e:
        print(f"ERROR DE RED O API: {e}")
    except pymysql.Error as e:
        print(f"ERROR DE BASE DE DATOS: {e}")
        traceback.print_exc()
    except Exception as e:
        print(f"ERROR INESPERADO: {type(e).__name__} - {e}")
        traceback.print_exc()

if __name__ == "__main__":
    main()