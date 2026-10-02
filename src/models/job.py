"""Job Model for Career Hunter Module"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship

from .base import Base


class Job(Base):
    """Job entity representing scraped job listings.
    
    Stores job postings scraped from various sources (LinkedIn, Indeed, etc.)
    for matching with player skills and career goals.
    
    Attributes:
        id (int): Primary key
        source (str): Job source platform (linkedin/indeed/other)
        title (str): Job title
        company (str): Company name
        location (str): Job location
        description (str): Full job description text
        url (str): Original job posting URL
        posted_date (datetime): Date job was posted (if available)
        scraped_at (datetime): Timestamp when job was scraped
        
    Relationships:
        job_matches: JobMatch records for this job
        applications: Application records for this job
    """
    
    __tablename__ = "jobs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Job Source
    source = Column(String(50), nullable=False, index=True)
    
    # Job Details
    title = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=False, index=True)
    location = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    
    # Timestamps
    posted_date = Column(DateTime, nullable=True)
    scraped_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    job_matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Job(id={self.id}, title='{self.title}', company='{self.company}', source='{self.source}')>"
    
    def to_dict(self):
        """Convert Job instance to dictionary.
        
        Returns:
            dict: Job data as dictionary
        """
        return {
            "id": self.id,
            "source": self.source,
            "title": self.title,
            "company": self.company,
            "location": self.location,
            "description": self.description,
            "url": self.url,
            "posted_date": self.posted_date.isoformat() if self.posted_date else None,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
        }
