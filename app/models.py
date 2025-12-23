import uuid
from app import db
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone


def generate_uuid():
    return str(uuid.uuid4())


class Transcript(db.Model):
    __tablename__ = 'transcripts'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.String(36), nullable=False, index=True)
    session_id = db.Column(db.String, nullable=False, index=True, default=generate_uuid())
    transcript_text = db.Column(db.Text, nullable=False, index=True)
    extra_data = db.Column(JSONB, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))
    deleted_at = db.Column(db.DateTime, default=None, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "transcript_text": self.transcript_text,
            "extra_data": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
