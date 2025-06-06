import requests
import json
from datetime import datetime, timedelta
import base64
import urllib3
import mysql.connector
import uuid 
from dateutil.relativedelta import relativedelta
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_CONFIG = {
    'host': '192.168.9.41',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'agriness', 
    'port': 3306,
}

# --- MAPEADOR DE NOMBRES DE KPI DE API A COLUMNAS DE DB ---
KPI_MAPPING = {
    "AVERAGE_ACTIVE_SOWS_INVENTORY": "hembras_activas",
    "RATE_REPLACEMENT_SOWS_PROJECTED_YEAR": "porcentaje_reposicion",
    "RATE_MORTALITY_FEMALES_PROJECTED": "porcentaje_mortalidad_hembras",
    "PIGS_WEANED_MATED_FEMALE_YEAR": "lechones_destetados_por_hembra_por_ano",
    "LITTERS_FEMALE_YEAR": "partos_hembra_ano",
    "WAVERAGE_WEANED_PIGS_AGE": "edad_promedio_destete",
    "AVERAGE_BORN_ALIVE": "promedio_lechones_nacidos_vivos",
    "RATE_WEANING_PIG_DEATHS": "porcentaje_mortalidad_lactancia",
    "TOTAL_WEANING_PIG_DEATHS": "cantidad_lechones_muertos_lactancia",
    "WAVERAGE_WEANED_PIGS_DAILY_WEIGHT_GAIN": "ganancia_peso_lechones",
    "AVERAGE_NON_PRODUCTIVE_DAYS": "promedio_dias_no_productivos",
    "AVERAGE_BORN_CYCLE_1": "promedio_lechones_nacidos_totales_primerizas",
    "AVERAGE_BORN_ALIVE_CYCLE_1": "promedio_lechones_nacidos_vivos_primerizas",
    "FARROWING_RATE_CYCLE_1": "tasa_partos_primerizas",
    "PIGLET_WEIGHT_WEAN": "peso_promedio_destete",
    "WEIGHT_WEANED_MATED_FEMALE_YEAR": "kg_destetados_por_hembra_por_ano",
    "TOTAL_FARROWINGS": "total_partos",
    "TOTAL_BORN_ALIVE": "total_lechones_nacidos_vivos",
    "TOTAL_BORN_STILLBORN": "total_lechones_nacidos_muertos",
    "TOTAL_BORN_MUMMIFIED": "total_lechones_nacidos_momias",
    "TOTAL_BORN": "total_lechones_nacidos",
    "AVERAGE_BORN": "promedio_lechones_totales",
    "FARROWING_RATE": "tasa_partos", 
}


class SwineKPIsClient:
    def __init__(self, gateway_username, gateway_password, basic_auth_header, 
                 app_username, app_password, fixed_application_api_key):
        """
        Inicializar el cliente para consumir la API de KPIs reproductivos.
        """
        self.gateway_username = gateway_username
        self.gateway_password = gateway_password
        self.basic_auth_header = basic_auth_header
        self.app_username = app_username
        self.app_password = app_password
        self.fixed_application_api_key = fixed_application_api_key

        self.oauth_url = "https://am.agriness.com:9443/oauth2/token"
        self.login_base_url = "https://am.agriness.com:8243/sitio1-swine-default"
        self.kpis_base_url = "https://am.agriness.com:8243/swinekpisdefault"
        
        self.login_url = f"{self.login_base_url}/api/v1/login"
        self.kpis_url = f"{self.kpis_base_url}/v1/swine/reproductive/kpis"
        
        self.wso2_token = None
        self.api_token = None 
        
        print(f"✔️ Cliente SwineKPIsClient inicializado.")
    
    def get_wso2_token(self):
        """
        Obtener token OAuth2 de WSO2 (Primer token, para el Gateway)
        """
        headers = {
            'Authorization': self.basic_auth_header,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'grant_type': 'password',
            'username': self.gateway_username,
            'password': self.gateway_password
        }
        
        try:
            print("⏳ Intentando obtener token WSO2...")
            response = requests.post(self.oauth_url, headers=headers, data=data, verify=False)
            response.raise_for_status()
            
            token_data = response.json()
            self.wso2_token = token_data['access_token']
            
            print(f"✅ Token WSO2 obtenido exitosamente")
            print(f"   Expira en: {token_data.get('expires_in', 'N/A')} segundos")
            
            return self.wso2_token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo token WSO2: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Respuesta: {e.response.text}")
            raise

    def get_api_token(self):
        """
        Obtener token de autenticación para la API (Segundo token, de la aplicación S4)
        """
        if not self.wso2_token:
            raise ValueError("El token WSO2 es requerido. Llama primero a get_wso2_token()")

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.wso2_token}'
        }
        
        login_data = {
            'username': self.app_username,
            'password': self.app_password
        }
        
        try:
            print(f"⏳ Intentando obtener token API desde {self.login_url}...")
            response = requests.post(self.login_url, headers=headers, json=login_data, verify=False)
            response.raise_for_status()
            
            response_data = response.json()
            
            print(f"DEBUG: Respuesta JSON de /api/v1/login: {json.dumps(response_data, indent=2)}")

            if 'access_token' in response_data:
                self.api_token = response_data['access_token']
            else:
                raise ValueError("No se encontró 'access_token' en la respuesta de /api/v1/login.")
            
            print(f"✅ Token API (para HTTP-AUTHORIZATION) obtenido exitosamente.")
            
            return self.api_token
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo token API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status Code: {e.response.status_code}")
                print(f"   Respuesta: {e.response.text}")
            raise
    
    def get_reproductive_kpis(self, query_data):
        """
        Consultar KPIs reproductivos (Consulta final con ambos tokens y el fixed_api_key)
        """
        if not self.api_token:
            raise ValueError("Se requiere el token API (de /api/v1/login). Llama primero a get_api_token().")
        if not self.fixed_application_api_key:
            raise ValueError("Se requiere el API Key fijo de la aplicación.")
        if not self.wso2_token: 
             print("⚠️ Advertencia: El token WSO2 no está disponible para la consulta de KPIs. Esto podría causar un 401.")
        
        headers = {
            'Content-Type': 'application/json',
            'HTTP-AUTHORIZATION': self.api_token, 
            'apikey': self.fixed_application_api_key 
        }
        
        if self.wso2_token:
            headers['Authorization'] = f'Bearer {self.wso2_token}' 

        try:
            print(f"🔄 Consultando KPIs reproductivos...")
            print(f"   URL: {self.kpis_url}")
            print(f"   Parámetros: {json.dumps(query_data, indent=2)}")
            
            response = requests.post(self.kpis_url, headers=headers, json=query_data, verify=False)
            response.raise_for_status()
            
            print(f"✅ Consulta exitosa! Status Code: {response.status_code}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error consultando KPIs: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Status Code: {e.response.status_code}")
                print(f"   Respuesta: {e.response.text}")
            raise

def insert_kpis_to_db(kpis_data, db_config, kpi_mapping, original_query_data):
    """
    Inserta los datos de KPIs en la base de datos MySQL.
    """
    if not kpis_data or 'data' not in kpis_data or not kpis_data['data']:
        print("⚠️ No hay datos de KPIs para insertar.")
        return

    db_connection = None
    cursor = None
    try:
        print("\n⚙️ Conectando a la base de datos...")
        db_connection = mysql.connector.connect(**db_config)
        cursor = db_connection.cursor()
        print("✅ Conexión a la base de datos exitosa.")

        table_name = "kpis_reproductivos_sitio1" 
        rows_inserted = 0

        for item in kpis_data['data']:
            farm_uid = item.get('key') 
            kpis_values_from_api = item.get('kpis', {}) 

            # fecha_registro will be a datetime.date object (first day of the month)
            date_str_from_item = item.get('date') 
            fecha_registro_date_obj = None # This will hold the actual date object

            if date_str_from_item:
                try:
                    # Parse as YYYY-MM to get the first day of that month
                    fecha_registro_date_obj = datetime.strptime(date_str_from_item, "%Y-%m").date() 
                except ValueError:
                    print(f"🚫 No se pudo parsear la fecha '{date_str_from_item}' del item. Intentando inferir.")
            
            if fecha_registro_date_obj is None:
                try:
                    # Infer from original_query_data, again getting the first day of the month
                    inferred_month_year = original_query_data['start_date'][:7] 
                    fecha_registro_date_obj = datetime.strptime(inferred_month_year, "%Y-%m").date()
                except Exception as e:
                    print(f"🚫 No se pudo inferir la fecha de inicio de '{original_query_data.get('start_date')}'. Ignorando fila.")
                    print(f"   Error de inferencia: {e}")
                    continue 
            
            if not farm_uid or not fecha_registro_date_obj:
                print(f"🚫 Ignorando fila debido a granja_uid o fecha_registro faltante: {item}")
                continue
            
            # --- USAR LAS FECHAS EXACTAS DE start_date y end_date ---
            # Usar directamente las fechas de la consulta original
            start_date_from_query = original_query_data.get('start_date')
            end_date_from_query = original_query_data.get('end_date') 
            
            # Si ambas fechas son iguales (mismo día), usar solo esa fecha
            if start_date_from_query == end_date_from_query:
                fecha_registro_range_str = start_date_from_query
            else:
                # Si son diferentes, usar el formato de rango
                fecha_registro_range_str = f"{start_date_from_query}/{end_date_from_query}"
            # --- END NEW LOGIC ---

            record_guid = str(uuid.uuid4()) 
            metadata = datetime.now() 

            columns = ["granjauid", "fecha_registro", "guid", "metadata"] 
            # Use the new range string for fecha_registro
            values = [farm_uid, fecha_registro_range_str, record_guid, metadata]

            for api_kpi_name, db_column_name in kpi_mapping.items():
                if api_kpi_name in kpis_values_from_api:
                    value = kpis_values_from_api[api_kpi_name]
                    columns.append(db_column_name)
                    values.append(str(value) if value is not None else None)
            
            columns_str = ", ".join(columns)
            placeholders = ", ".join(["%s"] * len(values))
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

            try:
                # --- AÑADIR DEBUGGING PARA LA CONSULTA SQL ---
                print(f"DEBUG SQL: {sql}")
                print(f"DEBUG VALUES: {tuple(values)}")
                # --------------------------------------------
                cursor.execute(sql, tuple(values))
                rows_inserted += 1
            except mysql.connector.Error as err:
                print(f"❌ Error al insertar fila para granja {farm_uid} en {fecha_registro_range_str}: {err}")
                print(f"   SQL: {sql}")
                print(f"   Values (first 10): {values[:10]}...")

        db_connection.commit()
        print(f"\n✅ Total de {rows_inserted} filas insertadas exitosamente.")

    except mysql.connector.Error as err:
        print(f"❌ Error de base de datos: {err}")
    except Exception as e:
        print(f"❌ Ocurrió un error inesperado al insertar datos: {e}")
    finally:
        if cursor:
            cursor.close()
        if db_connection and db_connection.is_connected():
            db_connection.close()
            print("🔒 Conexión a la base de datos cerrada.")


def main():
    """
    Función principal para ejecutar el script
    """
    GATEWAY_USERNAME = "cercafe"
    GATEWAY_PASSWORD = "J9yKEaHOKH"
    BASIC_AUTH_HEADER = "Basic X2xRcERmX01GNHc4WkJ1eHZDTTJHRmxaUVIwYTpuckRZZEZEbGJidHVBWThjdnFDMUVGYVA0b2Nh"
    
    APP_USERNAME = "jefferson.villamizar@cercafe.com.co"
    APP_PASSWORD = "Teamohij4" 
    
    FIXED_APPLICATION_API_KEY = "eyJ4NXQiOiJOMkpqTWpOaU0yRXhZalJrTnpaalptWTFZVEF4Tm1GbE5qZzRPV1UxWVdRMll6YzFObVk1TlE9PSIsImtpZCI6ImdhdGV3YXlfY2VydGlmaWNhdGVfYWxpYXMiLCJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJjZXJjYWZlQGNhcmJvbi5zdXBlciIsImFwcGxpY2F0aW9uIjp7Im93bmVyIjoiY2VyY2FmZSIsInRpZXJRdW90YVR5cGUiOm51bGwsInRpZXIiOiJVbmxpbWl0ZWQiLCJuYW1lIjoiY2VyY2FmZSIsImlkIjoxMDM2LCJ1dWlkIjoiY2YyMGZkNDQtZDBlNS00NzBjLWE4ZjktZGUyYTQ4ZWRlNDQ3In0sImlzcyI6Imh0dHBzOlwvXC9hbS5hZ3JpbmVzcy5jb206OTQ0M1wvb2F1dGgyXC90b2tlbiIsInRpZXJJbmZvIjp7IkJyb256ZSI6eyJ0aWVyUXVvdGFUeXBlIjoicmVxdWVzdENvdW50IiwiZ3JhcGhRTE1heENvbXBsZXhpdHkiOjAsImdyYXBoUUxNYXhEZXB0aCI6MCwic3RvcE9uUXVvdGFSZWFjaCI6dHJ1ZSwic3Bpa2VBcnJlc3RMaW1pdCI6MCwic3Bpa2VBcnJlc3RVbml0IjpudWxsfX0sImtleXR5cGUiOiJQUk9EVUNUSU9OIiwic3Vic2NyaWJlZEFQSXMiOlt7InN1YnNjcmliZXJUZW5hbnREb21haW4iOiJjYXJib24uc3VwZXIiLCJuYW1lIjoiU3dpbmUtS1BJcy1kZWZhdWx0IiwiY29udGV4dCI6Ilwvc3dpbmVrcGlzZGVmYXVsdCIsInB1Ymxpc2hlciI6ImFkbWluIiwidmVyc2lvbiI6IjEuMC4wIiwic3Vic2NyaXB0aW9uVGllciI6IkJyb256ZSJ9LHsic3Vic2NyaWJlclRlbmFudERvbWFpbiI6ImNhcmJvbi5zdXBlciIsIm5hbWUiOiJFdmVudG9zLXNpdGlvMS1wYWRyYW8iLCJjb250ZXh0IjoiXC9zaXRpbzEtc3dpbmUtZGVmYXVsdCIsInB1Ymxpc2hlciI6ImFkbWluIiwidmVyc2lvbiI6IjEuMC4wIiwic3Vic2NyaXB0aW9uVGllciI6IkJyb256ZSJ9LHsic3Vic2NyaWJlclRlbmFudERvbWFpbiI6ImNhcmJvbi5zdXBlciIsIm5hbWUiOiJFdmVudHMtZmFybS1zaXRpbzItMy1kZWZhdWx0IiwiY29udGV4dCI6IlwvZXZlbnRzLWZhcm0tc2l0aW8yLTMtZGVmYXVsdCIsInB1Ymxpc2hlciI6ImFkbWluIiwidmVyc2lvbiI6IjEuMC4wIiwic3Vic2NyaXB0aW9uVGllciI6IkJyb256ZSJ9XSwidG9rZW5fdHlwZSI6ImFwaUtleSIsImlhdCI6MTc0ODYzNDA1MywianRpIjoiNGVjYTZkZTItMWEzNC00MTZkLTkwZTQtYjI4MzU1NTA3NTNmIn0=.dlb7ll0MBerFfdFBhP0GvnTZfraT6alLtelUaKvRLcc8V9QJKOujfvqprImKQQSQtlefcKHW4L6hqeBIEL4PMZkGClPnuEdMAqFT_Ds7awmx3A9qK2jVj6OOeWBlBU48QFOTTP65sBcyJV1fhD_Juk_wnU6RLyDrJo1hjLCk_yeBo5sGEPUHFqNMon7TC0MzlBe-4bXhlYGt5K2zIRGU4LMH-6FClvNI89WHATxCJL6S95jf0Z454vmKWVnIwin_dIt_llIlDvsd58H--GgRr9A27_nmVFs7aburPvv_fIocuzyRgdPmG1Ssy-X610bBWm3yf-M7zMpLsw4f5Jvc2g=="
    
    # Obtener la fecha actual
    today = datetime.now().date()
    today_str = today.strftime("%Y-%m-%d")
    
    print(f"📅 Fecha actual: {today_str}")
    
    query_data = {
        "farms": ["06f35e5f-bf77-4118-8096-9efcccc328c9","44c6bcdc-bf3c-4333-876a-35cd88b8d092",
                  "4603ec1a-7c2c-468a-b765-4baafb6f8cb1","49c2da18-bb8a-4c9a-9092-addb316e6202",
                  "5d7114b2-0b6e-4e90-8fa1-65f7b09adf51","82a66e1b-be0c-417a-98dc-a4515247d24f",
                  "8cb21bd7-7989-4b7a-9957-b28295b285b4","8ed92efc-cf93-455d-98c2-ffc75e444bf9",
                  "9006e0dc-c1d7-4c0c-b660-9e9ce66cb5d0","92264637-4952-4b03-8a47-08f2769959cf",
                  "950d6b15-5673-4512-ae96-e76920a56067","a4932d6f-7f18-4b8f-b444-7e29ba0ed0b6",
                  "a7ca7121-d825-4dbd-831c-b5af67924b2e","bf116d0b-bcf0-40c7-83d9-7ffa7a1d5bbf",
                  "c2e5841f-d39a-472a-9ac8-d04b0e1dd88c","c91d0fb7-9c64-40c8-9b94-ae3f9786418e",
                  "d68d325d-7543-4b9e-af44-a6da1d74e328","db3e95ea-eecd-4687-b4b9-6d1455af2f74",
                  "dfeb1020-97ca-480b-b21c-e2539b33a8c1","f4b0f9f4-c493-4362-9045-ddd4a25216c1"],
        "start_date": today_str,  # Fecha actual
        "end_date": today_str,    # Fecha actual
        "group_by": "farm_id",
        "date_format": "year_month", 
        "sort": "asc",
        "kpis": [   
            "AVERAGE_ACTIVE_SOWS_INVENTORY", "RATE_REPLACEMENT_SOWS_PROJECTED_YEAR", 
            "RATE_MORTALITY_FEMALES_PROJECTED", "PIGS_WEANED_MATED_FEMALE_YEAR",
            "LITTERS_FEMALE_YEAR", "WAVERAGE_WEANED_PIGS_AGE", "AVERAGE_BORN_ALIVE",
            "TOTAL_FARROWINGS","TOTAL_BORN_ALIVE","TOTAL_BORN_STILLBORN","TOTAL_BORN_MUMMIFIED",
            "TOTAL_BORN","AVERAGE_BORN","RATE_WEANING_PIG_DEATHS",
            "TOTAL_WEANING_PIG_DEATHS", "WAVERAGE_WEANED_PIGS_DAILY_WEIGHT_GAIN",
            "FARROWING_RATE","AVERAGE_NON_PRODUCTIVE_DAYS",
            "AVERAGE_BORN_CYCLE_1","AVERAGE_BORN_ALIVE_CYCLE_1",
            "FARROWING_RATE_CYCLE_1","PIGLET_WEIGHT_WEAN","WEIGHT_WEANED_MATED_FEMALE_YEAR"
        ],
        "limit": 500
    }
    
    try:
        print("🐷 Iniciando consulta de KPIs reproductivos de cerdos")
        print("=" * 60)
        
        client = SwineKPIsClient(
            gateway_username=GATEWAY_USERNAME,
            gateway_password=GATEWAY_PASSWORD,
            basic_auth_header=BASIC_AUTH_HEADER,
            app_username=APP_USERNAME,
            app_password=APP_PASSWORD,
            fixed_application_api_key=FIXED_APPLICATION_API_KEY
        )
        
        client.get_wso2_token()
        client.get_api_token() 
        
        print("\n📊 Consultando KPIs reproductivos...")
        result = client.get_reproductive_kpis(query_data)
        
        print("\n📈 Resultados obtenidos de la API (muestra del primer registro):")
        print("=" * 60)
        if result and 'data' in result and result['data']:
            json_output = json.dumps(result['data'][0] if len(result['data']) > 0 else {}, indent=2, ensure_ascii=False)
            print(json_output[:1000] + "...\n(Primer registro de " + str(len(result['data'])) + " en total)" if len(json_output) > 1000 else json_output)
        else:
            print("No se recibieron datos de KPIs de la API.")
            
        insert_kpis_to_db(result, DB_CONFIG, KPI_MAPPING, query_data)
        
    except Exception as e:
        print(f"\n❌ Error en la ejecución principal: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()