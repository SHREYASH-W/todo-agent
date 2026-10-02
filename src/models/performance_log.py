"""Performance Log Model"""
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from .base import Base


class PerformanceLog(Base):
    """
    Performance logging model for system monitoring.
    Tracks performance metrics over time for system optimization.
    """
    __tablename__ = 'performance_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<PerformanceLog(id={self.id}, metric='{self.metric_name}', value={self.metric_value}, timestamp={self.timestamp})>"
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'metric_value': self.metric_value,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
