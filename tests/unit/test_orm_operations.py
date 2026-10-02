"""
Test basic CRUD operations with SQLAlchemy ORM models.
"""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import (
    Base, engine, SessionLocal,
    Player, Quest, Skill, PlayerSkill,
    Achievement, PlayerAchievement,
    Title, PlayerTitle,
    InventoryItem, Notification
)


def test_create_player():
    """Test creating a player."""
    print("Testing player creation...")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Create a test player
        player = Player(
            username="test_hunter",
            email="test@lifehunter.com",
            password_hash="$2b$12$fakehash",
            level=1,
            xp=0,
            rank="E",
            gold=0,
            str_stat=10,
            int_stat=10,
            agi_stat=10,
            vit_stat=10,
            sen_stat=10,
            luk_stat=10,
            hp=200,
            mp=100,
            stat_points=0,
            skill_points=0
        )
        
        db.add(player)
        db.commit()
        db.refresh(player)
        
        print(f"  ✓ Created player: {player}")
        return player.id
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error creating player: {e}")
        return None
    finally:
        db.close()


def test_create_quest(player_id):
    """Test creating a quest for a player."""
    print("\nTesting quest creation...")
    
    db = SessionLocal()
    
    try:
        quest = Quest(
            player_id=player_id,
            quest_type="daily",
            title="Complete 10 pushups",
            description="Do 10 pushups to build strength",
            xp_reward=50,
            gold_reward=10,
            difficulty="easy",
            status="active"
        )
        
        db.add(quest)
        db.commit()
        db.refresh(quest)
        
        print(f"  ✓ Created quest: {quest}")
        return quest.id
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error creating quest: {e}")
        return None
    finally:
        db.close()


def test_create_skill_and_unlock(player_id):
    """Test creating a skill and unlocking it for a player."""
    print("\nTesting skill creation and unlock...")
    
    db = SessionLocal()
    
    try:
        # Create skill
        skill = Skill(
            name="Time Management",
            description="Increases quest completion speed by 10%",
            skill_type="passive",
            max_level=10,
            unlock_level=5
        )
        
        db.add(skill)
        db.commit()
        db.refresh(skill)
        
        print(f"  ✓ Created skill: {skill}")
        
        # Unlock skill for player
        player_skill = PlayerSkill(
            player_id=player_id,
            skill_id=skill.id,
            current_level=1
        )
        
        db.add(player_skill)
        db.commit()
        db.refresh(player_skill)
        
        print(f"  ✓ Unlocked skill for player: {player_skill}")
        return skill.id
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error with skill operations: {e}")
        return None
    finally:
        db.close()


def test_create_achievement_and_unlock(player_id):
    """Test creating an achievement and unlocking it."""
    print("\nTesting achievement creation and unlock...")
    
    db = SessionLocal()
    
    try:
        # Create achievement
        achievement = Achievement(
            name="First Steps",
            description="Complete your first quest",
            rarity="common",
            condition_type="quest_count",
            condition_value='{"count": 1}',
            stat_bonus='{"xp_bonus": 50}'
        )
        
        db.add(achievement)
        db.commit()
        db.refresh(achievement)
        
        print(f"  ✓ Created achievement: {achievement}")
        
        # Unlock achievement for player
        player_achievement = PlayerAchievement(
            player_id=player_id,
            achievement_id=achievement.id
        )
        
        db.add(player_achievement)
        db.commit()
        db.refresh(player_achievement)
        
        print(f"  ✓ Unlocked achievement for player: {player_achievement}")
        return achievement.id
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error with achievement operations: {e}")
        return None
    finally:
        db.close()


def test_create_title_and_unlock(player_id):
    """Test creating a title and unlocking it."""
    print("\nTesting title creation and unlock...")
    
    db = SessionLocal()
    
    try:
        # Create title
        title = Title(
            name="Novice Hunter",
            description="A beginner on the path of self-improvement",
            unlock_condition="Reach level 5",
            stat_bonuses='{"str_stat": 5, "int_stat": 5}'
        )
        
        db.add(title)
        db.commit()
        db.refresh(title)
        
        print(f"  ✓ Created title: {title}")
        
        # Unlock title for player
        player_title = PlayerTitle(
            player_id=player_id,
            title_id=title.id
        )
        
        db.add(player_title)
        db.commit()
        db.refresh(player_title)
        
        print(f"  ✓ Unlocked title for player: {player_title}")
        return title.id
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error with title operations: {e}")
        return None
    finally:
        db.close()


def test_create_inventory_item(player_id):
    """Test creating an inventory item."""
    print("\nTesting inventory item creation...")
    
    db = SessionLocal()
    
    try:
        item = InventoryItem(
            player_id=player_id,
            item_type="template",
            name="Resume Template - Software Engineer",
            content="Professional software engineer resume template..."
        )
        
        db.add(item)
        db.commit()
        db.refresh(item)
        
        print(f"  ✓ Created inventory item: {item}")
        return item.id
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error creating inventory item: {e}")
        return None
    finally:
        db.close()


def test_create_notification(player_id):
    """Test creating a notification."""
    print("\nTesting notification creation...")
    
    db = SessionLocal()
    
    try:
        notification = Notification(
            player_id=player_id,
            notification_type="quest_complete",
            title="Quest Completed!",
            message="You completed 'Complete 10 pushups' and earned 50 XP!",
            is_read=False
        )
        
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        print(f"  ✓ Created notification: {notification}")
        return notification.id
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error creating notification: {e}")
        return None
    finally:
        db.close()


def test_query_player_with_relationships(player_id):
    """Test querying a player with all relationships."""
    print("\nTesting player query with relationships...")
    
    db = SessionLocal()
    
    try:
        player = db.query(Player).filter(Player.id == player_id).first()
        
        if player:
            print(f"  ✓ Retrieved player: {player.username}")
            print(f"    - Quests: {len(player.quests)}")
            print(f"    - Skills: {len(player.player_skills)}")
            print(f"    - Achievements: {len(player.player_achievements)}")
            print(f"    - Titles: {len(player.player_titles)}")
            print(f"    - Inventory Items: {len(player.inventory_items)}")
            print(f"    - Notifications: {len(player.notifications)}")
            return True
        else:
            print(f"  ✗ Player not found")
            return False
            
    except Exception as e:
        print(f"  ✗ Error querying player: {e}")
        return False
    finally:
        db.close()


def cleanup_test_data():
    """Clean up test data."""
    print("\nCleaning up test data...")
    
    db = SessionLocal()
    
    try:
        # Delete in reverse order of dependencies
        db.query(Notification).delete()
        db.query(InventoryItem).delete()
        db.query(PlayerTitle).delete()
        db.query(Title).delete()
        db.query(PlayerAchievement).delete()
        db.query(Achievement).delete()
        db.query(PlayerSkill).delete()
        db.query(Skill).delete()
        db.query(Quest).delete()
        db.query(Player).delete()
        
        db.commit()
        print("  ✓ Test data cleaned up")
        
    except Exception as e:
        db.rollback()
        print(f"  ✗ Error cleaning up: {e}")
    finally:
        db.close()


def main():
    """Run all ORM operation tests."""
    print("=" * 60)
    print("SQLAlchemy ORM Operations Test")
    print("=" * 60 + "\n")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Run tests
    player_id = test_create_player()
    
    if player_id:
        test_create_quest(player_id)
        test_create_skill_and_unlock(player_id)
        test_create_achievement_and_unlock(player_id)
        test_create_title_and_unlock(player_id)
        test_create_inventory_item(player_id)
        test_create_notification(player_id)
        test_query_player_with_relationships(player_id)
        
        # Clean up
        cleanup_test_data()
    
    print("\n" + "=" * 60)
    print("✓ ORM operations test complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
