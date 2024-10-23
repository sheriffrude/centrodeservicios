import requests
import mysql.connector
from datetime import datetime, timedelta

# Configuración de la conexión a la base de datos MySQL
db_config = {
    'host': '192.168.9.41',
    'port': 3306,
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'data360'
}

# URL de la API y headers
api_url = "https://api.appsheet.com/api/v2/apps/4e9efc90-42bb-4fb9-8a4d-bd00de241be5/tables/Forms/data"
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
time_difference = timedelta(hours=-7)
# Comprobar la estructura de `data`
if isinstance(data, list):
    rows = data
else:
    rows = data.get('Rows', [])

# Transformar los datos
transformed_data = []
for item in rows:
    # Obtener el valor de metadata
    metadata_value = item.get('METADATA', '')
    print(f"Valor de METADATA: {metadata_value}")  # Depuración
    
    # Transformar el valor de metadata
    if metadata_value:
        try:
            # Asumiendo que 'METADATA' llega en el formato '10/23/2024 00:24:04'
            metadata_datetime = datetime.strptime(metadata_value, '%m/%d/%Y %H:%M:%S')
            # Ajustar la hora restando 7 horas
            adjusted_datetime = metadata_datetime + time_difference
            print(f"Hora ajustada: {adjusted_datetime}")  # Depuración
            
            # Convertir a formato de cadena si es necesario
            formatted_metadata = adjusted_datetime.strftime('%m/%d/%Y %I:%M %p')  # O simplemente usa adjusted_datetime si no necesitas formato
        except ValueError as e:
            print(f"Error en la conversión de fecha: {e}")
            formatted_metadata = ''
    else:
        formatted_metadata = ''
    
    transformed_data.append((
        item.get('Mes', ''),
        item.get('Semana', ''),
        datetime.strptime(item['Fecha de Ingreso'], '%m/%d/%Y').date(),  # Convertir a DATE
        item.get('Consecutivo Cercafe', ''),
        item.get('Orden Frigotun', ''),
        item.get('Numero de animales', ''),
        item.get('Medidas Vehiculo', ''),
        item.get('Bioseguridad (Obs)', ''),
        item.get('PISOS (1-2)', ''),
        item.get('Hora LLegada', ''),
        item.get('Tiempo Desembarque (minutos)', ''),
        item.get('Novedad Tiempo Desembarque', ''),
        item.get('Tiempo de espera', ''),
        item.get('Novedad Tiempo Espera', ''),
        item.get('Muertos desembarque', ''),
        item.get('Tiquete Muertos desembarque', ''),
        item.get('Muertos Transporte', ''),
        item.get('Tiquete Muertos Transporte', ''),
        item.get('Muertos Reposo', ''),
        item.get('Tiquete Muertos Reposo', ''),
        item.get('Lesionados', ''),
        item.get('Lesiones', ''),
        item.get('Tiquete Lesiones', ''),
        item.get('Agitados', ''),
        item.get('Tiquetes Agitados', ''),
        item.get('Caidos', ''),
        item.get('Tiquetes Caidos', ''),
        item.get('Corral ( N°-Recepcion/sacrificio)', ''),
        item.get('Observaciones Corral', ''),
        item.get('Comportamiento Sexual', ''),
        item.get('Observaciones CS', ''),
        item.get('Peso Granja', ''),
        item.get('Peso Planta', ''),
        item.get('Responsable Desembarque', ''),
        item.get('Granja', ''),
        item.get('Placa', ''),
        item.get('GranjaID', ''),
        item.get('placaID', ''),
        formatted_metadata
    ))

# Conectar a la base de datos MySQL e insertar los datos
try:
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    truncate_query = "TRUNCATE TABLE llegada_animales"
    cursor.execute(truncate_query)
    # SQL para insertar datos
    insert_query = """
    INSERT INTO llegada_animales (
        mes, semana, fecha_ingreso, consecutivo_cercafe, orden_frigotun, numero_animales, 
        medidas_vehiculo, bioseguridad_obs, pisos, hora_llegada, tiempo_desembarque_minutos, 
        novedad_tiempo_desembarque, tiempo_espera, novedad_tiempo_espera, muertos_desembarque,tiquete_desembarque,muertos_transporte, 
        tiquete_transporte,muertos_reposo,tiquete_reposo, lesionados, lesiones, tiquete_lesiones, agitados, tiquetes_agitados, 
        caidos, tiquetes_caidos, corral_recepcion_sacrificio, observaciones_corral, 
        comportamiento_sexual, observaciones_cs, peso_granja, peso_planta, 
        responsable_desembarque, granja, placa, granjaID, placaID, metadata
    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
              %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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