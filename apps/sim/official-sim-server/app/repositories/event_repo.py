from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import SimulationEvent


class EventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        run_id: UUID,
        step_no: int,
        event_type: str,
        source_type: Optional[str] = None,
        payload: Optional[dict] = None,
    ) -> SimulationEvent:
        event = SimulationEvent(
            run_id=run_id,
            step_no=step_no,
            event_type=event_type,
            source_type=source_type,
            payload_json=payload or {},
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def list_by_run(self, run_id: UUID) -> List[SimulationEvent]:
        stmt = (
            select(SimulationEvent)
            .where(SimulationEvent.run_id == run_id)
            .order_by(SimulationEvent.step_no)
        )
        return list(self.db.execute(stmt).scalars().all())
