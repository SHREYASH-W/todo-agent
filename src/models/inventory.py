"""
Inventory model for LifeHunter system.

This module defines the InventoryItem entity for managing player items
including templates, certificates, and consumables.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base


class InventoryItem(Base):
    """
    InventoryItem entity representing an item in a player's inventory.
    
    Supports three item categories:
    - template: Reusable document templates (resumes, cover letters)
    - certificate: Achievement certificates and credentials
    - consumable: Single-use items that are removed after use
    
    Attributes:
        id: Primary key
        player_id: Foreign key to Player
        item_type: Category of item (template/certificate/consumable)
        name: Item name/title
        content: Item content (text content or file path)
        acquired_at: Timestamp when item was acquired
        used_at: Optional timestamp when consumable was used
    """
    __tablename__ = 'inventory_items'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign keys
    player_id = Column(Integer, ForeignKey('players.id'), nullable=False)
    
    # Item properties
    item_type = Column(String(20), nullable=False)  # template/certificate/consumable
    name = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)  # Text content or file path
    
    # Timestamps
    acquired_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    used_at = Column(DateTime, nullable=True)  # For consumables
    
    # Relationships
    player = relationship('Player', back_populates='inventory_items')
    
    def __repr__(self):
        return f"<InventoryItem(id={self.id}, name='{self.name}', type='{self.item_type}', player_id={self.player_id})>"
