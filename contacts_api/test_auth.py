import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from smtplib import SMTPException
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    send_verification_email,
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS
)


class TestAuthModule(unittest.TestCase):
    def setUp(self):
        """Set up initial variables and objects for testing."""
        self.password = "secure_password"
        self.hashed_password = hash_password(self.password)
        self.data = {"sub": "test@example.com"}
        self.email = "test@example.com"
        self.token = create_access_token(self.data)
        self.refresh_token = create_refresh_token(self.data)

    def test_hash_password(self):
        """Test if password hashing works correctly."""
        self.assertTrue(verify_password(self.password, self.hashed_password))

    def test_verify_password(self):
        """Test if password verification works correctly."""
        self.assertFalse(verify_password("wrong_password", self.hashed_password))

    def test_create_access_token(self):
        """Test if access token is generated correctly."""
        decoded_token = jwt.decode(self.token, SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(decoded_token["sub"], self.data["sub"])
        self.assertIn("exp", decoded_token)

    def test_create_refresh_token(self):
        """Test if refresh token is generated correctly."""
        decoded_token = jwt.decode(self.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        self.assertEqual(decoded_token["sub"], self.data["sub"])
        self.assertIn("exp", decoded_token)

    def test_verify_token_valid(self):
        """Test if token verification works for a valid token."""
        payload = verify_token(self.token)
        self.assertEqual(payload["sub"], self.data["sub"])

    def test_verify_token_invalid(self):
        """Test if token verification fails for an invalid token."""
        with self.assertRaises(Exception):
            verify_token("invalid_token")


    @patch("smtplib.SMTP", side_effect=SMTPException("SMTP error"))
    def test_send_verification_email_failure(self, mock_smtp):
        """Test if email verification handles SMTP exceptions."""
        with self.assertRaises(SMTPException):
            send_verification_email(self.email, self.token)


if __name__ == "__main__":
    unittest.main()
