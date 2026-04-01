from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import SimulationRun, RunStatus


class RunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        platform: str,
        run_code: str,
        account_id: Optional[UUID] = None,
        strict_mode: bool = True,
        push_enabled: bool = True,
        seed: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> SimulationRun:
        run = SimulationRun(
            platform=platform,
            run_code=run_code,
            account_id=account_id,
            strict_mode="1" if strict_mode else "0",
            push_enabled="1" if push_enabled else "0",
            seed=seed,
            metadata_json=metadata or {},
            status=RunStatus.CREATED,
            current_step=0,
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def get_by_id(self, run_id: UUID) -> Optional[SimulationRun]:
        stmt = select(SimulationRun).where(SimulationRun.id == run_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_run_code(self, run_code: str) -> Optional[SimulationRun]:
        stmt = select(SimulationRun).where(SimulationRun.run_code == run_code)
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_platform(
        self, platform: str, limit: int = 100, offset: int = 0
    ) -> List[SimulationRun]:
        stmt = (
            select(SimulationRun)
            .where(SimulationRun.platform == platform)
            .order_by(SimulationRun.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self.db.execute(stmt).scalars().all())

    def update_status(self, run_id: UUID, status: RunStatus) -> Optional[SimulationRun]:
        run = self.get_by_id(run_id)
        if run:
            run.status = status
            self.db.commit()
            self.db.refresh(run)
        return run

    def advance_step(self, run_id: UUID) -> Optional[SimulationRun]:
        run = self.get_by_id(run_id)
        if run:
            run.current_step += 1
            self.db.commit()
            self.db.refresh(run)
        return run

    def delete(self, run_id: UUID) -> bool:
        run = self.get_by_id(run_id)
        if run:
            self.db.delete(run)
            self.db.commit()
            return True
        return False
