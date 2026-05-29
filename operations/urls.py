from django.urls import path
from . import views

urlpatterns = [
    path("",                       views.dashboard,      name="operations_dashboard"),
    path("check/",                 views.check_now,      name="operations_check"),
    path("<int:pk>/confirm/",      views.confirm_signal, name="operations_confirm"),
    path("<int:pk>/cancel/",       views.cancel_signal,  name="operations_cancel"),
]
