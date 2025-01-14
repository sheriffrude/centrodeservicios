import requests
import pymysql
from datetime import datetime

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

# API Configuration
API_URL = "https://api.controlfrigo.com/api/v1/receptions"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"

# Función para consumir la API
def fetch_data_from_api(start_date, end_date):
    headers = {'Key': API_KEY}
    params = {'startDate': start_date, 'endDate': end_date}
    
    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

# Función para obtener el registro IC y frigorífico de la tabla externa
def get_registro_ic_and_frigorifico(consecutivo_cercafe):
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    query = """
    SELECT regic, frigorifico, granja
    FROM prodsostenible.despacholotesgranjas
    WHERE consecutivo_cercafe = %s
    LIMIT 1
    """
    cursor.execute(query, (consecutivo_cercafe,))
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return result if result else (None, None, None)

# Obtener la hora actual en formato HH:MM:SS
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



# Función para obtener el ID del propietario basado en el NIT
def get_id_propietario(nit_propietario):
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    query = """
    SELECT id
    FROM dhc.razon_social
    WHERE ID_tributaria = %s
    LIMIT 1
    """
    cursor.execute(query, (nit_propietario,))
    result = cursor.fetchone()
    
    cursor.close()
    connection.close()
    
    return result[0] if result else None

# Función para insertar los datos en la base de datos
def insert_data_into_db(data):
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    
    query = """
    INSERT INTO recepcion (
        fecha_recepcion, consecutivo_cercafe, orden_recepcion, nit_propietario,
        id_propietario, id_granja, cerdos_recibidos, peso_total, ingreso_qr,
        registro_ic, id_frigorifico, placa, ica, tipo_corte
    ) VALUES (
        %(fecha_recepcion)s, %(consecutivo_cercafe)s, %(orden)s, %(nit_propietario)s,
        %(id_propietario)s, %(id_granja)s, %(cantidad)s, %(peso_total)s, %(ingreso_qr)s,
        %(registro_ic)s, %(id_frigorifico)s, %(placa)s, %(ica)s, %(tipo_corte)s
    )
    """
    
    for record in data:
        # Validación de ingreso_qr
        record['ingreso_qr'] = "SI" if record.get('placa') else "NO"
        
        # Obtener registro IC y frigorífico
        registro_ic, id_frigorifico, id_granja = get_registro_ic_and_frigorifico(record.get('consecutivo_cercafe'))
        record['registro_ic'] = registro_ic
        record['id_frigorifico'] = id_frigorifico
        record['id_granja'] = id_granja
        
        # Obtener ID del propietario
        record['id_propietario'] = get_id_propietario(record.get('nit_propietario'))
        
        # Obtener el id_tipo_corte según la hora actual
        current_time = datetime.now().strftime("%H:%M")
        tipo_corte = get_tipo_corte_id(current_time)
        record['tipo_corte'] = tipo_corte
        
        cursor.execute(query, record)
    
    connection.commit()
    cursor.close()
    connection.close()


def validate_and_update_orders(data):
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()

    # Query para obtener registros relacionados con un consecutivo
    fetch_query = """
    SELECT consecutivo_cercafe, cerdosDespachados, granja, regica
    FROM prodsostenible.despachoLotesGranjas
    WHERE consecutivo_cercafe = %s
    """

    # Query para obtener el Nit_asociado de la granja
    fetch_nit_query = """
    SELECT
        C.ID AS ID,
        C.ID AS ID_INTRANET,
        UPPER(C.GRANJAS) AS Granja,
        E.ID_tributaria AS Nit_asociado,
        UPPER(E.razon_social) AS Asociado
    FROM
        dhc.granjas C
    JOIN 
        dhc.nombre_comercial D ON C.NOMBRE_COMERCIAL = D.ID
    JOIN 
        dhc.razon_social E ON C.RAZON_SOCIAL = E.ID
    WHERE 
        UPPER(C.ID) = %s
    """

    # Query para actualizar el campo 'orden' en prod_carnica.recepcion
    update_query = """
    UPDATE prod_carnica.recepcion
    SET orden = %s
    WHERE consecutivo_cercafe = %s
    """
    
    for record in data:
        consecutivo_cercafe = record.get('consecutivo_cercafe')
        cantidad_api = record.get('cantidad')
        granja_api = record.get('id_granja')
        propietario_api = record.get('nit_propietario')
        ingreso_qr = record.get('ingreso_qr')

        # Buscar registros en despachoLotesGranjas
        cursor.execute(fetch_query, (consecutivo_cercafe,))
        results = cursor.fetchall()

        # Obtener el Nit_asociado de la granja
        cursor.execute(fetch_nit_query, (granja_api,))
        nit_result = cursor.fetchone()
        nit_asociado = nit_result[3] if nit_result else None

        if not results or not nit_asociado:
            # Si no hay registros o no se encuentra el Nit_asociado, marcar como ABIERTA
            orden_status = 'ABIERTA'
        else:
            # Calcular la suma de cerdos despachados y validar otros campos
            total_cerdos_despachados = sum(row[1] for row in results)
            granjas_bd = {row[2] for row in results}

            # Validar coincidencias
            if (cantidad_api == total_cerdos_despachados and
                granja_api in granjas_bd and
                propietario_api == nit_asociado and
                ingreso_qr == "SI"):
                orden_status = 'CERRADA'
            else:
                orden_status = 'ABIERTA'

        # Actualizar la tabla recepcion con el estado de orden
        cursor.execute(update_query, (orden_status, consecutivo_cercafe))

    connection.commit()
    cursor.close()
    connection.close()

# Llamar a esta función después de obtener los datos de la API
def main():
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = '2025-01-13'
    end_date = today

    try:
        # Obtén los datos de la API
        data = fetch_data_from_api(start_date, end_date)
        
        # Insertar datos en la base de datos
        insert_data_into_db(data)

        # Validar y actualizar las órdenes
        validate_and_update_orders(data)
        
        print("Datos insertados y órdenes actualizadas correctamente.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
