"""Database Backup Model"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from .base import Base


class DatabaseBackup(Base):
    """
    Database backup tracking model.
    Records information about database backup operations.
    """
    __tablename__ = 'database_backups'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<DatabaseBackup(id={self.id}, file_path='{self.file_path}', size={self.file_size}, created_at={self.created_at})>"
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
