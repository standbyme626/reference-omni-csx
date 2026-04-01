import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session

from app.models.models import Artifact, ArtifactType


class ArtifactBuilder:
    def __init__(self, db: Session):
        self.db = db

    def build_api_response(
        self,
        run_id: uuid.UUID,
        step_no: int,
        platform: str,
        route_key: str,
        request_headers: Dict[str, Any],
        request_body: Dict[str, Any],
        response_headers: Dict[str, Any],
        response_body: Dict[str, Any],
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            run_id=run_id,
            step_no=step_no,
            platform=platform,
            artifact_type=ArtifactType.API_RESPONSE,
            route_key=route_key,
            request_headers_json=request_headers,
            request_body_json=request_body,
            response_headers_json=response_headers,
            response_body_json=response_body,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def build_callback(
        self,
        run_id: uuid.UUID,
        step_no: int,
        platform: str,
        route_key: str,
        request_body: Dict[str, Any],
        response_body: Dict[str, Any],
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            run_id=run_id,
            step_no=step_no,
            platform=platform,
            artifact_type=ArtifactType.CALLBACK,
            route_key=route_key,
            request_body_json=request_body,
            response_body_json=response_body,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def build_webhook(
        self,
        run_id: uuid.UUID,
        step_no: int,
        platform: str,
        event_type: str,
        request_body: Dict[str, Any],
        response_body: Dict[str, Any],
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            run_id=run_id,
            step_no=step_no,
            platform=platform,
            artifact_type=ArtifactType.WEBHOOK,
            route_key=event_type,
            request_body_json=request_body,
            response_body_json=response_body,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def build_message_sync(
        self,
        run_id: uuid.UUID,
        step_no: int,
        platform: str,
        request_body: Dict[str, Any],
        response_body: Dict[str, Any],
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            run_id=run_id,
            step_no=step_no,
            platform=platform,
            artifact_type=ArtifactType.MESSAGE_SYNC,
            request_body_json=request_body,
            response_body_json=response_body,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

    def build_error_response(
        self,
        run_id: uuid.UUID,
        step_no: int,
        platform: str,
        route_key: str,
        error_code: str,
        error_message: str,
        http_status: int,
    ) -> Artifact:
        artifact = Artifact(
            id=uuid.uuid4(),
            run_id=run_id,
            step_no=step_no,
            platform=platform,
            artifact_type=ArtifactType.ERROR_RESPONSE,
            route_key=route_key,
            request_body_json={"error_code": error_code},
            response_body_json={
                "error": error_code,
                "message": error_message,
                "http_status": http_status,
            },
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(artifact)
        self.db.commit()
        self.db.refresh(artifact)
        return artifact

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
