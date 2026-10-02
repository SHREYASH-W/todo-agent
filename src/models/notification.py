"""
Notification model for LifeHunter system.

This module defines the Notification entity for managing player notifications
about events, achievements, and system updates.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base


class Notification(Base):
    """
    Notification entity representing a message to the player about system events.
    
    Notifications are generated for important events such as:
    - Quest completion
    - Level up and rank advancement
    - Achievement unlocks
    - Quest deadlines
    - System updates
    
    Attributes:
        id: Primary key
        player_id: Foreign key to Player
        notification_type: Category of notification (quest_complete/level_up/achievement/etc)
        title: Notification title/header
        message: Notification content/body
        is_read: Whether player has read the notification
        created_at: Notification creation timestamp
    """
    __tablename__ = 'notifications'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    
    # Notification properties
    notification_type = Column(String(50), nullable=False)  # quest_complete/level_up/achievement/deadline/etc
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    player = relationship('Player', back_populates='notifications')
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.notification_type}', title='{self.title}', read={self.is_read})>"
