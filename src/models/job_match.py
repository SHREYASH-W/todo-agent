"""JobMatch Model for Career Hunter Module"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship

from .base import Base


class JobMatch(Base):
    """JobMatch entity representing AI-calculated job matches.
    
    Stores match scores between players and jobs based on skill analysis.
    The match_score ranges from 0-100, with higher scores indicating better fits.
    
    Attributes:
        id (int): Primary key
        player_id (int): Foreign key to Player
        job_id (int): Foreign key to Job
        match_score (int): Match score (0-100)
        matching_skills (str): JSON array of matching skills
        calculated_at (datetime): Timestamp when match was calculated
        
    Relationships:
        player: Associated Player record
        job: Associated Job record
    """
    
    __tablename__ = "job_matches"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    player_id = Column(Integer, ForeignKey("players.id"), nullable=False, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=False, index=True)
    
    # Match Data
    match_score = Column(
        Integer, 
        nullable=False, 
        index=True
    )
    matching_skills = Column(String(1000), nullable=False)  # JSON array as string
    
    # Timestamp
    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('match_score >= 0 AND match_score <= 100', name='check_match_score_range'),
    )
    
    # Relationships
    player = relationship("Player", back_populates="job_matches")
    job = relationship("Job", back_populates="job_matches")
    
    def __repr__(self):
        return f"<JobMatch(id={self.id}, player_id={self.player_id}, job_id={self.job_id}, score={self.match_score})>"
    
    def to_dict(self):
        """Convert JobMatch instance to dictionary.
        
        Returns:
            dict: JobMatch data as dictionary
        """
        return {
            "id": self.id,
            "player_id": self.player_id,
            "job_id": self.job_id,
            "match_score": self.match_score,
            "matching_skills": self.matching_skills,
            "calculated_at": self.calculated_at.isoformat() if self.calculated_at else None,
        }
