import logging
import os
import threading
import time

from django.apps import AppConfig

logger = logging.getLogger(__name__)

INTERVAL = 3600  # segundos entre verificações


class OperationsConfig(AppConfig):
    name = "operations"

    def ready(self):
        # RUN_MAIN == 'true' apenas no processo principal do runserver.
        # Evita iniciar duas threads: uma no reloader e outra no servidor.
        # Em produção (gunicorn/uwsgi) RUN_MAIN não existe — thread inicia normalmente.
        if os.environ.get("RUN_MAIN") == "false":
            return

        thread = threading.Thread(target=self._checker_loop, daemon=True)
        thread.start()
        logger.info("Operations checker iniciado (intervalo: %ds)", INTERVAL)

    @staticmethod
    def _checker_loop():
        # Aguarda Django terminar de inicializar antes do primeiro check
        time.sleep(60)
        while True:
            try:
                from .checker import check_all
                n = check_all()
                if n:
                    logger.info("Operations check: %d novo(s) sinal(is)", n)
                else:
                    logger.debug("Operations check: nenhum novo sinal")
            except Exception:
                logger.exception("Erro no operations checker")
            time.sleep(INTERVAL)
