"""
Player model for LifeHunter system.

This module defines the core Player entity with progression stats, attributes,
and relationships to other game entities.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Player(Base):
    """
    Player entity representing a user in the LifeHunter system.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        password_hash: bcrypt hashed password
        created_at: Registration timestamp
        last_login: Last login timestamp
        
        # Progression attributes
        level: Current level (1-999)
        xp: Current experience points
        rank: Current rank (E/D/C/B/A/S/National)
        gold: Currency balance
        
        # Base stat attributes
        str_stat: Strength attribute
        int_stat: Intelligence attribute
        agi_stat: Agility attribute
        vit_stat: Vitality attribute
        sen_stat: Sense attribute
        luk_stat: Luck attribute
        
        # Derived stat attributes
        hp: Health points (calculated from VIT)
        mp: Mana points (calculated from INT)
        
        # Available points
        stat_points: Available stat points for allocation
        skill_points: Available skill points for allocation
        
        # Active title
        active_title_id: Foreign key to currently equipped Title
    """
    __tablename__ = 'players'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Authentication
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Progression
    level = Column(Integer, default=1, nullable=False)
    xp = Column(Integer, default=0, nullable=False)
    rank = Column(String(20), default='E', nullable=False)
    gold = Column(Integer, default=0, nullable=False)
    
    # Base stats (all start at 10)
    str_stat = Column(Integer, default=10, nullable=False)
    int_stat = Column(Integer, default=10, nullable=False)
    agi_stat = Column(Integer, default=10, nullable=False)
    vit_stat = Column(Integer, default=10, nullable=False)
    sen_stat = Column(Integer, default=10, nullable=False)
    luk_stat = Column(Integer, default=10, nullable=False)
    
    # Derived stats
    hp = Column(Integer, default=200, nullable=False)  # 100 + (10 * 10)
    mp = Column(Integer, default=100, nullable=False)  # 50 + (10 * 5)
    
    # Available points
    stat_points = Column(Integer, default=0, nullable=False)
    skill_points = Column(Integer, default=0, nullable=False)
    
    # Active title
    active_title_id = Column(Integer, ForeignKey('titles.id'), nullable=True)
    
    # Relationships
    quests = relationship('Quest', back_populates='player', cascade='all, delete-orphan')
    player_skills = relationship('PlayerSkill', back_populates='player', cascade='all, delete-orphan')
    player_achievements = relationship('PlayerAchievement', back_populates='player', cascade='all, delete-orphan')
    player_titles = relationship('PlayerTitle', back_populates='player', cascade='all, delete-orphan')
    inventory_items = relationship('InventoryItem', back_populates='player', cascade='all, delete-orphan')
    notifications = relationship('Notification', back_populates='player', cascade='all, delete-orphan')
    job_matches = relationship('JobMatch', back_populates='player', cascade='all, delete-orphan')
    applications = relationship('Application', back_populates='player', cascade='all, delete-orphan')
    active_title = relationship('Title', foreign_keys=[active_title_id])
    
    def __repr__(self):
        return f"<Player(id={self.id}, username='{self.username}', level={self.level}, rank='{self.rank}')>"
