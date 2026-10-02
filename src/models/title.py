"""
Title models for LifeHunter system.

This module defines the Title and PlayerTitle entities for managing
player titles that provide stat bonuses.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base


class Title(Base):
    """
    Title entity representing an earned designation that provides stat bonuses.
    
    Players can unlock titles through various achievements and activities.
    Only one title can be equipped at a time, and equipped titles apply
    their stat bonuses to the player.
    
    Attributes:
        id: Primary key
        name: Title name
        description: Title description and flavor text
        unlock_condition: Description of how to unlock the title
        stat_bonuses: JSON string containing stat bonus data
    """
    __tablename__ = 'titles'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Title properties
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=False)
    unlock_condition = Column(Text, nullable=False)
    
    # Bonuses
    stat_bonuses = Column(Text, nullable=False)  # JSON encoded stat bonus data
    
    # Relationships
    player_titles = relationship('PlayerTitle', back_populates='title', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Title(id={self.id}, name='{self.name}')>"


class PlayerTitle(Base):
    """
    PlayerTitle entity representing a player's unlocked title.
    
    Tracks when a player unlocked a specific title. The player can equip
    one title at a time through the Player.active_title_id field.
    
    Attributes:
        id: Primary key
        player_id: Foreign key to Player
        title_id: Foreign key to Title
        unlocked_at: Timestamp when title was unlocked
    """
    __tablename__ = 'player_titles'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    title_id = Column(Integer, ForeignKey('titles.id'), nullable=False)
    
    # Timestamps
    unlocked_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    player = relationship('Player', back_populates='player_titles')
    title = relationship('Title', back_populates='player_titles')
    
    def __repr__(self):
        return f"<PlayerTitle(player_id={self.player_id}, title_id={self.title_id})>"
