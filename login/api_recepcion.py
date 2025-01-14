import requests
import pymysql
from datetime import datetime


DB_CONFIG = {
    'host': '192.168.9.134',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'prod_carnica',
    'port': 3308,
    'charset': 'utf8mb4',
    'autocommit': True,
}


API_URL = "https://api.controlfrigo.com/api/v1/receptions"
API_KEY = "a2217af9-7730-430b-8a28-32935108f49e"


def fetch_data_from_api(start_date, end_date):
    headers = {'Key': API_KEY}
    params = {'startDate': start_date, 'endDate': end_date}
    
    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


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


current_time = datetime.now().strftime("%H:%M")
def get_tipo_corte_id(current_time):
    connection = pymysql.connect(**DB_CONFIG)
    cursor = connection.cursor()
    

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
       
        record['ingreso_qr'] = "SI" if record.get('placa') else "NO"
        
        
        registro_ic, id_frigorifico, id_granja = get_registro_ic_and_frigorifico(record.get('consecutivo_cercafe'))
        record['registro_ic'] = registro_ic
        record['id_frigorifico'] = id_frigorifico
        record['id_granja'] = id_granja
        
        
        record['id_propietario'] = get_id_propietario(record.get('nit_propietario'))
        
        
        current_time = datetime.now().strftime("%H:%M")
        tipo_corte = get_tipo_corte_id(current_time)
        record['tipo_corte'] = tipo_corte
        
        cursor.execute(query, record)
    
    connection.commit()
    cursor.close()
    connection.close()



def main():
    
    today = datetime.now().strftime("%Y-%m-%d")
    start_date = "2025-01-13"
    end_date = today
    
    try:
        
        data = fetch_data_from_api(start_date, end_date)
        
        
        insert_data_into_db(data)
        
        print("Datos insertados correctamente.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()