"""
Database models for the Machine Downtime Log application.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean
from .database import Base


class DowntimeEvent(Base):
    """Model representing a machine downtime event."""
    __tablename__ = "downtime_events"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(50), nullable=False, index=True)
    machine_type = Column(String(100), nullable=False)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    downtime_minutes = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    reason_category = Column(String(50), nullable=True)
    severity = Column(String(20), nullable=True)
    manual_note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "downtime_minutes": self.downtime_minutes,
            "description": self.description,
            "reason_category": self.reason_category,
            "severity": self.severity,
            "manual_note": self.manual_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class EventStream(Base):
    """Model representing raw events from the event stream."""
    __tablename__ = "event_stream"

    id = Column(Integer, primary_key=True, index=True)
    machine_id = Column(String(50), nullable=False, index=True)
    machine_type = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)  # start, stop, etc.
    description = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    processed = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        """Convert model instance to dictionary."""
        return {
            "id": self.id,
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "event_type": self.event_type,
            "description": self.description,
            "latency_ms": self.latency_ms,
            "processed": self.processed,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }