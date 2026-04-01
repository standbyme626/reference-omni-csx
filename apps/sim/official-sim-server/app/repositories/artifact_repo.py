import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.models import Artifact, ArtifactType


class ArtifactRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        run_id: uuid.UUID,
        step_no: int,
        platform: str,
        artifact_type: str,
        route_key: Optional[str] = None,
        request_headers: Optional[Dict[str, Any]] = None,
        request_body: Optional[Dict[str, Any]] = None,
        response_headers: Optional[Dict[str, Any]] = None,
        response_body: Optional[Dict[str, Any]] = None,
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            run_id=run_id,
            step_no=step_no,
            platform=platform,
            artifact_type=ArtifactType(artifact_type),
            route_key=route_key,
            request_headers_json=request_headers or {},
            request_body_json=request_body or {},
            response_headers_json=response_headers or {},
            response_body_json=response_body or {},
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def get_by_id(self, artifact_id: uuid.UUID) -> Optional[Artifact]:
        return self.db.query(Artifact).filter(Artifact.id == artifact_id).first()

    def list_by_run(self, run_id: uuid.UUID) -> List[Artifact]:
        return (
            self.db.query(Artifact)
            .filter(Artifact.run_id == run_id)
            .order_by(Artifact.step_no.desc(), Artifact.created_at.desc())
            .all()
        )

    def list_by_run_and_step(self, run_id: uuid.UUID, step_no: int) -> List[Artifact]:
        return (
            self.db.query(Artifact)
            .filter(Artifact.run_id == run_id, Artifact.step_no == step_no)
            .order_by(Artifact.created_at.desc())
            .all()
        )

    def delete(self, artifact_id: uuid.UUID) -> bool:
        artifact = self.get_by_id(artifact_id)
        if artifact:
            self.db.delete(artifact)
            self.db.commit()
            return True
        return False
