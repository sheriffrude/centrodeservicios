from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import connections
import pandas as pd
from django.http import HttpResponse, HttpResponseRedirect
from .forms import UploadFileForm
from django.http import JsonResponse
import openpyxl
from django.contrib import messages
from django.template.loader import render_to_string
import xlsxwriter
import pdfkit


#---Define La Vista del login-----
def signin(request):
   if request.method == 'GET' :
        return render(request, 'login.html',{
            'form' : AuthenticationForm
            })
   else:
       user = authenticate(authenticate, username=request.POST['username'], 
                           password=request.POST['password'])
       if user is None:
        return render(request, 'login.html',{
                'form' : AuthenticationForm,
                'error' : 'Usuario o Contraseña incorrectos'
                })
       else:
           login (request, user)
           return redirect('home')

#---Define La Vista Principal----
@login_required
def home(request):
    return render(request, 'home.html')


#---Define La Vista del logout-----
@login_required
def exit(request):
    logout(request)
    return redirect('/')
#---Define La Vista del modulo granja-----
@login_required
def granja(request):
   return render(request, 'granja.html')

#---Define La Vista del modulo financiera-----

@login_required
def financiera(request):
   return render(request, 'financiera.html')

#---Define La Vista del modulo reportes-----
@login_required
def repoprove(request):
   return render(request, 'report_prov.html')
@login_required
def carexitosa(request):
   return render(request, 'carga_exitosa.html')

@login_required
def repofina(request):
   return render(request, 'report_finan.html')

#------ vista para el cargue de excel en proveeduria----
@login_required
def cargar_excel(request):
    if request.method == 'POST':
        archivo_excel = request.FILES['archivo_excel']
        wb = openpyxl.load_workbook(archivo_excel)
        ws = wb.active

        # Abre una conexión a la base de datos b_ca
        with connections['base_ca'].cursor() as cursor:
            for row in ws.iter_rows(min_row=2):
                granja, mes, semana, cantidad_cerdos = row
                # Ejecuta una consulta SQL para insertar los datos en la tabla compromiso_mes
                cursor.execute(
                    'INSERT INTO compromiso_mes (granja, mes, semana, cantidad_cerdos) VALUES (%s, %s, %s, %s)',
                    (granja.value, mes.value, semana.value, cantidad_cerdos.value)
                )
        messages.success(request, 'Carga de datos en proveeduria exitosa')
        return redirect('home')
    return render(request, '/home/')

def reproved(request):
    with connections['base_ca'].cursor() as cursor:
        cursor.execute('SELECT granja, mes, semana, cantidad_cerdos FROM compromiso_mes')
        compromisos = cursor.fetchall()

    data = [{'granja': granja, 'mes': mes, 'semana': semana, 'cantidad_cerdos': cantidad_cerdos} for granja, mes, semana, cantidad_cerdos in compromisos]

    return JsonResponse({'data': data})

import logging
from django.views.decorators.csrf import csrf_exempt
logger = logging.getLogger(__name__)



def repfinan(request):
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
   
    
    with connections['base_gaf'].cursor() as cursor:
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
    pdf = pdfkit.from_string(html, False)

    # Enviar el PDF como respuesta
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="reporte.pdf"'
    return response

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
        for col, value in enumerate(compromiso, start=1):
            worksheet.write(row, col, value)

    # Cerrar el archivo Excel
    workbook.close()

    # Enviar el archivo Excel como respuesta
    with open('reporte.xlsx', 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="reporte.xlsx"'
        return redirect('financiera')

def get_filtered_data(start_date, end_date):
    with connections['base_gaf'].cursor() as cursor:
        cursor.execute('''
            SELECT Fecha_transformacion,Unidades,Peso_canal_fria,Consecutivo_Cercafe,Codigo_granja,Remision,Valor,Cliente,Planta_Beneficio,Granja,Nit_asociado,Asociado,Grupo_Granja,Retencion,Valor_a_pagar_asociado,Valor_kilo
            FROM B_GAF.OPERACION_DESPOSTE
            WHERE Fecha_transformacion BETWEEN %s AND %s
        ''', [start_date, end_date])
        compromisos = cursor.fetchall()

    # Loguear los datos recuperados
    logger.info(compromisos)

    return compromisos