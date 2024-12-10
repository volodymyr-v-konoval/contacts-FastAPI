import unittest
from fastapi.testclient import TestClient
from main import app 
from database import get_db, SessionLocal
from models import Base, User, Contact
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class TestAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Налаштовуємо тестову базу
        self.SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
        self.engine = create_engine(self.SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal.configure(bind=self.engine)

        Base.metadata.create_all(bind=self.engine)

    def tearDown(self):
        with self.engine.begin() as conn:
            conn.execute("DROP TABLE IF EXISTS user, contact")
        self.engine.dispose()

    def test_register_user(self):
        response = self.client.post("/register", json={"email": "test@example.com", "password": "password"})
        self.assertEqual(response.status_code, 201)
        self.assertIn("email", response.json())
        self.assertEqual(response.json()["email"], "test@example.com")

    def test_create_contact(self):
        self.client.post("/register", json={"email": "test@example.com", "password": "password"})
        
        login_response = self.client.post("/login", data={"username": "test@example.com", "password": "password"})
        access_token = login_response.json()["access_token"]

        contact_data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "johndoe@example.com",
            "birthday": "1990-01-01"
        }
        
        response = self.client.post(
            "/contacts/",
            json=contact_data,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.json())
        self.assertEqual(response.json()["email"], "johndoe@example.com")

    def test_read_contacts(self):
        self.client.post("/register", json={"email": "test@example.com", "password": "password"})
        
        login_response = self.client.post("/login", data={"username": "test@example.com", "password": "password"})
        access_token = login_response.json()["access_token"]

        self.client.post(
            "/contacts/",
            json={"first_name": "John", "last_name": "Doe", "email": "johndoe@example.com", "birthday": "1990-01-01"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.client.post(
            "/contacts/",
            json={"first_name": "Jane", "last_name": "Doe", "email": "janedoe@example.com", "birthday": "1992-02-02"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = self.client.get("/contacts/", headers={"Authorization": f"Bearer {access_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 2)

    def test_search_contacts(self):
        self.client.post("/register", json={"email": "test@example.com", "password": "password"})
        
        login_response = self.client.post("/login", data={"username": "test@example.com", "password": "password"})
        access_token = login_response.json()["access_token"]

        self.client.post(
            "/contacts/",
            json={"first_name": "John", "last_name": "Doe", "email": "johndoe@example.com", "birthday": "1990-01-01"},
            headers={"Authorization": f"Bearer {access_token}"}
        )
        self.client.post(
            "/contacts/",
            json={"first_name": "Jane", "last_name": "Doe", "email": "janedoe@example.com", "birthday": "1992-02-02"},
            headers={"Authorization": f"Bearer {access_token}"}
        )

        response = self.client.get("/contacts/search/?query=johndoe@example.com", headers={"Authorization": f"Bearer {access_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]["email"], "johndoe@example.com")

    def test_rate_limit(self):
        self.client.post("/register", json={"email": "test@example.com", "password": "password"})
        
        login_response = self.client.post("/login", data={"username": "test@example.com", "password": "password"})
        access_token = login_response.json()["access_token"]

        for _ in range(6):
            response = self.client.post(
                "/contacts/",
                json={"first_name": "John", "last_name": "Doe", "email": f"johndoe{_}@example.com", "birthday": "1990-01-01"},
                headers={"Authorization": f"Bearer {access_token}"}
            )
        self.assertEqual(response.status_code, 429)

if __name__ == "__main__":
    unittest.main()
