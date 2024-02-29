from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db import connections
import pandas as pd
from django.http import HttpResponseRedirect
from .forms import UploadFileForm

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



def mi_vista(request):
    with connections['proveeduria'].cursor() as cursor:
        cursor.execute("SELECT nombre FROM grupo")
        grupos = [row[0] for row in cursor.fetchall()]

    print(grupos)  # Verifica los resultados en la consola del servidor

    return render(request, '/granja/', {'grupos': grupos})

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            archivo_excel = request.FILES['archivo_excel']
            df = pd.read_excel(archivo_excel)
            df.to_sql('compromiso_mes', connections['b_ca'], schema='b_ca', if_exists='append', index=False)
            return HttpResponseRedirect('granja')
    else:
        form = UploadFileForm()
    return render(request, 'granja.html', {'form': form})

