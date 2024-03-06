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
from django.template import loader
from django.http import FileResponse

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
    print(compromisos)
    return compromisos

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

from django.views.decorators.csrf import csrf_protect

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
            with connections['base_gaf'].cursor() as cursor:
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
    with connections['base_gaf'].cursor() as cursor:
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

