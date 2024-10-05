import requests
import mysql.connector
from datetime import datetime

def main2():
# Configuración de la conexión a la base de datos MySQL
    db_config = {
        'host': '192.168.9.41',
        'port': 3306,
        'user': 'DEV_USER',
        'password': 'DEV-USER12345',
        'database': 'data360'
    }

    # URL de la API y headers
    api_url = "https://api.appsheet.com/api/v2/apps/4e9efc90-42bb-4fb9-8a4d-bd00de241be5/tables/postmortem/data"
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
            datetime.strptime(item['Fecha de ingreso'], '%m/%d/%Y').date(),  # Convertir a DATE
            item.get('Apical Derecho', ''),
            item.get('consecutivo', item.get('Consecutivo Cercafe', '')),
            item.get('Cardiaco Derecho', ''),
            item.get('Diafragmatico Derecho', ''),
            item.get('Apical Izquierdo', ''),
            item.get('Cardiaco Izquierdo', ''),
            item.get('Diafragmatico Izquierdo', ''),
            item.get('Accesorio', ''),
            item.get('Cicatriz En Pulmones', ''),
            item.get('Pleuritis', ''),
            item.get('Adherencia Pulmon', ''),
            item.get('Pleuritis Craneal', ''),
            item.get('Neumonia Intersticial', ''),
            item.get('Abceso Pulmon', ''),
            item.get('Nodulo Pulmon', ''),
            item.get('Petequias Riñon', ''),
            item.get('Pericarditis', '')
        
        ))

    # Conectar a la base de datos MySQL e insertar los datos
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        truncate_query = "TRUNCATE TABLE auditoria_postmortem"
        cursor.execute(truncate_query)
        # SQL para insertar datos
        insert_query = """
        INSERT INTO auditoria_postmortem (
            fecha_ingreso, apical_derecho, consecutivo_cercafe, cardiaco_derecho, diafragmatico_derecho,
            apical_izquierdo, cardiaco_izquierdo, diafragmatico_izquierdo, accesorio, cicatriz_en_pulmones,
            pleuritis, adherencia_pulmon, pleuritis_craneal, neumonia_intersticial, abceso_pulmon,
            nodulo_pulmon, petequias_rinon, pericarditis
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
