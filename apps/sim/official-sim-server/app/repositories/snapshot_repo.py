from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.models import StateSnapshot


class SnapshotRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        run_id: UUID,
        step_no: int,
        auth_state: Optional[dict] = None,
        order_state: Optional[dict] = None,
        shipment_state: Optional[dict] = None,
        after_sale_state: Optional[dict] = None,
        conversation_state: Optional[dict] = None,
        push_state: Optional[dict] = None,
    ) -> StateSnapshot:
        snapshot = StateSnapshot(
            run_id=run_id,
            step_no=step_no,
            auth_state_json=auth_state or {},
            order_state_json=order_state or {},
            shipment_state_json=shipment_state or {},
            after_sale_state_json=after_sale_state or {},
            conversation_state_json=conversation_state or {},
            push_state_json=push_state or {},
        )
        self.db.add(snapshot)
        self.db.commit()
        self.db.refresh(snapshot)
        return snapshot

    def get_latest(self, run_id: UUID) -> Optional[StateSnapshot]:
        stmt = (
            select(StateSnapshot)
            .where(StateSnapshot.run_id == run_id)
            .order_by(StateSnapshot.step_no.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def get_by_step(self, run_id: UUID, step_no: int) -> Optional[StateSnapshot]:
        stmt = select(StateSnapshot).where(
            StateSnapshot.run_id == run_id,
            StateSnapshot.step_no == step_no,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_by_run(self, run_id: UUID) -> List[StateSnapshot]:
        stmt = (
            select(StateSnapshot)
            .where(StateSnapshot.run_id == run_id)
            .order_by(StateSnapshot.step_no)
        )
        return list(self.db.execute(stmt).scalars().all())
