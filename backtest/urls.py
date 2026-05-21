from django.urls import path
from . import views

urlpatterns = [
    path("", views.backtest_index, name="backtest_index"),
]
