import importlib.util
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from utils import database
from utils.captures import populate_tables


class DatabaseConnectionTests(unittest.TestCase):
    def test_populate_tables_uses_the_supplied_connection(self):
        connection = sqlite3.connect(":memory:")

        populate_tables(
            [("20260929", "FL01", "capture.jpg", "C:/captures/capture.jpg")],
            connection,
        )

        captures = connection.execute("SELECT station FROM captures").fetchall()
        self.assertEqual(captures, [("FL01",)])
        connection.close()

    def test_generate_stacks_queries_the_supplied_connection(self):
        script_path = Path(__file__).resolve().parents[1] / "make-stacks.py"
        spec = importlib.util.spec_from_file_location("make_stacks", script_path)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        make_stacks = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(make_stacks)

        connection = sqlite3.connect(":memory:")
        capture_path = "C:/captures/FL01/capture.jpg"
        populate_tables(
            [("20260929", "FL01", "capture.jpg", capture_path)],
            connection,
        )

        with patch.object(make_stacks.captures, "stack") as stack:
            make_stacks.generate_stacks(connection)

        stack.assert_called_once_with(
            [capture_path],
            "{}/stack.jpg".format(os.path.dirname(capture_path)),
        )
        connection.close()

    def test_close_connection_preserves_the_database_file(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "capturas.db"
            with patch.object(database, "DatabaseFile", str(database_path)):
                connection = database.get_connection()
                database.close_connection(connection)

            self.assertTrue(database_path.exists())
            with self.assertRaises(sqlite3.ProgrammingError):
                connection.execute("SELECT 1")


if __name__ == "__main__":
    unittest.main()