from django.contrib import admin
from .models import Stock


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ["ticker", "name", "quantity", "avg_price", "min_profit_pct", "max_profit_pct", "active"]
    list_filter = ["active"]
    search_fields = ["ticker", "name"]
