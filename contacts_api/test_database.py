import unittest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session
from database import get_db, SessionLocal


class TestDatabaseModule(unittest.TestCase):
    def setUp(self):
        """Set up mock database session."""
        self.mock_session = MagicMock(spec=Session)

    @patch("database.SessionLocal")
    def test_get_db_yields_session(self, mock_session_local):
        """
        Test if get_db correctly yields a database session and closes it afterward.
        """
        mock_session_local.return_value = self.mock_session

        db = next(get_db())
        self.assertEqual(db, self.mock_session)
        
        self.mock_session.close.assert_called_once()

    @patch("database.SessionLocal")
    def test_get_db_closes_session_on_exception(self, mock_session_local):
        """
        Test if get_db correctly closes the database session in case of an exception.
        """
        mock_session_local.return_value = self.mock_session

        generator = get_db()
        try:
            db = next(generator)
            self.assertEqual(db, self.mock_session)
            raise RuntimeError("Simulated exception")
        except RuntimeError as e:
            self.assertEqual(str(e), "Simulated exception")
        finally:
            generator.close()

        self.mock_session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
