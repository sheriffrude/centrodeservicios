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
      -- RENDIMIENTOS PORCINOS GRANJAS

	USE DHC;
    SET @Fecha_inicial = '{}';
	SET @Fecha_Final = '{}';

	-- Convertimos las fechas de varchar a date
	SET @Fecha_inicial_t = STR_TO_DATE(@Fecha_inicial, '%d/%m/%Y');
	SET @Fecha_Final_t = STR_TO_DATE(@Fecha_Final, '%d/%m/%Y');

	DROP TEMPORARY TABLE IF EXISTS t_homologacion_granjas;
    DROP TEMPORARY TABLE IF EXISTS t_rendimientos_porcinos;
    DROP TEMPORARY TABLE IF EXISTS t_trazabilidad_oinc;
    DROP TEMPORARY TABLE IF EXISTS t_rendimientos_porcinos_granjas;

    CREATE TEMPORARY TABLE t_homologacion_granjas LIKE dhc.homologacion_granjas;

    INSERT INTO t_homologacion_granjas
    SELECT * FROM dhc.homologacion_granjas;
    
    CREATE TEMPORARY TABLE t_trazabilidad_oinc LIKE oinc.trazabilidad_oinc;
    
	INSERT INTO t_trazabilidad_oinc
    SELECT * FROM oinc.trazabilidad_oinc WHERE F_Beneficio BETWEEN @Fecha_inicial_t AND @Fecha_Final_t;
    
    CREATE TEMPORARY TABLE t_rendimientos_porcinos(
		tiquete int,
		id_orden int ,
		descripcion_exp varchar(80),
		tercero varchar(80),
		peso_pie decimal(5,2),
		peso_caliente decimal(5,2),
		rendimiento decimal(10,2),
		peso_frio decimal(5,2),
		rendimiento_cf decimal(10,2),
		guia int,
		fecha_despacho date,
		fecha_sacrificio date,
		mm_magro tinyint,
		porcentaje_magro decimal(5,2),
		clasificacion_magro varchar(12),
		profundidad_lomo decimal(5,2),
        Lote VARCHAR(500),
		Granja VARCHAR(500),
        id_granja INT,
        FRIGORIFICO VARCHAR(50)
    );

    INSERT INTO t_rendimientos_porcinos(tiquete,id_orden,descripcion_exp,tercero,peso_pie,peso_caliente,
		rendimiento,peso_frio,rendimiento_cf,guia,fecha_despacho,fecha_sacrificio,mm_magro,porcentaje_magro,
		clasificacion_magro,profundidad_lomo,Lote,Granja,id_granja,FRIGORIFICO)
    SELECT
		A.tiquete,
        A.id_orden,
        A.descripcion_exp,
        A.tercero,
        A.peso_pie,
        A.peso_caliente,
		A.rendimiento,
        A.peso_frio,
        A.rendimiento_cf,
        A.guia,
        A.fecha_despacho,
        A.fecha_sacrificio,
        A.mm_magro,
        A.porcentaje_magro,
		A.clasificacion_magro,
        A.profundidad_lomo,
        B.ConsecutivoDespacho AS Lote,
        UPPER(B.granja) AS Granja,
        C.id AS id_granja,
        'FRIGOTUN' AS FRIGORIFICO
	FROM frigotun.rendimientos_porcinos A 
	JOIN frigotun.ordenes_porcinos B ON A.id_orden = B.id_orden
    JOIN FRIGOTUN.granjas C ON B.Granja = C.nombre_granja
    WHERE A.fecha_sacrificio BETWEEN @Fecha_inicial_t AND @Fecha_Final_t
	AND B.fecha BETWEEN @Fecha_inicial_t AND @Fecha_Final_t;
    
-- SELECT * FROM t_rendimientos_porcinos;
    
-- SELECT * FROM frigotun.rendimientos_porcinos;
-- SELECT * FROM frigotun.ordenes_porcinos;
     CREATE TEMPORARY TABLE t_rendimientos_porcinos_granjas(
		tiquete VARCHAR(500),
		id_orden VARCHAR(500) ,
		descripcion_exp varchar(80),
		tercero varchar(80),
		peso_pie decimal(5,2),
		peso_caliente decimal(5,2),
		rendimiento decimal(10,2),
		peso_frio decimal(5,2),
		rendimiento_cf decimal(10,2),
		guia VARCHAR(500),
		fecha_despacho date,
		fecha_sacrificio date,
		mm_magro decimal(5,2),
		porcentaje_magro decimal(5,2),
		clasificacion_magro varchar(12),
		profundidad_lomo decimal(5,2),
        Lote VARCHAR(500),
		Codigo_granja VARCHAR(100),
		Granja VARCHAR(100),
		Nit_asociado VARCHAR(100),
		Asociado VARCHAR(100),
		Grupo_Granja VARCHAR(100),
        FRIGORIFICO VARCHAR(50)
		);

	INSERT INTO t_rendimientos_porcinos_granjas (tiquete,id_orden,descripcion_exp,tercero,peso_pie,peso_caliente,
	rendimiento,peso_frio,rendimiento_cf,guia,fecha_despacho,fecha_sacrificio,mm_magro,porcentaje_magro,
	clasificacion_magro,profundidad_lomo,Lote,Codigo_granja,Granja,Nit_asociado,Asociado,Grupo_Granja,FRIGORIFICO)
	SELECT
    A.tiquete,
	A.id_orden,
	UPPER(A.descripcion_exp) AS descripcion_exp,
	UPPER(A.tercero) AS tercero,
	A.peso_pie,
	A.peso_caliente,
	A.rendimiento,
	A.peso_frio,
	A.rendimiento_cf,
	A.guia,
	A.fecha_despacho,
	A.fecha_sacrificio,
	A.mm_magro,
	A.porcentaje_magro,
	UPPER(A.clasificacion_magro) AS clasificacion_magro,
	A.profundidad_lomo,
    A.Lote,
    B.ID AS Codigo_granja,
    UPPER(C.GRANJAS) AS Granja,
    D.CODIGO AS Nit_asociado,
    UPPER(E.RAZON_SOCIAL) AS Asociado,
    UPPER(F.GRUPO_ASOCIADO) AS Grupo_Granja,
    A.FRIGORIFICO
	FROM t_rendimientos_porcinos A
    JOIN DHC.homologacion_granjas B ON A.id_granja = B.ID_FRIGOTUN
    JOIN DHC.granjas C ON B.ID = C.ID
    JOIN DHC.nombre_comercial D ON C.NOMBRE_COMERCIAL = D.ID
    JOIN DHC.RAZON_SOCIAL E ON C.RAZON_SOCIAL = E.ID
    JOIN DHC.GRUPO_ASOCIADO F ON C.GRUPO_ASOCIADO = F.ID;
	
    INSERT INTO t_rendimientos_porcinos_granjas (
    tiquete,
    id_orden,
    descripcion_exp,
    tercero,
    peso_pie,
    peso_caliente,
    rendimiento,
    peso_frio,
    rendimiento_cf,
    guia,
    fecha_despacho,
    fecha_sacrificio,
    mm_magro,
    porcentaje_magro,
    clasificacion_magro,
    profundidad_lomo,
    Lote,
    Codigo_granja,
    Granja,
    Nit_asociado,
    Asociado,
    Grupo_Granja,
    FRIGORIFICO
)
SELECT
    A.Lote_Cod_Canal AS tiquete,
    A.Lote_Turn_Bene AS id_orden,
    A.Direccion_Remision AS descripcion_exp,
    A.Proveedor AS tercero,
    A.PROM_Peso_Pie AS peso_pie,
    A.C_Caliente AS peso_caliente,
    REPLACE(A.RTO_PCC, ',', '.') AS rendimiento,
    A.C_Fria AS peso_frio,
    REPLACE(A.RTO_PCF, ',', '.') AS rendimiento_cf,
    A.Remision AS guia,
    A.F_Remision AS fecha_despacho,
    A.F_Beneficio AS fecha_sacrificio,
    A.Grasa_Dorsal AS mm_magro,
    REPLACE(A.Magro, ',', '.') AS porcentaje_magro, -- Reemplazar comas por puntos
    A.Clasificacion AS clasificacion_magro,
    A.Grasa_Dorsal AS profundidad_lomo,
    A.Lote AS Lote,
    B.ID AS Codigo_granja,
    UPPER(C.GRANJAS) AS Granja,
    D.CODIGO AS Nit_asociado,
    UPPER(E.RAZON_SOCIAL) AS Asociado,
    UPPER(F.GRUPO_ASOCIADO) AS Grupo_Granja,
    'OINC' AS FRIGORIFICO
FROM
    t_trazabilidad_oinc A
JOIN
    DHC.homologacion_granjas B ON A.Granja = B.NOMBRE_OINC
JOIN
    DHC.granjas C ON B.ID = C.ID
JOIN
    DHC.nombre_comercial D ON C.NOMBRE_COMERCIAL = D.ID
JOIN
    DHC.RAZON_SOCIAL E ON C.RAZON_SOCIAL = E.ID
JOIN
    DHC.GRUPO_ASOCIADO F ON C.GRUPO_ASOCIADO = F.ID;


	-- SELECT * FROM t_rendimientos_porcinos_granjas;
	-- SELECT * FROM t_rendimientos_porcinos_granjas WHERE FRIGORIFICO = 'OINC' AND descripcion_exp LIKE '%DESPOSTE CERCAFE%';
    -- SELECT * FROM t_rendimientos_porcinos_granjas WHERE FRIGORIFICO = 'FRIGOTUN' AND descripcion_exp LIKE '%DESPOSTE%';
    
    INSERT INTO B_CA.rendimientos_porcinos_granjas(tiquete,id_orden,descripcion_exp,tercero,peso_pie,peso_caliente,
	rendimiento,peso_frio,rendimiento_cf,guia,fecha_despacho,fecha_sacrificio,mm_magro,porcentaje_magro,
	clasificacion_magro,profundidad_lomo,Lote,Codigo_granja,Granja,Nit_asociado,Asociado,Grupo_Granja,FRIGORIFICO)
	SELECT
    tiquete,id_orden,descripcion_exp,tercero,peso_pie,peso_caliente,
	rendimiento,peso_frio,rendimiento_cf,guia,fecha_despacho,fecha_sacrificio,mm_magro,porcentaje_magro,
	clasificacion_magro,profundidad_lomo,Lote,Codigo_granja,Granja,Nit_asociado,Asociado,Grupo_Granja,FRIGORIFICO
    FROM t_rendimientos_porcinos_granjas;
    
	DROP TEMPORARY TABLE IF EXISTS t_homologacion_granjas;
    DROP TEMPORARY TABLE IF EXISTS t_rendimientos_porcinos;
    DROP TEMPORARY TABLE IF EXISTS t_trazabilidad_oinc;
    DROP TEMPORARY TABLE IF EXISTS t_rendimientos_porcinos_granjas;
    """.format(fecha_inicial, fecha_final)
    print("Consulta SQL:")
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
    
def main():
    fecha_inicial, fecha_final = obtener_fechas()
    ejecutar_consulta(fecha_inicial, fecha_final)
    print('ejecutando script RENDIMIENTOS PORCINOS GRANJAS')
    
if __name__ == "__main__":
    main()
