"""
Debug test to check tags table creation
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app
from models import Base, Tag
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

def test_tags_table_creation():
    """Test if tags table is created correctly"""
    # Create test database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    
    # Check if tags table exists
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Created tables: {tables}")
    
    assert "tags" in tables
    
    # Check table columns
    columns = inspector.get_columns("tags")
    column_names = [col["name"] for col in columns]
    print(f"Tags table columns: {column_names}")
    
    expected_columns = ["id", "user_id", "name", "color", "version", "created_at", "updated_at"]
    for col in expected_columns:
        assert col in column_names

if __name__ == "__main__":
    test_tags_table_creation()
