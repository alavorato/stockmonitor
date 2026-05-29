from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("stocks.urls")),
    path("monitor/", include("monitor.urls")),
    path("backtest/",    include("backtest.urls")),
    path("operations/",  include("operations.urls")),
]
