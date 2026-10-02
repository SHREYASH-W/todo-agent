"""
Skill models for LifeHunter system.

This module defines the Skill and PlayerSkill entities for managing
player abilities and skill progression.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base


class Skill(Base):
    """
    Skill entity representing an ability that players can unlock and upgrade.
    
    Skills can be either active (require player activation) or passive
    (automatically apply bonuses).
    
    Attributes:
        id: Primary key
        name: Skill name
        description: Skill description and effects
        skill_type: Type of skill (active/passive)
        max_level: Maximum skill level (typically 10)
        unlock_level: Player level required to unlock
        prerequisite_skill_id: Optional required skill to unlock first
    """
    __tablename__ = 'skills'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Skill properties
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    skill_type = Column(String(20), nullable=False)  # active/passive
    
    # Progression
    max_level = Column(Integer, default=10, nullable=False)
    unlock_level = Column(Integer, default=1, nullable=False)
    
    # Prerequisites
    prerequisite_skill_id = Column(Integer, ForeignKey('skills.id'), nullable=True)
    
    # Relationships
    player_skills = relationship('PlayerSkill', back_populates='skill', cascade='all, delete-orphan')
    prerequisite_skill = relationship('Skill', remote_side=[id], backref='unlocks')
    
    def __repr__(self):
        return f"<Skill(id={self.id}, name='{self.name}', type='{self.skill_type}', unlock_level={self.unlock_level})>"


class PlayerSkill(Base):
    """
    PlayerSkill entity representing a player's unlocked skill and its current level.
    
    Tracks when a skill was unlocked and the player's current proficiency level
    in that skill.
    
    Attributes:
        id: Primary key
        player_id: Foreign key to Player
        skill_id: Foreign key to Skill
        current_level: Current skill level (1 to max_level)
        unlocked_at: Timestamp when skill was unlocked
    """
    __tablename__ = 'player_skills'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id'), nullable=False)
    
    # Skill progression
    current_level = Column(Integer, default=1, nullable=False)
    
    # Timestamps
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    player = relationship('Player', back_populates='player_skills')
    skill = relationship('Skill', back_populates='player_skills')
    
    def __repr__(self):
        return f"<PlayerSkill(player_id={self.player_id}, skill_id={self.skill_id}, level={self.current_level})>"
