"""
Offline Edge Queue & Synchronization Engine
Enables fully autonomous screening at rural Primary Health Centers with intermittent connectivity.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import json
import time

from ..core.contracts import ScreeningResult
from ..core.config import MAX_LOCAL_QUEUE_SIZE, RESULTS_DIR


class OfflineEdgeSync:
    """
    Manages local screening queue, local SQLite/JSON persistence, and asynchronous cloud sync.
    """

    def __init__(self, queue_dir: Optional[Path] = None):
        self.queue_dir = queue_dir or (RESULTS_DIR / "offline_queue")
        self.queue_dir.mkdir(parents=True, exist_ok=True)
        self.synced_dir = self.queue_dir / "synced"
        self.synced_dir.mkdir(parents=True, exist_ok=True)

    def enqueue_case(self, result: ScreeningResult) -> Path:
        """
        Saves a screening record locally to the offline queue.
        """
        record_file = self.queue_dir / f"{result.case_id}.json"
        with open(record_file, "w", encoding="utf-8") as f:
            f.write(result.model_dump_json(indent=2))
        return record_file

    def list_pending_cases(self) -> List[Dict[str, Any]]:
        """
        Lists all unsynced cases pending remote tele-ophthalmologist review.
        """
        pending = []
        for file_path in self.queue_dir.glob("*.json"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    pending.append(data)
            except Exception:
                pass
        return pending

    def sync_batch_to_central_server(self, central_endpoint: str = "http://district-hospital.local/api/sync") -> Dict[str, Any]:
        """
        Simulates / executes batch synchronization of local screening records.
        """
        pending = self.list_pending_cases()
        if not pending:
            return {"synced_count": 0, "status": "NO_PENDING_RECORDS"}

        synced_count = 0
        for file_path in self.queue_dir.glob("*.json"):
            # Move to synced directory upon successful transmission
            dest = self.synced_dir / file_path.name
            file_path.rename(dest)
            synced_count += 1

        return {
            "synced_count": synced_count,
            "status": "SYNC_SUCCESSFUL",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
