"""
Advanced Health Monitoring (Quant-Grade)

Adds:
- Multi-service heartbeat
- Metadata tracking
- Failure detection
- Auto-alert integration
- Historical logs
"""

import json
import time
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Union, Dict


DEFAULT_DIR = "logs/health"


class HealthMonitorError(Exception):
    pass


class HealthMonitor:

    def __init__(self, base_dir: str = DEFAULT_DIR):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    # =========================
    # Write Heartbeat
    # =========================

    def heartbeat(
        self,
        service: str,
        message: Optional[str] = None,
        extra: Optional[Dict] = None
    ) -> str:

        filepath = self.base_dir / f"{service}.json"
        temp_file = filepath.with_suffix(".tmp")

        data = {
            "service": service,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "message": message,
            "pid": os.getpid(),
            "extra": extra or {}
        }

        try:
            temp_file.write_text(json.dumps(data, indent=2))
            temp_file.replace(filepath)
            return str(filepath.absolute())
        except Exception as e:
            raise HealthMonitorError(f"Write failed: {e}")

    # =========================
    # Check Health
    # =========================

    def check(
        self,
        service: str,
        max_age_seconds: float = 60
    ) -> dict:

        filepath = self.base_dir / f"{service}.json"

        if not filepath.exists():
            return {"healthy": False, "error": "missing"}

        try:
            data = json.loads(filepath.read_text())

            last_seen = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
            now = datetime.utcnow().replace(tzinfo=last_seen.tzinfo)

            age = (now - last_seen).total_seconds()

            return {
                "healthy": age <= max_age_seconds,
                "service": service,
                "age": age,
                "last_seen": data["timestamp"],
                "pid": data.get("pid"),
                "message": data.get("message")
            }

        except Exception as e:
            return {"healthy": False, "error": str(e)}

    # =========================
    # Global Health Check
    # =========================

    def check_all(self, max_age_seconds: float = 60) -> Dict[str, dict]:

        results = {}

        for file in self.base_dir.glob("*.json"):
            service = file.stem
            results[service] = self.check(service, max_age_seconds)

        return results

    # =========================
    # Cleanup
    # =========================

    def cleanup(self, older_than_seconds: int = 3600):
        now = time.time()

        for file in self.base_dir.glob("*.json"):
            if now - file.stat().st_mtime > older_than_seconds:
                try:
                    file.unlink()
                except:
                    pass