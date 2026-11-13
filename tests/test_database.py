"""Language Routes — Dennis & Neylan, Engineering in Python.

Test schema integrity and connection cleanup using temporary, synthetic records.
The fixture labels are test placeholders, not words or linguistic evidence.
"""

import csv
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from language_routes import database


SOURCE_TABLES = (
    "languages", "parameters", "forms", "cognatesets",
    "cognates", "loans", "authors", "clades",
)


@pytest.fixture
def database_path(tmp_path):
    """Use pytest's temporary directory; return a newly initialized database path."""
    return database.initialize_database(tmp_path / "nested" / "test.sqlite3")


@pytest.fixture
def connection(database_path):
    """Yield a temporary database connection and close it after each test."""
    with database.database_connection(database_path) as connection:
        yield connection


@pytest.fixture
def seeded_connection(connection):
    """Return a connection with minimal synthetic rows for constraint tests."""
    connection.execute("INSERT INTO languages (ID) VALUES (?)", ("test-language",))
    connection.execute("INSERT INTO parameters (ID) VALUES (?)", ("test-concept",))
    connection.executemany(
        "INSERT INTO cognatesets (ID) VALUES (?)", [("test-set-a",), ("test-set-b",)]
    )
    connection.execute(
        "INSERT INTO forms (ID, Language_ID, Parameter_ID, Value, Form) VALUES (?, ?, ?, ?, ?)",
        ("test-form", "test-language", "test-concept", "test-placeholder", "test-placeholder"),
    )
    connection.execute(
        "INSERT INTO cognates (ID, Form_ID, Cognateset_ID) VALUES (?, ?, ?)",
        ("test-assignment", "test-form", "test-set-a"),
    )
    connection.execute("INSERT INTO loans (Cognateset_ID) VALUES (?)", ("test-set-a",))
    connection.execute("INSERT INTO authors (ID) VALUES (?)", ("test-author",))
    connection.execute("INSERT INTO clades (ID) VALUES (?)", ("test-clade",))
    connection.commit()
    return connection


def test_initialization_creates_only_expected_empty_tables(connection):
    """Check a fresh schema has nine empty tables and passes SQLite integrity checks."""
    names = {
        row[0] for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    assert names == set(SOURCE_TABLES) | {"dataset_imports"}
    # Table identifiers come from our fixed allowlist, never from user input.
    for table in names:
        assert connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0] == 0
    assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    assert connection.execute("PRAGMA foreign_key_check").fetchall() == []


def test_schema_preserves_all_actual_csv_columns(connection):
    """Read source headers and metadata only; verify no source columns were dropped."""
    raw = database.RAW_DATA_DIRECTORY / "cldf"
    metadata = json.loads((raw / "cldf-metadata.json").read_text(encoding="utf-8"))
    for table in metadata["tables"]:
        table_name = Path(table["url"]).stem
        assert table_name in SOURCE_TABLES
        with (raw / table["url"]).open(encoding="utf-8", newline="") as source:
            columns = next(csv.reader(source))
        assert columns == [column["name"] for column in table["tableSchema"]["columns"]]
        actual = [row["name"] for row in connection.execute(f'PRAGMA table_info("{table_name}")')]
        assert actual == columns


@pytest.mark.parametrize("table", SOURCE_TABLES)
def test_duplicate_primary_keys_are_rejected(seeded_connection, table):
    """Attempt to repeat a synthetic row in each source table; expect rejection."""
    with pytest.raises(sqlite3.IntegrityError):
        seeded_connection.execute(f'INSERT INTO "{table}" SELECT * FROM "{table}" LIMIT 1')


@pytest.mark.parametrize("table", SOURCE_TABLES)
@pytest.mark.parametrize("invalid_key", [None, "", "   "])
def test_missing_primary_keys_are_rejected(seeded_connection, table, invalid_key):
    """Reject NULL and blank source identifiers across all source tables."""
    column = "Cognateset_ID" if table == "loans" else "ID"
    with pytest.raises(sqlite3.IntegrityError):
        seeded_connection.execute(f'UPDATE "{table}" SET "{column}" = ?', (invalid_key,))


@pytest.mark.parametrize(
    "table,column",
    [
        ("forms", "Language_ID"), ("forms", "Parameter_ID"),
        ("cognates", "Form_ID"), ("cognates", "Cognateset_ID"),
        ("loans", "Cognateset_ID"), ("loans", "SourceCognateset_ID"),
    ],
)
def test_all_foreign_keys_reject_unknown_parents(seeded_connection, table, column):
    """Try an unknown referenced ID in each relationship; expect an integrity error."""
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        seeded_connection.execute(f'UPDATE "{table}" SET "{column}" = ?', ("missing-parent",))


def test_referenced_parent_cannot_be_deleted(seeded_connection):
    """Avoid silently deleting forms or assignments when a parent is removed."""
    with pytest.raises(sqlite3.IntegrityError, match="FOREIGN KEY"):
        seeded_connection.execute("DELETE FROM languages WHERE ID = ?", ("test-language",))


@pytest.mark.parametrize(
    "table,column",
    [("forms", "Language_ID"), ("forms", "Parameter_ID"), ("forms", "Value"),
     ("forms", "Form"), ("cognates", "Form_ID"), ("cognates", "Cognateset_ID")],
)
def test_required_fields_reject_null(seeded_connection, table, column):
    """Require a form's essential fields and an assignment's two references."""
    with pytest.raises(sqlite3.IntegrityError):
        seeded_connection.execute(f'UPDATE "{table}" SET "{column}" = NULL')


def test_optional_fields_remain_null(seeded_connection):
    """Accept absent roots, coordinates, booleans, and donor IDs without inventing data."""
    queries = [
        "SELECT Root_Form, Root_Language, Root_Form_calc, Root_Language_calc FROM cognatesets",
        "SELECT Latitude, Longitude, historical FROM languages",
        "SELECT Loan, native_script, Source FROM forms",
        "SELECT SourceCognateset_ID, Parallel_loan_event FROM loans",
    ]
    for query in queries:
        assert all(value is None for row in seeded_connection.execute(query) for value in row)


def test_multiple_memberships_and_alternative_forms_are_allowed(seeded_connection):
    """Allow a second set for one form and another form for the same language/concept."""
    seeded_connection.execute(
        "INSERT INTO cognates (ID, Form_ID, Cognateset_ID) VALUES (?, ?, ?)",
        ("test-assignment-2", "test-form", "test-set-b"),
    )
    seeded_connection.execute(
        "INSERT INTO forms (ID, Language_ID, Parameter_ID, Value, Form) VALUES (?, ?, ?, ?, ?)",
        ("test-form-2", "test-language", "test-concept", "test-alternative", "test-alternative"),
    )
    assert seeded_connection.execute("SELECT COUNT(*) FROM cognates").fetchone()[0] == 2
    assert seeded_connection.execute("SELECT COUNT(*) FROM forms").fetchone()[0] == 2


def test_unicode_ids_and_unconstrained_root_labels_are_preserved(connection):
    """Keep leading zeros and combining marks; root labels need not reference languages."""
    sample = "test-e\u0301-ɑ-Ж-字"
    connection.execute(
        "INSERT INTO cognatesets (ID, Root_Form, Root_Language, supersetid) VALUES (?, ?, ?, ?)",
        ("0001", sample, "test-unlisted-label", "0009"),
    )
    row = connection.execute("SELECT ID, Root_Form, Root_Language, supersetid FROM cognatesets").fetchone()
    assert tuple(row) == ("0001", sample, "test-unlisted-label", "0009")


@pytest.mark.parametrize("column,value", [("Latitude", 91), ("Latitude", -91),
                                          ("Longitude", 181), ("Longitude", -181),
                                          ("Latitude", "not-a-number")])
def test_invalid_coordinates_are_rejected(connection, column, value):
    """Enforce numeric geographic values and valid latitude/longitude ranges."""
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(f'INSERT INTO languages (ID, "{column}") VALUES (?, ?)', ("test", value))


@pytest.mark.parametrize("historical", [0, 1, None])
def test_modern_historical_and_unknown_status_are_allowed(connection, historical):
    """Accept both historical statuses and missing status, including boundary coordinates."""
    connection.execute(
        "INSERT INTO languages (ID, historical, Latitude, Longitude) VALUES (?, ?, ?, ?)",
        ("test", historical, -90, 180),
    )
    assert connection.execute("SELECT historical FROM languages").fetchone()[0] == historical


@pytest.mark.parametrize("table,column", [("languages", "historical"), ("languages", "fossil"),
    ("forms", "Loan"), ("cognates", "Doubt"), ("cognatesets", "Ideophonic"),
    ("cognatesets", "parallelDerivation"), ("loans", "Parallel_loan_event")])
def test_invalid_booleans_are_rejected(seeded_connection, table, column):
    """Prevent numeric values other than zero or one from becoming booleans."""
    with pytest.raises(sqlite3.IntegrityError):
        seeded_connection.execute(f'UPDATE "{table}" SET "{column}" = 2')


def test_provenance_record_requires_hash_and_unique_id(connection):
    """Validate synthetic import bookkeeping without importing any source rows."""
    sql = """INSERT INTO dataset_imports
             (import_id, dataset_title, bibliographic_citation, source_url, license_url, metadata_sha256)
             VALUES (?, ?, ?, ?, ?, ?)"""
    record = (1, "test-dataset", "test-citation", "test-source", "test-license", "a" * 64)
    connection.execute(sql, record)
    assert connection.execute("SELECT imported_at FROM dataset_imports").fetchone()[0].endswith("Z")
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(sql, record)
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(sql, (2, *record[1:-1], "invalid-hash"))


def test_foreign_keys_enabled_on_every_connection(database_path):
    """Reopening a database must enable foreign keys again: the flag is per connection."""
    for _ in range(2):
        with database.database_connection(database_path) as connection:
            assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_context_manager_commits_and_closes(database_path):
    """A successful context saves its writes and releases the connection."""
    with database.database_connection(database_path) as connection:
        connection.execute("INSERT INTO authors (ID) VALUES (?)", ("test-persist",))
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
    with database.database_connection(database_path) as reopened:
        assert reopened.execute("SELECT ID FROM authors").fetchone()[0] == "test-persist"


def test_context_manager_rolls_back_and_closes_on_error(database_path):
    """An exception must discard pending writes, close the connection, and propagate."""
    with pytest.raises(RuntimeError, match="test-failure"):
        with database.database_connection(database_path) as connection:
            connection.execute("INSERT INTO authors (ID) VALUES (?)", ("test-rollback",))
            raise RuntimeError("test-failure")
    with pytest.raises(sqlite3.ProgrammingError):
        connection.execute("SELECT 1")
    with database.database_connection(database_path) as reopened:
        assert reopened.execute("SELECT COUNT(*) FROM authors").fetchone()[0] == 0


def test_explicit_close_discards_pending_writes(database_path):
    """Closing directly must not silently commit; repeated close is safe."""
    connection = database.connect_database(database_path)
    connection.execute("INSERT INTO authors (ID) VALUES (?)", ("test-uncommitted",))
    database.close_connection(connection)
    database.close_connection(connection)
    with database.database_connection(database_path) as reopened:
        assert reopened.execute("SELECT COUNT(*) FROM authors").fetchone()[0] == 0


def test_reinitialization_preserves_data_and_works_from_another_directory(database_path, monkeypatch, tmp_path):
    """Use the schema beside the module and preserve previously committed rows."""
    with database.database_connection(database_path) as connection:
        connection.execute("INSERT INTO authors (ID) VALUES (?)", ("test-preserved",))
    monkeypatch.chdir(tmp_path)
    assert database.initialize_database(database_path) == database_path
    with database.database_connection(database_path) as connection:
        assert connection.execute("SELECT ID FROM authors").fetchone()[0] == "test-preserved"


def test_schema_rejects_pending_transaction_without_committing(connection):
    """Do not let executescript commit writes that belong to its caller."""
    connection.execute("INSERT INTO authors (ID) VALUES (?)", ("test-pending",))
    with pytest.raises(ValueError, match="transaction"):
        database.create_tables(connection)
    assert connection.in_transaction
    connection.rollback()
    assert connection.execute("SELECT COUNT(*) FROM authors").fetchone()[0] == 0


def test_schema_rejects_disabled_foreign_keys(connection):
    """Require the connection's integrity setting before schema initialization."""
    connection.execute("PRAGMA foreign_keys = OFF")
    with pytest.raises(ValueError, match="foreign keys"):
        database.create_tables(connection)


def test_schema_failure_rolls_back_partial_creation(tmp_path, monkeypatch):
    """A malformed temporary schema must leave no partially created tables."""
    broken_schema = tmp_path / "broken.sql"
    broken_schema.write_text("CREATE TABLE partial (ID TEXT); INVALID SQL;", encoding="utf-8")
    monkeypatch.setattr(database, "SCHEMA_PATH", broken_schema)
    with database.database_connection(tmp_path / "failed.sqlite3") as connection:
        with pytest.raises(sqlite3.Error):
            database.create_tables(connection)
        assert not connection.in_transaction
        assert connection.execute("SELECT name FROM sqlite_schema WHERE type = 'table'").fetchall() == []


@pytest.mark.parametrize("operation", [database.connect_database, database.initialize_database])
def test_original_dataset_paths_are_rejected(operation):
    """Reject a source-file destination before opening SQLite or changing files."""
    with pytest.raises(ValueError, match="data/raw"):
        operation(database.RAW_DATA_DIRECTORY / "cldf" / "forms.csv")


def test_cli_initializes_custom_database(tmp_path):
    """Run the documented module command against a temporary output file."""
    destination = tmp_path / "cli.sqlite3"
    result = subprocess.run(
        [sys.executable, "-m", "language_routes.database", "--database", str(destination)],
        cwd=database.PROJECT_ROOT, capture_output=True, text=True, check=True,
    )
    assert "No data imported" in result.stdout
    with database.database_connection(destination) as connection:
        assert connection.execute("SELECT COUNT(*) FROM forms").fetchone()[0] == 0
