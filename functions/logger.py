"""
Sistema de logging centralizado do Eclipse Store Bot.
Substitui todos os print() dispersos pela source.

Uso:
    from functions.logger import get_logger
    logger = get_logger(__name__)
    logger.info("mensagem")
    logger.error("erro", exc_info=True)
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_configured = False


def setup_logging(level: str = "INFO") -> None:
    """Configura handlers de logging (chamar uma vez no startup)."""
    global _configured
    if _configured:
        return
    _configured = True

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger("eclipse_store")
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(numeric_level)
    console.setFormatter(fmt)
    root.addHandler(console)

    try:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            log_dir / "bot.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        root.addHandler(file_handler)
    except Exception:
        pass


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger filho do namespace eclipse_store."""
    if not name.startswith("eclipse_store"):
        name = f"eclipse_store.{name}"
    return logging.getLogger(name)
