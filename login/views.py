from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, connections
import pandas as pd
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from django.http import JsonResponse
import openpyxl
from django.contrib import messages
from django.template.loader import render_to_string
import xlsxwriter
import pdfkit
from django.template import loader
from django.http import FileResponse
import logging
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.cache import never_cache

#---Define La Vista del login-----
def signin(request):
   if request.method == 'GET' :
        return render(request, 'login.html',{
            'form' : AuthenticationForm
            })
   else:
       user = authenticate( username=request.POST['username'], 
                           password=request.POST['password'])
       if user is None or not user.is_active:
            # Usuario no válido o cuenta desactivada
            return render(request, 'login.html', {
                'form': AuthenticationForm,
                'error': 'Usuario o contraseña incorrectos'
    })
       else:
           login (request, user)
           return redirect('home')

#---Define La Vista Principal----
@never_cache
@login_required
def home(request):
    return render(request, 'home.html')


#---Define La Vista del logout-----
@never_cache
@login_required
def exit(request):
    logout(request)
    return redirect('/')
#---Define La Vista del modulo cadena de abastecimiento-----
@never_cache
@login_required
def cadenaabastecimiento(request):
   return render(request, 'cadenaabastecimiento.html')

#---Define La Vistas del modulo Gestion Comercial-----
@never_cache
@login_required
def gestioncomercial(request):
   return render(request, 'gestioncomercial.html')

#---Define La Vistas del modulo Gestion Humana-----

@never_cache
@login_required
def gestionhumana(request):
   return render(request, 'gestionhumana.html')
#---Define La Vistas del modulo Gestion Tecnica-----

@never_cache
@login_required
def gestiontecnica(request):
   return render(request, 'gestiontecnica.html')

#---Define La Vistas del modulo Gestion ALIMENTO BALANCEADO-----

@never_cache
@login_required
def gestionalbal(request):
   return render(request, 'gestionalimentobal.html')
#---Define La Vistas del modulo Gestion CALIDAD-----

@never_cache
@login_required
def calidad(request):
   return render(request, 'calidad.html')
#---Define La Vistas del modulo Gestion TI-----

@never_cache
@login_required
def ti(request):
   return render(request, 'tecnologia.html')

#---Define La Vista del modulo financiera-----
@never_cache
@login_required
def financiera(request):
   return render(request, 'financiera.html')

#---Define La Vista del modulo reportes-----
@never_cache
@login_required
def repoprove(request):
   return render(request, 'report_prov.html')

@never_cache
@login_required
def carexitosa(request):
   return render(request, 'carga_exitosa.html')

@never_cache
@login_required
def repofina(request):
   return render(request, 'report_finan.html')
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#---------------CADENA DE ABASTECIMIENTO --------------------------------------------------------------
#------ vista para el cargue de excel en cadena de abastecimiento--------------------------------------
@never_cache
@login_required
def cargar_excel_cadenaabastecimiento(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    granja, mes, semana, cantidad_cerdos = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla compromiso_mes
                    cursor.execute(
                        'INSERT INTO compromiso_mes (granja, mes, semana, cantidad_cerdos) VALUES (%s, %s, %s, %s)',
                        (granja.value, mes.value, semana.value, cantidad_cerdos.value)
                    )
            messages.success(request, 'Carga de datos en VENTAS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')

#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------------------ CARGA DE GESTION COMERCIAL --------------------------------------------------------
#------------------------------------------------------------------------------------------------------
#------ vista para el cargue de excel en clientes activos----------------------------------------------
@never_cache
@login_required
def cargar_excel_clientesactivos(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gc
            with connections['B_GC'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_CORTE, CANTIDAD_CLIENTES, ZONA_CLIENTE, KG_FACTURADOS,DINERO_APORTADO,ESTADO_CLIENTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla compromiso_mes
                    cursor.execute(
                        'INSERT INTO CLIENTES_ACTIVOS (FECHA_CORTE,CANTIDAD_CLIENTES,ZONA_CLIENTE,KG_FACTURADOS,DINERO_APORTADO,ESTADO_CLIENTE) VALUES (%s, %s, %s, %s,%s,%s)',
                        (FECHA_CORTE.value, CANTIDAD_CLIENTES.value, ZONA_CLIENTE.value, KG_FACTURADOS.value,DINERO_APORTADO.value,ESTADO_CLIENTE.value)
                    )
            messages.success(request, 'Carga de datos en VENTAS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en ventas---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_ventas(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gc
            with connections['B_GC'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_CORTE,LINEA_NEGOCIO,PRESUPUESTO_UNIDADES,PRESUPUESTO_KG,UNIDADES_VENDIDAS,KG_VENDIDO,VALOR_VENTA,PRESUPUESTO_VENTA= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO VENTAS (FECHA_CORTE,LINEA_NEGOCIO,PRESUPUESTO_UNIDADES,PRESUPUESTO_KG,UNIDADES_VENDIDAS,KG_VENDIDO,VALOR_VENTA,PRESUPUESTO_VENTA) VALUES (%s, %s, %s, %s,%s,%s,%s,%s)',
                        (FECHA_CORTE.value, LINEA_NEGOCIO.value, PRESUPUESTO_UNIDADES.value, PRESUPUESTO_KG.value,UNIDADES_VENDIDAS.value,KG_VENDIDO.value,VALOR_VENTA.value,PRESUPUESTO_VENTA.value)
                    )
            messages.success(request, 'Carga de datos en VENTAS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
# ----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#--------------------------------- CARGA DE GESTION HUMANA -------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#------ vista para el cargue de excel en NOMINA---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_nomina(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_CORTE,AREA,CENTRO_COSTO,NUM_COLABORADORES,COSTO_PROV= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO NOMINA (FECHA_CORTE,AREA,CENTRO_COSTO,NUM_COLABORADORES,COSTO_PROV) VALUES (%s, %s, %s, %s,%s)',
                        (FECHA_CORTE.value, AREA.value, CENTRO_COSTO.value, NUM_COLABORADORES.value,COSTO_PROV.value)
                    )
                messages.success(request, 'Carga de datos en NOMINA exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: archivo diferente a la plantilla')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en PROMOCIONES---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_promo(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_CORTE,NOMBRE,ANTIGUO_CARGO,NUEVO_CARGO= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO PROMOCIONES (FECHA_CORTE,NOMBRE,ANTIGUO_CARGO,NUEVO_CARGO) VALUES (%s, %s, %s, %s)',
                        (FECHA_CORTE.value, NOMBRE.value, ANTIGUO_CARGO.value, NUEVO_CARGO.value)
                    )
            messages.success(request, 'Carga de datos en PROMOCIONES exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en PROCESOS DE SELECCION---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_prosele(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    NUM_REQUISICION,FECHA_APROBACION,AREA_CENTRO_COSTO,FECHA_RETIRO,NOMBRE_RETIRADO,CARGO,CUBRIMIENTO_ESPERADO_DIAS,NOMBRE_CANDIDATO,TIPO_INGRESO_PROMO_INT,EXAMEN_MEDICO,VISITA_DOMICILIARIA,POLIGRAFIA,FECHA_INGRESO= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROCESO_SELECCION
                    cursor.execute(
                        'INSERT INTO PROCESO_SELECCION (NUM_REQUISICION,FECHA_APROBACION,AREA_CENTRO_COSTO,FECHA_RETIRO,NOMBRE_RETIRADO,CARGO,CUBRIMIENTO_ESPERADO_DIAS,NOMBRE_CANDIDATO,TIPO_INGRESO_PROMO_INT,EXAMEN_MEDICO,VISITA_DOMICILIARIA,POLIGRAFIA,FECHA_INGRESO) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (NUM_REQUISICION.value,FECHA_APROBACION.value,AREA_CENTRO_COSTO.value,FECHA_RETIRO.value,NOMBRE_RETIRADO.value,CARGO.value,CUBRIMIENTO_ESPERADO_DIAS.value,NOMBRE_CANDIDATO.value,TIPO_INGRESO_PROMO_INT.value,EXAMEN_MEDICO.value,VISITA_DOMICILIARIA.value,POLIGRAFIA.value,FECHA_INGRESO.value)
                    )
            messages.success(request, 'Carga de datos en PROCESO SELECCION exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en RETENCION ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_retencion(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_REPORTE,INDICADOR_RETENCION,OBSERVACIONES= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla RETENCION
                    cursor.execute(
                        'INSERT INTO RETENCION (FECHA_REPORTE,INDICADOR_RETENCION,OBSERVACIONES) VALUES (%s, %s, %s)',
                        (FECHA_REPORTE.value,INDICADOR_RETENCION.value,OBSERVACIONES.value)
                    )
            messages.success(request, 'Carga de datos en RETENCION exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en ROTACION ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_rotacion(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_REPORTE,INDICADOR_ROTACION,OBSERVACIONES= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO ROTACION (FECHA_REPORTE,INDICADOR_ROTACION,OBSERVACIONES) VALUES (%s, %s, %s)',
                        (FECHA_REPORTE.value, INDICADOR_ROTACION.value, OBSERVACIONES.value)
                    )
                messages.success(request, 'Carga de datos en ROTACION exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en SST DIAGNOSTICOS INDICADORES ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_sstdiag(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    FECHA_CORTE,SEDE,DIAGNOSTICO,CANTIDAD,OBSERVACION= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla SST_DIAGNOSTICOS_INDICADORES
                    cursor.execute(
                        'INSERT INTO SST_DIAGNOSTICOS_INDICADORES (FECHA_CORTE,SEDE,DIAGNOSTICO,CANTIDAD,OBSERVACION) VALUES (%s, %s, %s, %s, %s)',
                        (FECHA_CORTE.value, SEDE.value, DIAGNOSTICO.value,CANTIDAD.value,OBSERVACION.value)
                    )
                messages.success(request, 'Carga de datos en SST DIAGNOSTICOS INDICADORES exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en SST INDICADORES ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_sstindi(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                   
                    FECHA_CORTE,SEDE,CANTIDAD_PEG,DIAS_INCAPACIDAD_PEL,CANTIDAD_PAT,PRORROGAS,DIAS_INCAPACIDAD_PAT,LICENCIA_MATERNIDAD,DIAS_LICENCIA_MAT,LICENCIA_PATERNIDAD,DIAS_LICENCIA_PAT,COSTO_INCAPACIDAD,OBSERVACIONES= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO SST_INDICADORES (FECHA_CORTE,SEDE,CANTIDAD_PEG,DIAS_INCAPACIDAD_PEL,CANTIDAD_PAT,PRORROGAS,DIAS_INCAPACIDAD_PAT,LICENCIA_MATERNIDAD,DIAS_LICENCIA_MAT,LICENCIA_PATERNIDAD,DIAS_LICENCIA_PAT,COSTO_INCAPACIDAD,OBSERVACIONES) VALUES (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s)',
                        (FECHA_CORTE.value,SEDE.value,CANTIDAD_PEG.value,DIAS_INCAPACIDAD_PEL.value,CANTIDAD_PAT.value,PRORROGAS.value,DIAS_INCAPACIDAD_PAT.value,LICENCIA_MATERNIDAD.value,DIAS_LICENCIA_MAT.value,LICENCIA_PATERNIDAD.value,DIAS_LICENCIA_PAT.value,COSTO_INCAPACIDAD.value,OBSERVACIONES.value)
                    )
                messages.success(request, 'Carga de datos en SST INDICADORES exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en SST SEVERIDAD Y FRECUENCIA ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_sstseveridad(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                   
                    FECHA_CORTE,CANT_ENF_GENERAL,CANT_ACC_TRABAJO,NUM_EMPLEADOS,FREC_ACC,DIAS_INC_GENERAL,DIAS_INC_ACC,SEV_ACC,INCID_ENF_LAB,PORC_AUSENTISMO= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla SST_SEVERIDAD_Y_FRECUENCIA
                    cursor.execute(
                        'INSERT INTO SST_SEVERIDAD_Y_FRECUENCIA (FECHA_CORTE,CANT_ENF_GENERAL,CANT_ACC_TRABAJO,NUM_EMPLEADOS,FREC_ACC,DIAS_INC_GENERAL,DIAS_INC_ACC,SEV_ACC,INCID_ENF_LAB,PORC_AUSENTISMO) VALUES (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s)',
                        (FECHA_CORTE.value,CANT_ENF_GENERAL.value,CANT_ACC_TRABAJO.value,NUM_EMPLEADOS.value,FREC_ACC.value,DIAS_INC_GENERAL.value,DIAS_INC_ACC.value,SEV_ACC.value,INCID_ENF_LAB.value,PORC_AUSENTISMO.value)
                    )
                messages.success(request, 'Carga de datos en SST SEVERIDAD Y FRECUENCIA exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
# ----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#--------------------------------- CARGA DE GESTION TECNICA -------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#------ vista para el cargue de excel en Abastecimiento Hembras ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_abashem(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                   
                    GRANJA,CANTIDAD_ENTREGADA,PORCENTAJE_CUMPLIMIENTO,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla SST_SEVERIDAD_Y_FRECUENCIA
                    cursor.execute(
                        'INSERT INTO ABASTECIMIENTO_HEMBRAS (GRANJA,CANTIDAD_ENTREGADA,PORCENTAJE_CUMPLIMIENTO,FECHA_CORTE) VALUES (%s, %s, %s, %s)',
                        (GRANJA.value,CANTIDAD_ENTREGADA.value,PORCENTAJE_CUMPLIMIENTO.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en SST SEVERIDAD Y FRECUENCIA exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')

#------ vista para el cargue de excel en FORTUITOS ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_fortuitos(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                  
                    FECHA_CORTE,GRANJA,CANTIDAD,ESTADO,NUMERO_ORDEN,CANTIDAD_MUERTE_TRANSPORTE,CANTIDAD_MUERTE_REPOSO,CANTIDAD_RETOMAS,NUMERO_TIQUETE,REGISTRO_FOTO,DESTINO= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla SST_SEVERIDAD_Y_FRECUENCIA
                    cursor.execute(
                        'INSERT INTO FORTUITOS (FECHA_CORTE,GRANJA,CANTIDAD,ESTADO,NUMERO_ORDEN,CANTIDAD_MUERTE_TRANSPORTE,CANTIDAD_MUERTE_REPOSO,CANTIDAD_RETOMAS,NUMERO_TIQUETE,REGISTRO_FOTO,DESTINO) VALUES (%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s)',
                        (FECHA_CORTE.value,GRANJA.value,CANTIDAD.value,ESTADO.value,NUMERO_ORDEN.value,CANTIDAD_MUERTE_TRANSPORTE.value,CANTIDAD_MUERTE_REPOSO.value,CANTIDAD_RETOMAS.value,NUMERO_TIQUETE.value,REGISTRO_FOTO.value,DESTINO.value)
                    )
                messages.success(request, 'Carga de datos en FORTUITOS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en KG VENDIDOS HEMBRA ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_kgvend(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                  
                    GRANJA,KG_V_H_A,ASOCIADO,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla KG_VENDIDOS_HEMBRA
                    cursor.execute(
                        'INSERT INTO KG_VENDIDOS_HEMBRA (GRANJA,KG_V_H_A,ASOCIADO,FECHA_CORTE) VALUES (%s, %s, %s, %s)',
                        (GRANJA.value,KG_V_H_A.value,ASOCIADO.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en KG VENDIDOS HEMBRA exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en PESO FINAL CONVERSION ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_pesofinconver(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                  
                    GRANJA,PESO,META_PESO,CONVERSION_META,CONVERSION,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PESO_FINAL_CONVERSION
                    cursor.execute(
                        'INSERT INTO PESO_FINAL_CONVERSION (GRANJA,PESO,META_PESO,CONVERSION_META,CONVERSION,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s)',
                        (GRANJA.value,PESO.value,META_PESO.value,CONVERSION_META.value,CONVERSION.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en PESO FINAL CONVERSION exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en PROYECCION HEMBRAS ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_proyhem(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    
                    PARTOS,TASA_PARTOS,CUMPLIMIENTO_PROYECTADO,CUMPLIMIENTO_REAL,AÑO_SERVICIO,OBSERVACIONES,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROYECCION_HEMBRAS
                    cursor.execute(
                        'INSERT INTO PROYECCION_HEMBRAS (PARTOS,TASA_PARTOS,CUMPLIMIENTO_PROYECTADO,CUMPLIMIENTO_REAL,AÑO_SERVICIO,OBSERVACIONES,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (PARTOS.value,TASA_PARTOS.value,CUMPLIMIENTO_PROYECTADO.value,CUMPLIMIENTO_REAL.value,AÑO_SERVICIO.value,OBSERVACIONES.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en PROYECCION HEMBRAS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en TECNICA CIA ---------------------------------------------------------------
@never_cache
@login_required
def cargar_excel_tecnicacia(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    
                    LINEA_GENETICA,CANTIDAD_MACHOS,PORCENTAJE_DISTRIBUCION_MACHOS,CANTIDAD_DESECHADO,PORCENTAJE_DESCECHADO,DOSIS_PRODUCIDAS,DOSIS_VENDIDAS,PROMEDIO_MORFOLOGIA,OBSERVACION,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla TECNICA_CIA
                    cursor.execute(
                        'INSERT INTO TECNICA_CIA (LINEA_GENETICA,CANTIDAD_MACHOS,PORCENTAJE_DISTRIBUCION_MACHOS,CANTIDAD_DESECHADO,PORCENTAJE_DESCECHADO,DOSIS_PRODUCIDAS,DOSIS_VENDIDAS,PROMEDIO_MORFOLOGIA,OBSERVACION,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (LINEA_GENETICA.value,CANTIDAD_MACHOS.value,PORCENTAJE_DISTRIBUCION_MACHOS.value,CANTIDAD_DESECHADO.value,PORCENTAJE_DESCECHADO.value,DOSIS_PRODUCIDAS.value,DOSIS_VENDIDAS.value,PROMEDIO_MORFOLOGIA.value,OBSERVACION.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en TECNICA CIA exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
# ----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#--------------------------------- CARGA DE GESTION ALIMENTO BALANCEADO -----------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-------- vista para el cargue de excel en Planta Alimento Balanceado -----------------------------------------------
@never_cache
@login_required
def cargar_excel_alibal(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_gt
            with connections['B_GAB'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    
                    TONELADAS_PRODUCIDAS_MES,TONELADAS_PRESUPUESTO_MES,PORCENTAJE_VARIACION_MES,PORCENTAJE_CUMPLIMIENTO_MES,OBSERVACION_VARIACION,PORCENTAJE_BULTO_MES,PORCENTAJE_GRANEL_MES,SACK_OFF,PORCENTAJE_OTIF,OBSERVACION_OTIF,PRESUPUESTO_MO_CIF,MO_CIF,TIEMPO_MUERTO,COSTO_TIEMPO_MUERTO,OBSERVACION_TIEMPO_MUERTO,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PLANTA_ALIMENTOS_BALANCEADOS
                    cursor.execute(
                        'INSERT INTO PLANTA_ALIMENTOS_BALANCEADOS (TONELADAS_PRODUCIDAS_MES,TONELADAS_PRESUPUESTO_MES,PORCENTAJE_VARIACION_MES,PORCENTAJE_CUMPLIMIENTO_MES,OBSERVACION_VARIACION,PORCENTAJE_BULTO_MES,PORCENTAJE_GRANEL_MES,SACK_OFF,PORCENTAJE_OTIF,OBSERVACION_OTIF,PRESUPUESTO_MO_CIF,MO_CIF,TIEMPO_MUERTO,COSTO_TIEMPO_MUERTO,OBSERVACION_TIEMPO_MUERTO,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (TONELADAS_PRODUCIDAS_MES.value,TONELADAS_PRESUPUESTO_MES.value,PORCENTAJE_VARIACION_MES.value,PORCENTAJE_CUMPLIMIENTO_MES.value,OBSERVACION_VARIACION.value,PORCENTAJE_BULTO_MES.value,PORCENTAJE_GRANEL_MES.value,SACK_OFF.value,PORCENTAJE_OTIF.value,OBSERVACION_OTIF.value,PRESUPUESTO_MO_CIF.value,MO_CIF.value,TIEMPO_MUERTO.value,COSTO_TIEMPO_MUERTO.value,OBSERVACION_TIEMPO_MUERTO.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en PLANTA ALIMENTOS BALANCEADOS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
# ----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#--------------------------------- CARGA DE   CALIDAD ------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-------- vista para el cargue de excel en Avance Proceso --------------------------------------------------------
@never_cache
@login_required
def cargar_excel_avancepro(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_c
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    TIPO,PROCESO,DETALLE_PROCESO,AVANCE,META,FECHA_CORTE,_= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla AVANCE_PROCESO
                    cursor.execute(
                        'INSERT INTO AVANCE_PROCESO (TIPO,PROCESO,DETALLE_PROCESO,AVANCE,META,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s)',
                        (TIPO.value,PROCESO.value,DETALLE_PROCESO.value,AVANCE.value,META.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en AVANCE PROCESO exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#-------- vista para el cargue de excel en Calidad Planta --------------------------------------------------------
@never_cache
@login_required
def cargar_excel_calidadpl(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_c
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    PORCENTAJE_DESVIACIONES_CALIDAD,TONELADAS_REPROCESADAS,TONELADAS_LIBERADAS_CONCESION,PORCENTAJE_RETENCION,PORCENTAJE_MEZCLA,PORCENTAJE_DURABILIDAD,PORCENTAJE_FINOS,PORCENTAJE_FORMULACION,CUMPLIMIENTO_BPM,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla CALIDAD_PLANTA
                    cursor.execute(
                        'INSERT INTO CALIDAD_PLANTA (PORCENTAJE_DESVIACIONES_CALIDAD,TONELADAS_REPROCESADAS,TONELADAS_LIBERADAS_CONCESION,PORCENTAJE_RETENCION,PORCENTAJE_MEZCLA,PORCENTAJE_DURABILIDAD,PORCENTAJE_FINOS,PORCENTAJE_FORMULACION,CUMPLIMIENTO_BPM,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (PORCENTAJE_DESVIACIONES_CALIDAD.value,TONELADAS_REPROCESADAS.value,TONELADAS_LIBERADAS_CONCESION.value,PORCENTAJE_RETENCION.value,PORCENTAJE_MEZCLA.value,PORCENTAJE_DURABILIDAD.value,PORCENTAJE_FINOS.value,PORCENTAJE_FORMULACION.value,CUMPLIMIENTO_BPM.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en CALIDAD PLANTA exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')

#-------- vista para el cargue de excel en CAUSAS DESVIACIONES --------------------------------------------------------
@never_cache
@login_required
def cargar_excel_causasdes(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_c
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    CAUSA,PLAN_ACCION,TON_REPROCESADAS,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla CAUSAS_DESVIACIONES
                    cursor.execute(
                        'INSERT INTO CAUSAS_DESVIACIONES (CAUSA,PLAN_ACCION,TON_REPROCESADAS,FECHA_CORTE) VALUES (%s, %s, %s, %s)',
                        (CAUSA.value,PLAN_ACCION.value,TON_REPROCESADAS.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en CAUSAS_DESVIACIONES exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#-------- vista para el cargue de excel en PQRSF --------------------------------------------------------
@never_cache
@login_required
def cargar_excel_pqrsf(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_c
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    PROCESO,TIPO,ESTADO_MOTIVO,CANTIDAD,CATEGORIA,TIEMPO_RESPUESTA,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PQRSF
                    cursor.execute(
                        'INSERT INTO PQRSF (PROCESO,TIPO,ESTADO_MOTIVO,CANTIDAD,CATEGORIA,TIEMPO_RESPUESTA,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (PROCESO.value,TIPO.value,ESTADO_MOTIVO.value,CANTIDAD.value,CATEGORIA.value,TIEMPO_RESPUESTA.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en PQRSF exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
# ----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#--------------------------------- CARGA DE   T.I ------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-------- vista para el cargue de excel en Transformacion Digital --------------------------------------------------------
@never_cache
@login_required
def cargar_excel_transfordig(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

             # Abre una conexión a la base de datos b_ti
            with connections['B_TI'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    PROYECTO_ESTRATEGICO,CAPA_ARQUITECTURA,NOMBRE_PROYECTO,PESO_CAPA,PESO_PROYECTO_ESTRATEGICO,PORCENTAJE_AVANCE,PORCENTAJE_META,PORCENTAJE_META_PROYECTO,TAREAS_PROYECTO,TAREAS_PLANEADAS,TAREAS_EJECUTADAS,COSTO_PLANEADO,COSTO_EJECUTADO,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla TRANSFORMACION_DIGITAL
                    cursor.execute(
                        'INSERT INTO TRANSFORMACION_DIGITAL (PROYECTO_ESTRATEGICO,CAPA_ARQUITECTURA,NOMBRE_PROYECTO,PESO_CAPA,PESO_PROYECTO_ESTRATEGICO,PORCENTAJE_AVANCE,PORCENTAJE_META,PORCENTAJE_META_PROYECTO,TAREAS_PROYECTO,TAREAS_PLANEADAS,TAREAS_EJECUTADAS,COSTO_PLANEADO,COSTO_EJECUTADO,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s)',
                        (PROYECTO_ESTRATEGICO.value,CAPA_ARQUITECTURA.value,NOMBRE_PROYECTO.value,PESO_CAPA.value,PESO_PROYECTO_ESTRATEGICO.value,PORCENTAJE_AVANCE.value,PORCENTAJE_META.value,PORCENTAJE_META_PROYECTO.value,TAREAS_PROYECTO.value,TAREAS_PLANEADAS.value,TAREAS_EJECUTADAS.value,COSTO_PLANEADO.value,COSTO_EJECUTADO.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en TRANSFORMACION_DIGITAL exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#-------- vista para el cargue de excel en Indicadores Economicos --------------------------------------------------------
@never_cache
@login_required
def cargar_excel_inideco(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active

             # Abre una conexión a la base de datos b_ti
            with connections['B_TI'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    INDICADOR,VALOR,FUENTE,LINK,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla TRANSFORMACION_DIGITAL
                    cursor.execute(
                        'INSERT INTO INDICADORES_ECONOMICOS (INDICADOR,VALOR,FUENTE,LINK,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s)',
                        (INDICADOR.value,VALOR.value,FUENTE.value,LINK.value,FECHA_CORTE.value)
                    )
                messages.success(request, 'Carga de datos en Indicadores Economicos exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
















@never_cache
@login_required
def reproved(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('SELECT granja, mes, semana, cantidad_cerdos FROM compromiso_mes')
        compromisos = cursor.fetchall()

    data = [{'granja': granja, 'mes': mes, 'semana': semana, 'cantidad_cerdos': cantidad_cerdos} for granja, mes, semana, cantidad_cerdos in compromisos]

    response = JsonResponse({'data': data})
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    
    return response

logger = logging.getLogger(__name__)


@never_cache
def repfinan(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
   
    
    with connections['B_GAF'].cursor() as cursor:
        cursor.execute('''
            SELECT Fecha_transformacion,Unidades,Peso_canal_fria,Consecutivo_Cercafe,Codigo_granja,Remision,Valor,Cliente,Planta_Beneficio,Granja,Nit_asociado,Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado,Valor_kilo
            FROM B_GAF.OPERACION_DESPOSTE
            WHERE Fecha_transformacion BETWEEN %s AND %s
        ''', [start_date, end_date])
        compromisos = cursor.fetchall()

    # Loguear los datos recuperados
    logger.info(compromisos)

    data = [{'Fecha_transformacion': Fecha_transformacion, 'Unidades': Unidades, 'Peso_canal_fria': Peso_canal_fria, 'Consecutivo_Cercafe': Consecutivo_Cercafe, 'Codigo_granja': Codigo_granja, 'Remision': Remision, 'Valor': Valor, 'Cliente': Cliente, 'Planta_Beneficio': Planta_Beneficio, 'Granja': Granja, 'Nit_asociado': Nit_asociado, 'Asociado': Asociado, 'Grupo_Granja': Grupo_Granja, 'Retencion': Retencion, 'Valor_a_pagar_asociado': Valor_a_pagar_asociado, 'Valor_kilo': Valor_kilo} for Fecha_transformacion, Unidades, Peso_canal_fria, Consecutivo_Cercafe, Codigo_granja, Remision, Valor, Cliente, Planta_Beneficio, Granja, Nit_asociado, Asociado, Grupo_Granja, Retencion, Valor_a_pagar_asociado, Valor_kilo in compromisos]

    return JsonResponse({'data': data})

@never_cache
def get_filtered_data(start_date, end_date):
    with connections['b_gaf'].cursor() as cursor:
        cursor.execute('''
            SELECT Fecha_transformacion,Unidades,Peso_canal_fria,Consecutivo_Cercafe,Codigo_granja,Remision,Valor,Cliente,Planta_Beneficio,Granja,Nit_asociado,Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado,Valor_kilo
            FROM B_GAF.OPERACION_DESPOSTE
            WHERE Fecha_transformacion BETWEEN %s AND %s
        ''', [start_date, end_date])
        compromisos = cursor.fetchall()

    # Loguear los datos recuperados
    logger.info(compromisos)

    return compromisos
@never_cache
def export_pdf(request):
    # Obtener los datos para exportar
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Obtener los datos filtrados
    compromisos = get_filtered_data(start_date, end_date)

    # Crear el PDF
    html = '<html><body><table><thead><tr><th>Fecha Transformación</th><th>Unidades</th><th>Peso Canal Fría</th><th>Consecutivo Cercafe</th><th>Código Granja</th><th>Remisión</th><th>Valor</th><th>Cliente</th><th>Planta Beneficio</th><th>Granja</th><th>Nit Asociado</th><th>Asociado</th><th>Grupo Granja</th><th>Retención</th><th>Valor a Pagar Asociado</th><th>Valor Kilo</th></tr></thead><tbody>'
    for compromiso in compromisos:
        html += '<tr>'
        for value in compromiso:
            html += '<td>' + str(value) + '</td>'
        html += '</tr>'
    html += '</tbody></table></body></html>'

    # Convertir HTML a PDF
    pdf = pdfkit.from_string(html, False, configuration=pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'))

    # Enviar el PDF como respuesta
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte.pdf"'
    response['Content-Length'] = len(pdf)
    return redirect('financiera')
@never_cache
def export_excel(request):
    # Obtener los datos para exportar
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Obtener los datos filtrados
    compromisos = get_filtered_data(start_date, end_date)

    # Crear el archivo Excel
    workbook = xlsxwriter.Workbook('reporte.xlsx')
    worksheet = workbook.add_worksheet()

    # Escribir los encabezados
    headers = ['Fecha Transformación', 'Unidades', 'Peso Canal Fría', 'Consecutivo_Cercafe', 'Código Granja', 'Remisión', 'Valor', 'Cliente', 'Planta Beneficio', 'Granja', 'Nit Asociado', 'Asociado', 'Grupo Granja', 'Retención', 'Valor a Pagar Asociado', 'Valor Kilo']
    for i, header in enumerate(headers):
        worksheet.write(0, i, header)

    # Escribir los datos
    for row, compromiso in enumerate(compromisos, start=1):
        # Formatear la fecha como un string
        fecha_transformacion = compromiso[0].strftime('%Y-%m-%d')
        # Escribir la fecha en la columna 0
        worksheet.write(row, 0, fecha_transformacion)
        # Escribir los demás valores en las columnas correspondientes
        worksheet.write(row, 1, compromiso[1])  # Unidades
        worksheet.write(row, 2, compromiso[2])  # Peso Canal Fría
        worksheet.write(row, 3, compromiso[3])  # Consecutivo_Cercafe
        worksheet.write(row, 4, compromiso[4])  # Código Granja
        worksheet.write(row, 5, compromiso[5])  # Remisión
        worksheet.write(row, 6, compromiso[6])  # Valor
        worksheet.write(row, 7, compromiso[7])  # Cliente
        worksheet.write(row, 8, compromiso[8])  # Planta Beneficio
        worksheet.write(row, 9, compromiso[9])  # Granja
        worksheet.write(row, 10, compromiso[10])  # Nit Asociado
        worksheet.write(row, 11, compromiso[11])  # Asociado
        worksheet.write(row, 12, compromiso[12])  # Grupo Granja
        worksheet.write(row, 13, compromiso[13])  # Retención
        worksheet.write(row, 14, compromiso[14])  # Valor a Pagar Asociado
        worksheet.write(row, 15, compromiso[15])  # Valor Kilo

    # Cerrar el archivo Excel
    workbook.close()

    # Enviar el archivo Excel como respuesta
    with open('reporte.xlsx', 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte.xlsx"'
        return response


@csrf_protect
def save_changes(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        id = request.POST.get('id')
        newValue = request.POST.get('newValue')

        # Validar los datos
        if not id.isdigit():
            return JsonResponse({'success': False, 'error': 'El ID debe ser un número entero válido'})

        # Realizar la actualización en la base de datos
        try:
            # Actualizar el campo 'Valor Kilo'
            with connections['B_GAF'].cursor() as cursor:
                cursor.execute('''
                    UPDATE B_GAF.OPERACION_DESPOSTE
                    SET Valor_kilo = %s
                    WHERE Consecutivo_Cercafe = %s
                ''', [newValue, id])
            # Devolver una respuesta de éxito
            return JsonResponse({'success': True})
        except Exception as e:
            # Devolver una respuesta de error si ocurre algún error
            return JsonResponse({'success': False, 'error': str(e)})
    else:
        # Devolver una respuesta de error si la solicitud no es POST
        return JsonResponse({'success': False, 'error': 'Método de solicitud no permitido'})
    
def get_filtered_data_by_group(start_date, end_date, selected_group):
    with connections['b_gaf'].cursor() as cursor:
        cursor.execute('''
            SELECT Granja,Cliente,Unidades,Peso_canal_fria,Valor_kilo,Valor,Retencion,Valor_a_pagar_asociado
            FROM B_GAF.OPERACION_DESPOSTE
            WHERE Fecha_transformacion BETWEEN %s AND %s AND Grupo_Granja = %s
        ''', [start_date, end_date, selected_group])
        compromisos = cursor.fetchall()

    # Loguear los datos recuperados
    logger.info(compromisos)

    return compromisos

from collections import defaultdict
    
def generate_excel_report(request):
    # Obtener los datos para exportar
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    selected_group = request.GET.get('selected_group')

    # Obtener los datos filtrados para el grupo seleccionado
    compromisos = get_filtered_data_by_group(start_date, end_date, selected_group)

    # Crear el archivo Excel
    workbook = xlsxwriter.Workbook('reporte_grupo_' + selected_group + '.xlsx')
    worksheet = workbook.add_worksheet()

    # Escribir los encabezados
    headers = ['Granja', 'Cliente', 'Unidades', 'Peso Canal', 'Valor Kilo', 'Valor a facturar', 'Retención',
               'Valor a Pagar Asociado']
    for i, header in enumerate(headers):
        worksheet.write(0, i, header)

    # Escribir los datos
    current_granja = None
    current_row = 1
    for compromiso in compromisos:
        if current_granja is None or current_granja != compromiso[0]:
            # Si la granja cambió, agregar dos líneas vacías
            if current_row > 1:
                current_row += 2
            current_granja = compromiso[0]
            worksheet.write(current_row, 0, current_granja)  
            current_row += 1

        # Escribir los demás valores en las columnas correspondientes
        for col, value in enumerate(compromiso[1:], start=1):
            worksheet.write(current_row, col, value)

        current_row += 1

    # Cerrar el archivo Excel
    workbook.close()

    # Enviar el archivo Excel como respuesta
    with open('reporte_grupo_' + selected_group + '.xlsx', 'rb') as file:
        response = HttpResponse(file.read(),
                                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte_grupo_' + selected_group + '.xlsx"'
        return response

