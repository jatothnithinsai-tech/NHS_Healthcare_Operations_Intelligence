import json
import logging
from datetime import datetime, timezone
from src.ingestion.acquire import ROOT


class JSONFormatter(logging.Formatter):
    def format(self, record):
        result = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname, "logger": record.name, "message": record.getMessage()}
        for key in ("dataset", "month", "revised", "rows", "run_id"):
            if hasattr(record, key):
                result[key] = getattr(record, key)
        if record.exc_info:
            result["exception"] = self.formatException(record.exc_info)
        return json.dumps(result)


def configure_logging():
    (ROOT / "logs").mkdir(exist_ok=True)
    handler = logging.FileHandler(ROOT / "logs/pipeline.jsonl", encoding="utf-8")
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(level=logging.INFO, handlers=[handler, logging.StreamHandler()], force=True)
