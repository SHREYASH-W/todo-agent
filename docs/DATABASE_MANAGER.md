# Database Manager Documentation

## Overview

The Database Manager is a core component of the LifeHunter system that provides a robust interface for all database operations. It wraps SQLite database access with features designed for reliability, security, and performance.

## Key Features

### 1. Connection Pooling
- **Maximum Connections**: 10 concurrent connections
- **Connection Timeout**: 30 seconds
- **Automatic Connection Validation**: Stale connections are detected and replaced
- **Efficient Reuse**: Connections are returned to the pool for reuse

### 2. Query Execution
- **Parameterized Queries**: All queries use parameter binding to prevent SQL injection
- **Type Safety**: Results are returned as dictionaries for easy access
- **Automatic Commits**: Transactions are committed automatically
- **Error Handling**: Comprehensive error handling with logging

### 3. Transaction Management
- **ACID Compliance**: All transactions maintain atomicity, consistency, isolation, and durability
- **Automatic Rollback**: Failed transactions are automatically rolled back
- **Multi-Query Support**: Execute multiple related queries as a single atomic operation

### 4. Security
- **Query Validation**: Validates queries for common SQL injection patterns
- **Parameterized Queries**: Enforces use of parameter binding
- **Dangerous Pattern Detection**: Blocks queries with known attack patterns

### 5. Backup Functionality
- **Consistent Backups**: Uses SQLite backup API for consistent snapshots
- **Automatic Logging**: Backup operations are logged to database
- **Flexible Paths**: Support for custom backup locations or auto-generated filenames

### 6. Logging
- **Operation Logging**: All database operations are logged with timing
- **Error Logging**: Detailed error information for debugging
- **Performance Tracking**: Query execution times are recorded

## Installation

The Database Manager is included in the LifeHunter system. No additional installation is required.

## Usage

### Basic Usage

```python
from src.services.database_manager import get_database_manager

# Get singleton instance
db_manager = get_database_manager()

# Execute a SELECT query
players = db_manager.execute_query(
    "SELECT * FROM players WHERE level >= ?",
    (10,)
)

# Execute an INSERT query
result = db_manager.execute_query(
    "INSERT INTO players (username, email, password_hash) VALUES (?, ?, ?)",
    ("newuser", "newuser@example.com", "hashed_password")
)
player_id = result[0]["lastrowid"]

# Execute an UPDATE query
result = db_manager.execute_query(
    "UPDATE players SET xp = xp + ? WHERE id = ?",
    (100, player_id)
)
```

### Transaction Management

```python
# Execute multiple queries atomically
queries = [
    ("UPDATE quests SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?", 
     ("completed", quest_id)),
    ("UPDATE players SET xp = xp + ? WHERE id = ?", 
     (75, player_id)),
    ("INSERT INTO notifications (player_id, message) VALUES (?, ?)", 
     (player_id, "Quest completed! +75 XP"))
]

success = db_manager.execute_transaction(queries)
if success:
    print("Transaction completed successfully")
else:
    print("Transaction failed - all changes rolled back")
```

### Database Backup

```python
# Create backup with auto-generated filename
success = db_manager.backup_database()

# Create backup with custom path
success = db_manager.backup_database("backups/lifehunter_backup_20250124.db")

if success:
    print("Backup created successfully")
```

### Query Validation

```python
# Validate query before execution
safe_query = "SELECT * FROM players WHERE id = ?"
if db_manager.validate_query(safe_query):
    results = db_manager.execute_query(safe_query, (player_id,))

# Unsafe queries are rejected
unsafe_query = "SELECT * FROM players WHERE id = 1; DROP TABLE players"
if not db_manager.validate_query(unsafe_query):
    print("Query rejected - potential SQL injection")
```

### Context Manager

```python
# Automatic resource cleanup
with DatabaseManager("database.db") as db_manager:
    results = db_manager.execute_query("SELECT * FROM players")
    # Process results
# Database connections are automatically closed when context exits
```

### Connection Pool

```python
# Get connection directly from pool (advanced usage)
conn = db_manager.get_connection()

try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players")
    results = cursor.fetchall()
finally:
    # Always return connection to pool
    db_manager.connection_pool.return_connection(conn)
```

## API Reference

### DatabaseManager Class

#### `__init__(database_path: str = "database.db")`
Initialize the Database Manager.

**Parameters:**
- `database_path` (str): Path to SQLite database file

#### `execute_query(query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]`
Execute a parameterized SQL query.

**Parameters:**
- `query` (str): SQL query with ? placeholders
- `params` (Tuple, optional): Parameters to bind to query

**Returns:**
- List[Dict]: Result rows as dictionaries (SELECT queries)
- List[Dict]: Affected rows and lastrowid (INSERT/UPDATE/DELETE queries)

**Raises:**
- `ValueError`: If query validation fails
- `sqlite3.Error`: If query execution fails

#### `execute_transaction(queries: List[Tuple[str, Tuple]]) -> bool`
Execute multiple queries in a transaction.

**Parameters:**
- `queries` (List[Tuple]): List of (query, params) tuples

**Returns:**
- bool: True if transaction succeeded, False otherwise

#### `backup_database(backup_path: Optional[str] = None) -> bool`
Create a database backup.

**Parameters:**
- `backup_path` (str, optional): Path for backup file. Auto-generated if None.

**Returns:**
- bool: True if backup succeeded, False otherwise

#### `validate_query(query: str) -> bool`
Validate query for safety.

**Parameters:**
- `query` (str): SQL query to validate

**Returns:**
- bool: True if query appears safe, False otherwise

#### `get_connection() -> sqlite3.Connection`
Get a connection from the pool.

**Returns:**
- sqlite3.Connection: Database connection

**Note:** Caller must return connection using `connection_pool.return_connection()`

#### `close()`
Close all connections and clean up resources.

### ConnectionPool Class

#### `__init__(database_path: str, max_connections: int = 10, timeout: int = 30)`
Initialize connection pool.

**Parameters:**
- `database_path` (str): Path to SQLite database
- `max_connections` (int): Maximum connections in pool
- `timeout` (int): Connection timeout in seconds

#### `get_connection() -> sqlite3.Connection`
Get a connection from the pool.

**Returns:**
- sqlite3.Connection: Database connection

**Raises:**
- `TimeoutError`: If no connection available within timeout

#### `return_connection(conn: sqlite3.Connection)`
Return a connection to the pool.

**Parameters:**
- `conn` (sqlite3.Connection): Connection to return

#### `close_all()`
Close all connections in the pool.

## Configuration

### Connection Pool Settings

```python
# Default configuration
MAX_CONNECTIONS = 10      # Maximum concurrent connections
CONNECTION_TIMEOUT = 30   # Seconds to wait for available connection
IDLE_TIMEOUT = 300        # Seconds before closing idle connections
```

### Validation Settings

The Database Manager validates queries for the following patterns:
- SQL injection attempts (`' OR '1'='1`, `OR 1=1`, etc.)
- Dangerous operations (`;DROP`, `;DELETE`, `;TRUNCATE`)
- Comment-based attacks (`--`, `/*`, `*/`)
- Command execution attempts (`xp_cmdshell`, `exec(`, `execute(`)

## Best Practices

### 1. Always Use Parameterized Queries

❌ **Bad:**
```python
# Vulnerable to SQL injection
username = user_input
query = f"SELECT * FROM players WHERE username = '{username}'"
results = db_manager.execute_query(query)
```

✅ **Good:**
```python
# Safe with parameter binding
username = user_input
results = db_manager.execute_query(
    "SELECT * FROM players WHERE username = ?",
    (username,)
)
```

### 2. Use Transactions for Related Operations

❌ **Bad:**
```python
# Non-atomic operations
db_manager.execute_query("UPDATE players SET xp = xp + ?", (100,))
db_manager.execute_query("INSERT INTO notifications (message) VALUES (?)", ("XP awarded",))
# If second query fails, first is already committed!
```

✅ **Good:**
```python
# Atomic transaction
queries = [
    ("UPDATE players SET xp = xp + ?", (100,)),
    ("INSERT INTO notifications (message) VALUES (?)", ("XP awarded",))
]
success = db_manager.execute_transaction(queries)
# Both succeed or both fail together
```

### 3. Handle Transaction Failures

```python
success = db_manager.execute_transaction(queries)
if not success:
    # Log error, notify user, or retry
    logger.error("Transaction failed, changes rolled back")
    # Take appropriate recovery action
```

### 4. Use Singleton for Application-Wide Access

```python
# Get singleton instance
db_manager = get_database_manager()

# All parts of application share the same instance and connection pool
```

### 5. Validate Queries from Untrusted Sources

```python
# If query comes from external source, validate first
if db_manager.validate_query(user_provided_query):
    results = db_manager.execute_query(user_provided_query, params)
else:
    raise SecurityError("Invalid query detected")
```

## Performance Considerations

### Connection Pooling Benefits
- **Reduced Overhead**: Connection reuse eliminates connection creation cost
- **Controlled Resources**: Maximum connection limit prevents resource exhaustion
- **Better Throughput**: Multiple concurrent operations can share pool

### Transaction Best Practices
- **Keep Transactions Short**: Long transactions can block other operations
- **Batch Related Operations**: Combine related operations into single transaction
- **Avoid User Input in Transactions**: Don't wait for user input during transaction

### Query Optimization
- **Use Indexes**: Create indexes on frequently queried columns
- **Limit Result Sets**: Use LIMIT clause for large result sets
- **Avoid SELECT ***: Select only needed columns

## Error Handling

### Common Errors

#### Connection Pool Exhausted
```python
try:
    conn = db_manager.get_connection()
except TimeoutError:
    logger.error("Connection pool exhausted - all connections in use")
    # Wait and retry, or scale up max_connections
```

#### Query Validation Failed
```python
try:
    db_manager.execute_query(unsafe_query)
except ValueError as e:
    logger.error(f"Query validation failed: {e}")
    # Query contains dangerous patterns
```

#### Transaction Rollback
```python
success = db_manager.execute_transaction(queries)
if not success:
    logger.error("Transaction failed and was rolled back")
    # All changes were reverted
```

#### Database Locked
```python
try:
    db_manager.execute_query(query, params)
except sqlite3.OperationalError as e:
    if "database is locked" in str(e):
        # Retry with exponential backoff
        time.sleep(0.1)
```

## Testing

The Database Manager includes comprehensive test coverage:

- **Unit Tests**: 30 tests covering all core functionality
- **Integration Tests**: 9 tests with actual database operations
- **Test Coverage**: Query execution, transactions, connection pooling, backups, validation

Run tests with:
```bash
python -m pytest tests/unit/test_database_manager.py -v
python -m pytest tests/unit/test_database_manager_integration.py -v
```

## Migration Notes

### From Direct SQLite Access

If migrating from direct SQLite usage:

**Before:**
```python
import sqlite3
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))
results = cursor.fetchall()
conn.close()
```

**After:**
```python
from src.services.database_manager import get_database_manager
db_manager = get_database_manager()
results = db_manager.execute_query(
    "SELECT * FROM players WHERE id = ?",
    (player_id,)
)
# No need to close - connection is pooled
```

### From SQLAlchemy ORM

Database Manager complements SQLAlchemy ORM. Use ORM for complex models and Database Manager for:
- Performance-critical queries
- Bulk operations
- Complex transactions
- Database administration tasks

## Future Enhancements

Planned features for future releases:
- **MCP SQLite Protocol**: Native integration with MCP SQLite server
- **Read Replicas**: Support for read replica connections
- **Query Caching**: Automatic caching of frequently-used queries
- **Metrics Collection**: Built-in performance metrics and monitoring
- **Async Support**: Async/await interface for concurrent operations

## Support

For issues, questions, or contributions:
- **Documentation**: See `docs/` directory
- **Examples**: See `examples/database_manager_usage.py`
- **Tests**: See `tests/unit/test_database_manager*.py`

## License

Part of the LifeHunter system. See main project LICENSE file.
