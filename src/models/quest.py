"""
Quest model for LifeHunter system.

This module defines the Quest entity for tracking player tasks and objectives.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base


class Quest(Base):
    """
    Quest entity representing a task or objective for a player.
    
    Supports four quest types:
    - daily: Recurring tasks that refresh every 24 hours
    - main: Long-term goals composed of sub-quests
    - instant: Time-limited challenges (15 min - 4 hours)
    - emergency: Urgent high-priority tasks
    
    Attributes:
        id: Primary key
        player_id: Foreign key to Player
        quest_type: Type of quest (daily/main/instant/emergency)
        title: Quest title
        description: Detailed quest description
        xp_reward: Experience points awarded on completion
        gold_reward: Gold currency awarded on completion
        difficulty: Quest difficulty level
        status: Current quest status (active/completed/failed)
        created_at: Quest creation timestamp
        deadline: Optional completion deadline
        completed_at: Optional completion timestamp
        parent_quest_id: Optional foreign key for sub-quests
    """
    __tablename__ = 'quests'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    parent_quest_id = Column(Integer, ForeignKey('quests.id'), nullable=True)
    
    # Quest properties
    quest_type = Column(String(20), nullable=False)  # daily/main/instant/emergency
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    
    # Rewards
    xp_reward = Column(Integer, default=0, nullable=False)
    gold_reward = Column(Integer, default=0, nullable=False)
    
    # Status
    difficulty = Column(String(20), default='medium', nullable=False)  # very_easy/easy/medium/hard/very_hard
    status = Column(String(20), default='active', nullable=False)  # active/completed/failed
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    deadline = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    player = relationship('Player', back_populates='quests')
    sub_quests = relationship('Quest', 
                            backref='parent_quest',
                            remote_side=[id],
                            cascade='all, delete-orphan',
                            single_parent=True)
    
    def __repr__(self):
        return f"<Quest(id={self.id}, title='{self.title}', type='{self.quest_type}', status='{self.status}')>"
