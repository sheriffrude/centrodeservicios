import requests
import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime

# --- CONFIGURACIÓN ---

# Configuración de logging para ver el proceso en la consola
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuración de la API
API_TOKEN_URL = "https://www.easysales.com.co/API_Entrega_Gestiones_Cercafe/api/WS_01_Controller/WSGES001"
API_DATA_URL = "https://www.easysales.com.co/API_Entrega_Gestiones_Cercafe/api/WS_02_Controller/WSGES001"
API_CREDENTIALS = {
  "Usuario": "easynet.cer",
  "Clave": "Easynet123"
}

# Configuración de la Base de Datos
DB_CONFIG = {
    'host': '192.168.9.134',
    'user': 'DEV_USER',
    'password': 'DEV-USER12345',
    'database': 'easy_sales',
    'port': 3308,
    'charset': 'utf8mb4',
    'autocommit': False 
}


# --- FUNCIONES DE LA API ---

def get_api_token():
    """Obtiene el token de autenticación de la API."""
    try:
        logging.info("Solicitando token de la API...")
        response = requests.post(API_TOKEN_URL, json=API_CREDENTIALS)
        response.raise_for_status()  # Lanza un error para códigos 4xx/5xx
        
        data = response.json()
        if data.get("Token") and data["Respuesta"]["Resultado"] == "0000":
            logging.info("Token obtenido exitosamente.")
            return data["Token"]
        else:
            logging.error(f"Error al obtener el token: {data.get('Respuesta', 'Respuesta no encontrada')}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de conexión al solicitar el token: {e}")
        return None

def get_pedidos_data(token):
    """Obtiene los datos de los pedidos usando el token."""
    if not token:
        return None
    
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        logging.info("Consultando datos de pedidos...")
        response = requests.get(API_DATA_URL, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        if "Lista_pedidos" in data:
            logging.info(f"Se encontraron {len(data['Lista_pedidos'])} pedidos en la API.")
            return data["Lista_pedidos"]
        else:
            logging.error(f"La respuesta de la API no contiene 'Lista_pedidos'. Respuesta: {data}")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error de conexión al solicitar los pedidos: {e}")
        return None


# --- FUNCIONES DE LA BASE DE DATOS ---

def process_pedidos(pedidos):
    """Procesa la lista de pedidos y los ingesta en la base de datos."""
    if not pedidos:
        logging.warning("No hay pedidos para procesar.")
        return

    try:
        # Usamos 'with' para asegurar que la conexión se cierre automáticamente
        with mysql.connector.connect(**DB_CONFIG) as conn:
            with conn.cursor(dictionary=True) as cursor:
                
                for pedido_api in pedidos:
                    pedido_id = pedido_api.get('Pedido_ID')
                    if not pedido_id:
                        logging.warning(f"Pedido omitido por no tener Pedido_ID: {pedido_api}")
                        continue
                    
                    try:
                        logging.info(f"Procesando Pedido ID: {pedido_id}")
                        
                        # 1. Buscar si el pedido ya existe
                        cursor.execute("SELECT * FROM encabezado_pedidos_easy WHERE pedido_id = %s", (pedido_id,))
                        pedido_db = cursor.fetchone()

                        # 2. Mapear datos de la API a los campos de la BD
                        datos_encabezado_api = {
                            'pedido_id': pedido_id,
                            'clase_pedido': pedido_api.get('Clase_Pedido_Nombre'),
                            'tipo_venta_cliente': pedido_api.get('Tipo_Venta_Cliente_Nombre'),
                            'orden_compra': pedido_api.get('Orden_Compra'),
                            'estado_actual': pedido_api.get('Estado_Actual'),
                            'tipo_pago_pedido': pedido_api.get('Tipo_Pago_Pedido'),
                            'tipo_pago_cliente': pedido_api.get('Tipo_Pago_Cliente'),
                            'valor_total': pedido_api.get('Valor_Total'),
                            'fecha_pedido': pedido_api.get('Fecha_Pedido'),
                            'fecha_entrega': pedido_api.get('Fecha_Entrega'),
                            'hora_desde': str(pedido_api.get('Hora_Entrega_Desde', '00:00:00'))[:8],
                            'hora_hasta': str(pedido_api.get('Hora_Entrega_Hasta', '00:00:00'))[:8],
                            'cliente_id': pedido_api.get('Cliente_ID'),
                            'asesor_id': pedido_api.get('Asesor_ID'),
                            'direccion_entrega_id': pedido_api.get('Ubicacion_ID_Despacho'), 
                            'punto_visita_id': pedido_api.get('Ubicacion_ID'), 
                            'observacion_comercial': pedido_api.get('Obs_Comercial'),
                            'observacion_despacho': pedido_api.get('Obs_Despacho')
                        }

                        if pedido_db is None:
                            # 3.A. El pedido es nuevo, INSERTAR
                            logging.info(f"Pedido {pedido_id} es nuevo. Insertando...")
                            
                            datos_encabezado_api['novedad'] = 'nuevo'
                            datos_encabezado_api['obs_novedad'] = ''
                            
                            sql_insert_encabezado = """
                                INSERT INTO encabezado_pedidos_easy (
                                    pedido_id, clase_pedido, tipo_venta_cliente, orden_compra, estado_actual, tipo_pago_pedido, 
                                    tipo_pago_cliente, valor_total, fecha_pedido, fecha_entrega, hora_desde, hora_hasta, cliente_id, 
                                    asesor_id, direccion_entrega_id, punto_visita_id, observacion_comercial, observacion_despacho, 
                                    novedad, obs_novedad
                                ) VALUES (
                                    %(pedido_id)s, %(clase_pedido)s, %(tipo_venta_cliente)s, %(orden_compra)s, %(estado_actual)s, 
                                    %(tipo_pago_pedido)s, %(tipo_pago_cliente)s, %(valor_total)s, %(fecha_pedido)s, 
                                    %(fecha_entrega)s, %(hora_desde)s, %(hora_hasta)s, %(cliente_id)s, %(asesor_id)s, 
                                    %(direccion_entrega_id)s, %(punto_visita_id)s, %(observacion_comercial)s, 
                                    %(observacion_despacho)s, %(novedad)s, %(obs_novedad)s
                                )
                            """
                            cursor.execute(sql_insert_encabezado, datos_encabezado_api)

                        else:
                       
                            cambios = []
                            # Campos a comparar (excluimos los que no deben cambiar o se manejan aparte)
                            campos_a_comparar = [
                                'clase_pedido', 'tipo_venta_cliente',  'estado_actual',  'fecha_pedido', 'fecha_entrega', 
                                'cliente_id', 'asesor_id', 'direccion_entrega_id', 'punto_visita_id', 'observacion_comercial',
                                'observacion_despacho'
                            ]
                            
                            for campo in campos_a_comparar:
                                valor_api = datos_encabezado_api[campo]
                                valor_db = pedido_db[campo]

                                # Normalizar tipos para una comparación justa
                                if isinstance(valor_db, datetime):
                                    valor_db = valor_db.strftime('%Y-%m-%dT%H:%M:%S')
                                if isinstance(valor_db, (int, float)):
                                    valor_api = float(valor_api or 0) # Convertir a float para comparar
                                    valor_db = float(valor_db or 0)
                                
                                if str(valor_api) != str(valor_db):
                                    cambios.append(f"{campo}:{valor_db},{valor_api}")
                            
                            if cambios:
                                logging.info(f"Pedido {pedido_id} tiene cambios. Actualizando...")
                                
                                datos_encabezado_api['novedad'] = 'actualizado'
                                datos_encabezado_api['obs_novedad'] = ";".join(cambios) # Unimos los cambios con ;

                                sql_update_encabezado = """
                                    UPDATE encabezado_pedidos_easy SET
                                        clase_pedido = %(clase_pedido)s, tipo_venta_cliente = %(tipo_venta_cliente)s, 
                                        estado_actual = %(estado_actual)s, fecha_pedido = %(fecha_pedido)s, 
                                        fecha_entrega = %(fecha_entrega)s, cliente_id = %(cliente_id)s, asesor_id = %(asesor_id)s, 
                                        direccion_entrega_id = %(direccion_entrega_id)s, punto_visita_id = %(punto_visita_id)s, 
                                        observacion_comercial = %(observacion_comercial)s, observacion_despacho = %(observacion_despacho)s, 
                                        novedad = %(novedad)s, obs_novedad = %(obs_novedad)s, metadata = CURRENT_TIMESTAMP
                                    WHERE pedido_id = %(pedido_id)s
                                """
                                cursor.execute(sql_update_encabezado, datos_encabezado_api)
                            else:
                                logging.info(f"Pedido {pedido_id} sin cambios en el encabezado.")

                        # 4. Procesar detalles del pedido (borrar e insertar de nuevo para simplicidad)
                        detalles_api = pedido_api.get("Lista_Detalles", [])
                        if detalles_api:
                            # Borramos los detalles antiguos para evitar duplicados o inconsistencias
                            cursor.execute("DELETE FROM detalle_pedidos_easy WHERE pedido_id = %s", (pedido_id,))
                            
                            sql_insert_detalle = """
                                INSERT INTO detalle_pedidos_easy (
                                    pedido_id, producto_id, cantidad, precio_lista, porcentaje_iva, 
                                    descuento, bodega_id, observacion_producto
                                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            
                            detalles_para_insertar = []
                            for detalle in detalles_api:
                                detalles_para_insertar.append((
                                    pedido_id,
                                    detalle.get('Producto_ID'),
                                    detalle.get('Cantidad_Pedida'),
                                    detalle.get('Precio_Unitario'),
                                    detalle.get('Porcentaje_IVA'),
                                    detalle.get('Porcentaje_Descuento'),
                                    detalle.get('Bodega_ID'),
                                    detalle.get('Observaciones')
                                ))
                            
                            cursor.executemany(sql_insert_detalle, detalles_para_insertar)
                            logging.info(f"Insertados/actualizados {len(detalles_para_insertar)} detalles para el pedido {pedido_id}.")

                        # Confirmar los cambios para este pedido
                        conn.commit()
                        logging.info(f"Pedido {pedido_id} procesado y guardado exitosamente.")

                    except Exception as e:
                        logging.error(f"Error procesando el pedido {pedido_id}: {e}")
                        conn.rollback() # Revertir cambios si algo falló para este pedido en específico

    except Error as e:
        logging.error(f"Error de conexión o de base de datos: {e}")
    except Exception as e:
        logging.error(f"Ocurrió un error inesperado: {e}")



def main():
    """Función principal que orquesta todo el proceso."""
    logging.info("--- INICIANDO SCRIPT DE INGESTA DE PEDIDOS ---")
    
    token = get_api_token()
    if token:
        pedidos = get_pedidos_data(token)
        if pedidos:
            process_pedidos(pedidos)
            
    logging.info("--- SCRIPT DE INGESTA FINALIZADO ---")


if __name__ == "__main__":
    main()