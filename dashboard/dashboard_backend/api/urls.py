from django.urls import path

from . import views

urlpatterns = [
    path("update_ltp", views.update_ltp, name="update_ltp"),
    path("get_ltp/<int:script_id>", views.get_ltp, name="get_ltp"),
    path("dashboard", views.dashboard, name="dashboard"),
    path("update_dashboard_info", views.update_dashboard_info, name="update_dashboard_info"),
    path("get_dashboard_info", views.get_dashboard_info, name="get_dashboard_info"),

]
