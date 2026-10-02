"""
Root conftest for LifeHunter test suite.

Sets up shared fixtures for integration/ORM tests that need a real SQLite DB.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.models.base import Base
from src.models.player import Player


@pytest.fixture(scope="function")
def test_db():
    """
    Create an in-memory SQLite database with all tables for ORM integration tests.
    Torn down after each test function.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def player_id(test_db):
    """
    Create a test player and return its ID.
    Used by ORM integration tests that need a valid player_id.
    """
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
        skill_points=0,
    )
    test_db.add(player)
    test_db.commit()
    test_db.refresh(player)
    return player.id
