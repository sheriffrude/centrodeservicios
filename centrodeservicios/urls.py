from django.contrib import admin
from django.urls import path
from login import views

#--Todas las urls de Centro de servicios ---

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.signin, name='signin'),
    path('signin/', views.signin, name='signin'),
    path('home/', views.home, name='home'),
    path('exit/', views.exit, name='exit'),
    path('granja/', views.granja, name='granja'),
    path('mi_vista/', views.mi_vista, name='mi_vista'),
    
]
