from django.db import models


class StockPosition(models.Model):
    """Estado atual de cada ativo monitorado para operações em tempo real."""
    stock = models.OneToOneField(
        'stocks.Stock', on_delete=models.CASCADE, related_name='position'
    )
    # Estado atual
    shares = models.IntegerField()
    avg_price = models.DecimalField(max_digits=12, decimal_places=4)
    peak_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    pending_buybacks = models.JSONField(default=list)

    # Estado inicial (para cálculo de resultado)
    initial_shares = models.IntegerField()
    initial_avg_price = models.DecimalField(max_digits=12, decimal_places=4)

    # Parâmetros da estratégia
    trailing_stop_pct = models.DecimalField(max_digits=5, decimal_places=2, default=3.0)
    buyback_pct = models.DecimalField(max_digits=5, decimal_places=2, default=5.0)
    min_hold_pct = models.DecimalField(max_digits=5, decimal_places=2, default=60.0)
    fee_pct = models.DecimalField(max_digits=6, decimal_places=4, default=0.0305)

    # Monitoramento
    last_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    tracking_started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Posição {self.stock.ticker}"


class TradeSignal(models.Model):
    TYPE_CHOICES = [('SELL', 'Venda'), ('BUY', 'Recompra')]
    STATUS_CHOICES = [
        ('pending',   'Pendente'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
    ]

    stock = models.ForeignKey(
        'stocks.Stock', on_delete=models.CASCADE, related_name='signals'
    )
    signal_type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    status = models.CharField(max_length=10, default='pending', choices=STATUS_CHOICES)

    # Preço e cotas no momento do sinal
    suggested_price = models.DecimalField(max_digits=12, decimal_places=4)
    shares = models.IntegerField()

    # Campos de VENDA
    peak_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    profit_pct = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    avg_price_ref = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    buyback_trigger = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)
    sale_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    profit_captured = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    # Campos de RECOMPRA
    pending_buyback_id = models.CharField(max_length=16, null=True, blank=True)
    sell_ref_date = models.CharField(max_length=12, null=True, blank=True)
    buy_value = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    saved = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    new_avg_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    # Resultado comum
    shares_after = models.IntegerField(null=True, blank=True)
    executed_price = models.DecimalField(max_digits=12, decimal_places=4, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.signal_type} {self.stock.ticker} @ {self.suggested_price} [{self.status}]"
