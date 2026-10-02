"""Unit tests for system models (PerformanceLog and DatabaseBackup)."""

import pytest
from datetime import datetime
from src.models import PerformanceLog, DatabaseBackup, Base, engine


@pytest.fixture(scope="function")
def setup_test_db():
    """Create tables before each test and drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestPerformanceLog:
    """Test cases for PerformanceLog model."""
    
    def test_create_performance_log(self, setup_test_db):
        """Test creating a PerformanceLog instance with all required fields."""
        log = PerformanceLog(
            metric_name="response_time",
            metric_value=125.5,
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        assert log.metric_name == "response_time"
        assert log.metric_value == 125.5
        assert log.timestamp == datetime(2024, 1, 15, 10, 30, 0)
    
    def test_performance_log_default_timestamp(self, setup_test_db):
        """Test that PerformanceLog uses current timestamp by default."""
        before = datetime.utcnow()
        log = PerformanceLog(
            metric_name="cpu_usage",
            metric_value=45.2
        )
        after = datetime.utcnow()
        
        assert before <= log.timestamp <= after
    
    def test_performance_log_repr(self, setup_test_db):
        """Test PerformanceLog string representation."""
        log = PerformanceLog(
            id=1,
            metric_name="memory_usage",
            metric_value=78.9,
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        repr_str = repr(log)
        assert "PerformanceLog" in repr_str
        assert "metric='memory_usage'" in repr_str
        assert "value=78.9" in repr_str
    
    def test_performance_log_to_dict(self, setup_test_db):
        """Test PerformanceLog conversion to dictionary."""
        log = PerformanceLog(
            id=1,
            metric_name="disk_io",
            metric_value=500.0,
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        result = log.to_dict()
        
        assert result['id'] == 1
        assert result['metric_name'] == "disk_io"
        assert result['metric_value'] == 500.0
        assert result['timestamp'] == "2024-01-15T10:30:00"
    
    def test_performance_log_negative_value(self, setup_test_db):
        """Test PerformanceLog with negative metric values."""
        log = PerformanceLog(
            metric_name="temperature_delta",
            metric_value=-15.3
        )
        
        assert log.metric_value == -15.3
    
    def test_performance_log_zero_value(self, setup_test_db):
        """Test PerformanceLog with zero metric value."""
        log = PerformanceLog(
            metric_name="error_count",
            metric_value=0.0
        )
        
        assert log.metric_value == 0.0


class TestDatabaseBackup:
    """Test cases for DatabaseBackup model."""
    
    def test_create_database_backup(self, setup_test_db):
        """Test creating a DatabaseBackup instance with all required fields."""
        backup = DatabaseBackup(
            file_path="/backups/db_2024-01-15.sql",
            file_size=1048576,
            created_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        assert backup.file_path == "/backups/db_2024-01-15.sql"
        assert backup.file_size == 1048576
        assert backup.created_at == datetime(2024, 1, 15, 10, 30, 0)
    
    def test_database_backup_default_timestamp(self, setup_test_db):
        """Test that DatabaseBackup uses current timestamp by default."""
        before = datetime.utcnow()
        backup = DatabaseBackup(
            file_path="/backups/db_latest.sql",
            file_size=2097152
        )
        after = datetime.utcnow()
        
        assert before <= backup.created_at <= after
    
    def test_database_backup_repr(self, setup_test_db):
        """Test DatabaseBackup string representation."""
        backup = DatabaseBackup(
            id=1,
            file_path="/backups/db_test.sql",
            file_size=512000,
            created_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        repr_str = repr(backup)
        assert "DatabaseBackup" in repr_str
        assert "file_path='/backups/db_test.sql'" in repr_str
        assert "size=512000" in repr_str
    
    def test_database_backup_to_dict(self, setup_test_db):
        """Test DatabaseBackup conversion to dictionary."""
        backup = DatabaseBackup(
            id=1,
            file_path="/backups/db_prod.sql",
            file_size=3145728,
            created_at=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        result = backup.to_dict()
        
        assert result['id'] == 1
        assert result['file_path'] == "/backups/db_prod.sql"
        assert result['file_size'] == 3145728
        assert result['created_at'] == "2024-01-15T10:30:00"
    
    def test_database_backup_large_file(self, setup_test_db):
        """Test DatabaseBackup with large file size."""
        backup = DatabaseBackup(
            file_path="/backups/db_huge.sql",
            file_size=10737418240  # 10 GB
        )
        
        assert backup.file_size == 10737418240
    
    def test_database_backup_windows_path(self, setup_test_db):
        """Test DatabaseBackup with Windows-style file path."""
        backup = DatabaseBackup(
            file_path="C:\\backups\\db_2024-01-15.sql",
            file_size=1024000
        )
        
        assert backup.file_path == "C:\\backups\\db_2024-01-15.sql"
    
    def test_database_backup_relative_path(self, setup_test_db):
        """Test DatabaseBackup with relative file path."""
        backup = DatabaseBackup(
            file_path="./backups/db_relative.sql",
            file_size=2048000
        )
        
        assert backup.file_path == "./backups/db_relative.sql"
