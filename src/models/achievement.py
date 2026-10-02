"""
Achievement models for LifeHunter system.

This module defines the Achievement and PlayerAchievement entities for
tracking player milestones and accomplishments.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base


class Achievement(Base):
    """
    Achievement entity representing a milestone that players can unlock.
    
    Achievements are categorized by rarity and can grant permanent stat bonuses
    when unlocked.
    
    Attributes:
        id: Primary key
        name: Achievement name
        description: Achievement description and requirements
        rarity: Achievement rarity tier (common/rare/epic/legendary)
        condition_type: Type of unlock condition (level/quest_count/stat/custom)
        condition_value: JSON string containing condition data
        stat_bonus: JSON string containing stat bonus data (optional)
        icon_url: Path to achievement icon image
    """
    __tablename__ = 'achievements'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Achievement properties
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    rarity = Column(String(20), nullable=False)  # common/rare/epic/legendary
    
    # Unlock conditions
    condition_type = Column(String(50), nullable=False)  # level/quest_count/stat/custom
    condition_value = Column(Text, nullable=False)  # JSON encoded condition data
    
    # Rewards
    stat_bonus = Column(Text, nullable=True)  # JSON encoded stat bonus data
    
    # Display
    icon_url = Column(String(255), nullable=True)
    
    # Relationships
    player_achievements = relationship('PlayerAchievement', back_populates='achievement', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Achievement(id={self.id}, name='{self.name}', rarity='{self.rarity}')>"


class PlayerAchievement(Base):
    """
    PlayerAchievement entity representing a player's unlocked achievement.
    
    Tracks when a player unlocked a specific achievement.
    
    Attributes:
        id: Primary key
        player_id: Foreign key to Player
        achievement_id: Foreign key to Achievement
        unlocked_at: Timestamp when achievement was unlocked
    """
    __tablename__ = 'player_achievements'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    achievement_id = Column(Integer, ForeignKey('achievements.id'), nullable=False)
    
    # Timestamps
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    player = relationship('Player', back_populates='player_achievements')
    achievement = relationship('Achievement', back_populates='player_achievements')
    
    def __repr__(self):
        return f"<PlayerAchievement(player_id={self.player_id}, achievement_id={self.achievement_id})>"
