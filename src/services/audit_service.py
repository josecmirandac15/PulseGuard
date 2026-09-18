import json
import os
from datetime import datetime
from typing import List
from ..agent.models import AuditLog


class AuditService:
    def __init__(self):
        self.data_dir = os.path.join(os.path.dirname(__file__), "../../data")
        self.audit_file = os.path.join(self.data_dir, "audit_logs.json")
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.audit_file):
            with open(self.audit_file, "w") as f:
                json.dump([], f)

    def _load_logs(self) -> List[dict]:
        with open(self.audit_file, "r") as f:
            return json.load(f)

    def _save_logs(self, logs: List[dict]):
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(self.audit_file, "w") as f:
            json.dump(logs, f, indent=2, default=serialize_datetime)

    def log_action(self, admission_id: str, action: str, details: dict) -> AuditLog:
        import uuid
        log = AuditLog(
            log_id=str(uuid.uuid4()),
            admission_id=admission_id,
            agent_action=action,
            details=details,
            timestamp=datetime.now()
        )

        logs = self._load_logs()
        logs.append(log.model_dump())
        self._save_logs(logs)

        return log

    def get_logs_by_admission(self, admission_id: str) -> List[AuditLog]:
        logs = self._load_logs()
        return [AuditLog(**log) for log in logs if log["admission_id"] == admission_id]

    def get_all_logs(self) -> List[AuditLog]:
        logs = self._load_logs()
        return [AuditLog(**log) for log in logs]
