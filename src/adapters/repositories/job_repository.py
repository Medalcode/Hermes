import uuid
from typing import Any


class JobRepository:
    def __init__(self) -> None:
        self._jobs: dict[str, dict[str, Any]] = {}

    def create_job(self, skill_id: str, params: dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "job_id": job_id,
            "skill_id": skill_id,
            "params": params,
            "status": "pending",
            "result": None,
            "error": None,
        }
        return job_id

    def update_status(
        self, job_id: str, status: str, result: Any = None, error: str | None = None
    ) -> None:
        if job_id in self._jobs:
            self._jobs[job_id]["status"] = status
            if result is not None:
                self._jobs[job_id]["result"] = result
            if error is not None:
                self._jobs[job_id]["error"] = error

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        return self._jobs.get(job_id)


_job_repo_instance = JobRepository()


def get_job_repository() -> JobRepository:
    return _job_repo_instance
