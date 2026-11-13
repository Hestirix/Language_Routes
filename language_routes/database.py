"""Language Routes — Dennis & Neylan, Engineering in Python.

Open SQLite connections and initialize the schema without importing any data.
"""

import argparse
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DATA_DIRECTORY = PROJECT_ROOT / "data" / "raw"
DEFAULT_DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "language_routes.sqlite3"
SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def _database_path(path: str | Path) -> Path:
    """Return an absolute file path; reject paths inside the original data folder.

    Args:
        path: Database filename, relative to the working directory or absolute.
    Returns:
        The resolved database path.
    Raises:
        ValueError: If the destination is inside data/raw.
    """
    resolved = Path(path).expanduser().resolve()
    # Resolve first so '..' and directory links cannot bypass the raw-data guard.
    if resolved.is_relative_to(RAW_DATA_DIRECTORY.resolve()):
        raise ValueError("Database files must be outside data/raw; source data is read-only.")
    return resolved


def connect_database(path: str | Path = DEFAULT_DATABASE_PATH) -> sqlite3.Connection:
    """Open a database file with foreign keys enabled and named result columns.

    Args:
        path: SQLite file location; its parent directory must already exist.
    Returns:
        An open connection owned by the caller; no tables are created here.
    Raises:
        ValueError: For a destination inside data/raw.
        sqlite3.Error: If opening or configuring the connection fails.
    """
    # Explicit legacy mode opens transactions on writes, not on connect. This lets
    # PRAGMA foreign_keys take effect before a transaction is started.
    connection = sqlite3.connect(
        _database_path(path), autocommit=sqlite3.LEGACY_TRANSACTION_CONTROL
    )
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
            raise sqlite3.DatabaseError("SQLite foreign-key enforcement could not be enabled.")
        connection.row_factory = sqlite3.Row
    except BaseException:
        connection.close()
        raise
    return connection


def close_connection(connection: sqlite3.Connection) -> None:
    """Close the supplied connection, discarding uncommitted writes; return None.

    Commit intentionally before calling this function if changes should be saved.
    Closing an already closed sqlite3 connection is safe.
    """
    connection.close()


@contextmanager
def database_connection(
    path: str | Path = DEFAULT_DATABASE_PATH,
) -> Iterator[sqlite3.Connection]:
    """Yield a connection for path, commit on success, roll back on error, and close.

    Args:
        path: Database filename whose parent already exists.
    Yields:
        A configured connection. Exceptions propagate after cleanup.
    """
    connection = connect_database(path)
    try:
        # sqlite3's own context manager handles commit/rollback but does NOT close.
        with connection:
            yield connection
    finally:
        close_connection(connection)


def create_tables(connection: sqlite3.Connection) -> None:
    """Apply the bundled schema atomically to a configured, idle connection.

    Args:
        connection: Connection opened by connect_database with no pending writes.
    Returns:
        None. Existing tables and data are retained; this is not a migration tool.
    Raises:
        ValueError: If a transaction is active or foreign keys are disabled.
        OSError: If the schema cannot be read.
        sqlite3.Error: If SQL fails; schema changes from this call are rolled back.
    """
    # executescript can commit a pending transaction before executing its SQL.
    # Reject that situation rather than unexpectedly committing caller-owned data.
    if connection.in_transaction:
        raise ValueError("Finish the current transaction before creating tables.")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise ValueError("Enable foreign keys before creating tables.")
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    try:
        connection.executescript("BEGIN;\n" + schema + "\nCOMMIT;")
    except BaseException:
        connection.rollback()
        raise


def initialize_database(path: str | Path = DEFAULT_DATABASE_PATH) -> Path:
    """Create parent folders and initialize a database, then close its connection.

    Args:
        path: Output file; defaults to data/processed/language_routes.sqlite3.
    Returns:
        The absolute database path. A new database contains no records.
    Raises:
        ValueError: For a destination inside data/raw.
        OSError or sqlite3.Error: If filesystem access or initialization fails.

    Repeating this function preserves existing tables and rows. It does not erase,
    import, or migrate data. A failed new initialization may leave an empty file.
    """
    destination = _database_path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with database_connection(destination) as connection:
        create_tables(connection)
    return destination


def main() -> None:
    """Read an optional database path from command-line arguments and initialize it.

    Returns None; argparse reports filesystem/database errors and exits nonzero.
    """
    parser = argparse.ArgumentParser(description="Initialize the Language Routes schema; import no data.")
    parser.add_argument(
        "--database", type=Path, default=DEFAULT_DATABASE_PATH,
        help="Output SQLite file (default: project data/processed/language_routes.sqlite3).",
    )
    arguments = parser.parse_args()
    try:
        destination = initialize_database(arguments.database)
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.error(str(error))
    print(f"Schema initialized: {destination}\nNo data imported; existing rows, if any, retained.")


if __name__ == "__main__":
    main()
