import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.models import PushEvent


class PushEventRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, push_event: PushEvent) -> PushEvent:
        self.db.add(push_event)
        self.db.commit()
        self.db.refresh(push_event)
        return push_event

    def get_by_id(self, push_id: uuid.UUID) -> Optional[PushEvent]:
        return self.db.query(PushEvent).filter(PushEvent.id == push_id).first()

    def list_by_run(self, run_id: uuid.UUID) -> List[PushEvent]:
        return (
            self.db.query(PushEvent)
            .filter(PushEvent.run_id == run_id)
            .order_by(PushEvent.step_no.desc(), PushEvent.created_at.desc())
            .all()
        )

    def list_by_run_and_step(self, run_id: uuid.UUID, step_no: int) -> List[PushEvent]:
        return (
            self.db.query(PushEvent)
            .filter(PushEvent.run_id == run_id, PushEvent.step_no == step_no)
            .order_by(PushEvent.created_at.desc())
            .all()
        )

    def update_status(self, push_id: uuid.UUID, status) -> Optional[PushEvent]:
        push = self.get_by_id(push_id)
        if push:
            push.status = status
            self.db.commit()
            self.db.refresh(push)
        return push

    def create_from_replay(self, original: PushEvent) -> PushEvent:
        from app.models.models import PushEventStatus
        import datetime
        new_push = PushEvent(
            id=uuid.uuid4(),
            run_id=original.run_id,
            step_no=original.step_no,
            platform=original.platform,
            event_type=original.event_type,
            status=PushEventStatus.REPLAYED,
            headers_json=original.headers_json,
            body_json=original.body_json,
            retry_count=0,
            created_at=datetime.datetime.now(datetime.timezone.utc),
        )
        self.db.add(new_push)
        self.db.commit()
        self.db.refresh(new_push)
        return new_push
