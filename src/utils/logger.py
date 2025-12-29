from loguru import logger
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure logger
logger.add(
    log_dir / "runtime.log",
    rotation="1 day",       # new file each day
    retention="7 days",     # keep logs for a week
    level="INFO",
    backtrace=True,
    diagnose=True
)

log = logger