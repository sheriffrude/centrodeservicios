from django.contrib import admin
from django.urls import path
from centrodeservicios import settings
from login import views
from django.conf.urls.static import static
#--Todas las urls de Centro de servicios ---

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.signin, name='signin'),
    path('signin/', views.signin, name='signin'),
    path('home/', views.home, name='home'),
    path('exit/', views.exit, name='exit'),
    path('granja/', views.granja, name='granja'),
    path('granja/', views.cargar_excel, name='granja'),
    path('financiera/', views.financiera, name='financiera'),
    path('repoprove/', views.repoprove, name='repoprove'),
    path('repofina/', views.repofina, name='repofina'),
    path('cargar_excel/', views.cargar_excel, name='cargar_excel'),
    path('carexitosa/', views.carexitosa, name='carexitosa'),
    path('reproved/', views.reproved, name='reproved'), 
    path('repfinan/', views.repfinan, name='repfinan'),
    path('export/', views.export_pdf, name="export-pdf" )
    
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
