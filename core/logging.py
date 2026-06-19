import json
import logging


class JSONFormatter(logging.Formatter):
    """Formatador de logs em formato JSON estruturado."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Evita incluir chaves padrão do LogRecord para focar nas chaves passadas via `extra`
        standard_attrs = {
            "args",
            "asctime",
            "created",
            "exc_info",
            "exc_text",
            "filename",
            "funcName",
            "levelname",
            "levelno",
            "lineno",
            "module",
            "msecs",
            "message",
            "msg",
            "name",
            "pathname",
            "process",
            "processName",
            "relativeCreated",
            "stack_info",
            "thread",
            "threadName",
        }

        for key, val in record.__dict__.items():
            if key not in standard_attrs and not key.startswith("_"):
                log_data[key] = val

        return json.dumps(log_data, default=str, ensure_ascii=False)
