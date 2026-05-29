from django.core.management.base import BaseCommand
from operations.checker import check_all


class Command(BaseCommand):
    help = "Verifica condições de venda/recompra para todos os ativos e gera sinais."

    def handle(self, *args, **options):
        self.stdout.write("Verificando ativos...")
        n = check_all()
        if n:
            self.stdout.write(self.style.SUCCESS(f"{n} novo(s) sinal(is) gerado(s)."))
        else:
            self.stdout.write("Nenhum novo sinal.")
