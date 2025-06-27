import logging

from pathlib import Path

LOGS_DIR = Path("logs/")
LOGS_DIR.mkdir(parents=True, exist_ok=True)

formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

file_handler = logging.FileHandler(LOGS_DIR / "solver-bot.log", encoding="utf-8")
file_handler.setFormatter(formatter)

logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
