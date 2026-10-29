import logging
import os
from datetime import datetime


class ImmediateFileHandler(logging.FileHandler):
    """FileHandler que hace flush a disco tras cada registro emitido.

    El FileHandler estándar de Python acumula registros en un buffer interno
    y los escribe en bloque. Si el proceso muere de forma inesperada (crash,
    SIGKILL, corte de luz…), ese buffer se pierde.

    Esta subclase sobreescribe `emit` para llamar a `flush()` inmediatamente
    después de escribir cada registro, garantizando que cada línea llegue al
    sistema de archivos antes de continuar la ejecución.

    El archivo siempre se abre en modo 'a' (append), de forma que:
      - Los datos previos nunca se borran.
      - Reinicios del proceso continúan en el mismo archivo.
    """

    def emit(self, record: logging.LogRecord) -> None:
        super().emit(record)
        self.flush()


def setup_logging() -> logging.Logger:
    """Inicializa el sistema de logging y devuelve el logger raíz.

    - Crea la carpeta Logs/ si no existe.
    - Crea un archivo YYYY-MM-DD_HH-MM-SS.log para cada arranque.
    - Usa ImmediateFileHandler: flush a disco tras cada registro (sin buffer).
    - Nivel DEBUG para capturar absolutamente toda la información disponible.
    """
    log_dir = os.path.join(os.getcwd(), "Logs")

    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_filepath = os.path.join(log_dir, f"{current_time}.log")

    # Logger raíz — captura todo
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Formato detallado: timestamp | módulo | nivel | archivo:línea | función | mensaje
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s - %(message)s"
    )

    # Manejador con flush inmediato tras cada registro, modo append
    file_handler = ImmediateFileHandler(log_filepath, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Evitar handlers duplicados si setup_logging() se llama más de una vez
    if not any(isinstance(h, ImmediateFileHandler) for h in root_logger.handlers):
        root_logger.addHandler(file_handler)

    root_logger.info("Sistema de logging iniciado. Archivo: %s", log_filepath)
    root_logger.info(
        "Modo escritura: append + flush inmediato por registro "
        "(sin pérdida de datos en caso de cierre inesperado)"
    )

    return root_logger
