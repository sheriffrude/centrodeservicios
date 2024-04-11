from django.contrib import admin
from django.urls import path
from centrodeservicios import settings
from login import views
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
#--Todas las urls de Centro de servicios ---

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.signin, name='signin'),
    path('signin/', views.signin, name='signin'),
    path('home/', views.home, name='home'),
    path('exit/', views.exit, name='exit'),
    path('reset_password/', auth_views.PasswordResetView.as_view(), name='reset_password'),
    path('reset_password_sent/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset_password_complete/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    #----------------------cadena de abastecimiento ----------------------------------
    path('cadenaabastecimiento/', views.cadenaabastecimiento, name='cadenaabastecimiento'),
    path('cargar_excel_disponibilidad/', views.cargar_excel_disponibilidad, name='cargar_excel_disponibilidad'),
    path('cargar_excel_cadenaabastecimiento/', views.cargar_excel_cadenaabastecimiento, name='cargar_excel_cadenaabastecimiento'),
    path('cargar_excel_cerdosbeneficiados/', views.cargar_excel_cerdosbeneficiados, name='cargar_excel_cerdosbeneficiados'),
    path('cargar_excel_compaplanta/', views.cargar_excel_compaplanta, name='cargar_excel_compaplanta'), 
    path('cargar_excel_costodespos/', views.cargar_excel_costodespos, name='cargar_excel_costodespos'), 
    path('cargar_excel_kgbeneficio/', views.cargar_excel_kgbeneficio, name='cargar_excel_kgbeneficio'), 
    path('cargar_excel_kgdesposte/', views.cargar_excel_kgdesposte, name='cargar_excel_kgdesposte'), 
    path('cargar_excel_particortes/', views.cargar_excel_particortes, name='cargar_excel_particortes'), 
    path('cargar_excel_toneladasimport/', views.cargar_excel_toneladasimport, name='cargar_excel_toneladasimport'), 
    
    # -----------------------gestion comercial-------------------------------------------
    path('gestioncomercial/', views.gestioncomercial, name='gestioncomercial'),
    path('gestioncomercial/', views.cargar_excel_clientesactivos, name='gestioncomercial'),
    path('cargar_excel_clientesactivos/', views.cargar_excel_clientesactivos, name='cargar_excel_clientesactivos'),
    path('gestioncomercial/', views.cargar_excel_ventas, name='gestioncomercial'),
    path('cargar_excel_ventas/', views.cargar_excel_ventas, name='cargar_excel_ventas'),
    #------------------------gestion humana ------------------------------------------------
    path('gestionhumana/', views.gestionhumana, name='gestionhumana'),

    path('cargar_excel_nomina/', views.cargar_excel_nomina, name='cargar_excel_nomina'),
    path('cargar_excel_promo/', views.cargar_excel_promo, name='cargar_excel_promo'),
    path('cargar_excel_prosele/', views.cargar_excel_prosele, name='cargar_excel_prosele'),
    path('cargar_excel_retencion/', views.cargar_excel_retencion, name='cargar_excel_retencion'),
    path('cargar_excel_rotacion/', views.cargar_excel_rotacion, name='cargar_excel_rotacion'),
    path('cargar_excel_sstdiag/', views.cargar_excel_sstdiag, name='cargar_excel_sstdiag'),
    path('cargar_excel_sstindi/', views.cargar_excel_sstindi, name='cargar_excel_sstindi'),
    path('cargar_excel_sstseveridad/', views.cargar_excel_sstseveridad, name='cargar_excel_sstseveridad'),
    
    #------------------------gestion Tecnica ------------------------------------------------
    path('gestiontecnica/', views.gestiontecnica, name='gestiontecnica'),
  
    path('cargar_excel_abashem/', views.cargar_excel_abashem, name='cargar_excel_abashem'),
    path('cargar_excel_fortuitos/', views.cargar_excel_fortuitos, name='cargar_excel_fortuitos'),
    path('cargar_excel_kgvend/', views.cargar_excel_kgvend, name='cargar_excel_kgvend'),
    path('cargar_excel_pesofinconver/', views.cargar_excel_pesofinconver, name='cargar_excel_pesofinconver'),
    path('cargar_excel_proyhem/', views.cargar_excel_proyhem, name='cargar_excel_proyhem'),
    path('cargar_excel_tecnicacia/', views.cargar_excel_tecnicacia, name='cargar_excel_tecnicacia'),
    
    #------------------------gestion Alimento Balanceado ------------------------------------------------
    path('gestionalbal/', views.gestionalbal, name='gestionalbal'),
    
    
    path('cargar_excel_alibal/', views.cargar_excel_alibal, name='cargar_excel_alibal'),
    
     #--------------------------------- CALIDAD ------------------------------------------------
    path('calidad/', views.calidad, name='calidad'),
   
    path('cargar_excel_avancepro/', views.cargar_excel_avancepro, name='cargar_excel_avancepro'),
    path('cargar_excel_calidadpl/', views.cargar_excel_calidadpl, name='cargar_excel_calidadpl'),
    path('cargar_excel_causasdes/', views.cargar_excel_causasdes, name='cargar_excel_causasdes'),
    path('cargar_excel_pqrsf/', views.cargar_excel_pqrsf, name='cargar_excel_pqrsf'),
    
     #--------------------------------- T.I ------------------------------------------------
    path('ti/', views.ti, name='ti'),
  
    
    path('cargar_excel_transfordig/', views.cargar_excel_transfordig, name='cargar_excel_transfordig'),
    path('cargar_excel_inideco/', views.cargar_excel_inideco, name='cargar_excel_inideco'),
    
     #--------------------------------- Admin y Financiera ------------------------------------------------
    path('adminfinan/', views.adminfinan, name='adminfinan'),
    path('cargar_excel_compramatprima/', views.cargar_excel_compramatprima, name='cargar_excel_compramatprima'),
    path('cargar_excel_compramed/', views.cargar_excel_compramed, name='cargar_excel_compramed'),
    path('cargar_excel_preciocanal/', views.cargar_excel_preciocanal, name='cargar_excel_preciocanal'),
    path('cargar_excel_clientes/', views.cargar_excel_clientes, name='cargar_excel_clientes'),
    
    
    
    path('financiera/', views.financiera, name='financiera'),
    path('repoprove/', views.repoprove, name='repoprove'),
    path('repofina/', views.repofina, name='repofina'),
    
    
    path('carexitosa/', views.carexitosa, name='carexitosa'),
    path('reproved/', views.reproved, name='reproved'), 
    path('repfinan/', views.repfinan, name='repfinan'),
    path('export-excel/', views.export_excel, name='export_excel'),
    path('export-pdf/', views.export_pdf, name='export-pdf'),
    path('save-changes/', views.save_changes, name='save_changes'),
    path('generate_excel_report/', views.generate_excel_report, name='generate_excel_report'),
    path('grupos/', views.grupos_asociados, name='grupos_asociados'),
    path('tabla/', views.tablarepclient, name='tablarepclient'),
    path('frigorificos/', views.frigorificos, name='frigorificos'),
    

#--------------------------------- REPORTES------------------------------------------------
    
    
    path('repgcomercial/', views.repgcomercial, name='repgcomercial'),
    path('repgtecnica/', views.repgtecnica, name='repgtecnica'),
    path('repcadabastecimiento/', views.repcadabastecimiento, name='repcadabastecimiento'),
    path('repplantaalibal/', views.repplantaalibal, name='repplantaalibal'),
    path('repcalidad/', views.repcalidad, name='repcalidad'),
    path('repadminfinan/', views.repadminfinan, name='repadminfinan'),
    path('repgestionhumana/', views.repgestionhumana, name='repgestionhumana'),
    path('repremision/', views.repremision, name='repremision'),
    path('generar_pdf/', views.generar_pdf, name='generar_pdf'),
    path('api/hembras-registradas/', views.api_hembras_registradas),

    


] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
