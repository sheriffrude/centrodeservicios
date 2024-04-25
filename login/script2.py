import mysql.connector
from datetime import datetime, timedelta

def ejecutar_consulta(fecha_inicial, fecha_final):
    # Conexión a la base de datos MySQL
  
    conexion = mysql.connector.connect(
        host="192.168.9.200",
        port= "3308",
        user="DEV_USER",
        password="DEV-USER12345",
        
        
    )
    print("Conexión establecida con la base de datos.")
    cursor = conexion.cursor()
    
    # Ejecutar la consulta SQL
    consulta_sql = """
    
    -- OPERACION DESPOSTE A FACTURAR
    
    use dhc;
    SET @Fecha_inicial = '{}';
	SET @Fecha_Final = '{}';

	-- Convertimos las fechas de varchar a date
	SET @Fecha_inicial_t = STR_TO_DATE(@Fecha_inicial, '%d/%m/%Y');
	SET @Fecha_Final_t = STR_TO_DATE(@Fecha_Final, '%d/%m/%Y');
    
    -- Creamos e Importamos tablas temporales globales
    DROP TEMPORARY TABLE IF EXISTS t_rendimientos_porcinos_granjas;
	DROP TEMPORARY TABLE IF EXISTS t_remisiones_porcinos;
    DROP TEMPORARY TABLE IF EXISTS t_operacion_desposte;
    
    CREATE TEMPORARY TABLE t_rendimientos_porcinos_granjas LIKE b_ca.rendimientos_porcinos_granjas;
    
    CREATE TEMPORARY TABLE t_remisiones_porcinos LIKE frigotun.remisiones_porcinos;
	
	INSERT INTO t_rendimientos_porcinos_granjas
    SELECT * FROM b_ca.rendimientos_porcinos_granjas
	WHERE descripcion_exp LIKE '%DESPOSTE%'
    AND fecha_despacho BETWEEN @Fecha_inicial_t AND @Fecha_Final_t;
    
    -- SELECT * FROM t_rendimientos_porcinos_granjas;
    
	INSERT INTO t_remisiones_porcinos 
    SELECT * FROM frigotun.remisiones_porcinos;
    
    CREATE TEMPORARY TABLE t_operacion_desposte (
		Fecha_transformacion DATE,
		Unidades INT,
		Peso_canal_fria DECIMAL(22,9),
		Lote VARCHAR (500),
		Codigo_granja VARCHAR (10),
		Remision VARCHAR(500),
		Valor_kilo DECIMAL(22,9),
		Valor DECIMAL(22,9),
		Cliente VARCHAR(500),
		Planta_Beneficio VARCHAR(20),
		Granja VARCHAR(500),
		Nit_asociado VARCHAR(500),
		Asociado VARCHAR(500),
		Grupo_Granja VARCHAR(500),
		Retencion DECIMAL(22,9),
		Valor_a_pagar_asociado DECIMAL(22,9)
    );
    
    INSERT INTO t_operacion_desposte (Fecha_transformacion,Unidades,Peso_canal_fria,Lote,Codigo_granja,Remision,Valor_kilo,Valor,Cliente,
	Planta_Beneficio,Granja,Nit_asociado,Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado)
    SELECT 
	A.fecha_despacho AS Fecha_transformacion,
    COUNT(A.tiquete) AS Unidades,
    SUM(A.peso_frio) AS Peso_canal_fria,
    A.Lote AS Lote,
    A.Codigo_granja AS Codigo_granja,
    A.GUIA AS Remision,
    0 AS Valor_kilo,
	0 AS Valor,
    B.tercero AS Cliente,
    A.FRIGORIFICO AS Planta_Beneficio,
    A.Granja AS Granja,
    A.Nit_asociado AS Nit_asociado,
    A.Asociado AS Asociado,
    A.Grupo_Granja AS Grupo_Granja,
    0 AS Retencion,
    0 AS Valor_a_pagar_asociado
	FROM t_rendimientos_porcinos_granjas A 
    JOIN t_remisiones_porcinos B ON A.Guia = B.GUIA
    WHERE A.FRIGORIFICO = 'FRIGOTUN' AND B.tercero LIKE '%CERCAFE DESPOSTE%' GROUP BY Fecha_transformacion,Lote,Codigo_granja,Remision,Cliente,Planta_Beneficio,Granja,
    Nit_asociado,Asociado,Grupo_Granja;
    -- select * from t_operacion_desposte;
    
    INSERT INTO t_operacion_desposte (Fecha_transformacion,Unidades,Peso_canal_fria,Lote,Codigo_granja,Remision,Valor_kilo,Valor,Cliente,
	Planta_Beneficio,Granja,Nit_asociado,Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado)
    SELECT 
	fecha_despacho AS Fecha_transformacion,
    COUNT(tiquete) AS Unidades,
    SUM(peso_frio) AS Peso_canal_fria,
    Lote AS Lote,
    Codigo_granja AS Codigo_granja,
    GUIA AS Remision,
    0 AS Valor_kilo,
	0 AS Valor,
    descripcion_exp AS Cliente,
    FRIGORIFICO AS Planta_Beneficio,
    Granja AS Granja,
    Nit_asociado AS Nit_asociado,
    Asociado AS Asociado,
    Grupo_Granja AS Grupo_Granja,
    0 AS Retencion,
    0 AS Valor_a_pagar_asociado
	FROM t_rendimientos_porcinos_granjas
    WHERE FRIGORIFICO = 'OINC' GROUP BY Fecha_transformacion,Lote,Codigo_granja,Remision,Cliente,Planta_Beneficio,Granja,
    Nit_asociado,Asociado,Grupo_Granja;
    
    -- SELECT * FROM t_operacion_desposte;
    SET @GUID = UUID();
    
    INSERT INTO B_GAF.OPERACION_DESPOSTE(Fecha_transformacion,Unidades,Peso_canal_fria,Consecutivo_Cercafe,Codigo_granja,Remision,Valor,
	Cliente,Planta_Beneficio,Granja,Nit_asociado,Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado,Valor_kilo,GUID)
    SELECT
    Fecha_transformacion as Fecha_transformacion,
	Unidades,
	Peso_canal_fria,
	Lote AS Consecutivo_Cercafe,
	Codigo_granja,
	Remision,
	Valor,
	Cliente,
	Planta_Beneficio,
	Granja,
	Nit_asociado,
	Asociado,
	Grupo_Granja,
	Retencion,
	Valor_a_pagar_asociado,
    Valor_kilo,
    @GUID AS GUID
    FROM t_operacion_desposte;
    
    /*
    ALTER TABLE b_gaf.operacion_desposte
	CHANGE COLUMN Lote Consecutivo_Cercafe varchar(500);
    */
    
    /* Consulta a ejecutar
    SELECT Fecha_transformacion,Unidades,Peso_canal_fria,Lote,Codigo_granja,Remision,Valor,Cliente,Planta_Beneficio,Granja,Nit_asociado,
	Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado,Valor_kilo
	FROM B_GAF.OPERACION_DESPOSTE
	WHERE GUID=(SELECT GUID FROM B_GAF.OPERACION_DESPOSTE WHERE FECHA_DATOS=(SELECT MAX(FECHA_DATOS) FROM B_GAF.OPERACION_DESPOSTE) LIMIT 1)
    */ 
    -- Eliminamos tablas temporales
    DROP TEMPORARY TABLE IF EXISTS t_rendimientos_porcinos_granjas;
	DROP TEMPORARY TABLE IF EXISTS t_remisiones_porcinos;
    DROP TEMPORARY TABLE IF EXISTS t_operacion_desposte;
    
    """.format(fecha_inicial, fecha_final)
    print("Consulta SQL operacion desposte a facturar:")
    print(consulta_sql)
    cursor.execute(consulta_sql)

    # Guardar los resultados si es necesario
    resultados = cursor.fetchall()
    
    # Cerrar cursor y conexión
    cursor.close()
    conexion.close()

def obtener_fechas():
    hoy = datetime.now()
    dia_semana = hoy.weekday()  # 0 para lunes, 1 para martes, etc.

    if dia_semana in [0, 1, 2, 3]:  # Lunes a jueves
        fecha_inicial = hoy - timedelta(days=1)
        fecha_final = hoy - timedelta(days=1)
    elif dia_semana == 4:  # Viernes
        fecha_inicial = hoy - timedelta(days=3)  # Viernes - 3 días = Martes
        fecha_final = hoy - timedelta(days=1)    # Viernes - 1 día = Jueves
    else:  # Fin de semana, domingo (5) y sábado (6)
        fecha_inicial = hoy - timedelta(days=2)  # Domingo - 2 días = Viernes
        fecha_final = hoy - timedelta(days=1)    # Domingo - 1 día = Sábado

    # Formatear fechas como 'dd/mm/yyyy'
    fecha_inicial_str = fecha_inicial.strftime("%d/%m/%Y")
    fecha_final_str = fecha_final.strftime("%d/%m/%Y")
    print("Fecha inicial:", fecha_inicial)
    print("Fecha final:", fecha_final)
    return fecha_inicial_str, fecha_final_str
    
def main2():
    fecha_inicial, fecha_final = obtener_fechas()
    ejecutar_consulta(fecha_inicial, fecha_final)
    print('ejecutando script operacion desposte a facturar')
    
if __name__ == "__main__":
    main2()
