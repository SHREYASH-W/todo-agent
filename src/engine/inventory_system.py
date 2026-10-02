"""
Inventory System for LifeHunter System

Manages player inventory with categories: templates, certificates, consumables.
Capacity: 100 items per category.

Requirements: 12.1-12.7
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

ITEM_CATEGORIES = {"template", "certificate", "consumable"}
MAX_ITEMS_PER_CATEGORY = 100  # Requirement 12.5


class InventorySystem:
    """Manages player inventory items."""

    def get_category_count(self, items: List[Dict], category: str) -> int:
        """Count items in a specific category."""
        return sum(1 for item in items if item.get("item_type") == category)

    def add_item(
        self,
        player_id: int,
        item_data: Dict[str, Any],
        current_items: List[Dict],
    ) -> Optional[Dict[str, Any]]:
        """
        Add an item to the player's inventory.

        Requirements 12.2, 12.5.

        Args:
            player_id: Player ID
            item_data: Dict with name, item_type, content
            current_items: Current inventory items for capacity check

        Returns:
            Dict: New InventoryItem record, or None if category is full
        """
        item_type = item_data.get("item_type", "consumable")
        if item_type not in ITEM_CATEGORIES:
            logger.warning(f"Invalid item category: {item_type}")
            return None

        count = self.get_category_count(current_items, item_type)
        if count >= MAX_ITEMS_PER_CATEGORY:
            logger.warning(
                f"Inventory full for category '{item_type}' "
                f"(max {MAX_ITEMS_PER_CATEGORY} per category)"
            )
            return None

        item = {
            "player_id": player_id,
            "item_type": item_type,
            "name": item_data.get("name", "Item"),
            "content": item_data.get("content", ""),
            "acquired_at": datetime.utcnow(),
            "used_at": None,
        }
        logger.info(f"Item added: '{item['name']}' ({item_type}) for player {player_id}")
        return item

    def remove_item(
        self,
        item_id: int,
        items: List[Dict],
    ) -> bool:
        """
        Remove an item from the inventory by marking it removed.

        Requirement 12.4.

        Returns:
            bool: True if item was found and removed
        """
        item = next((i for i in items if i.get("id") == item_id), None)
        if item is None:
            logger.warning(f"Item {item_id} not found in inventory")
            return False

        items.remove(item)
        logger.info(f"Item {item_id} removed from inventory")
        return True

    def use_consumable(
        self,
        item_id: int,
        items: List[Dict],
    ) -> Optional[Dict[str, Any]]:
        """
        Use a consumable item and mark it as used.

        Requirement 12.4.

        Returns:
            Dict: The used item, or None if not found or wrong type
        """
        item = next((i for i in items if i.get("id") == item_id), None)
        if item is None:
            logger.warning(f"Consumable {item_id} not found")
            return None
        if item.get("item_type") != "consumable":
            logger.warning(f"Item {item_id} is not a consumable")
            return None

        item["used_at"] = datetime.utcnow()
        items.remove(item)
        logger.info(f"Consumable used: '{item.get('name')}'")
        return item

    def search_items(
        self,
        items: List[Dict],
        query: str = "",
        category: Optional[str] = None,
    ) -> List[Dict]:
        """
        Search inventory items by name or category.

        Requirement 12.6.

        Args:
            items: All player inventory items
            query: Search string (matches item name case-insensitively)
            category: Optional category filter ('template', 'certificate', 'consumable')

        Returns:
            List[Dict]: Matching items
        """
        results = items

        if category and category in ITEM_CATEGORIES:
            results = [i for i in results if i.get("item_type") == category]

        if query:
            query_lower = query.lower()
            results = [i for i in results if query_lower in i.get("name", "").lower()]

        return results

    def get_items_by_category(self, items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Organize inventory items by category.

        Requirement 12.1, 12.3.

        Returns:
            Dict: {'template': [...], 'certificate': [...], 'consumable': [...]}
        """
        return {
            "template": [i for i in items if i.get("item_type") == "template"],
            "certificate": [i for i in items if i.get("item_type") == "certificate"],
            "consumable": [i for i in items if i.get("item_type") == "consumable"],
        }
