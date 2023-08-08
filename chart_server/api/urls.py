from django.urls import path
from . import views
from chart_server import settings
from django.conf.urls.static import static


urlpatterns = [
    path('time', views.get_time, name='get_time'),
    path('history', views.history, name='history'),
    path('import', views.import_excel_pandas,name='import_excel_pandas'),
    path('config', views.config,name='config'),
    path('symbols', views.symbols,name='symbols'),
    path('marks', views.marks,name='marks'),
    #path('change_marks_visibility', views.marks,name='change_marks_visibility'),





]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root = settings.STATIC_ROOT)
    
