"""
Test script to verify SQLAlchemy ORM models can be imported and tables created.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.models import (
    Base, engine, init_db,
    Player, Quest, Skill, PlayerSkill,
    Achievement, PlayerAchievement,
    Title, PlayerTitle,
    InventoryItem, Notification
)


def test_model_imports():
    """Test that all models can be imported successfully."""
    print("Testing model imports...")
    
    models = [
        Player, Quest, Skill, PlayerSkill,
        Achievement, PlayerAchievement,
        Title, PlayerTitle,
        InventoryItem, Notification
    ]
    
    for model in models:
        print(f"  ✓ {model.__name__} imported successfully")
    
    print(f"\nTotal models imported: {len(models)}")
    return True


def test_table_creation():
    """Test that database tables can be created."""
    print("\nTesting table creation...")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        # Get table names
        tables = Base.metadata.tables.keys()
        print(f"  ✓ Created {len(tables)} tables:")
        for table_name in sorted(tables):
            print(f"    - {table_name}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error creating tables: {e}")
        return False


def test_model_relationships():
    """Test that model relationships are properly defined."""
    print("\nTesting model relationships...")
    
    # Test Player relationships
    player_relationships = [
        'quests', 'player_skills', 'player_achievements',
        'player_titles', 'inventory_items', 'notifications'
    ]
    
    for rel_name in player_relationships:
        if hasattr(Player, rel_name):
            print(f"  ✓ Player.{rel_name} relationship defined")
        else:
            print(f"  ✗ Player.{rel_name} relationship missing")
            return False
    
    return True


def main():
    """Run all model tests."""
    print("=" * 60)
    print("SQLAlchemy ORM Models Verification")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Model Imports", test_model_imports()))
    results.append(("Table Creation", test_table_creation()))
    results.append(("Model Relationships", test_model_relationships()))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "PASSED" if passed else "FAILED"
        symbol = "✓" if passed else "✗"
        print(f"{symbol} {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed!")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
