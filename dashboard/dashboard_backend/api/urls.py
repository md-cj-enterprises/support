from django.urls import path

from . import views

urlpatterns = [
    path("update_ltp", views.update_ltp, name="update_ltp"),
    path("get_ltp/", views.get_ltp, name="get_ltp"),
    path("dashboard", views.dashboard, name="dashboard"),

]
