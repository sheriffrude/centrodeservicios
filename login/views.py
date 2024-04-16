from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, connection, connections
import pandas as pd
from django.http import HttpResponse, HttpResponseRedirect

from centrodeservicios import settings

from .forms import UploadFileForm
from django.http import JsonResponse
import openpyxl
from openpyxl import load_workbook
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
from uuid import uuid4
import os
import datetime




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
#---Define La Vistas del modulo Gestion frigorificos-----

@never_cache
@login_required
def frigorificos(request):
   return render(request, 'frigorificos.html')
#---Define La Vistas del modulo Gestion TI-----

@never_cache
@login_required
def ti(request):
   return render(request, 'tecnologia.html')

#---Define La Vista del modulo Gestion admin y finan-----
@never_cache
@login_required
def adminfinan(request):
   return render(request, 'gestionadminfinan.html')

#---Define La Vista del modulo financiera-----
@never_cache
@login_required
def financiera(request):
    grupos = grupos_asociados(request)  
    return render(request, 'financiera.html', {'grupos_asociados': grupos})



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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    granja, mes, semana, cantidad_cerdos, año = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla compromiso_mes
                    cursor.execute(
                        'INSERT INTO compromiso_mes (granja, mes, semana, cantidad_cerdos, año, GUID, USUARIO) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (granja.value, mes.value, semana.value, cantidad_cerdos.value, año.value,guid,usuario.username)
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

@never_cache
@login_required
def cargar_excel_disponibilidad(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    granja, mes, semana, cantidad_cerdos, año = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla disponibilidad_semanal
                    cursor.execute(
                        'INSERT INTO disponibilidad_semanal (granja, mes, semana, cantidad_cerdos, año, GUID, USUARIO) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (granja.value, mes.value, semana.value, cantidad_cerdos.value, año.value,guid,usuario.username)
                    )
            messages.success(request, 'Carga de datos en Disponibilidad semanal exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en produccion  cerdos  beneficiados--------------------------------------
@never_cache
@login_required
def cargar_excel_cerdosbeneficiados(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    CER_BENEF_COLOMBIA,CER_BENEF_EJE_CAFETERO,PARTICIPACION_EJE_CAFETERO,CER_BENEF_CERCAFE,PARTICIPACION_EJE_CAF_CERCAFE,PARTICIPACION_NACIONAL_CERCAFE,FECHA_CORTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROD_CARNICA_CERDOS_BENEFICIADOS
                    cursor.execute(
                        'INSERT INTO PROD_CARNICA_CERDOS_BENEFICIADOS (CER_BENEF_COLOMBIA,CER_BENEF_EJE_CAFETERO,PARTICIPACION_EJE_CAFETERO,CER_BENEF_CERCAFE,PARTICIPACION_EJE_CAF_CERCAFE,PARTICIPACION_NACIONAL_CERCAFE,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s)',
                        (CER_BENEF_COLOMBIA.value,CER_BENEF_EJE_CAFETERO.value,PARTICIPACION_EJE_CAFETERO.value,CER_BENEF_CERCAFE.value,PARTICIPACION_EJE_CAF_CERCAFE.value,PARTICIPACION_NACIONAL_CERCAFE.value,FECHA_CORTE.value,guid,usuario.username)
                    )
            messages.success(request, 'Carga de datos en PROD_CARNICA_CERDOS_BENEFICIADOS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en comparatico plantas--------------------------------------
@never_cache
@login_required
def cargar_excel_compaplanta(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    PARAMETRO,VALOR,EMPRESA,FECHA_CORTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROD_CARNICA_COMPARATIVO_PLANTAS
                    cursor.execute(
                        'INSERT INTO PROD_CARNICA_COMPARATIVO_PLANTAS (PARAMETRO,VALOR,EMPRESA,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s, %s, %s, %s, %s)',
                        (PARAMETRO.value,VALOR.value,EMPRESA.value,FECHA_CORTE.value,guid,usuario.username)
                    )
            messages.success(request, 'Carga de datos en PROD_CARNICA_COMPARATIVO_PLANTAS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en COSTO DESPOSTE--------------------------------------
@never_cache
@login_required
def cargar_excel_costodespos(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    TIPO_CLIENTE,NUM_CERDOS_DESPOSTADOS,KG_DESPOSTADOS,PESO_PROM_CERDOS,PRECIO_PROM_KG,COSTO_MATERIA_PRIMA,COSTO_MAQUILA,COSTO_KG_MAQUILADO,MAQUILA_SIN_MP,FECHA_CORTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROD_CARNICA_COSTO_DESPOSTE
                    cursor.execute(
                        'INSERT INTO PROD_CARNICA_COSTO_DESPOSTE (TIPO_CLIENTE,NUM_CERDOS_DESPOSTADOS,KG_DESPOSTADOS,PESO_PROM_CERDOS,PRECIO_PROM_KG,COSTO_MATERIA_PRIMA,COSTO_MAQUILA,COSTO_KG_MAQUILADO,MAQUILA_SIN_MP,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (TIPO_CLIENTE.value,NUM_CERDOS_DESPOSTADOS.value,KG_DESPOSTADOS.value,PESO_PROM_CERDOS.value,PRECIO_PROM_KG.value,COSTO_MATERIA_PRIMA.value,COSTO_MAQUILA.value,COSTO_KG_MAQUILADO.value,MAQUILA_SIN_MP.value,FECHA_CORTE.value,guid,usuario.username)
                    )
            messages.success(request, 'Carga de datos en PROD_CARNICA_COSTO_DESPOSTE exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel enKG_BENEFICIO--------------------------------------
@never_cache
@login_required
def cargar_excel_kgbeneficio(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    CER_BENEF_COLOMBIA,CER_BENEF_EJE_CAFETERO,PARTICIPACION_EJE_CAFETERO,CER_BENEF_CERCAFE,PARTICIPACION_EJE_CAF_CERCAFE,PARTICIPACION_NACIONAL_CERCAFE,PESO_CF_NACIONAL,PESO_EJE_CAFETERO,PESO_CF_CERCAFE,KG_NACIONAL,KG_EJE_CAFETERO,KG_CERCAFE,FECHA_CORTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROD_CARNICA_KG_BENEFICIO
                    cursor.execute(
                        'INSERT INTO PROD_CARNICA_KG_BENEFICIO (CER_BENEF_COLOMBIA,CER_BENEF_EJE_CAFETERO,PARTICIPACION_EJE_CAFETERO,CER_BENEF_CERCAFE,PARTICIPACION_EJE_CAF_CERCAFE,PARTICIPACION_NACIONAL_CERCAFE,PESO_CF_NACIONAL,PESO_EJE_CAFETERO,PESO_CF_CERCAFE,KG_NACIONAL,KG_EJE_CAFETERO,KG_CERCAFE,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (CER_BENEF_COLOMBIA.value,CER_BENEF_EJE_CAFETERO.value,PARTICIPACION_EJE_CAFETERO.value,CER_BENEF_CERCAFE.value,PARTICIPACION_EJE_CAF_CERCAFE.value,
                          PARTICIPACION_NACIONAL_CERCAFE.value,PESO_CF_NACIONAL.value,PESO_EJE_CAFETERO.value,PESO_CF_CERCAFE.value,KG_NACIONAL.value,KG_EJE_CAFETERO.value,KG_CERCAFE.value,FECHA_CORTE.value,guid,usuario.username)
                    )
            messages.success(request, 'Carga de datos en PROD_CARNICA_KG_BENEFICIO exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en KG_DESPOSTADOS--------------------------------------
@never_cache 
@login_required
def cargar_excel_kgdesposte(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    KG_PRODUCIDOS_CERCAFE,KG_DESPOSTADOS_CERCAFE,PORCENTAJE_PARTICIPACION,TRIMESTRE_2022_CERCAFE,TRIMESTRE_2022_DESPOSTE,TRIMESTRE_2023_CERCAFE,TRIMESTRE_2023_DESPOSTE,CERCIMIENTO_22_23,FECHA_CORTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROD_CARNICA_KG_DESPOSTADOS
                    cursor.execute(
                        'INSERT INTO PROD_CARNICA_KG_DESPOSTADOS (KG_PRODUCIDOS_CERCAFE,KG_DESPOSTADOS_CERCAFE,PORCENTAJE_PARTICIPACION,TRIMESTRE_2022_CERCAFE,TRIMESTRE_2022_DESPOSTE,TRIMESTRE_2023_CERCAFE,TRIMESTRE_2023_DESPOSTE,CERCIMIENTO_22_23,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (KG_PRODUCIDOS_CERCAFE.value,KG_DESPOSTADOS_CERCAFE.value,PORCENTAJE_PARTICIPACION.value,TRIMESTRE_2022_CERCAFE.value,TRIMESTRE_2022_DESPOSTE.value,TRIMESTRE_2023_CERCAFE.value,
                          TRIMESTRE_2023_DESPOSTE.value,CERCIMIENTO_22_23.value,FECHA_CORTE.value,guid,usuario.username)
                    )
            messages.success(request, 'Carga de datos en PROD_CARNICA_KG_DESPOSTADOS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en PARTICIPACION_CORTES--------------------------------------
@never_cache 
@login_required
def cargar_excel_particortes(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    CORTE,PORCENTAJE_PARTICIPACION,PORCENTAJE_META,PESO_PROM_CANAL,CANTIDAD_CANALES,FECHA_CORTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROD_CARNICA_PARTICIPACION_CORTES
                    cursor.execute(
                        'INSERT INTO PROD_CARNICA_PARTICIPACION_CORTES (CORTE,PORCENTAJE_PARTICIPACION,PORCENTAJE_META,PESO_PROM_CANAL,CANTIDAD_CANALES,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s)',
                        (CORTE.value,PORCENTAJE_PARTICIPACION.value,PORCENTAJE_META.value,PESO_PROM_CANAL.value,CANTIDAD_CANALES.value,FECHA_CORTE.value,guid,usuario.username)
                    )
            messages.success(request, 'Carga de datos en PROD_CARNICA_PARTICIPACION_CORTES exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')
#------ vista para el cargue de excel en TON_IMPORTADAS--------------------------------------
@never_cache 
@login_required
def cargar_excel_toneladasimport(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ca
            with connections['B_CA'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    CER_BENEF_COLOMBIA,TON_BENEF_COLOMBIA,TON_IMPORT_COLOMBIA,CERDOS_IMPORTADOS,ENE_FEB_22_TON_BENEF,ENE_FEB_23_TON_BENEF,CRECIMIENTO_22_23,ENE_FEB_MAR_22_TON_IMPORT,ENE_FEB_MAR_23_TON_IMPORT,CRECIMIENTO_OMPORT_22_23,FECHA_CORTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROD_CARNICA_TON_IMPORTADAS
                    cursor.execute(
                        'INSERT INTO PROD_CARNICA_TON_IMPORTADAS (CER_BENEF_COLOMBIA,TON_BENEF_COLOMBIA,TON_IMPORT_COLOMBIA,CERDOS_IMPORTADOS,ENE_FEB_22_TON_BENEF,ENE_FEB_23_TON_BENEF,CRECIMIENTO_22_23,ENE_FEB_MAR_22_TON_IMPORT,ENE_FEB_MAR_23_TON_IMPORT,CRECIMIENTO_OMPORT_22_23,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (CER_BENEF_COLOMBIA.value,TON_BENEF_COLOMBIA.value,TON_IMPORT_COLOMBIA.value,CERDOS_IMPORTADOS.value,ENE_FEB_22_TON_BENEF.value,ENE_FEB_23_TON_BENEF.value,CRECIMIENTO_22_23.value,ENE_FEB_MAR_22_TON_IMPORT.value,ENE_FEB_MAR_23_TON_IMPORT.value,CRECIMIENTO_OMPORT_22_23.value,FECHA_CORTE.value,guid,usuario.username)
                    )
            messages.success(request, 'Carga de datos en PROD_CARNICA_TON_IMPORTADAS exitosa')
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gc
            with connections['B_GC'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_CORTE, CANTIDAD_CLIENTES, ZONA_CLIENTE, KG_FACTURADOS,DINERO_APORTADO,ESTADO_CLIENTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla compromiso_mes
                    cursor.execute(
                        'INSERT INTO CLIENTES_ACTIVOS (FECHA_CORTE,CANTIDAD_CLIENTES,ZONA_CLIENTE,KG_FACTURADOS,DINERO_APORTADO,ESTADO_CLIENTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s,%s,%s)',
                        (FECHA_CORTE.value, CANTIDAD_CLIENTES.value, ZONA_CLIENTE.value, KG_FACTURADOS.value,DINERO_APORTADO.value,ESTADO_CLIENTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gc
            with connections['B_GC'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_CORTE,LINEA_NEGOCIO,PRESUPUESTO_UNIDADES,PRESUPUESTO_KG,UNIDADES_VENDIDAS,KG_VENDIDO,VALOR_VENTA,PRESUPUESTO_VENTA= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO VENTAS (FECHA_CORTE,LINEA_NEGOCIO,PRESUPUESTO_UNIDADES,PRESUPUESTO_KG,UNIDADES_VENDIDAS,KG_VENDIDO,VALOR_VENTA,PRESUPUESTO_VENTA,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s,%s,%s,%s,%s)',
                        (FECHA_CORTE.value, LINEA_NEGOCIO.value, PRESUPUESTO_UNIDADES.value, PRESUPUESTO_KG.value,UNIDADES_VENDIDAS.value,KG_VENDIDO.value,VALOR_VENTA.value,PRESUPUESTO_VENTA.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_CORTE,AREA,CENTRO_COSTO,NUM_COLABORADORES,COSTO_PROV= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO NOMINA (FECHA_CORTE,AREA,CENTRO_COSTO,NUM_COLABORADORES,COSTO_PROV,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s,%s)',
                        (FECHA_CORTE.value, AREA.value, CENTRO_COSTO.value, NUM_COLABORADORES.value,COSTO_PROV.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_CORTE,NOMBRE,ANTIGUO_CARGO,NUEVO_CARGO= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO PROMOCIONES (FECHA_CORTE,NOMBRE,ANTIGUO_CARGO,NUEVO_CARGO,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s)',
                        (FECHA_CORTE.value, NOMBRE.value, ANTIGUO_CARGO.value, NUEVO_CARGO.value,guid,usuario.usuario)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    
                    NUM_REQUISICION,FECHA_APROBACION,AREA_CENTRO_COSTO,FECHA_RETIRO,NOMBRE_RETIRADO,CARGO,CUBRIMIENTO_ESPERADO_DIAS,NOMBRE_CANDIDATO,TIPO_INGRESO_PROMO_INT,EXAMEN_MEDICO,VISITA_DOMICILIARIA,POLIGRAFIA,FECHA_INGRESO = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROCESO_SELECCION
                    cursor.execute(
                        'INSERT INTO PROCESO_SELECCION (NUM_REQUISICION,FECHA_APROBACION,AREA_CENTRO_COSTO,FECHA_RETIRO,NOMBRE_RETIRADO,CARGO,CUBRIMIENTO_ESPERADO_DIAS,NOMBRE_CANDIDATO,TIPO_INGRESO_PROMO_INT,EXAMEN_MEDICO,VISITA_DOMICILIARIA,POLIGRAFIA,FECHA_INGRESO,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (NUM_REQUISICION.value,FECHA_APROBACION.value,AREA_CENTRO_COSTO.value,FECHA_RETIRO.value,NOMBRE_RETIRADO.value,CARGO.value,CUBRIMIENTO_ESPERADO_DIAS.value,NOMBRE_CANDIDATO.value,TIPO_INGRESO_PROMO_INT.value,EXAMEN_MEDICO.value,VISITA_DOMICILIARIA.value,POLIGRAFIA.value,FECHA_INGRESO.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_REPORTE,INDICADOR_RETENCION,OBSERVACIONES= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla RETENCION
                    cursor.execute(
                        'INSERT INTO RETENCION (FECHA_REPORTE,INDICADOR_RETENCION,OBSERVACIONES,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s)',
                        (FECHA_REPORTE.value,INDICADOR_RETENCION.value,OBSERVACIONES.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    FECHA_REPORTE,INDICADOR_ROTACION,OBSERVACIONES= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO ROTACION (FECHA_REPORTE,INDICADOR_ROTACION,OBSERVACIONES,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s)',
                        (FECHA_REPORTE.value, INDICADOR_ROTACION.value, OBSERVACIONES.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    FECHA_CORTE,SEDE,DIAGNOSTICO,CANTIDAD,OBSERVACION= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla SST_DIAGNOSTICOS_INDICADORES
                    cursor.execute(
                        'INSERT INTO SST_DIAGNOSTICOS_INDICADORES (FECHA_CORTE,SEDE,DIAGNOSTICO,CANTIDAD,OBSERVACION,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s)',
                        (FECHA_CORTE.value, SEDE.value, DIAGNOSTICO.value,CANTIDAD.value,OBSERVACION.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                   
                    FECHA_CORTE,SEDE,CANTIDAD_PEG,DIAS_INCAPACIDAD_PEL,CANTIDAD_PAT,PRORROGAS,DIAS_INCAPACIDAD_PAT,LICENCIA_MATERNIDAD,DIAS_LICENCIA_MAT,LICENCIA_PATERNIDAD,DIAS_LICENCIA_PAT,COSTO_INCAPACIDAD,OBSERVACIONES= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla VENTAS
                    cursor.execute(
                        'INSERT INTO SST_INDICADORES (FECHA_CORTE,SEDE,CANTIDAD_PEG,DIAS_INCAPACIDAD_PEL,CANTIDAD_PAT,PRORROGAS,DIAS_INCAPACIDAD_PAT,LICENCIA_MATERNIDAD,DIAS_LICENCIA_MAT,LICENCIA_PATERNIDAD,DIAS_LICENCIA_PAT,COSTO_INCAPACIDAD,OBSERVACIONES,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s)',
                        (FECHA_CORTE.value,SEDE.value,CANTIDAD_PEG.value,DIAS_INCAPACIDAD_PEL.value,CANTIDAD_PAT.value,PRORROGAS.value,DIAS_INCAPACIDAD_PAT.value,LICENCIA_MATERNIDAD.value,DIAS_LICENCIA_MAT.value,LICENCIA_PATERNIDAD.value,DIAS_LICENCIA_PAT.value,COSTO_INCAPACIDAD.value,OBSERVACIONES.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gh
            with connections['B_GH'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                   
                    FECHA_CORTE,CANT_ENF_GENERAL,CANT_ACC_TRABAJO,NUM_EMPLEADOS,FREC_ACC,DIAS_INC_GENERAL,DIAS_INC_ACC,SEV_ACC,INCID_ENF_LAB,PORC_AUSENTISMO= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla SST_SEVERIDAD_Y_FRECUENCIA
                    cursor.execute(
                        'INSERT INTO SST_SEVERIDAD_Y_FRECUENCIA (FECHA_CORTE,CANT_ENF_GENERAL,CANT_ACC_TRABAJO,NUM_EMPLEADOS,FREC_ACC,DIAS_INC_GENERAL,DIAS_INC_ACC,SEV_ACC,INCID_ENF_LAB,PORC_AUSENTISMO,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s,%s, %s, %s, %s, %s)',
                        (FECHA_CORTE.value,CANT_ENF_GENERAL.value,CANT_ACC_TRABAJO.value,NUM_EMPLEADOS.value,FREC_ACC.value,DIAS_INC_GENERAL.value,DIAS_INC_ACC.value,SEV_ACC.value,INCID_ENF_LAB.value,PORC_AUSENTISMO.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                   
                    GRANJA,CANTIDAD_ENTREGADA,PORCENTAJE_CUMPLIMIENTO,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla SST_SEVERIDAD_Y_FRECUENCIA
                    cursor.execute(
                        'INSERT INTO ABASTECIMIENTO_HEMBRAS (GRANJA,CANTIDAD_ENTREGADA,PORCENTAJE_CUMPLIMIENTO,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s)',
                        (GRANJA.value,CANTIDAD_ENTREGADA.value,PORCENTAJE_CUMPLIMIENTO.value,FECHA_CORTE.value,guid,usuario.username)
                    )
                messages.success(request, 'Carga de datos en ABASTECIMIENTO HEMBRAS exitosa')
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                  
                    FECHA_CORTE,PLANTA,GRANJA,CANTIDAD_MUERTE_TRANSPORTE,CANTIDAD_MUERTE_REPOSO,AGITADOS,LESIONADOS,RETOMAS,TOTAL= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla SST_SEVERIDAD_Y_FRECUENCIA
                    cursor.execute(
                        'INSERT INTO FORTUITOS3 (FECHA_CORTE,PLANTA,GRANJA,CANTIDAD_MUERTE_TRANSPORTE,CANTIDAD_MUERTE_REPOSO,AGITADOS,LESIONADOS,RETOMAS,TOTAL,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s,%s, %s, %s)',
                        (FECHA_CORTE.value,PLANTA.value,GRANJA.value,CANTIDAD_MUERTE_TRANSPORTE.value,CANTIDAD_MUERTE_REPOSO.value,AGITADOS.value,LESIONADOS.value,RETOMAS.value,TOTAL.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                  
                    GRANJA,KG_V_H_A,ASOCIADO,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla KG_VENDIDOS_HEMBRA
                    cursor.execute(
                        'INSERT INTO KG_VENDIDOS_HEMBRA (GRANJA,KG_V_H_A,ASOCIADO,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s)',
                        (GRANJA.value,KG_V_H_A.value,ASOCIADO.value,FECHA_CORTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user

            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                  
                    GRANJA,PESO,META_PESO,CONVERSION_META,CONVERSION,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PESO_FINAL_CONVERSION
                    cursor.execute(
                        'INSERT INTO PESO_FINAL_CONVERSION (GRANJA,PESO,META_PESO,CONVERSION_META,CONVERSION,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s)',
                        (GRANJA.value,PESO.value,META_PESO.value,CONVERSION_META.value,CONVERSION.value,FECHA_CORTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    
                    PARTOS,TASA_PARTOS,CUMPLIMIENTO_PROYECTADO,CUMPLIMIENTO_REAL,AÑO_SERVICIO,OBSERVACIONES,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PROYECCION_HEMBRAS
                    cursor.execute(
                        'INSERT INTO PROYECCION_HEMBRAS (PARTOS,TASA_PARTOS,CUMPLIMIENTO_PROYECTADO,CUMPLIMIENTO_REAL,AÑO_SERVICIO,OBSERVACIONES,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s)',
                        (PARTOS.value,TASA_PARTOS.value,CUMPLIMIENTO_PROYECTADO.value,CUMPLIMIENTO_REAL.value,AÑO_SERVICIO.value,OBSERVACIONES.value,FECHA_CORTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user

            # Abre una conexión a la base de datos b_gt
            with connections['B_GT'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    
                    LINEA_GENETICA,CANTIDAD_MACHOS,PORCENTAJE_DISTRIBUCION_MACHOS,CANTIDAD_DESECHADO,PORCENTAJE_DESCECHADO,DOSIS_PRODUCIDAS,DOSIS_VENDIDAS,PROMEDIO_MORFOLOGIA,OBSERVACION,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla TECNICA_CIA
                    cursor.execute(
                        'INSERT INTO TECNICA_CIA (LINEA_GENETICA,CANTIDAD_MACHOS,PORCENTAJE_DISTRIBUCION_MACHOS,CANTIDAD_DESECHADO,PORCENTAJE_DESCECHADO,DOSIS_PRODUCIDAS,DOSIS_VENDIDAS,PROMEDIO_MORFOLOGIA,OBSERVACION,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (LINEA_GENETICA.value,CANTIDAD_MACHOS.value,PORCENTAJE_DISTRIBUCION_MACHOS.value,CANTIDAD_DESECHADO.value,PORCENTAJE_DESCECHADO.value,DOSIS_PRODUCIDAS.value,DOSIS_VENDIDAS.value,PROMEDIO_MORFOLOGIA.value,OBSERVACION.value,FECHA_CORTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_gt
            with connections['B_GAB'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    
                    TONELADAS_PRODUCIDAS_MES,TONELADAS_PRESUPUESTO_MES,PORCENTAJE_VARIACION_MES,PORCENTAJE_CUMPLIMIENTO_MES,OBSERVACION_VARIACION,PORCENTAJE_BULTO_MES,PORCENTAJE_GRANEL_MES,SACK_OFF,PORCENTAJE_OTIF,OBSERVACION_OTIF,PRESUPUESTO_MO_CIF,MO_CIF,TIEMPO_MUERTO,COSTO_TIEMPO_MUERTO,OBSERVACION_TIEMPO_MUERTO,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PLANTA_ALIMENTOS_BALANCEADOS
                    cursor.execute(
                        'INSERT INTO PLANTA_ALIMENTOS_BALANCEADOS (TONELADAS_PRODUCIDAS_MES,TONELADAS_PRESUPUESTO_MES,PORCENTAJE_VARIACION_MES,PORCENTAJE_CUMPLIMIENTO_MES,OBSERVACION_VARIACION,PORCENTAJE_BULTO_MES,PORCENTAJE_GRANEL_MES,SACK_OFF,PORCENTAJE_OTIF,OBSERVACION_OTIF,PRESUPUESTO_MO_CIF,MO_CIF,TIEMPO_MUERTO,COSTO_TIEMPO_MUERTO,OBSERVACION_TIEMPO_MUERTO,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (TONELADAS_PRODUCIDAS_MES.value,TONELADAS_PRESUPUESTO_MES.value,PORCENTAJE_VARIACION_MES.value,PORCENTAJE_CUMPLIMIENTO_MES.value,OBSERVACION_VARIACION.value,PORCENTAJE_BULTO_MES.value,PORCENTAJE_GRANEL_MES.value,SACK_OFF.value,PORCENTAJE_OTIF.value,OBSERVACION_OTIF.value,PRESUPUESTO_MO_CIF.value,MO_CIF.value,TIEMPO_MUERTO.value,COSTO_TIEMPO_MUERTO.value,OBSERVACION_TIEMPO_MUERTO.value,FECHA_CORTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_c
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    TIPO,PROCESO,DETALLE_PROCESO,AVANCE,META,FECHA_CORTE,_= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla AVANCE_PROCESO
                    cursor.execute(
                        'INSERT INTO AVANCE_PROCESO (TIPO,PROCESO,DETALLE_PROCESO,AVANCE,META,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s)',
                        (TIPO.value,PROCESO.value,DETALLE_PROCESO.value,AVANCE.value,META.value,FECHA_CORTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user

            # Abre una conexión a la base de datos b_c
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    PORCENTAJE_DESVIACIONES_CALIDAD,TONELADAS_REPROCESADAS,TONELADAS_LIBERADAS_CONCESION,PORCENTAJE_RETENCION,PORCENTAJE_MEZCLA,PORCENTAJE_DURABILIDAD,PORCENTAJE_FINOS,PORCENTAJE_FORMULACION,CUMPLIMIENTO_BPM,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla CALIDAD_PLANTA
                    cursor.execute(
                        'INSERT INTO CALIDAD_PLANTA (PORCENTAJE_DESVIACIONES_CALIDAD,TONELADAS_REPROCESADAS,TONELADAS_LIBERADAS_CONCESION,PORCENTAJE_RETENCION,PORCENTAJE_MEZCLA,PORCENTAJE_DURABILIDAD,PORCENTAJE_FINOS,PORCENTAJE_FORMULACION,CUMPLIMIENTO_BPM,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (PORCENTAJE_DESVIACIONES_CALIDAD.value,TONELADAS_REPROCESADAS.value,TONELADAS_LIBERADAS_CONCESION.value,PORCENTAJE_RETENCION.value,PORCENTAJE_MEZCLA.value,PORCENTAJE_DURABILIDAD.value,PORCENTAJE_FINOS.value,PORCENTAJE_FORMULACION.value,CUMPLIMIENTO_BPM.value,FECHA_CORTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_c
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    CAUSA,PLAN_ACCION,TON_REPROCESADAS,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla CAUSAS_DESVIACIONES
                    cursor.execute(
                        'INSERT INTO CAUSAS_DESVIACIONES (CAUSA,PLAN_ACCION,TON_REPROCESADAS,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s)',
                        (CAUSA.value,PLAN_ACCION.value,TON_REPROCESADAS.value,FECHA_CORTE.value,guid,usuario.username)
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
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_c
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    PROCESO,TIPO,ESTADO_MOTIVO,CANTIDAD,CATEGORIA,TIEMPO_RESPUESTA,FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla PQRSF
                    cursor.execute(
                        'INSERT INTO PQRSF (PROCESO,TIPO,ESTADO_MOTIVO,CANTIDAD,CATEGORIA,TIEMPO_RESPUESTA,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s, %s)',
                        (PROCESO.value,TIPO.value,ESTADO_MOTIVO.value,CANTIDAD.value,CATEGORIA.value,TIEMPO_RESPUESTA.value,FECHA_CORTE.value,guid,usuario.username)
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
@login_required
def cargar_excel_transfordig(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_ti
            with connections['B_C'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    PROYECTO_ESTRATEGICO,CAPA_ARQUITECTURA,NOMBRE_PROYECTO,PESO_CAPA,PESO_PROYECTO_ESTRATEGICO,PORCENTAJE_AVANCE,PORCENTAJE_META,PORCENTAJE_META_PROYECTO,TAREAS_PROYECTO,TAREAS_PLANEADAS,TAREAS_EJECUTADAS,COSTO_PLANEADO,COSTO_EJECUTADO,FECHA_CORTE = row

                    # Ejecuta una consulta SQL para insertar los datos en la tabla TRANSFORMACION_DIGITAL
                    cursor.execute(
                        'INSERT INTO TRANSFORMACION_DIGITAL (PROYECTO_ESTRATEGICO,CAPA_ARQUITECTURA,NOMBRE_PROYECTO,PESO_CAPA,PESO_PROYECTO_ESTRATEGICO,PORCENTAJE_AVANCE,PORCENTAJE_META,PORCENTAJE_META_PROYECTO,TAREAS_PROYECTO,TAREAS_PLANEADAS,TAREAS_EJECUTADAS,COSTO_PLANEADO,COSTO_EJECUTADO,FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s,%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s, %s)',
                        (PROYECTO_ESTRATEGICO.value,CAPA_ARQUITECTURA.value,NOMBRE_PROYECTO.value,PESO_CAPA.value,PESO_PROYECTO_ESTRATEGICO.value,PORCENTAJE_AVANCE.value,PORCENTAJE_META.value,PORCENTAJE_META_PROYECTO.value,TAREAS_PROYECTO.value,TAREAS_PLANEADAS.value,TAREAS_EJECUTADAS.value,COSTO_PLANEADO.value,COSTO_EJECUTADO.value,FECHA_CORTE.value,guid,usuario.username)
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

@login_required
def cargar_excel_inideco(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = load_workbook(archivo_excel)
            ws = wb.active

            # Abre una conexión a la base de datos b_ti
            with connections['B_TI'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    valores = []
                    for cell in row:
                        if isinstance(cell.value, str):
                            valores.append(cell.value.upper())
                        elif isinstance(cell.value, int) or isinstance(cell.value, float):
                            valores.append(str(cell.value))
                        else:
                            valores.append(None)
                    
                    # Ejecuta una consulta SQL para insertar los datos en la tabla INDICADORES_ECONOMICOS
                    cursor.execute(
                        'INSERT INTO INDICADORES_ECONOMICOS (INDICADOR,VALOR,FUENTE,LINK,FECHA_CORTE) VALUES (%s, %s, %s, %s, %s)',
                        tuple(valores)
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
# ----------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#--------------------------------- CARGA DE----G Admin Financiera ------------------------------------------------
#-----------------------------------------------------------------------------------------------------------------
#-------- vista para el cargue de excel en  Compras Materia Prima ------------------------------------------------

@login_required
def cargar_excel_compramatprima(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user
            # Abre una conexión a la base de datos b_c
            with connections['B_GAF'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    MATERIA_PRIMA, COSTO_PROMEDIO, CANTIDAD_COMPRADA, DIAS_INVENTARIO, FECHA_CORTE = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla COMPRAS_MATERIA_PRIMA
                    cursor.execute(
                        'INSERT INTO COMPRAS_MATERIA_PRIMA (MATERIA_PRIMA, COSTO_PROMEDIO, CANTIDAD_COMPRADA, DIAS_INVENTARIO, FECHA_CORTE,GUID,USUARIO) VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (MATERIA_PRIMA.value , COSTO_PROMEDIO.value, CANTIDAD_COMPRADA.value, DIAS_INVENTARIO.value,FECHA_CORTE.value,guid, usuario.username)
                    )
                messages.success(request, 'Carga de datos en COMPRAS_MATERIA_PRIMA exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')


#-------- vista para el cargue de excel en COMPRAS_MEDICAMENTOS --------------------------------------------------------

# @login_required
# def cargar_excel_compramed(request):
#     if request.method == 'POST':
#         try:
#             usuario = request.user
            
#             archivo_excel = request.FILES['archivo_excel']
#             wb = load_workbook(archivo_excel)
#             ws = wb.active
            
#             guid = str(uuid4())

#             # Abre una conexión a la base de datos B_GAF
#             with connections['B_GAF'].cursor() as cursor:
#                 for row in ws.iter_rows(min_row=2):
#                     valores = []
#                     for cell in row:
#                         if isinstance(cell.value, str):
#                             valores.append(cell.value.upper())
#                         elif isinstance(cell.value, int) or isinstance(cell.value, float):
#                             valores.append(str(cell.value))
#                         else:
#                             valores.append(None)
#                     print(valores)
#                     # Ejecuta una consulta SQL para insertar los datos en la tabla COMPRAS_MEDICAMENTOS
#                     cursor.execute(
#                         'INSERT INTO COMPRAS_MEDICAMENTOS (VALOR, MEDICAMENTO, CLASIFICACION, CANTIDAD, TIPO, FECHA_CORTE) VALUES (%s, %s, %s, %s, %s, %s)',
#                        tuple(valores)
#                     )
#                 messages.success(request, 'Carga de datos en COMPRAS_MEDICAMENTOS exitosa')
#         except KeyError:
#             messages.error(request, 'No se ha proporcionado un archivo Excel.')
#         except IntegrityError as e:
#             messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
#         except Exception as e:
#             messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
#         return redirect('home')
#     return render(request, '/home/')

@login_required
def cargar_excel_compramed(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user

            # Abre una conexión a la base de datos b_c
            with connections['B_GAF'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    print(row)
                    VALOR, MEDICAMENTO, CLASIFICACION, CANTIDAD, TIPO, FECHA_CORTE= row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla COMPRAS_MEDICAMENTOS
                    cursor.execute(
                        'INSERT INTO COMPRAS_MEDICAMENTOS (VALOR, MEDICAMENTO, CLASIFICACION, CANTIDAD, TIPO, FECHA_CORTE, GUID, USUARIO) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                        (VALOR.value, MEDICAMENTO.value, CLASIFICACION.value, CANTIDAD.value, TIPO.value, FECHA_CORTE.value, guid, usuario.username)
                    )
                messages.success(request, 'Carga de datos en COMPRAS_MEDICAMENTOS exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')


from django.db import connections

@login_required
def cargar_excel_preciocanal(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user

            # Abre una conexión a la base de datos DHC
            with connections['DHC'].cursor() as dhc_cursor:
                # Obtener todos los NITs existentes en la tabla clientes de DHC
                dhc_cursor.execute('''SELECT NIT FROM dhc.clientes''')
                nits_existentes = [row[0] for row in dhc_cursor.fetchall()]

            # Conjunto para almacenar NITs vistos en el archivo
            nits_vistos = set()

            # Abre una conexión a la base de datos B_GAF
            with connections['B_GAF'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    NIT, CLIENTE, ZONA, VALOR = row
                    
                    # Verificar si el NIT existe en la lista de NITs existentes
                    if int(NIT.value) not in map(int, nits_existentes):
                        messages.error(request, f'Error: El NIT {NIT.value} no existe en la base de datos de clientes.')
                        return redirect('home')

                    # Verificar si el NIT está repetido en el archivo subido
                    if NIT.value in nits_vistos:
                        messages.error(request, f'Error: El NIT {NIT.value} está repetido en el archivo.')
                        return redirect('home')
                    
                    # Añadir el NIT al conjunto de NITs vistos
                    nits_vistos.add(NIT.value)

                    # Ejecuta una consulta SQL para insertar los datos en la tabla precio_canales_semana
                    cursor.execute(
                        'INSERT INTO precio_canales_semana (NIT, CLIENTE, ZONA, VALOR, GUID, USUARIO) VALUES (%s, %s, %s, %s, %s, %s)',
                        (NIT.value, CLIENTE.value, ZONA.value, VALOR.value, guid, usuario.username)
                    )
                messages.success(request, 'Carga de datos en precio canales exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')






@login_required
def cargar_excel_clientes(request):
    if request.method == 'POST':
        try:
            archivo_excel = request.FILES['archivo_excel']
            wb = openpyxl.load_workbook(archivo_excel)
            ws = wb.active
            guid = str(uuid4())
            usuario = request.user

            # Abre una conexión a la base de datos b_c
            with connections['DHC'].cursor() as cursor:
                for row in ws.iter_rows(min_row=2):
                    
                    NIT,RAZON_SOCIAL,CUPO,DIRECCION_SEDE_PRINCIPAL,DIRECCION_EXPENDIO,ID_CLASIFICACION,ID_MUNICIPIO,ID_DEPARTAMENTO,ID_REGION,ID_VENDEDOR,ID_SEGMENTO,ID_MIX_VENTAS, = row
                    # Ejecuta una consulta SQL para insertar los datos en la tabla precio_canales_semana
                    cursor.execute(
                        'INSERT INTO clientes (NIT, RAZON_SOCIAL, CUPO, DIRECCION_SEDE_PRINCIPAL, DIRECCION_EXPENDIO, ID_CLASIFICACION, ID_MUNICIPIO, ID_DEPARTAMENTO, ID_REGION, ID_VENDEDOR, ID_SEGMENTO, ID_MIX_VENTAS, GUID, USUARIO) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                        (NIT.value, RAZON_SOCIAL.value, CUPO.value, DIRECCION_SEDE_PRINCIPAL.value, DIRECCION_EXPENDIO.value, ID_CLASIFICACION.value, ID_MUNICIPIO.value, ID_DEPARTAMENTO.value, ID_REGION.value, ID_VENDEDOR.value, ID_SEGMENTO.value, ID_MIX_VENTAS.value, guid, usuario.username)
                    )

                    print(row)
                messages.success(request, 'Carga de datos en clientes exitosa')
        except KeyError:
            messages.error(request, 'No se ha proporcionado un archivo Excel.')
        except IntegrityError as e:
            messages.error(request, f'Error al insertar datos en la base de datos: {str(e)}')
        except Exception as e:
            messages.error(request, f'Se ha producido un error inesperado: {str(e)}')
        return redirect('home')
    return render(request, '/home/')




# ------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------
#----------------------------Funciones   internas utilizadas por los html-------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------------------------

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



def repfinan(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
   
    
    with connections['B_GAF'].cursor() as cursor:
        cursor.execute('''
            SELECT Fecha_transformacion,Unidades,Peso_canal_fria,Consecutivo_Cercafe,Codigo_granja,Remision,Valor,Cliente,Planta_Beneficio,Granja,Nit_asociado,Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado,Valor_kilo,id
            FROM B_GAF.OPERACION_DESPOSTE
            WHERE Fecha_transformacion BETWEEN %s AND %s
        ''', [start_date, end_date])
        compromisos = cursor.fetchall()

    # Loguear los datos recuperados
    logger.info(compromisos)

    data = [{'Fecha_transformacion': Fecha_transformacion, 'Unidades': Unidades, 'Peso_canal_fria': Peso_canal_fria, 'Consecutivo_Cercafe': Consecutivo_Cercafe, 'Codigo_granja': Codigo_granja, 'Remision': Remision, 'Valor': Valor, 'Cliente': Cliente, 'Planta_Beneficio': Planta_Beneficio, 'Granja': Granja, 'Nit_asociado': Nit_asociado, 'Asociado': Asociado, 'Grupo_Granja': Grupo_Granja, 'Retencion': Retencion, 'Valor_a_pagar_asociado': Valor_a_pagar_asociado, 'Valor_kilo': Valor_kilo, 'id': id } for Fecha_transformacion, Unidades, Peso_canal_fria, Consecutivo_Cercafe, Codigo_granja, Remision, Valor, Cliente, Planta_Beneficio, Granja, Nit_asociado, Asociado, Grupo_Granja, Retencion, Valor_a_pagar_asociado, Valor_kilo, id in compromisos]

    return JsonResponse({'data': data})


def get_filtered_data(start_date, end_date):
    with connections['B_GAF'].cursor() as cursor:
        cursor.execute('''
            SELECT Fecha_transformacion,Unidades,Peso_canal_fria,Consecutivo_Cercafe,Codigo_granja,Remision,Valor,Cliente,Planta_Beneficio,Granja,Nit_asociado,Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado,Valor_kilo,id
            FROM B_GAF.OPERACION_DESPOSTE
            WHERE Fecha_transformacion BETWEEN %s AND %s
        ''', [start_date, end_date])
        compromisos = cursor.fetchall()

    # Loguear los datos recuperados
    logger.info(compromisos)

    return compromisos


def export_pdf(request):
    # Obtener los datos para exportar
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Obtener los datos filtrados
    compromisos = get_filtered_data(start_date, end_date)

    # Crear el HTML con los datos filtrados
    html = '<html><body><table><thead><tr><th>Fecha Transformación</th><th>Unidades</th><th>Peso Canal Fría</th><th>Consecutivo Cercafe</th><th>Código Granja</th><th>Remisión</th><th>Valor</th><th>Cliente</th><th>Planta Beneficio</th><th>Granja</th><th>Nit Asociado</th><th>Asociado</th><th>Grupo Granja</th><th>Retención</th><th>Valor a Pagar Asociado</th><th>Valor Kilo</th></tr></thead><tbody>'
    for compromiso in compromisos:
        html += '<tr>'
        for value in compromiso:
            html += '<td>' + str(value) + '</td>'
        html += '</tr>'
    html += '</tbody></table></body></html>'

    # Convertir el HTML a PDF
    pdf = pdfkit.from_string(html, False, configuration=pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'))

    # Enviar el PDF como respuesta de descarga
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte.pdf"'
    return response




def export_excel(request):
    # Obtener los datos para exportar
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Obtener los datos filtrados
    compromisos = get_filtered_data(start_date, end_date)

    # Obtener el directorio de descargas del usuario actual
    downloads_dir = os.path.join(settings.BASE_DIR, 'tmp')

    # Crear el archivo Excel en el directorio de descargas
    filename = 'reporte.xlsx'
    file_path = os.path.join(downloads_dir, filename)

    # Escribir los datos en el archivo Excel
    workbook = xlsxwriter.Workbook(file_path)
    worksheet = workbook.add_worksheet()

    # Escribir los encabezados
    headers = ['Fecha Transformación', 'Unidades', 'Peso Canal Fría', 'Consecutivo_Cercafe', 'Código Granja', 'Remisión', 'Valor', 'Cliente', 'Planta Beneficio', 'Granja', 'Nit Asociado', 'Asociado', 'Grupo Granja', 'Retención', 'Valor a Pagar Asociado', 'Valor Kilo','id']
    for i, header in enumerate(headers):
        worksheet.write(0, i, header)

    # Obtener el índice de la columna 'id'
    id_column_index = headers.index('id') if 'id' in headers else None

    # Escribir los datos
    for row, compromiso in enumerate(compromisos, start=1):
        for col, value in enumerate(compromiso):
            # Formatear la fecha como un string
            if isinstance(value, datetime.date):
                value = value.strftime('%Y-%m-%d')
            # Verificar si la columna actual no es 'id'
            if id_column_index is None or col != id_column_index:
                worksheet.write(row, col, value)

    # Cerrar el archivo Excel
    workbook.close()

    # Enviar el archivo Excel como respuesta de descarga
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
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
                    WHERE id = %s
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
    with connections['B_GAF'].cursor() as cursor:
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

def grupos_asociados(request):
    with connections['DHC'].cursor() as cursor:
        cursor.execute('''SELECT GRUPO_ASOCIADO FROM DHC.grupo_asociado''')
        grupos_asociados = [row[0] for row in cursor.fetchall()]
        print(grupos_asociados)  
    return grupos_asociados



#---------------- TABLAS DE REPORTES G COMERCIAL------------------------------------------
#---Define La Vista Rep-gestion comercial----
@never_cache
@login_required
def repgcomercial(request):
    clientes = tablarepclient(request)
    ventas = tablarepventas(request) 
    return render(request, 'report_gcomercial.html', {'clientes_act': clientes, 'repventas': ventas})

def tablarepclient(request):
    with connections['B_GC'].cursor() as cursor:
        cursor.execute('''SELECT FECHA_CORTE,CANTIDAD_CLIENTES,ZONA_CLIENTE,KG_FACTURADOS,DINERO_APORTADO,ESTADO_CLIENTE FROM B_GC.CLIENTES_ACTIVOS
                          WHERE GUID = (SELECT MAX(GUID) FROM B_GC.CLIENTES_ACTIVOS) ''')
        clientes_act = cursor.fetchall()   
    return clientes_act
def tablarepventas(request):
    with connections['B_GC'].cursor() as cursor:
        cursor.execute('''SELECT FECHA_CORTE,LINEA_NEGOCIO,PRESUPUESTO_UNIDADES,PRESUPUESTO_KG,UNIDADES_VENDIDAS,KG_VENDIDO,VALOR_VENTA,PRESUPUESTO_VENTA FROM B_GC.VENTAS 
                          WHERE GUID = (SELECT MAX(GUID) FROM B_GC.VENTAS)''')
        repventas = cursor.fetchall()   
    return repventas
#---------------- TABLAS DE REPORTES G TECNICA------------------------------------------
@never_cache
@login_required
def repgtecnica(request):
    abhembras = tablarepabhembras(request)
    fortuitos = tablarepfortuitos(request) 
    kgvendidos = tablarepkgvendidos(request) 
    pfinalcon = tablareppfinalcon(request) 
    prohembras = tablarepprohembras(request) 
    tecnicacia = tablareptecnicacia(request) 
    return render(request, 'report_gtecnica.html', {'abhembras': abhembras,'fortuitos':fortuitos,'kgvendidos':kgvendidos,'pfinalcon':pfinalcon,'prohembras':prohembras,'tecnicacia':tecnicacia})

def tablarepabhembras(request):
    with connections['B_GT'].cursor() as cursor:
        cursor.execute('''SELECT GRANJA,CANTIDAD_ENTREGADA,PORCENTAJE_CUMPLIMIENTO,FECHA_CORTE FROM B_GT.ABASTECIMIENTO_HEMBRAS
                        WHERE GUID = (SELECT MAX(GUID) FROM B_GT.ABASTECIMIENTO_HEMBRAS)''')
        abhembras = cursor.fetchall()   
    return abhembras
def tablarepfortuitos(request):
    with connections['B_GT'].cursor() as cursor:
        cursor.execute('''SELECT FECHA_CORTE,PLANTA,GRANJA,CANTIDAD_MUERTE_TRANSPORTE,CANTIDAD_MUERTE_REPOSO,AGITADOS,LESIONADOS,RETOMAS,TOTAL FROM B_GT.FORTUITOS3
                       WHERE GUID = (SELECT MAX(GUID) FROM B_GT.FORTUITOS3)''')
        fortuitos = cursor.fetchall()   
    return fortuitos
def tablarepkgvendidos(request):
    with connections['B_GT'].cursor() as cursor:
        cursor.execute('''SELECT GRANJA,KG_V_H_A,ASOCIADO,FECHA_CORTE FROM B_GT.KG_VENDIDOS_HEMBRA WHERE GUID = (SELECT MAX(GUID) FROM B_GT.KG_VENDIDOS_HEMBRA)''')
        kgvendidos = cursor.fetchall()   
    return kgvendidos
def tablareppfinalcon(request):
    with connections['B_GT'].cursor() as cursor:
        cursor.execute('''SELECT GRANJA,PESO,META_PESO,CONVERSION_META,CONVERSION,FECHA_CORTE FROM B_GT.PESO_FINAL_CONVERSION WHERE GUID = (SELECT MAX(GUID) FROM B_GT.PESO_FINAL_CONVERSION)''')
        pfinalcon = cursor.fetchall()   
    return pfinalcon
def tablarepprohembras(request):
    with connections['B_GT'].cursor() as cursor:
        cursor.execute('''SELECT PARTOS,TASA_PARTOS,CUMPLIMIENTO_PROYECTADO,CUMPLIMIENTO_REAL,AÑO_SERVICIO,OBSERVACIONES,FECHA_CORTE FROM B_GT.PROYECCION_HEMBRAS WHERE GUID = (SELECT MAX(GUID) FROM B_GT.PROYECCION_HEMBRAS)''')
        prohembras = cursor.fetchall()   
    return prohembras
def tablareptecnicacia(request):
    with connections['B_GT'].cursor() as cursor:
        cursor.execute('''SELECT LINEA_GENETICA,CANTIDAD_MACHOS,PORCENTAJE_DISTRIBUCION_MACHOS,CANTIDAD_DESECHADO,PORCENTAJE_DESCECHADO,DOSIS_PRODUCIDAS,DOSIS_VENDIDAS,PROMEDIO_MORFOLOGIA,OBSERVACION,FECHA_CORTE FROM B_GT.TECNICA_CIA WHERE GUID = (SELECT MAX(GUID) FROM B_GT.TECNICA_CIA)''')
        tecnicacia = cursor.fetchall()   
    return tecnicacia
#---------------- TABLAS DE REPORTES CADENA DE ABASTECIMIENTO------------------------------------------
@never_cache
@login_required
def repcadabastecimiento(request):
    compgranja = tablarepcompgranja(request)
    disposemana = tablarepdisposem(request)
    cerdosbenef = tablarepcerdosbenef(request) 
    comparativopl = tablarepcomparativopl(request) 
    costodespo = tablarepcostodespo(request) 
    kgbenef = tablarepkgbenef(request) 
    kgdespos = tablarepkgdespos(request) 
    particortes = tablarepparticortes(request) 
    toneladasimport = tablareptoneladasimport(request) 
    return render(request, 'report_cadabastecimiento.html', {'compgranja': compgranja,'disposemana': disposemana,'cerdosbenef':cerdosbenef,'comparativopl':comparativopl,'costodespo':costodespo,'kgbenef':kgbenef,'kgdespos':kgdespos,'particortes':particortes,'toneladasimport':toneladasimport})

def tablarepcompgranja(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''select  granja,mes,semana,cantidad_cerdos,año from B_CA.compromiso_mes''')
        compgranja = cursor.fetchall()
      
    return compgranja

def tablarepdisposem(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''select  granja,mes,semana,cantidad_cerdos,año from B_CA.disponibilidad_semanal''')
        disposemana = cursor.fetchall()
    return disposemana
def tablarepcerdosbenef(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT CER_BENEF_COLOMBIA,CER_BENEF_EJE_CAFETERO,PARTICIPACION_EJE_CAFETERO,CER_BENEF_CERCAFE,PARTICIPACION_EJE_CAF_CERCAFE,PARTICIPACION_NACIONAL_CERCAFE,FECHA_CORTE FROM B_CA.PROD_CARNICA_CERDOS_BENEFICIADOS ''')
        cerdosbenef = cursor.fetchall()   
    return cerdosbenef
def tablarepcomparativopl(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT PARAMETRO,VALOR,EMPRESA,FECHA_CORTE FROM B_CA.PROD_CARNICA_COMPARATIVO_PLANTAS''')
        comparativopl = cursor.fetchall()   
    return comparativopl
def tablarepcostodespo(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT TIPO_CLIENTE,NUM_CERDOS_DESPOSTADOS,KG_DESPOSTADOS,PESO_PROM_CERDOS,PRECIO_PROM_KG,COSTO_MATERIA_PRIMA,COSTO_MAQUILA,COSTO_KG_MAQUILADO,MAQUILA_SIN_MP,FECHA_CORTE FROM B_CA.PROD_CARNICA_COSTO_DESPOSTE''')
        costodespo = cursor.fetchall()   
    return costodespo
def tablarepkgbenef(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT CER_BENEF_COLOMBIA,CER_BENEF_EJE_CAFETERO,PARTICIPACION_EJE_CAFETERO,CER_BENEF_CERCAFE,PARTICIPACION_EJE_CAF_CERCAFE,PARTICIPACION_NACIONAL_CERCAFE,PESO_CF_NACIONAL,PESO_EJE_CAFETERO,PESO_CF_CERCAFE,KG_NACIONAL,KG_EJE_CAFETERO,KG_CERCAFE,FECHA_CORTE FROM B_CA.PROD_CARNICA_KG_BENEFICIO ''')
        kgbenef = cursor.fetchall()   
    return kgbenef
def tablarepkgdespos(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT KG_PRODUCIDOS_CERCAFE,KG_DESPOSTADOS_CERCAFE,PORCENTAJE_PARTICIPACION,TRIMESTRE_2022_CERCAFE,TRIMESTRE_2022_DESPOSTE,TRIMESTRE_2023_CERCAFE,TRIMESTRE_2023_DESPOSTE,CERCIMIENTO_22_23,FECHA_CORTE FROM B_CA.PROD_CARNICA_KG_DESPOSTADOS ''')
        kgdespos = cursor.fetchall()   
    return kgdespos
def tablarepparticortes(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT CORTE,PORCENTAJE_PARTICIPACION,PORCENTAJE_META,PESO_PROM_CANAL,CANTIDAD_CANALES,FECHA_CORTE FROM B_CA.PROD_CARNICA_PARTICIPACION_CORTES ''')
        particortes = cursor.fetchall()   
    return particortes
def tablareptoneladasimport(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT CER_BENEF_COLOMBIA,TON_BENEF_COLOMBIA,TON_IMPORT_COLOMBIA,CERDOS_IMPORTADOS,ENE_FEB_22_TON_BENEF,ENE_FEB_23_TON_BENEF,CRECIMIENTO_22_23,ENE_FEB_MAR_22_TON_IMPORT,ENE_FEB_MAR_23_TON_IMPORT,CRECIMIENTO_OMPORT_22_23,FECHA_CORTE FROM B_CA.PROD_CARNICA_TON_IMPORTADAS ''')
        toneladasimport = cursor.fetchall()   
    return toneladasimport

#---------------- TABLAS DE REPORTES  ALIMENTO BALANCEADO ------------------------------------------
@never_cache
@login_required
def repplantaalibal(request):
    plantaalib = tablarepplantab(request)
    return render(request, 'report_galimento.html', {'plantaalib': plantaalib})

def tablarepplantab(request):
    with connections['B_GAB'].cursor() as cursor:
        cursor.execute('''SELECT TONELADAS_PRODUCIDAS_MES,TONELADAS_PRESUPUESTO_MES,PORCENTAJE_VARIACION_MES,PORCENTAJE_CUMPLIMIENTO_MES,OBSERVACION_VARIACION,PORCENTAJE_BULTO_MES,PORCENTAJE_GRANEL_MES,SACK_OFF,PORCENTAJE_OTIF,OBSERVACION_OTIF,PRESUPUESTO_MO_CIF,MO_CIF,TIEMPO_MUERTO,COSTO_TIEMPO_MUERTO,OBSERVACION_TIEMPO_MUERTO,FECHA_CORTE FROM B_GAB.PLANTA_ALIMENTOS_BALANCEADOS ''')
        plantaalib = cursor.fetchall()   
    return plantaalib

#---------------- TABLAS DE REPORTES CALIDAD------------------------------------------
@never_cache
@login_required
def repcalidad(request):
    avancepro = tablarepavancepro(request)
    calidadpla = tablarepcalidadpla(request) 
    causadesvia = tablarepcausadesvia(request) 
    pqrsf = tablareppqrsf(request) 
    return render(request, 'report_calidad.html', {'avancepro': avancepro,'calidadpla':calidadpla,'causadesvia':causadesvia,'pqrsf':pqrsf})

def tablarepavancepro(request):
    with connections['B_C'].cursor() as cursor:
        cursor.execute('''SELECT TIPO,PROCESO,DETALLE_PROCESO,AVANCE,META,FECHA_CORTE FROM B_C.AVANCE_PROCESO WHERE GUID = (SELECT MIN(GUID) FROM b_c.avance_proceso) ''')
        avancepro = cursor.fetchall()   
    return avancepro
def tablarepcalidadpla(request):
    with connections['B_C'].cursor() as cursor:
        cursor.execute('''SELECT PORCENTAJE_DESVIACIONES_CALIDAD,TONELADAS_REPROCESADAS,TONELADAS_LIBERADAS_CONCESION,PORCENTAJE_RETENCION,PORCENTAJE_MEZCLA,PORCENTAJE_DURABILIDAD,PORCENTAJE_FINOS,PORCENTAJE_FORMULACION,CUMPLIMIENTO_BPM,FECHA_CORTE FROM B_C.CALIDAD_PLANTA WHERE GUID = (SELECT MIN(GUID) FROM B_C.CALIDAD_PLANTA)''')
        calidadpla = cursor.fetchall()   
    return calidadpla
def tablarepcausadesvia(request):
    with connections['B_C'].cursor() as cursor:
        cursor.execute('''SELECT CAUSA,PLAN_ACCION,TON_REPROCESADAS,FECHA_CORTE FROM B_C.CAUSAS_DESVIACIONES''')
        causadesvia = cursor.fetchall()   
    return causadesvia
def tablareppqrsf(request):
    with connections['B_C'].cursor() as cursor:
        cursor.execute('''SELECT PROCESO,TIPO,ESTADO_MOTIVO,CANTIDAD,CATEGORIA,TIEMPO_RESPUESTA,FECHA_CORTE FROM B_C.PQRSF''')
        pqrsf = cursor.fetchall()   
    return pqrsf

#---------------- TABLAS DE REPORTES GESTION ADMINISTRATIVA Y FINANCIERA------------------------------------------
@never_cache
@login_required
def repadminfinan(request):
    materiapr = tablarepmateriapr(request)
    compramed = tablarepcompramed(request) 
    preciocanal = tablareppreciocanal(request) 
    nuevosclientes = tablarepnuevosclientes(request) 
    return render(request, 'report_gadminfinan.html', {'materiapr': materiapr,'compramed':compramed,'preciocanal':preciocanal,'nuevosclientes':nuevosclientes})

def tablarepmateriapr(request):
    with connections['B_GAF'].cursor() as cursor:
        cursor.execute('''SELECT MATERIA_PRIMA,COSTO_PROMEDIO,CANTIDAD_COMPRADA,DIAS_INVENTARIO,FECHA_CORTE FROM B_GAF.COMPRAS_MATERIA_PRIMA''')
        materiapr = cursor.fetchall()   
    return materiapr
def tablarepcompramed(request):
    with connections['B_GAF'].cursor() as cursor:
        cursor.execute('''SELECT VALOR,MEDICAMENTO,CLASIFICACION,CANTIDAD,TIPO,FECHA_CORTE FROM B_GAF.COMPRAS_MEDICAMENTOS''')
        compramed = cursor.fetchall()   
    return compramed
def tablareppreciocanal(request):
    with connections['B_GAF'].cursor() as cursor:
        cursor.execute('''SELECT NIT,CLIENTE,ZONA,VALOR  FROM B_GAF.precio_canales_semana''')
        preciocanal = cursor.fetchall()   
    return preciocanal
def tablarepnuevosclientes(request):
    with connections['DHC'].cursor() as cursor:
        cursor.execute('''SELECT NIT,RAZON_SOCIAL,CUPO,DIRECCION_SEDE_PRINCIPAL,DIRECCION_EXPENDIO,ID_CLASIFICACION,ID_MUNICIPIO,ID_DEPARTAMENTO,ID_REGION,ID_VENDEDOR,ID_SEGMENTO,ID_MIX_VENTAS FROM dhc.clientes;''')
        nuevosclientes = cursor.fetchall()   
    return nuevosclientes

#---------------- TABLAS DE REPORTES CADENA DE ABASTECIMIENTO------------------------------------------
@never_cache
@login_required
def repgestionhumana(request):
    compgranja = tablarepcompgranja(request)
    disposemana = tablarepdisposem(request)
    cerdosbenef = tablarepcerdosbenef(request) 
    comparativopl = tablarepcomparativopl(request) 
    costodespo = tablarepcostodespo(request) 
    kgbenef = tablarepkgbenef(request) 
    kgdespos = tablarepkgdespos(request) 
    particortes = tablarepparticortes(request) 
    toneladasimport = tablareptoneladasimport(request) 
    return render(request, 'report_gestionhumana.html', {'compgranja': compgranja,'disposemana': disposemana,'cerdosbenef':cerdosbenef,'comparativopl':comparativopl,'costodespo':costodespo,'kgbenef':kgbenef,'kgdespos':kgdespos,'particortes':particortes,'toneladasimport':toneladasimport})

def tablarepcompgranja(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''select  granja,mes,semana,cantidad_cerdos,año from B_CA.compromiso_mes''')
        compgranja = cursor.fetchall()
      
    return compgranja

def tablarepdisposem(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''select  granja,mes,semana,cantidad_cerdos,año from B_CA.disponibilidad_semanal''')
        disposemana = cursor.fetchall()
    return disposemana
def tablarepcerdosbenef(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT CER_BENEF_COLOMBIA,CER_BENEF_EJE_CAFETERO,PARTICIPACION_EJE_CAFETERO,CER_BENEF_CERCAFE,PARTICIPACION_EJE_CAF_CERCAFE,PARTICIPACION_NACIONAL_CERCAFE,FECHA_CORTE FROM B_CA.PROD_CARNICA_CERDOS_BENEFICIADOS ''')
        cerdosbenef = cursor.fetchall()   
    return cerdosbenef
def tablarepcomparativopl(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT PARAMETRO,VALOR,EMPRESA,FECHA_CORTE FROM B_CA.PROD_CARNICA_COMPARATIVO_PLANTAS''')
        comparativopl = cursor.fetchall()   
    return comparativopl
def tablarepcostodespo(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT TIPO_CLIENTE,NUM_CERDOS_DESPOSTADOS,KG_DESPOSTADOS,PESO_PROM_CERDOS,PRECIO_PROM_KG,COSTO_MATERIA_PRIMA,COSTO_MAQUILA,COSTO_KG_MAQUILADO,MAQUILA_SIN_MP,FECHA_CORTE FROM B_CA.PROD_CARNICA_COSTO_DESPOSTE''')
        costodespo = cursor.fetchall()   
    return costodespo
def tablarepkgbenef(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT CER_BENEF_COLOMBIA,CER_BENEF_EJE_CAFETERO,PARTICIPACION_EJE_CAFETERO,CER_BENEF_CERCAFE,PARTICIPACION_EJE_CAF_CERCAFE,PARTICIPACION_NACIONAL_CERCAFE,PESO_CF_NACIONAL,PESO_EJE_CAFETERO,PESO_CF_CERCAFE,KG_NACIONAL,KG_EJE_CAFETERO,KG_CERCAFE,FECHA_CORTE FROM B_CA.PROD_CARNICA_KG_BENEFICIO ''')
        kgbenef = cursor.fetchall()   
    return kgbenef
def tablarepkgdespos(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT KG_PRODUCIDOS_CERCAFE,KG_DESPOSTADOS_CERCAFE,PORCENTAJE_PARTICIPACION,TRIMESTRE_2022_CERCAFE,TRIMESTRE_2022_DESPOSTE,TRIMESTRE_2023_CERCAFE,TRIMESTRE_2023_DESPOSTE,CERCIMIENTO_22_23,FECHA_CORTE FROM B_CA.PROD_CARNICA_KG_DESPOSTADOS ''')
        kgdespos = cursor.fetchall()   
    return kgdespos
def tablarepparticortes(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT CORTE,PORCENTAJE_PARTICIPACION,PORCENTAJE_META,PESO_PROM_CANAL,CANTIDAD_CANALES,FECHA_CORTE FROM B_CA.PROD_CARNICA_PARTICIPACION_CORTES ''')
        particortes = cursor.fetchall()   
    return particortes
def tablareptoneladasimport(request):
    with connections['B_CA'].cursor() as cursor:
        cursor.execute('''SELECT CER_BENEF_COLOMBIA,TON_BENEF_COLOMBIA,TON_IMPORT_COLOMBIA,CERDOS_IMPORTADOS,ENE_FEB_22_TON_BENEF,ENE_FEB_23_TON_BENEF,CRECIMIENTO_22_23,ENE_FEB_MAR_22_TON_IMPORT,ENE_FEB_MAR_23_TON_IMPORT,CRECIMIENTO_OMPORT_22_23,FECHA_CORTE FROM B_CA.PROD_CARNICA_TON_IMPORTADAS ''')
        toneladasimport = cursor.fetchall()   
    return toneladasimport



from django.db import OperationalError


@never_cache
@login_required
def repremision(request):
    consecutivo_cercafe = request.GET.get('consecutivoCercafe', None)
    if consecutivo_cercafe:
        remisionnew = tablaremisionnew(consecutivo_cercafe)
        print(consecutivo_cercafe)
        return JsonResponse({'remisionnew': remisionnew})
    else:
        # Si no se proporciona un consecutivo, simplemente renderiza la plantilla HTML
        return render(request, 'remision.html')




def tablaremisionnew(consecutivo_cercafe):
    intranetcercafe2_connection = connections['intranetcercafe2']
    with intranetcercafe2_connection.cursor() as cursor:
        if consecutivo_cercafe:
            cursor.execute("SELECT ConsecutivoDespacho,idSolicitud,granja,lote,cerdosDespachados,frigorifico,fechaEntrega,pesoTotal,conductor,placa,regic,regica,retiroalimento from intranetcercafe2.despachoLotesGranjas WHERE idSolicitud = %s", [consecutivo_cercafe])
        else:
            cursor.execute("SELECT ConsecutivoDespacho,idSolicitud,granja,lote,cerdosDespachados,frigorifico,fechaEntrega,pesoTotal,conductor,placa,regic,regica,retiroalimento from intranetcercafe2.despachoLotesGranjas")
        remisionnew = cursor.fetchall()
    return remisionnew


#--- script para creacion del PDF EN  REMISIONES
from django.template.loader import render_to_string
from django.http import HttpResponse
import pdfkit
import qrcode
from django.db import connections
from django.template.loader import render_to_string

def generate_qr_code(input_data):
    # Obtener la ruta absoluta del directorio 'static/images' dentro de tu proyecto Django
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    images_dir = os.path.join(static_dir, 'images')
    filename = 'qrcercafe.png'
    filepath = os.path.join(images_dir, filename)

    # Crear el directorio si no existe
    os.makedirs(images_dir, exist_ok=True)

    # Crear el código QR
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(input_data)
    qr.make(fit=True)

    # Crear la imagen del código QR
    img = qr.make_image(fill='black', back_color='white')

    # Guardar la imagen en la ruta especificada
    img.save(filepath)
    
    
def generar_pdf(request):
    intranetcercafe2_connection = connections['intranetcercafe2']
    dhc_connection = connections['DHC'] 
    consecutivo_cercafe = request.GET.get('consecutivoCercafe', None)
    
    # Verificar si se proporciona un consecutivo_cercafe
    if consecutivo_cercafe:
        # Obtener los datos de la remisión filtrados por el consecutivo ceracafe
        remisiones = tablaremisionnew(consecutivo_cercafe)
        
        # Consultar los datos de la tabla despachoLotesGranjas de intranetcercafe2
        with intranetcercafe2_connection.cursor() as cursor:
            if consecutivo_cercafe:
                cursor.execute("SELECT ConsecutivoDespacho,idSolicitud,granja,lote,cerdosDespachados,frigorifico,fechaEntrega,pesoTotal,conductor,placa,regic,regica,retiroalimento FROM despachoLotesGranjas WHERE idSolicitud = %s", [consecutivo_cercafe])
            else:
                cursor.execute("SELECT ConsecutivoDespacho,idSolicitud,granja,lote,cerdosDespachados,frigorifico,fechaEntrega,pesoTotal,conductor,placa,regic,regica,retiroalimento FROM despachoLotesGranjas")
            remisionnew = cursor.fetchall()
            
        granja_primera_consulta = remisionnew[0][2] if remisionnew else None
        
        print(granja_primera_consulta)
        if granja_primera_consulta:
            with dhc_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT
                        B.ID AS ID,
                        B.ID_FRIGOTUN AS ID_INTRANET,
                        UPPER(C.GRANJAS) AS Granja,
                        D.CODIGO AS Nit_asociado,
                        UPPER(E.RAZON_SOCIAL) AS Asociado
                    FROM
                        DHC.homologacion_granjas B
                    JOIN DHC.granjas C ON B.ID = C.ID
                    JOIN DHC.nombre_comercial D ON C.NOMBRE_COMERCIAL = D.ID
                    JOIN DHC.RAZON_SOCIAL E ON C.RAZON_SOCIAL = E.ID
                    WHERE UPPER(ID_INTRANET) = %s;
                """, [granja_primera_consulta])
                resultados_dhc = cursor.fetchall()
        print(resultados_dhc)

        # Combinar los resultados de ambas consultas si es necesario
        
        total_cantidad = sum(remisionne[7] for remisionne in remisionnew)
        
        total_cantidad1 = str(sum(remisionne[7] for remisionne in remisionnew))
        totalcerdos = sum(remisionne[4] for remisionne in remisionnew)
        totalcerdos1 = str(sum(remisionne[4] for remisionne in remisionnew))
        promedio = total_cantidad/totalcerdos
        promedio_formateado = f'{promedio:.2f}'
        input_data = (resultados_dhc[0][0], resultados_dhc[0][2],consecutivo_cercafe, totalcerdos1, total_cantidad1,remisionnew[0][9],remisionnew[0][11],resultados_dhc[0][3])
        generate_qr_code(input_data)
        # Renderizar el HTML con los datos de la remisión filtrados
        html = render_to_string('remision_pdf.html', {'remisiones': remisiones,'promedio_formateado':promedio_formateado ,'remisionnew':remisionnew, 'resultados_dhc':resultados_dhc,'consecutivo_cercafe':consecutivo_cercafe,'total_cantidad':total_cantidad,'totalcerdos':totalcerdos})
        
        # Convertir el HTML en PDF utilizando wkhtmltopdf
        pdf = pdfkit.from_string(html, False, configuration=pdfkit.configuration(wkhtmltopdf='C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe'))

        # Retornar el PDF como una respuesta HTTP para descargar
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="reporte_remisiones.pdf"'
        return response
    else:
        # Si no se proporciona un consecutivo, devolver un mensaje de error o redireccionar a otra página
        return HttpResponse("No se proporcionó un consecutivo válido.")























































































































def api_hembras_registradas(request):
    # Obtener la conexión a la base de datos intranetcercafe2
    intranetcercafe2_connection = connections['intranet']

    # Realizar la consulta a la base de datos
    with intranetcercafe2_connection.cursor() as cursor:
        cursor.execute("SELECT * FROM hembras_registradas")
        results = cursor.fetchall()

    # Procesar los resultados y construir la respuesta JSON
    items = {'Ingreso_lote': []}
    for granja in results:
        item = {
            'id': granja[0],
            'id_lote': granja[1],
            'nombre_hembra': granja[2],
            'estado': granja[3]
        }
        items['Ingreso_lote'].append(item)

    response = {
        'success': True,
        'data': items,
        'message': 'data_hembras_peso_esperado'
    }

    return JsonResponse(response, status=200)





