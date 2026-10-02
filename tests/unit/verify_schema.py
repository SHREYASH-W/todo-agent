"""
Verify that ORM models match the design specifications.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import (
    Player, Quest, Skill, PlayerSkill,
    Achievement, PlayerAchievement,
    Title, PlayerTitle,
    InventoryItem, Notification
)


def verify_player_model():
    """Verify Player model has all required fields."""
    print("Verifying Player model...")
    
    required_fields = {
        # Primary key
        'id': 'integer',
        
        # Authentication
        'username': 'string',
        'email': 'string',
        'password_hash': 'string',
        
        # Timestamps
        'created_at': 'datetime',
        'last_login': 'datetime',
        
        # Progression
        'level': 'integer',
        'xp': 'integer',
        'rank': 'string',
        'gold': 'integer',
        
        # Stats
        'str_stat': 'integer',
        'int_stat': 'integer',
        'agi_stat': 'integer',
        'vit_stat': 'integer',
        'sen_stat': 'integer',
        'luk_stat': 'integer',
        'hp': 'integer',
        'mp': 'integer',
        
        # Points
        'stat_points': 'integer',
        'skill_points': 'integer',
        
        # Title
        'active_title_id': 'integer',
    }
    
    for field_name in required_fields:
        if hasattr(Player, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    return True


def verify_quest_model():
    """Verify Quest model has all required fields."""
    print("\nVerifying Quest model...")
    
    required_fields = [
        'id', 'player_id', 'quest_type', 'title', 'description',
        'xp_reward', 'gold_reward', 'difficulty', 'status',
        'created_at', 'deadline', 'completed_at', 'parent_quest_id'
    ]
    
    for field_name in required_fields:
        if hasattr(Quest, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    return True


def verify_skill_models():
    """Verify Skill and PlayerSkill models."""
    print("\nVerifying Skill model...")
    
    skill_fields = [
        'id', 'name', 'description', 'skill_type',
        'max_level', 'unlock_level', 'prerequisite_skill_id'
    ]
    
    for field_name in skill_fields:
        if hasattr(Skill, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    print("\nVerifying PlayerSkill model...")
    
    player_skill_fields = [
        'id', 'player_id', 'skill_id', 'current_level', 'unlocked_at'
    ]
    
    for field_name in player_skill_fields:
        if hasattr(PlayerSkill, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    return True


def verify_achievement_models():
    """Verify Achievement and PlayerAchievement models."""
    print("\nVerifying Achievement model...")
    
    achievement_fields = [
        'id', 'name', 'description', 'rarity',
        'condition_type', 'condition_value', 'stat_bonus', 'icon_url'
    ]
    
    for field_name in achievement_fields:
        if hasattr(Achievement, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    print("\nVerifying PlayerAchievement model...")
    
    player_achievement_fields = [
        'id', 'player_id', 'achievement_id', 'unlocked_at'
    ]
    
    for field_name in player_achievement_fields:
        if hasattr(PlayerAchievement, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    return True


def verify_title_models():
    """Verify Title and PlayerTitle models."""
    print("\nVerifying Title model...")
    
    title_fields = [
        'id', 'name', 'description', 'unlock_condition', 'stat_bonuses'
    ]
    
    for field_name in title_fields:
        if hasattr(Title, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    print("\nVerifying PlayerTitle model...")
    
    player_title_fields = [
        'id', 'player_id', 'title_id', 'unlocked_at'
    ]
    
    for field_name in player_title_fields:
        if hasattr(PlayerTitle, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    return True


def verify_inventory_model():
    """Verify InventoryItem model."""
    print("\nVerifying InventoryItem model...")
    
    inventory_fields = [
        'id', 'player_id', 'item_type', 'name', 'content',
        'acquired_at', 'used_at'
    ]
    
    for field_name in inventory_fields:
        if hasattr(InventoryItem, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    return True


def verify_notification_model():
    """Verify Notification model."""
    print("\nVerifying Notification model...")
    
    notification_fields = [
        'id', 'player_id', 'notification_type', 'title', 'message',
        'is_read', 'created_at'
    ]
    
    for field_name in notification_fields:
        if hasattr(Notification, field_name):
            print(f"  ✓ {field_name}")
        else:
            print(f"  ✗ Missing: {field_name}")
    
    return True


def main():
    """Run all schema verifications."""
    print("=" * 60)
    print("ORM Schema Verification")
    print("=" * 60 + "\n")
    
    verify_player_model()
    verify_quest_model()
    verify_skill_models()
    verify_achievement_models()
    verify_title_models()
    verify_inventory_model()
    verify_notification_model()
    
    print("\n" + "=" * 60)
    print("✓ Schema verification complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
