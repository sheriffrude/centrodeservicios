from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required

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