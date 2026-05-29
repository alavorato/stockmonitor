from django import forms
from .models import Stock


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ["ticker", "name", "quantity", "avg_price", "min_profit_pct", "max_profit_pct", "active"]
        labels = {
            "ticker": "Ticker",
            "name": "Nome (opcional)",
            "quantity": "Quantidade de cotas",
            "avg_price": "Preço médio (R$)",
            "min_profit_pct": "Lucro mínimo (%)",
            "max_profit_pct": "Lucro máximo (%)",
            "active": "Monitorar este ativo",
        }
        widgets = {
            "ticker": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: PETR4"}),
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ex: Petrobras"}),
            "quantity": forms.NumberInput(attrs={"class": "form-control", "step": "1", "min": "1"}),
            "avg_price": forms.NumberInput(attrs={"class": "form-control", "step": "0.01", "min": "0"}),
            "min_profit_pct": forms.NumberInput(attrs={"class": "form-control", "step": "0.5", "min": "0"}),
            "max_profit_pct": forms.NumberInput(attrs={"class": "form-control", "step": "0.5", "min": "0"}),
            "active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_ticker(self):
        ticker = self.cleaned_data["ticker"].upper().strip()
        if ticker.endswith(".SA"):
            ticker = ticker[:-3]
        return ticker

    def clean(self):
        cleaned = super().clean()
        min_p = cleaned.get("min_profit_pct")
        max_p = cleaned.get("max_profit_pct")
        if min_p and max_p and max_p <= min_p:
            self.add_error("max_profit_pct", "O lucro máximo deve ser maior que o mínimo.")
        return cleaned
