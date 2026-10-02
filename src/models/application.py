"""Application Model for Career Hunter Module"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base


class Application(Base):
    """Application entity representing job applications.
    
    Tracks player job applications with status, cover letters, and interview details.
    Supports the application lifecycle from submission through to offer or rejection.
    
    Attributes:
        id (int): Primary key
        player_id (int): Foreign key to Player
        job_id (int): Foreign key to Job
        status (str): Application status (submitted/under_review/interview/rejected/offered)
        cover_letter (str): Generated cover letter text
        submitted_at (datetime): Submission timestamp
        updated_at (datetime): Last status update timestamp
        interview_date (datetime): Interview date (optional)
        notes (str): Player notes (optional)
        
    Relationships:
        player: Associated Player record
        job: Associated Job record
    """
    
    __tablename__ = "applications"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Application Status
    status = Column(
        String(50), 
        nullable=False, 
        default="submitted",
        index=True
    )
    
    # Application Content
    cover_letter = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    
    # Timestamps
    submitted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    interview_date = Column(DateTime, nullable=True)
    
    # Relationships
    player = relationship("Player", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    
    def __repr__(self):
        return f"<Application(id={self.id}, player_id={self.player_id}, job_id={self.job_id}, status='{self.status}')>"
    
    def to_dict(self):
        """Convert Application instance to dictionary.
        
        Returns:
            dict: Application data as dictionary
        """
        return {
            "id": self.id,
            "player_id": self.player_id,
            "job_id": self.job_id,
            "status": self.status,
            "cover_letter": self.cover_letter,
            "notes": self.notes,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "interview_date": self.interview_date.isoformat() if self.interview_date else None,
        }
    
    @property
    def is_active(self):
        """Check if application is still active (not rejected or offered).
        
        Returns:
            bool: True if status is submitted, under_review, or interview
        """
        return self.status in ["submitted", "under_review", "interview"]
