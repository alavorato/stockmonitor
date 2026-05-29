from django.db import models


class Stock(models.Model):
    ticker = models.CharField(max_length=15, unique=True)
    name = models.CharField(max_length=100, blank=True)
    quantity = models.PositiveIntegerField()
    avg_price = models.DecimalField(max_digits=10, decimal_places=4)
    min_profit_pct = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    max_profit_pct = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ticker"]
        verbose_name = "Ativo"
        verbose_name_plural = "Ativos"

    def __str__(self):
        return self.ticker

    @property
    def invested(self):
        return float(self.avg_price) * float(self.quantity)
