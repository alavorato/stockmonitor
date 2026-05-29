from django import template

register = template.Library()


@register.filter
def brl(value):
    """Formata como moeda brasileira: R$ 1.234,56"""
    try:
        f = float(value)
        formatted = f"{abs(f):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        sign = "−" if f < 0 else ""
        return f"R$ {sign}{formatted}"
    except (TypeError, ValueError):
        return "—"


@register.filter
def brl_plain(value):
    """Apenas o número formatado sem 'R$ ': 1.234,56"""
    try:
        f = float(value)
        formatted = f"{abs(f):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        sign = "−" if f < 0 else ""
        return f"{sign}{formatted}"
    except (TypeError, ValueError):
        return "—"
