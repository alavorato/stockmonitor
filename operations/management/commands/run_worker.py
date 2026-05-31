import logging
import time

from django.core.management.base import BaseCommand

from operations.checker import check_all

logger = logging.getLogger(__name__)

INTERVAL = 3600


class Command(BaseCommand):
    help = "Loop contínuo que verifica ativos a cada hora (worker de produção)."

    def handle(self, *args, **options):
        self.stdout.write("Operations worker iniciado (intervalo: 1h).")
        while True:
            try:
                n = check_all()
                if n:
                    self.stdout.write(self.style.SUCCESS(f"{n} novo(s) sinal(is) gerado(s)."))
                else:
                    self.stdout.write("Verificação concluída — nenhum novo sinal.")
            except Exception:
                logger.exception("Erro no operations worker")
                self.stderr.write("Erro durante verificação (ver log).")
            time.sleep(INTERVAL)
