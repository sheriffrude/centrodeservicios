import requests
import mysql.connector
from datetime import datetime

def main3():
    # Configuración de la conexión a la base de datos MySQL
    db_config = {
        'host': '192.168.9.41',
        'port': 3306,
        'user': 'DEV_USER',
        'password': 'DEV-USER12345',
        'database': 'data360'
    }

    # URL de la API y headers
    api_url = "https://api.appsheet.com/api/v2/apps/4e9efc90-42bb-4fb9-8a4d-bd00de241be5/tables/Vísceras rojas/data"
    headers = {
        "ApplicationAccessKey": "V2-DlbtU-FI8bn-Z7spA-vjwAJ-tsvmw-G2pmX-tLin7-MOGyN"
    }

    # Obtener datos de la API
    response = requests.post(api_url, headers=headers, json={
        "Action": "Find",
        "Properties": {
            "Locale": "en-US"
        },
        "Rows": []
    })

    # Verificar la respuesta
    if response.status_code == 200:
        data = response.json()
        # Imprimir la respuesta para verificar su estructura
        print(data)
    else:
        print(f"Error al obtener datos de la API: {response.status_code}")
        exit()

    # Comprobar la estructura de `data`
    if isinstance(data, list):
        rows = data
    else:
        rows = data.get('Rows', [])

    # Transformar los datos
    transformed_data = []
    for item in rows:
        transformed_data.append((
            datetime.strptime(item.get('Fecha de ingreso', ''), '%m/%d/%Y').date(),  # Convertir a DATE
            item.get('GranjaID', ''),
            item.get('Consecutivo Cercafe', ''),
            item.get('Orden Frigorifico', ''),
            item.get('Mes', ''),
            item.get('Semana', '')
            
        ))

    # Conectar a la base de datos MySQL e insertar los datos
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        truncate_query = "TRUNCATE TABLE auditoria_visceras"
        cursor.execute(truncate_query)
        # SQL para insertar datos
        insert_query = """
        INSERT INTO auditoria_visceras (
            fecha_ingreso,granjaID, consecutivo_cercafe, orden_frigorifico, mes, semana
        ) VALUES (%s, %s, %s, %s, %s, %s)
        """

        # Insertar los datos
        cursor.executemany(insert_query, transformed_data)
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Error al conectar con la base de datos: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

