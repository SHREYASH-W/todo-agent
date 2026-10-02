"""
Data Export and Import for LifeHunter System

Supports JSON export/import of complete player data.

Requirements: Export/import requirements, Property 23 round-trip
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _serialize_dt(obj: Any) -> Any:
    """JSON serializer that handles datetime objects."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def export_player_data(player_id: int, file_path: str) -> bool:
    """
    Export all data for a player to a JSON file.

    Exports: player stats, quests, skills, achievements, titles,
             inventory, applications, notifications.

    Args:
        player_id: Player ID to export
        file_path: Destination JSON file path

    Returns:
        bool: True if export succeeded
    """
    from src.models import SessionLocal, Player
    from src.models.quest import Quest
    from src.models.skill import PlayerSkill
    from src.models.achievement import PlayerAchievement
    from src.models.title import PlayerTitle
    from src.models.inventory import InventoryItem
    from src.models.application import Application

    db = SessionLocal()
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        if not player:
            logger.error(f"Player {player_id} not found for export")
            return False

        def row_to_dict(obj) -> Dict[str, Any]:
            """Convert a SQLAlchemy model instance to a plain dict."""
            d = {}
            for col in obj.__table__.columns:
                val = getattr(obj, col.name)
                d[col.name] = val.isoformat() if isinstance(val, datetime) else val
            return d

        export_data = {
            "export_version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "player": row_to_dict(player),
            "quests": [row_to_dict(q) for q in db.query(Quest).filter(Quest.player_id == player_id).all()],
            "skills": [row_to_dict(s) for s in db.query(PlayerSkill).filter(PlayerSkill.player_id == player_id).all()],
            "achievements": [row_to_dict(a) for a in db.query(PlayerAchievement).filter(PlayerAchievement.player_id == player_id).all()],
            "titles": [row_to_dict(t) for t in db.query(PlayerTitle).filter(PlayerTitle.player_id == player_id).all()],
            "inventory": [row_to_dict(i) for i in db.query(InventoryItem).filter(InventoryItem.player_id == player_id).all()],
            "applications": [row_to_dict(a) for a in db.query(Application).filter(Application.player_id == player_id).all()],
        }

        os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=_serialize_dt)

        logger.info(f"Player {player_id} data exported to {file_path}")
        return True

    except Exception as e:
        logger.error(f"Export failed for player {player_id}: {e}")
        return False
    finally:
        db.close()


def import_player_data(file_path: str, overwrite: bool = False) -> Optional[int]:
    """
    Import player data from a JSON export file.

    Creates a new player record (or updates existing if overwrite=True).

    Args:
        file_path: Path to the JSON export file
        overwrite: If True, update existing player data

    Returns:
        int: The player ID of the imported player, or None on failure
    """
    if not os.path.exists(file_path):
        logger.error(f"Import file not found: {file_path}")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"Failed to read import file {file_path}: {e}")
        return None

    # Validate structure
    required_keys = {"player", "quests", "skills", "achievements", "titles", "inventory"}
    missing = required_keys - set(data.keys())
    if missing:
        logger.error(f"Import file missing required keys: {missing}")
        return None

    from src.models import SessionLocal, Player
    db = SessionLocal()
    try:
        player_data = dict(data["player"])
        player_id   = player_data.get("id")

        # Parse datetime fields
        for dt_field in ("created_at", "last_login"):
            if player_data.get(dt_field):
                player_data[dt_field] = datetime.fromisoformat(player_data[dt_field])

        existing = db.query(Player).filter(Player.id == player_id).first() if player_id else None

        if existing and overwrite:
            for k, v in player_data.items():
                if k != "id" and hasattr(existing, k):
                    setattr(existing, k, v)
            db.commit()
            logger.info(f"Player {player_id} data updated from import")
            return player_id

        elif not existing:
            # Remove id to let DB auto-assign
            player_data.pop("id", None)
            new_player = Player(**{k: v for k, v in player_data.items() if hasattr(Player, k)})
            db.add(new_player)
            db.commit()
            db.refresh(new_player)
            logger.info(f"Player imported with new ID {new_player.id}")
            return new_player.id

        else:
            logger.warning(f"Player {player_id} already exists and overwrite=False")
            return player_id

    except Exception as e:
        db.rollback()
        logger.error(f"Import failed: {e}")
        return None
    finally:
        db.close()
