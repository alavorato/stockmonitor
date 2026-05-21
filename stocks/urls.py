from django.urls import path
from . import views

urlpatterns = [
    path("", views.stock_list, name="stock_list"),
    path("stocks/add/", views.stock_add, name="stock_add"),
    path("stocks/<int:pk>/edit/", views.stock_edit, name="stock_edit"),
    path("stocks/<int:pk>/delete/", views.stock_delete, name="stock_delete"),
]
