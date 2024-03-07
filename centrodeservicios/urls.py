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
    
    #----------------------cadena de abastecimiento ----------------------------------
    path('cadenaabastecimiento/', views.cadenaabastecimiento, name='cadenaabastecimiento'),
    path('cadenaabastecimiento/', views.cargar_excel_cadenaabastecimiento, name='cadenaabastecimiento'),
    path('cargar_excel_cadenaabastecimiento/', views.cargar_excel_cadenaabastecimiento, name='cargar_excel_cadenaabastecimiento'),
    # -----------------------gestion comercial-------------------------------------------
    path('gestioncomercial/', views.gestioncomercial, name='gestioncomercial'),
    path('gestioncomercial/', views.cargar_excel_clientesactivos, name='gestioncomercial'),
    path('cargar_excel_clientesactivos/', views.cargar_excel_clientesactivos, name='cargar_excel_clientesactivos'),
    path('gestioncomercial/', views.cargar_excel_ventas, name='gestioncomercial'),
    path('cargar_excel_ventas/', views.cargar_excel_ventas, name='cargar_excel_ventas'),
    #------------------------gestion humana ------------------------------------------------
    path('gestionhumana/', views.gestionhumana, name='gestionhumana'),
    path('gestionhumana/', views.cargar_excel_nomina, name='gestionhumana'),
    path('gestionhumana/', views.cargar_excel_promo, name='gestionhumana'),
    path('gestionhumana/', views.cargar_excel_prosele, name='gestionhumana'),
    path('gestionhumana/', views.cargar_excel_retencion, name='gestionhumana'),
    path('gestionhumana/', views.cargar_excel_rotacion, name='gestionhumana'),
    path('gestionhumana/', views.cargar_excel_sstdiag, name='gestionhumana'),
    path('gestionhumana/', views.cargar_excel_sstindi, name='gestionhumana'),
    path('gestionhumana/', views.cargar_excel_sstseveridad, name='gestionhumana'),
    
    path('cargar_excel_nomina/', views.cargar_excel_nomina, name='cargar_excel_nomina'),
    path('cargar_excel_promo/', views.cargar_excel_promo, name='cargar_excel_promo'),
    path('cargar_excel_prosele/', views.cargar_excel_prosele, name='cargar_excel_prosele'),
    path('cargar_excel_retencion/', views.cargar_excel_retencion, name='cargar_excel_retencion'),
    path('cargar_excel_rotacion/', views.cargar_excel_rotacion, name='cargar_excel_rotacion'),
    path('cargar_excel_sstdiag/', views.cargar_excel_sstdiag, name='cargar_excel_sstdiag'),
    path('cargar_excel_sstindi/', views.cargar_excel_sstindi, name='cargar_excel_sstindi'),
    path('cargar_excel_sstseveridad/', views.cargar_excel_sstseveridad, name='cargar_excel_sstseveridad'),
    
    
    path('financiera/', views.financiera, name='financiera'),
    path('repoprove/', views.repoprove, name='repoprove'),
    path('repofina/', views.repofina, name='repofina'),
    
    
    path('carexitosa/', views.carexitosa, name='carexitosa'),
    path('reproved/', views.reproved, name='reproved'), 
    path('repfinan/', views.repfinan, name='repfinan'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('export-pdf/', views.export_pdf, name='export-pdf'),
    path('save-changes/', views.save_changes, name='save_changes'),
    path('generate-excel-report/', views.generate_excel_report, name='generate_excel_report'),
    
    
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
